"""
agent/core/adversarial_critic.py
Subagente Crítico Adversarial Reflexivo ("Abogado del Diablo" B2B).
Frontera 1 de Superinteligencia (Sprint 5.2).

Somete el dictamen de conciliación a un escrutinio hostil simulando ser el Director Legal
y Auditor del Retailer (Walmart, Amazon, Chedraui, etc.), detectando vacíos probatorios,
ambigüedades contractuales o plazos de prescripción antes de que el expediente sea emitido.
Si detecta debilidades, ejecuta el auto-refuerzo dialéctico incorporando blindaje jurídico.
"""

from decimal import Decimal
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from data.models import DisputeAnalysisReport
from agent.legal.cross_border_treaties import CrossBorderTreatiesEngine, CrossBorderEvaluationResult


class AdversarialVulnerability(BaseModel):
    """Representación de una vulnerabilidad jurídica o probatoria detectada."""
    category: str  # PROOF_INTEGRITY, CONTRACT_AMBIGUITY, STATUTORY_TIMEBAR, EDI_PROOF, TAX_CONSISTENCY
    severity: str  # HIGH, MEDIUM, LOW
    critic_argument: str  # La objeción que formulará el retailer
    rebuttal_strategy: str  # La contra-defensa jurídica preventiva recomendada


class AdversarialCritiqueResult(BaseModel):
    """Resultado del examen de auto-crítica adversarial."""
    case_id: str
    robustness_score: float = Field(..., ge=0.0, le=100.0)
    passed: bool
    vulnerabilities_detected: List[AdversarialVulnerability] = Field(default_factory=list)
    counter_arguments: List[str] = Field(default_factory=list)
    hardening_recommendations: List[str] = Field(default_factory=list)
    cross_border_assessment: Optional[CrossBorderEvaluationResult] = None
    preemptive_legal_shield: List[str] = Field(default_factory=list)
    audit_trail: List[str] = Field(default_factory=list)


