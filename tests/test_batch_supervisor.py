"""
tests/test_batch_supervisor.py
Suite de pruebas para el Supervisor y Monitor de Salud de la Corrida Desatendida de 12 Horas.

Valida:
1. Inspección de salud con estado NOT_STARTED cuando no hay latido previo.
2. Detección precisa de estado HEALTHY cuando el latido y proceso están vigentes.
3. Detección de estado STALLED cuando el latido excede el umbral de tolerancia.
4. Identificación de estado COMPLETED cuando el lote alcanza el 100% de tareas.
5. Extracción no invasiva de las últimas N tareas registradas en el stream JSONL.
6. Registro atómico de eventos de supervisión en bitácora dedicada.
"""

from datetime import datetime, timezone, timedelta
import json
import os
from pathlib import Path
import pytest

from tools.batch_processor.batch_supervisor import (
    BatchSupervisor,
    SupervisorHealthSnapshot,
)


def test_supervisor_inspect_health_not_started(tmp_path):
    """Verifica que el supervisor reporte NOT_STARTED si no existe archivo de latido."""
    supervisor = BatchSupervisor(reports_dir=tmp_path)
    snapshot = supervisor.inspect_health()

    assert isinstance(snapshot, SupervisorHealthSnapshot)
    assert snapshot.status == "NOT_STARTED"
    assert snapshot.is_pid_alive is False
    assert snapshot.completed_count == 0
    assert snapshot.progress_percentage == 0.0


def test_supervisor_inspect_health_healthy(tmp_path):
    """Verifica la detección de estado HEALTHY con PID actual y latido reciente."""
    supervisor = BatchSupervisor(reports_dir=tmp_path, stall_threshold_seconds=60.0)

    # Simular latido activo escrito hace 2 segundos por el proceso actual
    current_pid = os.getpid()
    recent_ts = datetime.now(timezone.utc).isoformat()
    heartbeat_data = {
        "timestamp": recent_ts,
        "pid": current_pid,
        "status": "RUNNING",
        "current_unit_index": 250,
        "total_units": 1024,
        "current_task_id": "work_unit_0250",
        "completed_count": 250,
        "total_cost_usd": 2.8350,
        "success_count": 242,
        "quarantine_count": 8,
        "failed_count": 0,
    }
    with open(supervisor.heartbeat_path, "w", encoding="utf-8") as f:
        json.dump(heartbeat_data, f)

    snapshot = supervisor.inspect_health()

    assert snapshot.status == "HEALTHY"
    assert snapshot.is_pid_alive is True
    assert snapshot.pid == current_pid
    assert snapshot.completed_count == 250
    assert snapshot.current_unit == 250
    assert snapshot.total_units == 1024
    assert snapshot.progress_percentage > 24.0
    assert snapshot.total_cost_usd == 2.8350
    assert snapshot.seconds_since_last_heartbeat < 10.0
    assert snapshot.projected_eta_iso is not None


def test_supervisor_inspect_health_stalled(tmp_path):
    """Verifica la detección de estado STALLED cuando el latido es viejo pero el PID existe."""
    supervisor = BatchSupervisor(reports_dir=tmp_path, stall_threshold_seconds=60.0)

    # Simular latido viejo de hace 10 minutos
    old_ts = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()
    heartbeat_data = {
        "timestamp": old_ts,
        "pid": os.getpid(),
        "status": "RUNNING",
        "current_unit_index": 100,
        "total_units": 1024,
        "completed_count": 100,
        "total_cost_usd": 1.1340,
        "success_count": 98,
        "quarantine_count": 2,
        "failed_count": 0,
    }
    with open(supervisor.heartbeat_path, "w", encoding="utf-8") as f:
        json.dump(heartbeat_data, f)

    snapshot = supervisor.inspect_health()

    assert snapshot.status == "STALLED"
    assert snapshot.is_pid_alive is True
    assert snapshot.seconds_since_last_heartbeat >= 590.0


def test_supervisor_inspect_health_completed(tmp_path):
    """Verifica la detección de estado COMPLETED al finalizar las 1,024 unidades."""
    supervisor = BatchSupervisor(reports_dir=tmp_path)

    heartbeat_data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "pid": os.getpid(),
        "status": "COMPLETED",
        "current_unit_index": 1024,
        "total_units": 1024,
        "completed_count": 1024,
        "total_cost_usd": 11.6020,
        "success_count": 993,
        "quarantine_count": 31,
        "failed_count": 0,
    }
    with open(supervisor.heartbeat_path, "w", encoding="utf-8") as f:
        json.dump(heartbeat_data, f)

    snapshot = supervisor.inspect_health()

    assert snapshot.status == "COMPLETED"
    assert snapshot.completed_count == 1024
    assert snapshot.progress_percentage == 100.0


def test_supervisor_recent_tasks_from_stream(tmp_path):
    """Valida la lectura no invasiva de las últimas N tareas del stream JSONL."""
    supervisor = BatchSupervisor(reports_dir=tmp_path)

    # Escribir 7 registros sintéticos en el stream
    sample_records = [
        {"unit_index": i, "task_id": f"work_unit_{i:04d}", "retailer_name": "Walmart", "disputed_amount": 1000.0, "status": "SUCCESS", "cost_usd": 0.01}
        for i in range(1, 8)
    ]
    with open(supervisor.stream_path, "w", encoding="utf-8") as f:
        for r in sample_records:
            f.write(json.dumps(r) + "\n")

    recent = supervisor.get_recent_tasks_from_stream(limit=3)

    assert len(recent) == 3
    assert recent[0]["unit_index"] == 5
    assert recent[1]["unit_index"] == 6
    assert recent[2]["unit_index"] == 7


def test_supervisor_log_event(tmp_path):
    """Valida el registro atómico de eventos de supervisión."""
    supervisor = BatchSupervisor(reports_dir=tmp_path)
    supervisor.log_supervisor_event("TEST_PING", {"details": "Verificación de latido"})

    assert supervisor.supervisor_log_path.exists()
    lines = supervisor.supervisor_log_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    data = json.loads(lines[0])
    assert data["event_type"] == "TEST_PING"
    assert data["details"]["details"] == "Verificación de latido"
