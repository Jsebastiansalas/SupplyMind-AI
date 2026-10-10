"""
agent/training/tribunal/tribunal.py
Tribunal Evaluador Colegiado (LLM-as-a-Judge) de SupplyMind AI.
Orquesta los 3 magistrados independientes:
1. Juez Financiero / CFO (40 pts)
2. Juez Jurídico Contractual (30 pts)
3. Juez Operativo / VP Supply Chain (30 pts)
Puntaje total: 100 puntos. Umbral de maestría: total_score >= 90.0 pts.
"""

from datetime import datetime, timezone
from typing import Any, List, Optional, Union
from data.models import DisputeAnalysisReport, CommercialContract
from agent.training.tribunal.models import JudgeScore, TribunalVerdict
from agent.training.tribunal.cfo_judge import CFOJudge
from agent.training.tribunal.legal_judge import LegalCounselJudge
from agent.training.tribunal.operations_judge import OperationsJudge


class CollegiateTribunal:
    """
    Tribunal Colegiado de Evaluación y Calibración para SupplyMind AI.
    Sintetiza los veredictos de los 3 jueces y determina la consecución de maestría.
    """

    def __init__(self):
        self.cfo_judge = CFOJudge()
        self.legal_judge = LegalCounselJudge()
        self.operations_judge = OperationsJudge()
        self.mastery_threshold = 90.0

    def aggregate_evaluations(
        self,
        case_id: str,
        cfo_score: Union[float, int, JudgeScore],
        legal_score: Union[float, int, JudgeScore],
        operations_score: Union[float, int, JudgeScore],
        observations: Optional[List[str]] = None,
        deficiencies: Optional[List[str]] = None,
        calibration_directives: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> TribunalVerdict:
        """
        Agrega las calificaciones de los tres magistrados en un TribunalVerdict formal.
        """
        # Normalizar cfo_evaluation
        if isinstance(cfo_score, JudgeScore):
            cfo_eval = cfo_score
        else:
            cfo_val = float(cfo_score)
            cfo_eval = JudgeScore(
                judge_name="Juez Financiero (CFO)",
                role="Chief Financial Officer",
                score=cfo_val,
                max_score=40.0,
                passed=(cfo_val >= 36.0),
                summary_verdict="APROBADO" if cfo_val >= 36.0 else "REPROBADO",
            )

        # Normalizar legal_evaluation
        if isinstance(legal_score, JudgeScore):
            legal_eval = legal_score
        else:
            legal_val = float(legal_score)
            legal_eval = JudgeScore(
                judge_name="Juez Jurídico Contractual",
                role="Legal Counsel",
                score=legal_val,
                max_score=30.0,
                passed=(legal_val >= 27.0),
                summary_verdict="APROBADO" if legal_val >= 27.0 else "REPROBADO",
            )

        # Normalizar operations_evaluation
        if isinstance(operations_score, JudgeScore):
            ops_eval = operations_score
        else:
            ops_val = float(operations_score)
            ops_eval = JudgeScore(
                judge_name="Juez Operativo (VP Supply Chain)",
                role="VP Supply Chain / Operations",
                score=ops_val,
                max_score=30.0,
                passed=(ops_val >= 25.0),
                summary_verdict="APROBADO" if ops_val >= 25.0 else "REPROBADO",
            )

        total = round(float(cfo_eval.score + legal_eval.score + ops_eval.score), 2)
        passed = (total >= self.mastery_threshold)

        # Consolidar observaciones y deficiencias
        combined_obs: List[str] = list(observations or [])
        combined_obs.extend(cfo_eval.observations)
        combined_obs.extend(legal_eval.observations)
        combined_obs.extend(ops_eval.observations)

        combined_def: List[str] = list(deficiencies or [])
        combined_def.extend(cfo_eval.deficiencies)
        combined_def.extend(legal_eval.deficiencies)
        combined_def.extend(ops_eval.deficiencies)

        combined_dir: List[str] = list(calibration_directives or [])
        combined_dir.extend(cfo_eval.directives)
        combined_dir.extend(legal_eval.directives)
        combined_dir.extend(ops_eval.directives)

        # Eliminar duplicados manteniendo orden
        seen_def = set()
        clean_def = [d for d in combined_def if not (d in seen_def or seen_def.add(d))]
        seen_dir = set()
        clean_dir = [d for d in combined_dir if not (d in seen_dir or seen_dir.add(d))]

        ts = datetime.now(timezone.utc).isoformat()
        verdict_id = f"VERDICT-{case_id}-{int(datetime.now().timestamp())}"

        return TribunalVerdict(
            verdict_id=verdict_id,
            case_id=case_id,
            timestamp=ts,
            total_score=total,
            max_score=100.0,
            passed_mastery=passed,
            mastery_threshold=self.mastery_threshold,
            cfo_evaluation=cfo_eval,
            legal_evaluation=legal_eval,
            operations_evaluation=ops_eval,
            observations=combined_obs,
            deficiencies=clean_def,
            calibration_directives=clean_dir,
            precedent_summary=clean_dir[0] if clean_dir else None,
        )

    def evaluate_case(
        self,
        report: DisputeAnalysisReport,
        ground_truth: Any,
        contract: Optional[CommercialContract] = None,
    ) -> TribunalVerdict:
        """
        Ejecuta la auditoría integral convocando a los tres magistrados sobre el reporte emitido.
        """
        cfo_score = self.cfo_judge.evaluate_report(report, ground_truth)
        legal_score = self.legal_judge.evaluate_report(report, ground_truth, contract=contract)
        operations_score = self.operations_judge.evaluate_report(report, ground_truth)

        case_id = getattr(report, "case_id", getattr(ground_truth, "case_id", "CASE-DISPUTE"))

        return self.aggregate_evaluations(
            case_id=case_id,
            cfo_score=cfo_score,
            legal_score=legal_score,
            operations_score=operations_score,
        )