class AdversarialCritic:
    """
    Subagente Crítico que actúa como el 'Abogado del Diablo' para auditar y
    fortalecer autónomamente los dictámenes del agente.
    """

    PASSING_THRESHOLD = 85.0

    @classmethod
    def critique_report(
        cls,
        report: DisputeAnalysisReport,
        docs: Optional[Dict[str, Any]] = None,
        seller_country: str = "MEXICO",
        buyer_country: str = "MEXICO",
        days_to_claim: int = 15,
        has_edi_997: bool = False
    ) -> AdversarialCritiqueResult:
        """
        Somete el dictamen preliminar a un examen pericial hostil riguroso.
        """
        docs = docs or {}
        vulnerabilities: List[AdversarialVulnerability] = []
        counter_args: List[str] = []
        recommendations: List[str] = []
        audit_trail: List[str] = []
        preemptive_shield: List[str] = []

        base_score = 100.0

        audit_trail.append(f"Iniciando escrutinio adversarial para caso '{report.case_id}'")

        # 1. EVALUACIÓN TRANSFRONTERIZA (CISG / T-MEC vs CCOM)
        treaty_eval = CrossBorderTreatiesEngine.evaluate_transaction(
            seller_country=seller_country,
            buyer_country=buyer_country,
            days_elapsed_before_claim=days_to_claim,
            claim_type=report.deduction_type or "SHORTAGE"
        )
        audit_trail.append(f"Régimen detectado: {treaty_eval.governing_regime} (Cross-Border: {treaty_eval.is_cross_border})")

        # 2. AUDITORÍA PROBATORIA: Remisión / POD (Proof of Delivery)
        delivery_doc = docs.get("delivery")
        delivery_signed = getattr(delivery_doc, "signed", True) if delivery_doc else True
        discrepancy_on_dock = getattr(delivery_doc, "discrepancy_reported", False) if delivery_doc else False

        if not delivery_signed:
            base_score -= 25.0
            vuln = AdversarialVulnerability(
                category="PROOF_INTEGRITY",
                severity="HIGH",
                critic_argument=(
                    "El comprador argumentará: 'La remisión no cuenta con firma autógrafa del receptor "
                    "ni número de empleado, por lo que carece de valor probatorio pleno conforme a la ley mercantil.'"
                ),
                rebuttal_strategy=(
                    "Cotejar bitácora de muelle (EDI 861) y sello electrónico de caseta de seguridad con "
                    "placas de la unidad de transporte para suplir la omisión formal de firma."
                )
            )
            vulnerabilities.append(vuln)
            counter_args.append(vuln.critic_argument)
            recommendations.append(vuln.rebuttal_strategy)
            audit_trail.append("PENALIZACIÓN: Falta de firma autógrafa en remisión (-25.0 pts)")

        # 3. AUDITORÍA DE ACUSES EDI (EDI 997 vs PENALIZACIÓN DE CITA)
        is_logistics_penalty = any(term in (report.deduction_type or "").upper() for term in ["OTIF", "ASN", "CITA", "DESPACHO"])
        if is_logistics_penalty and not has_edi_997:
            base_score -= 15.0
            vuln = AdversarialVulnerability(
                category="EDI_PROOF",
                severity="MEDIUM",
                critic_argument=(
                    "El comprador objetará: 'No consta en autos el acuse de recibo funcional EDI 997 que acredite "
                    "que el ASN (EDI 856) ingresó al portal antes del arribo del transporte a la caseta.'"
                ),
                rebuttal_strategy=(
                    "Exigir exhibición de los logs del protocolo AS2/VAN del comprador para verificar la "
                    "recepción del paquete electrónico en el servidor de intercambio."
                )
            )
            vulnerabilities.append(vuln)
            counter_args.append(vuln.critic_argument)
            recommendations.append(vuln.rebuttal_strategy)
            audit_trail.append("ADVERTENCIA: Falta de acuse EDI 997 en penalización logística (-15.0 pts)")

        # 4. AUDITORÍA DE CADUCIDAD PERENTORIA (Art. 88 CCom / Art. 39 CISG)
        if treaty_eval.claim_forfeited:
            # Si el comprador excedió el plazo pero el reporte no invoca la caducidad enfáticamente
            invoked_statute = any(code in " ".join(report.resolution_notes or []) for code in ["88", "38", "39", "Caducidad", "Prescripción"])
            if not invoked_statute:
                base_score -= 10.0
                vuln = AdversarialVulnerability(
                    category="STATUTORY_TIMEBAR",
                    severity="HIGH",
                    critic_argument=(
                        "El comprador intentará ocultar que la reclamación fue extemporánea formulándola meses "
                        "después en un corte trimestral de contabilidad sin apercibimiento formal."
                    ),
                    rebuttal_strategy=(
                        f"Inyectar perentoriamente la excepción de caducidad sustantiva "
                        f"({treaty_eval.binding_legal_thesis})."
                    )
                )
                vulnerabilities.append(vuln)
                counter_args.append(vuln.critic_argument)
                recommendations.append(vuln.rebuttal_strategy)
                audit_trail.append("VULNERABILIDAD: Omisión de excepción perentoria de caducidad (-10.0 pts)")
        else:
            preemptive_shield.append(
                f"Plazo legal respetado: Reclamación dentro del término preliminar ({days_to_claim} días vs "
                f"límite de {treaty_eval.peremptory_notice_limit_days} días)."
            )

        # 5. AUDITORÍA CONTRACTUAL: Cláusula de Arbitraje y Compensación
        contract_doc = docs.get("contract")
        has_arbitration = getattr(contract_doc, "arbitration_clause", False) if contract_doc else False
        unilateral_offset = getattr(contract_doc, "unilateral_offset_allowed", False) if contract_doc else False

        if unilateral_offset:
            base_score -= 10.0
            vuln = AdversarialVulnerability(
                category="CONTRACT_AMBIGUITY",
                severity="MEDIUM",
                critic_argument=(
                    "El comprador invocará la cláusula de compensación automática: 'El contrato nos faculta a debitar "
                    "unilateralmente cualquier discrepancia reportada sin previo aviso al vendedor.'"
                ),
                rebuttal_strategy=(
                    "Impugnar la cláusula por nulidad de pacto leonino conforme al Art. 78 del Código de Comercio "
                    "y principio de reciprocidad de la CISG, al generar desequilibrio asimétrico de las partes."
                )
            )
            vulnerabilities.append(vuln)
            counter_args.append(vuln.critic_argument)
            recommendations.append(vuln.rebuttal_strategy)
            audit_trail.append("ADVERTENCIA: Cláusula de compensación unilateral en contrato (-10.0 pts)")

        # Normalizar puntaje
        final_score = max(0.0, min(100.0, round(base_score, 1)))
        passed = final_score >= cls.PASSING_THRESHOLD

        audit_trail.append(f"Dictamen adversarial emitido: Robustness Score = {final_score:.1f}/100.0 (Passed: {passed})")

        # Escudo Jurídico Preventivo Generado
        preemptive_shield.append(treaty_eval.binding_legal_thesis)
        for rec in recommendations:
            preemptive_shield.append(f"Defensa Preventiva: {rec}")

        return AdversarialCritiqueResult(
            case_id=report.case_id,
            robustness_score=final_score,
            passed=passed,
            vulnerabilities_detected=vulnerabilities,
            counter_arguments=counter_args,
            hardening_recommendations=recommendations,
            cross_border_assessment=treaty_eval,
            preemptive_legal_shield=preemptive_shield,
            audit_trail=audit_trail
        )

    @classmethod
    def auto_harden_report(
        cls,
        report: DisputeAnalysisReport,
        critique: AdversarialCritiqueResult
    ) -> DisputeAnalysisReport:
        """
        Refuerza automáticamente el reporte incorporando el escudo jurídico
        preventivo y las excepciones perentorias formuladas por el subagente crítico.
        """
        # Crear copia enriquecida
        hardened = report.model_copy(deep=True)

        shield_header = "=== ESCUDO JURÍDICO ADVERSARIAL (BLINDAJE DIALÉCTICO 3.0) ==="
        shield_lines = [shield_header]

        if critique.cross_border_assessment:
            shield_lines.append(f"• Marco Jurídico: {critique.cross_border_assessment.governing_regime}")
            shield_lines.append(f"• Tesis Pericial: {critique.cross_border_assessment.binding_legal_thesis}")

        for vuln in critique.vulnerabilities_detected:
            shield_lines.append(f"• Contra-Argumento Previsto: {vuln.critic_argument}")
            shield_lines.append(f"  ↳ Blindaje Inapelable: {vuln.rebuttal_strategy}")

        # Inyectar en resolution_notes
        current_notes = hardened.resolution_notes or []
        # Evitar duplicaciones si ya fue blindado
        if not any(shield_header in note for note in current_notes):
            hardened.resolution_notes = current_notes + shield_lines

        # Elevar la categoría de irrefutabilidad si cuenta con escudo completo
        if critique.cross_border_assessment and critique.cross_border_assessment.claim_forfeited:
            if hasattr(hardened, "irrefutability_index"):
                setattr(hardened, "irrefutability_index", "NIVEL_1_INEXPUGNABLE")

        return hardened
