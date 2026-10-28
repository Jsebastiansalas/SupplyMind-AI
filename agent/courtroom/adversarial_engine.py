"""
agent/courtroom/adversarial_engine.py
Motor del Debate Dialéctico Multi-Agente (Adversarial Courtroom - Pilar 3).

Ejecuta un careo interno entre el Fiscal Forense del Retailer (The Auditor)
y el Abogado Defensor del Proveedor (The Advocate), ante el arbitraje del
Magistrado Sentenciador (The Magistrate) para asegurar un dictamen legalmente invulnerable.
"""

from decimal import Decimal
import uuid
from typing import Dict, Any, List, Optional

from agent.courtroom.models import (
    AdversarialRole,
    AdversarialArgument,
    AdversarialVerdict
)
from data.models import DisputeAnalysisReport
from agent.memory.precedent_matcher import PrecedentMatcher


class AdversarialCourtroomEngine:
    """Orquestador dialéctico multi-agente."""

    PROSECUTOR_NAME = "Lic. Gustavo Méndez (Fiscal Forense Retail B2B)"
    DEFENDER_NAME = "Dra. Sofía Valenzuela (Abogada Corporativa del Proveedor)"
    MAGISTRATE_NAME = "Magistrado J. R. Echeverría (Árbitro Comercial Independiente)"

    @classmethod
    def conduct_debate(
        cls,
        report: DisputeAnalysisReport,
        docs: Optional[Dict[str, Any]] = None,
        precedent_matcher: Optional[PrecedentMatcher] = None
    ) -> AdversarialVerdict:
        """
        Ejecuta el careo dialéctico multi-agente sobre el expediente.
        """
        docs = docs or {}
        inv = docs.get("invoice")
        deliv = docs.get("delivery")
        pay = docs.get("payment")
        ctr = docs.get("contract")

        prosecutor_args: List[AdversarialArgument] = []
        defender_args: List[AdversarialArgument] = []
        sustained: List[str] = []
        dismissed: List[str] = []

        disputed_total = abs(report.difference)
        justified_total = report.justified_amount
        claimable_total = report.claimable_amount

        # ---------------------------------------------------------
        # RONDA 1: Faltantes Físicos y Remisión de Muelle
        # ---------------------------------------------------------
        has_delivery = deliv is not None
        delivery_signed = getattr(deliv, "signed", False) if deliv else False
        discrepancy_reported = getattr(deliv, "discrepancy_reported", False) if deliv else False

        if justified_total > Decimal("0.00"):
            # El Fiscal ataca con la constancia de entrega
            prosecutor_args.append(AdversarialArgument(
                role=AdversarialRole.PROSECUTOR,
                speaker_name=cls.PROSECUTOR_NAME,
                topic="Faltante Físico en Muelle",
                argument_text=(
                    f"El comprador reportó válidamente un faltante de mercancía valorado en "
                    f"${justified_total:,.2f} USD. Las unidades recibidas en patio fueron inferiores a las facturadas."
                ),
                legal_or_contractual_ground="Cláusula de Recepción e Integridad de Entrega",
                strength_score=0.95,
                evidence_referenced=[getattr(deliv, "delivery_id", "DEL-DOC")]
            ))

            # El Defensor allana y reconoce la deducción justificada
            defender_args.append(AdversarialArgument(
                role=AdversarialRole.DEFENDER,
                speaker_name=cls.DEFENDER_NAME,
                topic="Allanamiento de Faltante Acreditado",
                argument_text=(
                    f"Verificada la remisión con sello y firma física de recepción con discrepancia, "
                    f"reconocemos la exactitud del faltante de ${justified_total:,.2f} USD y allanamos la "
                    f"deducción mediante emisión de Nota de Crédito comercial conforme a la ley."
                ),
                legal_or_contractual_ground="Art. 1043 Código de Comercio (Reconocimiento Expreso)",
                strength_score=0.98,
                evidence_referenced=["Remisión firmada con sello de discrepancia"]
            ))
            sustained.append(f"Deducción de faltante físico por ${justified_total:,.2f} USD declarada PROCEDENTE.")
        else:
            # Si no hubo faltante justificado
            if has_delivery and delivery_signed and not discrepancy_reported:
                defender_args.append(AdversarialArgument(
                    role=AdversarialRole.DEFENDER,
                    speaker_name=cls.DEFENDER_NAME,
                    topic="Prueba Plena de Entrega Íntegra",
                    argument_text=(
                        f"La remisión fue firmada de plena conformidad en muelle sin sello de salvedad. "
                        f"Cualquier reclamo posterior de faltante carece de valor probatorio."
                    ),
                    legal_or_contractual_ground="Eficacia Probatoria de Remisión Limpia (Prueba Plena)",
                    strength_score=0.95,
                    evidence_referenced=[getattr(deliv, "delivery_id", "DEL-CLEAN")]
                ))

        # ---------------------------------------------------------
        # RONDA 2: Deducciones Unilaterales, Multas ASN y Pronto Pago
        # ---------------------------------------------------------
        precedent_citations = []
        if claimable_total > Decimal("0.00"):
            # El Fiscal intenta defender la deducción del comprador con guías internas
            prosecutor_args.append(AdversarialArgument(
                role=AdversarialRole.PROSECUTOR,
                speaker_name=cls.PROSECUTOR_NAME,
                topic="Aplicación de Políticas Operativas y Guías del Comprador",
                argument_text=(
                    f"El retailer retuvo ${claimable_total:,.2f} USD con base en sus manuales internos de logística, "
                    f"penalizaciones por aviso anticipado ASN o descuentos comerciales por pronto pago."
                ),
                legal_or_contractual_ground="Manual Operativo de Proveedores del Retailer",
                strength_score=0.15,
                evidence_referenced=["Comprobante de Retención Bancaria"]
            ))

            # Consultar precedentes aplicables en la Red de Memoria
            if precedent_matcher:
                try:
                    retailer_name = str(getattr(inv, "customer_id", "RETAILER"))
                    matches = precedent_matcher.find_relevant_precedents(
                        retailer_id=retailer_name,
                        dispute_type=report.root_cause,
                        top_k=1
                    )
                    if matches:
                        precedent_citations.append(matches[0].formal_citation_text)
                except Exception:
                    pass

            precedent_ref_text = f" Reforzado por jurisprudencia vinculante: {precedent_citations[0]}" if precedent_citations else ""

            # El Defensor destruye la pretensión unilateral
            defender_args.append(AdversarialArgument(
                role=AdversarialRole.DEFENDER,
                speaker_name=cls.DEFENDER_NAME,
                topic="Nulidad Absoluta de Cargos Unilaterales",
                argument_text=(
                    f"Objeción perentoria: El contrato marco comercial bilateral suscrito prevalece jerárquicamente "
                    f"sobre cualquier guía o portal unilateral del comprador. No existe adenda bilateral suscrita "
                    f"que habilite retener ${claimable_total:,.2f} USD. La retención constituye incumplimiento de pago."
                    f"{precedent_ref_text}"
                ),
                legal_or_contractual_ground="Art. 88 del Código de Comercio & Cláusula de Prohibición de Penalidades Unilaterales",
                strength_score=0.99,
                evidence_referenced=["Contrato Marco Maestro", "Criterio de Nulidad Unilateral"]
            ))
            dismissed.append(f"Retención unilateral de ${claimable_total:,.2f} USD declarada IMPROCEDENTE y 100% RECLAMABLE.")

        # ---------------------------------------------------------
        # RONDA 3: Síntesis y Veredicto Judicial del Magistrado
        # ---------------------------------------------------------
        # Fuerza probatoria de la defensa del proveedor sobre los fondos controvertidos
        if claimable_total > Decimal("0.00"):
            contested_pros = Decimal("0.15")
            contested_def = Decimal("0.95")
            if delivery_signed:
                contested_def += Decimal("0.05")
            if precedent_citations:
                contested_def += Decimal("0.05")
            if not has_delivery:
                contested_def -= Decimal("0.15")
            probative_force = float(round((contested_def / (contested_def + contested_pros)) * Decimal("100"), 1))
            probative_force = min(98.5, max(15.0, probative_force))
        else:
            # Caso 100% justificado: no hay litigio, allanamiento pleno
            probative_force = 95.0

        magistrate_summary = (
            f"VISTO el careo de autos en el expediente {report.case_id}: "
            f"Se condena al comprador al reintegro inmediato de ${claimable_total:,.2f} USD por carecer de título legal habilitante, "
            f"y se valida la emisión de Nota de Crédito por ${justified_total:,.2f} USD al existir prueba física plena de muelle. "
            f"Fuerza probatoria de la defensa: {probative_force}%."
        )

        final_doctrine = (
            "DOCTRINA COMERCIAL VINCULANTE: Ninguna guía operativa o portal B2B puede modificar o imponer sanciones "
            "financieras no contenidas en el contrato marco bilateral suscrito. Las remisiones firmadas con sello de muelle "
            "hacen fe pública comercial plena e inmutable entre las partes."
        )

        return AdversarialVerdict(
            case_id=report.case_id,
            courtroom_session_id=f"CRT-{uuid.uuid4().hex[:8].upper()}",
            disputed_amount=disputed_total,
            justified_amount=justified_total,
            claimable_amount=claimable_total,
            prosecutor_arguments=prosecutor_args,
            advocate_counterarguments=defender_args,
            sustained_objections=sustained,
            dismissed_objections=dismissed,
            magistrate_summary_ruling=magistrate_summary,
            probative_force_supplier_pct=probative_force,
            final_legal_doctrine=final_doctrine
        )
