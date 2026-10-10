"""
agent/training/tribunal/legal_judge.py
Juez Jurídico Contractual / Legal Counsel Magistrate.
Audita la aplicación de la jerarquía probatoria (Nivel 1 POD firmado vs contrato),
la cita exacta de cláusulas contractuales y la invalidez de penalizaciones unilaterales.
Puntaje máximo de 30 puntos conforme a la rúbrica del tribunal colegiado.
"""

import re
from typing import Any, List, Optional
from data.models import DisputeAnalysisReport, CommercialContract
from agent.training.tribunal.models import CriterionScore, JudgeScore


def _normalize_clause(clause_id: str) -> str:
    """Normaliza identificadores de cláusula para comparación robusta (ej. 'CLAUSE-4.2' -> '4.2')."""
    if not clause_id:
        return ""
    c = clause_id.strip().upper()
    c = re.sub(r"^(?:CLAUSE|CLÁUSULA|CLAUSULA)[-\s]*", "", c)
    return c


class LegalCounselJudge:
    """
    Magistrado Jurídico del Tribunal Colegiado.
    
    Rúbrica de 30 puntos máximos:
    1. Jerarquía probatoria (10 pts): Nivel 1 (remisión firmada / prueba plena) vs aserciones sin firma.
    2. Cita de cláusulas contractuales (10 pts): Cita de cláusulas aplicables exactas.
    3. Invalidez de penalizaciones unilaterales (10 pts): Rechazo y reclamo de cargos sin adenda.
    """

    def __init__(self):
        self.judge_name = "Juez Jurídico Contractual"
        self.role = "Legal Counsel"
        self.max_score = 30.0

    def evaluate_legal_rigor(
        self,
        cited_clauses: List[str],
        required_clauses: List[str],
        is_signed_pod: bool,
        rejection_of_unilateral_penalty: bool,
    ) -> JudgeScore:
        """
        Audita el rigor probatorio, la correspondencia contractual y el rechazo de penalizaciones unilaterales.
        """
        criteria: List[CriterionScore] = []
        observations: List[str] = []
        deficiencies: List[str] = []
        directives: List[str] = []

        # 1. Jerarquía probatoria (10.0 pts)
        score_1 = 10.0 if is_signed_pod else 0.0
        passed_1 = (score_1 == 10.0)
        obs_1 = (
            "Jerarquía probatoria respetada: remisión firmada con valor pleno (Nivel 1)."
            if is_signed_pod
            else "Falta de rigor probatorio: se admitió deducción sin remisión firmada o se vulneró la jerarquía de evidencia."
        )
        criteria.append(CriterionScore(
            name="1. Jerarquía probatoria",
            score=score_1,
            max_score=10.0,
            passed=passed_1,
            observation=obs_1
        ))
        if not passed_1:
            deficiencies.append("Infracción a la jerarquía probatoria: falta de Prueba Plena (remisión firmada) en sustento de deducción.")
            directives.append("Aplicar la Regla de Oro: toda deducción física debe estar respaldada por remisión firmada en muelle (Nivel 1).")

        # 2. Cita exacta de cláusulas contractuales (10.0 pts)
        if not required_clauses:
            score_2 = 10.0
            passed_2 = True
            obs_2 = "No se requirieron cláusulas específicas para este caso."
        else:
            normalized_cited = {_normalize_clause(c) for c in cited_clauses if c}
            matched_clauses = [
                req for req in required_clauses
                if _normalize_clause(req) in normalized_cited
            ]
            fraction = len(matched_clauses) / len(required_clauses)
            score_2 = round(10.0 * fraction, 2)
            passed_2 = (score_2 == 10.0)
            missing = [req for req in required_clauses if _normalize_clause(req) not in normalized_cited]
            obs_2 = (
                f"Cláusulas requeridas: {required_clauses}. Citadas: {cited_clauses}. "
                f"Coincidencias: {matched_clauses} ({score_2}/10.0 pts)."
            )
            if missing:
                deficiencies.append(f"Cláusulas obligatorias omitidas o no citadas: {missing}.")
                directives.append(f"Citar expresamente las cláusulas contractuales aplicables: {missing}.")

        criteria.append(CriterionScore(
            name="2. Citas de cláusulas contractuales",
            score=score_2,
            max_score=10.0,
            passed=passed_2,
            observation=obs_2
        ))

        # 3. Rechazo de penalizaciones unilaterales (10.0 pts)
        score_3 = 10.0 if rejection_of_unilateral_penalty else 0.0
        passed_3 = (score_3 == 10.0)
        obs_3 = (
            "Penalizaciones unilaterales o extemporáneas debidamente invalidadas y reclamadas."
            if rejection_of_unilateral_penalty
            else "Se convalidó indebidamente una penalización unilateral o un cobro extemporáneo sin adenda."
        )
        criteria.append(CriterionScore(
            name="3. Rechazo de penalizaciones unilaterales",
            score=score_3,
            max_score=10.0,
            passed=passed_3,
            observation=obs_3
        ))
        if not passed_3:
            deficiencies.append("Concesión de retención arbitraria: no se impugnó el cargo unilateral o extemporáneo.")
            directives.append("Rechazar penalizaciones de clientes que carezcan de adenda contractual bilateral (Cláusula 7.3).")

        total_score = round(score_1 + score_2 + score_3, 2)
        passed_judge = (total_score >= 27.0)  # 90% de 30.0

        if passed_judge:
            observations.append(f"Auditoría legal contractual aprobada con {total_score}/30.0 pts.")
        else:
            observations.append(f"Auditoría legal contractual reprobada con {total_score}/30.0 pts. Requiere subsanar omisiones normativas.")

        return JudgeScore(
            judge_name=self.judge_name,
            role=self.role,
            score=total_score,
            max_score=self.max_score,
            passed=passed_judge,
            criteria_breakdown=criteria,
            summary_verdict="APROBADO" if passed_judge else "REPROBADO",
            observations=observations,
            deficiencies=deficiencies,
            directives=directives,
        )

    def evaluate_report(
        self,
        report: DisputeAnalysisReport,
        ground_truth: Any,
        contract: Optional[CommercialContract] = None,
    ) -> JudgeScore:
        """Audita un DisputeAnalysisReport analizando citas de evidencia y cláusulas."""
        evidence_text = " ".join(report.evidence) + " " + report.root_cause + " " + report.recommended_action
        
        # Extraer cláusulas citadas en el texto del reporte
        raw_clauses = re.findall(r"(?:CLAUSE|CLÁUSULA|CLAUSULA)?[-\s]*(\d+\.\d+)", evidence_text, re.IGNORECASE)
        named_clauses = re.findall(r"\bCLAUSE-[\w\.]+\b", evidence_text, re.IGNORECASE)
        all_cited = list(set(raw_clauses + named_clauses))

        required_clauses = list(getattr(ground_truth, "required_clause_citations", []))

        # Determinar si la jerarquía probatoria fue respetada
        category = getattr(ground_truth, "category", "")
        cat_str = str(category).upper()

        # Si el ground truth requería rechazar por falta de POD firmado
        if "UNSIGNED" in cat_str or "UNPROVEN" in cat_str:
            is_signed_pod = (report.claimable_amount > 0 and report.justified_amount == 0)
        else:
            # Caso con POD firmado o caso estándar
            is_signed_pod = True

        # Determinar rechazo de penalización unilateral
        if "UNILATERAL_PENALTY" in cat_str or "EXTEMPORANEOUS" in cat_str:
            rejection_of_unilateral = (
                report.claimable_amount > 0 and
                any(w in report.recommended_action.lower() for w in ["reclam", "rechaz", "carta", "cobro", "exig"])
            )
        else:
            rejection_of_unilateral = True

        return self.evaluate_legal_rigor(
            cited_clauses=all_cited,
            required_clauses=required_clauses,
            is_signed_pod=is_signed_pod,
            rejection_of_unilateral_penalty=rejection_of_unilateral,
        )
