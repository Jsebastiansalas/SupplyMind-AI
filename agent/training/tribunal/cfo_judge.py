"""
agent/training/tribunal/cfo_judge.py
Juez Financiero / Chief Financial Officer (CFO).
Evalúa la exactitud cuantitativa de los saldos, retenciones y deducciones
con un puntaje máximo de 40 puntos conforme a la rúbrica colegiada.
Garantiza cero alucinación numérica y precisión contable con Decimal.
"""

from decimal import Decimal
from typing import Any, List, Optional
from data.models import DisputeAnalysisReport
from agent.training.tribunal.models import CriterionScore, JudgeScore


class CFOJudge:
    """
    Magistrado Financiero del Tribunal Colegiado.
    
    Rúbrica de 40 puntos máximos:
    1. Exactitud de facturado y recibido (10 pts): 5 pts facturado, 5 pts recibido.
    2. Coincidencia de diferencia neta (10 pts): received - billed vs ground truth.
    3. Desglose justificado vs reclamable (15 pts): 8 pts justificado, 7 pts reclamable.
    4. Precisión Decimal y aritmética (5 pts): 2.5 pts tipos Decimal, 2.5 pts balance aritmético.
    """

    def __init__(self):
        self.judge_name = "Juez Financiero (CFO)"
        self.role = "Chief Financial Officer"
        self.max_score = 40.0

    def evaluate_amounts(
        self,
        reported_billed: Decimal,
        reported_received: Decimal,
        reported_justified: Decimal,
        reported_claimable: Decimal,
        gt_billed: Decimal,
        gt_received: Decimal,
        gt_justified: Decimal,
        gt_claimable: Decimal,
    ) -> JudgeScore:
        """
        Audita los montos cuantitativos reportados por el agente contra el Ground Truth.
        """
        criteria: List[CriterionScore] = []
        observations: List[str] = []
        deficiencies: List[str] = []
        directives: List[str] = []

        # 1. Exactitud de facturado y recibido (10.0 pts)
        billed_match = (reported_billed == gt_billed)
        received_match = (reported_received == gt_received)
        score_1 = (5.0 if billed_match else 0.0) + (5.0 if received_match else 0.0)
        passed_1 = (score_1 == 10.0)
        obs_1 = (
            f"Facturado: reportado ${reported_billed:,.2f} vs GT ${gt_billed:,.2f} ({'OK' if billed_match else 'ERROR'}). "
            f"Recibido: reportado ${reported_received:,.2f} vs GT ${gt_received:,.2f} ({'OK' if received_match else 'ERROR'})."
        )
        criteria.append(CriterionScore(
            name="1. Exactitud facturado y recibido",
            score=score_1,
            max_score=10.0,
            passed=passed_1,
            observation=obs_1
        ))
        if not passed_1:
            deficiencies.append(f"Discrepancia en importes base: facturado {reported_billed}!=GT {gt_billed} o recibido {reported_received}!=GT {gt_received}.")
            directives.append("Alinear los totales base de factura y pago con el comprobante bancario exacto.")

        # 2. Coincidencia de diferencia neta (10.0 pts)
        rep_net = reported_received - reported_billed
        gt_net = gt_received - gt_billed
        diff_match = (rep_net == gt_net)
        score_2 = 10.0 if diff_match else 0.0
        passed_2 = diff_match
        obs_2 = f"Diferencia neta reportada: ${rep_net:,.2f} vs GT ${gt_net:,.2f}."
        criteria.append(CriterionScore(
            name="2. Coincidencia de diferencia neta",
            score=score_2,
            max_score=10.0,
            passed=passed_2,
            observation=obs_2
        ))
        if not passed_2:
            deficiencies.append(f"Diferencia neta errónea: {rep_net} != GT {gt_net}.")
            directives.append("Verificar la fórmula contable: received_amount - billed_amount.")

        # 3. Desglose justificado vs reclamable (15.0 pts)
        justified_match = (reported_justified == gt_justified)
        claimable_match = (reported_claimable == gt_claimable)
        score_3 = (8.0 if justified_match else 0.0) + (7.0 if claimable_match else 0.0)
        passed_3 = (score_3 == 15.0)
        obs_3 = (
            f"Justificado: ${reported_justified:,.2f} vs GT ${gt_justified:,.2f} ({'OK' if justified_match else 'ERROR'}). "
            f"Reclamable: ${reported_claimable:,.2f} vs GT ${gt_claimable:,.2f} ({'OK' if claimable_match else 'ERROR'})."
        )
        criteria.append(CriterionScore(
            name="3. Desglose justificado vs reclamable",
            score=score_3,
            max_score=15.0,
            passed=passed_3,
            observation=obs_3
        ))
        if not passed_3:
            deficiencies.append(f"Desglose incorrecto: justificado {reported_justified}!=GT {gt_justified} o reclamable {reported_claimable}!=GT {gt_claimable}.")
            directives.append(f"Calibrar regla de clasificación: monto justificado debe ser ${gt_justified:,.2f} y reclamable ${gt_claimable:,.2f}.")

        # 4. Precisión Decimal y aritmética (5.0 pts)
        is_decimal = isinstance(reported_billed, Decimal) and isinstance(reported_received, Decimal)
        arithmetic_ok = (reported_justified + reported_claimable == abs(rep_net))
        score_4 = (2.5 if is_decimal else 0.0) + (2.5 if arithmetic_ok else 0.0)
        passed_4 = (score_4 == 5.0)
        obs_4 = (
            f"Precisión Decimal: {'Conforme' if is_decimal else 'No Decimal'}. "
            f"Balance aritmético (justificado + reclamable == abs(diff)): {'Conforme' if arithmetic_ok else 'Descuadrado'}."
        )
        criteria.append(CriterionScore(
            name="4. Precisión Decimal y aritmética",
            score=score_4,
            max_score=5.0,
            passed=passed_4,
            observation=obs_4
        ))
        if not passed_4:
            deficiencies.append("Inconsistencia aritmética o uso indebido de tipos de punto flotante.")
            directives.append("Utilizar estrictamente objetos Decimal de Python y asegurar justificado + reclamable == abs(diferencia).")

        total_score = round(score_1 + score_2 + score_3 + score_4, 2)
        passed_judge = (total_score >= 36.0)  # 90% de 40.0

        if passed_judge:
            observations.append(f"Auditoría cuantitativa aprobada por el CFO con {total_score}/40.0 pts. Cero alucinación financiera.")
        else:
            observations.append(f"Auditoría cuantitativa reprobada por el CFO con {total_score}/40.0 pts. Requiere corrección contable.")

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
        """Evalúa un DisputeAnalysisReport contra el estándar GroundTruth."""
        gt_b = getattr(ground_truth, "billed_amount", Decimal("0.00"))
        gt_r = getattr(ground_truth, "received_amount", Decimal("0.00"))
        gt_j = getattr(ground_truth, "expected_justified_amount", Decimal("0.00"))
        gt_c = getattr(ground_truth, "expected_claimable_amount", Decimal("0.00"))

        return self.evaluate_amounts(
            reported_billed=report.billed_amount,
            reported_received=report.received_amount,
            reported_justified=report.justified_amount,
            reported_claimable=report.claimable_amount,
            gt_billed=gt_b,
            gt_received=gt_r,
            gt_justified=gt_j,
            gt_claimable=gt_c,
        )
