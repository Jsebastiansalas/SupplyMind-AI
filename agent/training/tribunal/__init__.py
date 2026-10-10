"""
agent/training/tribunal/__init__.py
Tribunal Colegiado Evaluador (LLM-as-a-Judge) para SupplyMind AI.
Exporta modelos y magistrados para auditoría de disputas comerciales.
"""

from agent.training.tribunal.models import (
    CriterionScore,
    JudgeScore,
    JudgeEvaluation,
    TribunalVerdict,
)
from agent.training.tribunal.cfo_judge import CFOJudge
from agent.training.tribunal.legal_judge import LegalCounselJudge
from agent.training.tribunal.operations_judge import OperationsJudge
from agent.training.tribunal.tribunal import CollegiateTribunal

__all__ = [
    "CriterionScore",
    "JudgeScore",
    "JudgeEvaluation",
    "TribunalVerdict",
    "CFOJudge",
    "LegalCounselJudge",
    "OperationsJudge",
    "CollegiateTribunal",
]
