"""
agent/training/tribunal/operations_judge.py
Juez Operativo / VP Supply Chain Magistrate.
Evalúa la viabilidad de la acción comercial recomendada (Notas de Crédito vs Cartas de Reclamación),
la claridad diagnóstica de la causa raíz operativa y la mitigación de riesgo en la relación comercial.
Puntaje máximo de 30 puntos conforme a la rúbrica del tribunal colegiado.
"""

from typing import Any, List, Optional
from data.models import DisputeAnalysisReport
from agent.training.tribunal.models import CriterionScore, JudgeScore


class OperationsJudge:
    """
    Magistrado Operativo del Tribunal Colegiado (VP Supply Chain / COO).
    
    Rúbrica de 30 puntos máximos:
    1. Validez de la acción comercial (12 pts): Nota de Crédito para montos válidos vs Carta de Reclamación para cargos indebidos.
    2. Claridad de causa raíz operativa (10 pts): Diagnóstico preciso del origen físico, contractual o logístico.
    3. Mitigación de riesgo de relación comercial (8 pts): Preservación de la cuenta, regularización y prevención operativa.
    """

    def __init__(self):
        self.judge_name = "Juez Operativo (VP Supply Chain)"
        self.role = "VP Supply Chain / Operations"
        self.max_score = 30.0

    def evaluate_commercial_action(
        self,
        recommended_action: str,
        expected_action: str,
        root_cause: str,
        relationship_risk: str,
    ) -> JudgeScore:
        """
        Audita la viabilidad operativa y comercial de la acción recomendada por el agente.
        """
        criteria: List[CriterionScore] = []
        observations: List[str] = []
        deficiencies: List[str] = []
        directives: List[str] = []

        rec_act_lower = (recommended_action or "").lower()
        exp_act_upper = str(expected_action or "").upper()
        root_cause_clean = (root_cause or "").strip()
        risk_clean = (relationship_risk or "").strip()

        # 1. Validez de la acción comercial (12.0 pts)
        score_1 = 0.0
        has_credit_note = any(w in rec_act_lower for w in ["nota de crédito", "nota de credito", "credit note", "regulariz"])
        has_claim_letter = any(w in rec_act_lower for w in ["carta", "reclam", "rechaz", "cobro", "exig", "disputa", "collection"])

        if "CREDIT_NOTE" in exp_act_upper:
            if has_credit_note:
                score_1 = 12.0
            elif "aceptar" in rec_act_lower:
                score_1 = 8.0
        elif "COLLECTION_LETTER" in exp_act_upper or "FORMAL_CLAIM" in exp_act_upper:
            if has_claim_letter:
                score_1 = 12.0
            elif "rechazar" in rec_act_lower:
                score_1 = 8.0
        elif "MIXED" in exp_act_upper:
            if has_credit_note and has_claim_letter:
                score_1 = 12.0
            elif has_credit_note or has_claim_letter:
                score_1 = 6.0
        else:
            # Si no hay acción estricta, evaluar si propone acción constructiva
            if has_credit_note or has_claim_letter or "conciliar" in rec_act_lower:
                score_1 = 12.0

        passed_1 = (score_1 >= 10.0)
        obs_1 = f"Acción recomendada: '{recommended_action}'. Esperada: '{expected_action}' ({score_1}/12.0 pts)."
        criteria.append(CriterionScore(
            name="1. Validez de la acción comercial",
            score=score_1,
            max_score=12.0,
            passed=passed_1,
            observation=obs_1
        ))
        if not passed_1:
            deficiencies.append(f"Acción comercial inadecuada: se recomendó '{recommended_action}', pero se esperaba '{expected_action}'.")
            directives.append("Emitir Nota de Crédito para deducciones justificadas y Carta de Reclamación para cargos improcedentes.")

        # 2. Claridad diagnóstica de causa raíz operativa (10.0 pts)
        rc_lower = root_cause_clean.lower()
        operational_keywords = [
            "faltante", "avería", "averia", "daño", "danio", "precio", "tarifa", "penaliz",
            "entrega", "remisión", "remision", "muelle", "recepción", "recepcion", "cargo",
            "retención", "retencion", "unidades", "orden de compra", "factura", "sin discrepancias"
        ]
        has_keywords = any(k in rc_lower for k in operational_keywords)
        is_substantive = len(root_cause_clean) >= 15

        if has_keywords and is_substantive:
            score_2 = 10.0
        elif is_substantive or has_keywords:
            score_2 = 5.0
        else:
            score_2 = 0.0

        passed_2 = (score_2 == 10.0)
        obs_2 = f"Causa raíz reportada: '{root_cause_clean}' ({score_2}/10.0 pts)."
        criteria.append(CriterionScore(
            name="2. Claridad diagnóstica de causa raíz",
            score=score_2,
            max_score=10.0,
            passed=passed_2,
            observation=obs_2
        ))
        if not passed_2:
            deficiencies.append("Causa raíz ambigua, incompleta o sin especificidad operativa.")
            directives.append("Describir claramente el origen operativo de la discrepancia (faltante en muelle, avería física, error de catálogo o penalización unilateral).")

        # 3. Preservación de la relación y mitigación de riesgo (8.0 pts)
        risk_lower = (risk_clean + " " + rec_act_lower).lower()
        mitigation_keywords = [
            "bajo", "preserv", "regulariz", "concilia", "acuerdo", "mitig", "auditor",
            "preventiv", "erp", "comercial", "actualizar", "proceso", "cerrar"
        ]
        has_mitigation = any(k in risk_lower for k in mitigation_keywords)
        
        if has_mitigation:
            score_3 = 8.0
        elif len(risk_clean) > 0:
            score_3 = 4.0
        else:
            score_3 = 0.0

        passed_3 = (score_3 >= 7.0)
        obs_3 = f"Mitigación de riesgo y preservación de cuenta: '{risk_clean}' ({score_3}/8.0 pts)."
        criteria.append(CriterionScore(
            name="3. Mitigación de riesgo de relación comercial",
            score=score_3,
            max_score=8.0,
            passed=passed_3,
            observation=obs_3
        ))
        if not passed_3:
            deficiencies.append("Falta de medidas preventivas para preservar la relación comercial o evitar reincidencias.")
            directives.append("Acompañar las acciones comerciales con recomendaciones preventivas (auditar despacho en muelle, actualizar ERP o fijar adenda).")

        total_score = round(score_1 + score_2 + score_3, 2)
        passed_judge = (total_score >= 25.0)  # ~83% de 30.0

        if passed_judge:
            observations.append(f"Evaluación operativa y comercial aprobada con {total_score}/30.0 pts.")
        else:
            observations.append(f"Evaluación operativa reprobada con {total_score}/30.0 pts. Requiere afinar la estrategia comercial.")

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
    ) -> JudgeScore:
        """Audita la acción comercial y causa raíz de un DisputeAnalysisReport."""
        exp_action = getattr(ground_truth, "expected_commercial_action", "CREDIT_NOTE")
        rel_risk = "Bajo, relación comercial preservada mediante regularización documental y conciliación de saldos."

        return self.evaluate_commercial_action(
            recommended_action=report.recommended_action,
            expected_action=exp_action,
            root_cause=report.root_cause,
            relationship_risk=rel_risk,
        )
