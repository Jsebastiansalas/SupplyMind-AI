"""
agent/predictive/__init__.py
Módulos de Inteligencia Predictiva, Scoring de Cobranza y Radar Preventivo Pre-Despacho (DVI).
"""

from agent.predictive.models import (
    RecoveryTrack,
    SettlementScenario,
    RecoveryPredictionResult,
)
from agent.predictive.recovery_scorer import RecoveryPredictor
from agent.predictive.leakage_radar import (
    DviRiskFactor,
    DviPredictionResult,
    PreDispatchLeakageRadar,
    HIGH_RISK_DC_PROFILES,
)

__all__ = [
    "RecoveryTrack",
    "SettlementScenario",
    "RecoveryPredictionResult",
    "RecoveryPredictor",
    "DviRiskFactor",
    "DviPredictionResult",
    "PreDispatchLeakageRadar",
    "HIGH_RISK_DC_PROFILES",
]
