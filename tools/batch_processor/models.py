"""
tools/batch_processor/models.py
Modelos de Datos para el Procesador Batch Masivo Desatendido (Semana 4 - Sprint 4.2).
"""

from decimal import Decimal
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, ConfigDict, Field


class BatchCaseResult(BaseModel):
    """Resultado individual de un expediente auditado en el lote batch."""
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    case_id: str
    status: str = "SUCCESS"  # "SUCCESS" | "QUARANTINED" | "FAILED"
    billed_amount: Decimal = Field(default=Decimal("0.00"))
    received_amount: Decimal = Field(default=Decimal("0.00"))
    difference: Decimal = Field(default=Decimal("0.00"))
    justified_amount: Decimal = Field(default=Decimal("0.00"))
    claimable_amount: Decimal = Field(default=Decimal("0.00"))
    recovery_probability_pct: float = Field(default=0.0, ge=0.0, le=100.0)
    execution_time_ms: float = 0.0
    error_message: Optional[str] = None
    quarantine_reason: Optional[str] = None


class BatchExecutionSummary(BaseModel):
    """Resumen consolidado y métricas macroeconómicas de la cartera auditada en lote."""
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    batch_id: str
    timestamp: str
    total_cases_submitted: int
    total_cases_processed: int
    successful_cases: int
    quarantined_cases: int
    failed_cases: int
    total_volume_billed_usd: Decimal = Field(default=Decimal("0.00"))
    total_volume_received_usd: Decimal = Field(default=Decimal("0.00"))
    total_volume_disputed_usd: Decimal = Field(default=Decimal("0.00"))
    total_volume_justified_usd: Decimal = Field(default=Decimal("0.00"))
    total_volume_claimable_usd: Decimal = Field(default=Decimal("0.00"))
    average_recovery_probability_pct: float = Field(default=0.0, ge=0.0, le=100.0)
    arithmetic_error_rate_pct: float = Field(default=0.0)
    mean_absolute_error_usd: Decimal = Field(default=Decimal("0.00"))
    total_execution_time_seconds: float = 0.0
    avg_latency_per_case_ms: float = 0.0
    throughput_cases_per_second: float = 0.0
    results: List[BatchCaseResult] = Field(default_factory=list)
