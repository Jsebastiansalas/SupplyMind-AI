"""
agent/predictive/recovery_scorer.py
Motor Predictivo de Cobro & Simulación de Concesiones (Pilar 4).

Estima la probabilidad matemática de cobro (0.0% a 100.0%), determina la
ruta operativa óptima (Portal B2B, Concesión Estructurada o Vía Coactiva NIF C-3)
y simula escenarios de negociación considerando el dictamen del debate dialéctico
y los perfiles históricos de la Red de Memoria.
"""

from decimal import Decimal
from typing import Dict, Any, List, Optional

from agent.predictive.models import (
    RecoveryTrack,
    SettlementScenario,
    RecoveryPredictionResult
)
from agent.courtroom.models import AdversarialVerdict
from agent.memory.precedent_graph import RetailerPrecedentProfile
from data.models import DisputeAnalysisReport


class RecoveryPredictor:
    """Motor algorítmico de puntuación predictiva y simulación de cobranza."""

    @classmethod
    def calculate_prediction(
        cls,
        report: DisputeAnalysisReport,
        docs: Optional[Dict[str, Any]] = None,
        adversarial_verdict: Optional[AdversarialVerdict] = None,
        retailer_profile: Optional[RetailerPrecedentProfile] = None
    ) -> RecoveryPredictionResult:
        """
        Calcula la probabilidad predictiva de cobro y genera escenarios de resolución.
        """
        docs = docs or {}
        inv = docs.get("invoice")
        deliv = docs.get("delivery")
        pay = docs.get("payment")
        ctr = docs.get("contract")

        claimable = report.claimable_amount
        justified = report.justified_amount

        positive_drivers: List[str] = []
        risk_drivers: List[str] = []

        # 1. Puntuación Base
        score = 50.0

        # 2. Respaldo Documental Físico en Muelle
        if deliv:
            if getattr(deliv, "signed", False):
                score += 20.0
                positive_drivers.append("Remisión de entrega debidamente firmada en muelle receptor (+20%)")
            else:
                score -= 20.0
                risk_drivers.append("Remisión de entrega carece de firma o sello legible (-20%)")

            if getattr(deliv, "discrepancy_reported", False):
                if justified > Decimal("0.00"):
                    score += 10.0
                    positive_drivers.append("Discrepancia física allanada con sello formal de muelle (+10%)")
        else:
            score -= 25.0
            risk_drivers.append("Ausencia de remisión de entrega documental (-25%)")

        # 3. Soporte Contractual Bilateral
        if ctr and getattr(ctr, "clauses", None):
            score += 15.0
            positive_drivers.append("Contrato marco comercial vigente con cláusulas de prevalencia (+15%)")
        else:
            score -= 15.0
            risk_drivers.append("Relación comercial sin contrato formal suscrito (-15%)")

        # 4. Historial y Perfil de Precedentes en la Red de Memoria
        if retailer_profile:
            if retailer_profile.overall_success_rate_pct >= 80.0:
                score += 12.0
                positive_drivers.append(
                    f"Historial altamente favorable con {retailer_profile.retailer_name} "
                    f"({retailer_profile.overall_success_rate_pct}% de éxito histórico) (+12%)"
                )
            elif retailer_profile.overall_success_rate_pct >= 60.0:
                score += 6.0
                positive_drivers.append(
                    f"Antecedentes moderados con {retailer_profile.retailer_name} (+6%)"
                )
            if retailer_profile.cases_won > 0:
                score += 5.0
                positive_drivers.append("Existen precedentes ganados al 100% con este cliente corporativo (+5%)")

        # 5. Ponderación del Debate Dialéctico (Adversarial Courtroom)
        if adversarial_verdict:
            prob_force = adversarial_verdict.probative_force_supplier_pct
            if prob_force >= 85.0:
                score += 10.0
                positive_drivers.append(f"Dictamen judicial favorable con fuerza probatoria del {prob_force}% (+10%)")
            elif prob_force < 60.0:
                score -= 15.0
                risk_drivers.append(f"Vulnerabilidades dialécticas detectadas por el Fiscal Forense (-15%)")

        # Normalizar score entre 5.0% y 98.5%
        probability = max(5.0, min(98.5, round(score, 1)))

        # Clasificación por Grado y Ruta Recomendada
        if probability >= 85.0:
            grade = "ALTA_CERTEZA"
            track = RecoveryTrack.FAST_TRACK_B2B_PORTAL
            est_days = 10
            scenario_rec_idx = 0
        elif probability >= 55.0:
            grade = "MODERADA"
            track = RecoveryTrack.STRUCTURED_CONCESSION_SETTLEMENT
            est_days = 20
            scenario_rec_idx = 1
        else:
            grade = "RIESGO_ELEVADO"
            track = RecoveryTrack.LEGAL_ESCALATION_NIF_C3
            est_days = 45
            scenario_rec_idx = 2

        # 6. Simulación de Escenarios Financieros
        # Escenario 1: Cobro Íntegro Inmediato
        s1 = SettlementScenario(
            scenario_name="Ruta Rápida — Cobro Íntegro en Portal B2B",
            description="Reclamación directa del 100% del saldo insoluto con base documental plena.",
            projected_recovery_amount=claimable,
            concession_granted_amount=Decimal("0.00"),
            recovery_rate_pct=100.0,
            estimated_days_to_cash=10,
            legal_risk_level="BAJO",
            recommended=(scenario_rec_idx == 0)
        )

        # Escenario 2: Concesión Estructurada de Cierre Ágil
        discount_15 = (claimable * Decimal("0.15")).quantize(Decimal("0.01"))
        net_85 = claimable - discount_15
        s2 = SettlementScenario(
            scenario_name="Acuerdo Estructurado — Concesión Comercial del 15%",
            description="Oferta de descuento por pronto pago/relación para cierre garantizado en menos de 7 días.",
            projected_recovery_amount=net_85,
            concession_granted_amount=discount_15,
            recovery_rate_pct=85.0,
            estimated_days_to_cash=5,
            legal_risk_level="BAJO",
            recommended=(scenario_rec_idx == 1)
        )

        # Escenario 3: Cobranza Corporativa NIF C-3
        s3 = SettlementScenario(
            scenario_name="Escalamiento Legal — Póliza Contable NIF C-3",
            description="Exigencia formal y cobro coactivo con causación de intereses moratorios comerciales.",
            projected_recovery_amount=claimable,
            concession_granted_amount=Decimal("0.00"),
            recovery_rate_pct=100.0,
            estimated_days_to_cash=45,
            legal_risk_level="MEDIO",
            recommended=(scenario_rec_idx == 2)
        )

        scenarios = [s1, s2, s3]
        expected_net = (claimable * Decimal(str(probability / 100.0))).quantize(Decimal("0.01"))

        exec_summary = (
            f"El expediente presenta una probabilidad de recuperación del {probability:.1f}% ({grade}). "
            f"Se proyecta recuperar un valor neto ponderado de ${expected_net:,.2f} USD "
            f"dentro de un plazo estimado de {est_days} días naturales vía '{track.value}'."
        )

        return RecoveryPredictionResult(
            case_id=report.case_id,
            recovery_probability_pct=probability,
            confidence_grade=grade,
            recommended_track=track,
            target_claimable_amount=claimable,
            expected_net_recovery_usd=expected_net,
            estimated_days_to_cash=est_days,
            positive_drivers=positive_drivers,
            risk_drivers=risk_drivers,
            scenarios=scenarios,
            executive_summary=exec_summary
        )
