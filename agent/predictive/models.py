"""
agent/predictive/models.py
Modelos de Datos para el Motor Predictivo de Cobro & Simulación de Concesiones (Pilar 4).
"""

from decimal import Decimal
from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, ConfigDict, Field


class RecoveryTrack(str, Enum):
    FAST_TRACK_B2B_PORTAL = "FAST_TRACK_B2B_PORTAL"
    STRUCTURED_CONCESSION_SETTLEMENT = "STRUCTURED_CONCESSION_SETTLEMENT"
    LEGAL_ESCALATION_NIF_C3 = "LEGAL_ESCALATION_NIF_C3"


class SettlementScenario(BaseModel):
    """Escenario de negociación o cobro simulado."""
    model_config = ConfigDict(extra="allow")

    scenario_name: str
    description: str
    projected_recovery_amount: Decimal
    concession_granted_amount: Decimal
    recovery_rate_pct: float
    estimated_days_to_cash: int
    legal_risk_level: str  # "BAJO" | "MEDIO" | "ALTO"
    recommended: bool = False


class RecoveryPredictionResult(BaseModel):
    """Resultado del modelo predictivo de recuperabilidad de cartera comercial."""
    model_config = ConfigDict(extra="allow")

    case_id: str
    recovery_probability_pct: float = Field(ge=0.0, le=100.0)
    confidence_grade: str  # "ALTA_CERTEZA" | "MODERADA" | "RIESGO_ELEVADO"
    recommended_track: RecoveryTrack
    target_claimable_amount: Decimal
    expected_net_recovery_usd: Decimal
    estimated_days_to_cash: int
    positive_drivers: List[str] = Field(default_factory=list)
    risk_drivers: List[str] = Field(default_factory=list)
    scenarios: List[SettlementScenario] = Field(default_factory=list)
    executive_summary: str
