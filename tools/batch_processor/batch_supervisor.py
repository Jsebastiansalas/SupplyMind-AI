"""
tools/batch_processor/batch_supervisor.py
Módulo de Supervisión, Monitoreo en Tiempo Real y Tolerancia a Fallos para Procesamiento Desatendido.

Proporciona:
1. Inspección no invasiva del latido (heartbeat) y estado de salud del proceso.
2. Detección automática de procesos estancados o caídos (proceso huérfano / timeout).
3. Mecanismo de auto-recuperación y relanzamiento con reanudación atómica (--resume).
4. Telemetría de rendimiento en vivo: velocidad de procesamiento, ETA, costo acumulado y tasa de éxito.
5. Bitácora de auditoría del supervisor en streaming JSONL.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Any, Dict, List, Optional


@dataclass
class SupervisorHealthSnapshot:
    """Instantánea de salud y estado operativo del lote desatendido."""
    status: str  # "HEALTHY" | "STALLED" | "PROCESS_TERMINATED" | "COMPLETED" | "NOT_STARTED"
    is_pid_alive: bool
    pid: Optional[int]
    last_heartbeat_timestamp: Optional[str]
    seconds_since_last_heartbeat: float
    current_unit: int
    total_units: int
    completed_count: int
    progress_percentage: float
    total_cost_usd: float
    success_count: int
    quarantine_count: int
    failed_count: int
    projected_eta_iso: Optional[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class BatchSupervisor:
    """
    Supervisor autónomo de contingencia para la jornada de 12 horas.
    Supervisa el orquestador sin acoplamiento invasivo leyendo el latido y stream JSONL.
    """

    def __init__(
        self,
        reports_dir: Optional[Path] = None,
        stall_threshold_seconds: float = 300.0,  # 5 minutos sin latido = alerta
        python_executable: Optional[str] = None,
    ):
        self.workspace_root = Path(__file__).resolve().parent.parent.parent
        self.reports_dir = reports_dir or (self.workspace_root / "reports")
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        self.heartbeat_path = self.reports_dir / "unattended_batch_heartbeat.json"
        self.stream_path = self.reports_dir / "unattended_batch_execution_stream.jsonl"
        self.supervisor_log_path = self.reports_dir / "unattended_batch_supervisor_log.jsonl"
        self.stall_threshold_seconds = stall_threshold_seconds
        self.python_executable = python_executable or sys.executable

    @staticmethod
    def is_process_running(pid: int) -> bool:
        """Verifica de forma multiplataforma si un PID sigue activo."""
        if pid <= 0:
            return False
        if sys.platform == "win32":
            try:
                import ctypes
                kernel32 = ctypes.windll.kernel32
                SYNCHRONIZE = 0x00100000
                process = kernel32.OpenProcess(SYNCHRONIZE, False, pid)
                if process != 0:
                    kernel32.CloseHandle(process)
                    return True
                return False
            except Exception:
                # Fallback con tasklist
                try:
                    out = subprocess.check_output(
                        ["tasklist", "/fi", f"PID eq {pid}", "/fo", "csv", "/nh"],
                        stderr=subprocess.DEVNULL,
                        text=True,
                    )
                    return str(pid) in out
                except Exception:
                    return False
        else:
            try:
                os.kill(pid, 0)
                return True
            except (OSError, ProcessLookupError):
                return False

    def log_supervisor_event(self, event_type: str, details: Dict[str, Any]) -> None:
        """Registra un evento de supervisión atómicamente."""
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "details": details,
        }
        with open(self.supervisor_log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
            f.flush()

    def inspect_health(self) -> SupervisorHealthSnapshot:
        """Examina el latido y estado del proceso de la corrida desatendida."""
        now = datetime.now(timezone.utc)

        if not self.heartbeat_path.exists():
            return SupervisorHealthSnapshot(
                status="NOT_STARTED",
                is_pid_alive=False,
                pid=None,
                last_heartbeat_timestamp=None,
                seconds_since_last_heartbeat=999999.0,
                current_unit=0,
                total_units=1024,
                completed_count=0,
                progress_percentage=0.0,
                total_cost_usd=0.0,
                success_count=0,
                quarantine_count=0,
                failed_count=0,
                projected_eta_iso=None,
            )

        try:
            with open(self.heartbeat_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            return SupervisorHealthSnapshot(
                status="NOT_STARTED",
                is_pid_alive=False,
                pid=None,
                last_heartbeat_timestamp=None,
                seconds_since_last_heartbeat=999999.0,
                current_unit=0,
                total_units=1024,
                completed_count=0,
                progress_percentage=0.0,
                total_cost_usd=0.0,
                success_count=0,
                quarantine_count=0,
                failed_count=0,
                projected_eta_iso=None,
            )

        hb_time_str = data.get("timestamp")
        hb_pid = data.get("pid")
        hb_status = data.get("status", "UNKNOWN")
        curr_unit = data.get("current_unit_index", 0)
        tot_units = max(1, data.get("total_units", 1024))
        done_cnt = data.get("completed_count", 0)
        tot_cost = float(data.get("total_cost_usd", 0.0))
        succ_cnt = data.get("success_count", 0)
        quar_cnt = data.get("quarantine_count", 0)
        fail_cnt = data.get("failed_count", 0)

        seconds_since_hb = 0.0
        if hb_time_str:
            try:
                hb_dt = datetime.fromisoformat(hb_time_str)
                if hb_dt.tzinfo is None:
                    hb_dt = hb_dt.replace(tzinfo=timezone.utc)
                seconds_since_hb = max(0.0, (now - hb_dt).total_seconds())
            except Exception:
                seconds_since_hb = 0.0

        is_alive = self.is_process_running(hb_pid) if hb_pid else False

        # Evaluación de estado
        if hb_status == "COMPLETED" or curr_unit >= tot_units:
            overall_status = "COMPLETED"
        elif not is_alive:
            overall_status = "PROCESS_TERMINATED"
        elif seconds_since_hb > self.stall_threshold_seconds:
            overall_status = "STALLED"
        else:
            overall_status = "HEALTHY"

        pct = (done_cnt / tot_units) * 100.0

        # Cálculo aproximado de ETA
        projected_eta = None
        if done_cnt > 0 and done_cnt < tot_units and seconds_since_hb < self.stall_threshold_seconds:
            # Asumiendo ritmo de ~42s por unidad restante
            rem_units = tot_units - done_cnt
            rem_sec = rem_units * 42.18
            eta_dt = datetime.fromtimestamp(time.time() + rem_sec, tz=timezone.utc)
            projected_eta = eta_dt.strftime("%Y-%m-%d %H:%M:%S UTC")

        return SupervisorHealthSnapshot(
            status=overall_status,
            is_pid_alive=is_alive,
            pid=hb_pid,
            last_heartbeat_timestamp=hb_time_str,
            seconds_since_last_heartbeat=round(seconds_since_hb, 1),
            current_unit=curr_unit,
            total_units=tot_units,
            completed_count=done_cnt,
            progress_percentage=round(pct, 2),
            total_cost_usd=round(tot_cost, 4),
            success_count=succ_cnt,
            quarantine_count=quar_cnt,
            failed_count=fail_cnt,
            projected_eta_iso=projected_eta,
        )

    def trigger_batch_auto_recovery(self) -> subprocess.Popen:
        """
        Relanza de forma desatendida el orquestador con la bandera --resume
        cuando se detecta una caída de proceso o congelamiento prolongado.
        """
        launcher_script = self.workspace_root / "scripts" / "run_unattended_12h_batch.py"

        cmd = [
            self.python_executable,
            str(launcher_script),
            "--resume",
        ]

        self.log_supervisor_event(
            event_type="AUTO_RECOVERY_TRIGGERED",
            details={
                "command": " ".join(cmd),
                "reason": "Process terminated abnormally or stalled without heartbeat.",
            },
        )

        # Lanzar proceso en segundo plano de forma independiente
        if sys.platform == "win32":
            creationflags = subprocess.CREATE_NEW_PROCESS_GROUP
            proc = subprocess.Popen(cmd, creationflags=creationflags)
        else:
            proc = subprocess.Popen(cmd, start_new_session=True)

        return proc

    def get_recent_tasks_from_stream(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Lee las últimas N tareas registradas en el stream JSONL."""
        if not self.stream_path.exists():
            return []

        lines: List[str] = []
        try:
            with open(self.stream_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        lines.append(line)
        except Exception:
            return []

        recent: List[Dict[str, Any]] = []
        for line in lines[-limit:]:
            try:
                recent.append(json.loads(line))
            except Exception:
                continue
        return recent
