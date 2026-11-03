"""
agent/core/case_ledger.py
Fuente Única de Verdad (Single Source of Truth) para las cifras de cada expediente.

Todos los motores periféricos (SLA Watchdog, Optimizador de Cartera, Chat, Portal RPA,
Visión, ERP) deben consumir `CaseLedger.get(case_id)` en lugar de recalcular montos o
leer `ground_truth.json`.

Regla de oro: `ground_truth.json` es la hoja de respuestas del benchmark y JAMÁS debe
ser leída por código de producción.

Orden de resolución:
  1. Caché en memoria del proceso.
  2. Reporte canónico persistido `reports/dispute_report_<case_id>.json`.
  3. Ejecución determinística `SkynetRunner(fast_path=True)`.
"""

from __future__ import annotations

import json
import threading
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
REPORTS_DIR = ROOT_DIR / "reports"

QUARANTINE_MARKERS = ("PROTOCOLO FORENSE ACTIVADO", "CUARENTENA")


class CanonicalCase(BaseModel):
    """Cifras canónicas e inmutables de un expediente."""
    case_id: str
    currency: str = "USD"
    billed_amount: Decimal = Decimal("0.00")
    received_amount: Decimal = Decimal("0.00")
    difference: Decimal = Decimal("0.00")
    justified_amount: Decimal = Decimal("0.00")
    claimable_amount: Decimal = Decimal("0.00")
    root_cause: str = ""
    is_quarantined: bool = False
    source: str = Field(default="unknown", description="memory | persisted_report | skynet_runner | unavailable")

    @property
    def is_actionable(self) -> bool:
        """Un caso es accionable (cobro, ERP, aviso) solo si no está en cuarentena y hay monto."""
        return (not self.is_quarantined) and self.claimable_amount > Decimal("0.00")


def is_report_quarantined(report: Any) -> bool:
    """Criterio único de cuarentena, idéntico al usado por el benchmark Crucible."""
    def _get(obj: Any, key: str) -> Any:
        return obj.get(key) if isinstance(obj, dict) else getattr(obj, key, None)

    action = str(_get(report, "recommended_action") or "")
    if any(m in action for m in QUARANTINE_MARKERS):
        return True
    if _get(report, "quarantine_docket"):
        return True
    health = _get(report, "health_audit")
    if health is not None and _get(health, "status") == "QUARANTINE":
        return True
    return False


def _dec(value: Any) -> Decimal:
    try:
        return Decimal(str(value if value is not None else "0.00")).quantize(Decimal("0.01"))
    except Exception:
        return Decimal("0.00")


class CaseLedger:
    """Registro canónico de cifras por expediente (thread-safe, con caché en memoria)."""

    _cache: Dict[str, CanonicalCase] = {}
    _lock = threading.Lock()

    @classmethod
    def from_report(cls, report: Any, source: str = "memory") -> CanonicalCase:
        def _get(key: str) -> Any:
            return report.get(key) if isinstance(report, dict) else getattr(report, key, None)

        quarantined = is_report_quarantined(report)
        return CanonicalCase(
            case_id=str(_get("case_id") or ""),
            currency=str(_get("currency") or "USD"),
            billed_amount=_dec(_get("billed_amount")),
            received_amount=_dec(_get("received_amount")),
            difference=_dec(_get("difference")),
            # En cuarentena no existe monto justificado ni reclamable confiable.
            justified_amount=Decimal("0.00") if quarantined else _dec(_get("justified_amount")),
            claimable_amount=Decimal("0.00") if quarantined else _dec(_get("claimable_amount")),
            root_cause=str(_get("root_cause") or ""),
            is_quarantined=quarantined,
            source=source,
        )

    @classmethod
    def register(cls, report: Any) -> CanonicalCase:
        """Registra/actualiza el reporte canónico recién producido por el pipeline."""
        canon = cls.from_report(report, source="memory")
        if canon.case_id:
            with cls._lock:
                cls._cache[canon.case_id] = canon
        return canon

    @classmethod
    def invalidate(cls, case_id: Optional[str] = None) -> None:
        with cls._lock:
            if case_id is None:
                cls._cache.clear()
            else:
                cls._cache.pop(case_id, None)

    @classmethod
    def _load_persisted(cls, case_id: str) -> Optional[CanonicalCase]:
        path = REPORTS_DIR / f"dispute_report_{case_id}.json"
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            # Un reporte con concesiones aplicadas ya no es la línea base determinística;
            # se recalcula desde el pipeline para no heredar estado de negociación.
            if data.get("concessions"):
                return None
            data.setdefault("case_id", case_id)
            return cls.from_report(data, source="persisted_report")
        except Exception:
            return None

    @classmethod
    def _run_pipeline(cls, case_id: str) -> Optional[CanonicalCase]:
        try:
            from agent.core.skynet_runner import SkynetRunner
            report = SkynetRunner(case_id=case_id, fast_path=True, use_cache=True).run()
            if report is None:
                return None
            canon = cls.from_report(report, source="skynet_runner")
            if not canon.case_id:
                canon.case_id = case_id
            return canon
        except Exception:
            return None

    @classmethod
    def get(cls, case_id: str, refresh: bool = False) -> CanonicalCase:
        """Devuelve las cifras canónicas del caso. Nunca lee ground_truth.json."""
        if not refresh:
            with cls._lock:
                cached = cls._cache.get(case_id)
            if cached is not None:
                return cached

        canon = None if refresh else cls._load_persisted(case_id)
        if canon is None:
            canon = cls._run_pipeline(case_id)
        if canon is None:
            canon = CanonicalCase(case_id=case_id, source="unavailable")
        else:
            with cls._lock:
                cls._cache[case_id] = canon
        return canon
