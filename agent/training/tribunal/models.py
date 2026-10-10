"""
agent/training/tribunal/models.py
Pydantic models for the Collegiate Evaluator Tribunal (LLM-as-a-Judge).
Defines structured evaluation schemas for CFO, Legal, and Operations judges,
as well as the aggregated TribunalVerdict with a mastery threshold of >= 90.0 points.
"""

from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, ConfigDict, Field, model_validator


class CriterionScore(BaseModel):
    """Calificación y desglose de un criterio específico de evaluación."""
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    name: str
    score: float
    max_score: float
    passed: bool = True
    observation: str = ""


class JudgeScore(BaseModel):
    """Dictamen y puntaje de un magistrado individual."""
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    judge_name: str
    role: str = ""
    score: float
    max_score: float
    passed: bool = True
    criteria_breakdown: List[CriterionScore] = Field(default_factory=list)
    summary_verdict: str = ""
    observations: List[str] = Field(default_factory=list)
    deficiencies: List[str] = Field(default_factory=list)
    directives: List[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def populate_passed_flag(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "passed" not in data and "score" in data and "max_score" in data:
                max_sc = float(data.get("max_score", 1.0))
                sc = float(data.get("score", 0.0))
                # Consider passed if score >= 80% of max_score
                data["passed"] = sc >= (max_sc * 0.8)
            if "observations" not in data and "observation" in data:
                obs = data.get("observation")
                data["observations"] = [obs] if isinstance(obs, str) else list(obs)
            if "deficiencies" not in data and "deficiency" in data:
                defic = data.get("deficiency")
                data["deficiencies"] = [defic] if isinstance(defic, str) else list(defic)
        return data


class JudgeEvaluation(JudgeScore):
    """Alias / subclase de compatibilidad para JudgeScore."""
    pass


class TribunalVerdict(BaseModel):
    """
    Veredicto Colegiado emitido por el Tribunal de 3 Magistrados (CFO, Legal, Operaciones).
    Puntaje total sobre 100 puntos. Umbral de maestría >= 90.0 puntos.
    """
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    verdict_id: str = ""
    case_id: str
    timestamp: str = ""
    total_score: float
    max_score: float = 100.0
    passed_mastery: bool = False
    mastery_threshold: float = 90.0

    cfo_evaluation: JudgeScore
    legal_evaluation: JudgeScore
    operations_evaluation: JudgeScore

    observations: List[str] = Field(default_factory=list)
    deficiencies: List[str] = Field(default_factory=list)
    calibration_directives: List[str] = Field(default_factory=list)
    precedent_summary: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def normalize_verdict_data(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        # Mapeos de compatibilidad entre nomenclaturas
        if "cfo_judge" in data and "cfo_evaluation" not in data:
            data["cfo_evaluation"] = data["cfo_judge"]
        if "legal_judge" in data and "legal_evaluation" not in data:
            data["legal_evaluation"] = data["legal_judge"]
        if "supply_chain_judge" in data and "operations_evaluation" not in data:
            data["operations_evaluation"] = data["supply_chain_judge"]
        if "deficiencies_identified" in data and "deficiencies" not in data:
            data["deficiencies"] = data["deficiencies_identified"]

        tot = data.get("total_score")
        thresh = float(data.get("mastery_threshold", 90.0))
        if tot is not None and "passed_mastery" not in data:
            data["passed_mastery"] = float(tot) >= thresh

        return data

    @property
    def cfo_judge(self) -> JudgeScore:
        return self.cfo_evaluation

    @property
    def legal_judge(self) -> JudgeScore:
        return self.legal_evaluation

    @property
    def supply_chain_judge(self) -> JudgeScore:
        return self.operations_evaluation

    @property
    def deficiencies_identified(self) -> List[str]:
        return self.deficiencies
