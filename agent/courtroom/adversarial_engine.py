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
from agent.guardrails.sanity_gate import SanityGateEngine
from agent.core.dispute_sla_watchdog import DisputeSlaWatchdog
from tools.document_reader.reader import load_case_documents


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
        if not docs and getattr(report, "case_id", None):
            try:
                docs = load_case_documents(report.case_id)
            except Exception:
                docs = {}

        inv = docs.get("invoice")
        deliv = docs.get("delivery")
        pay = docs.get("payment")
        ctr = docs.get("contract")
        po = docs.get("purchase_order")

        # Extraer folios y datos probatorios periciales
        invoice_folio = getattr(inv, "invoice_id", None) or getattr(report, "invoice_id", None) or f"FAC-{report.case_id}"
        delivery_folio = getattr(deliv, "delivery_id", None) or "DEL-DOC"
        payment_folio = getattr(pay, "payment_id", None) or "REM-DOC"
        contract_folio = getattr(ctr, "contract_id", None) or "CTR-MARCO-BILATERAL"
        warehouse_loc = getattr(deliv, "warehouse_location", "") or "Muelle de Recepción"

        # Auditorías cruzadas de Sanity Gate y Watchdog de Prescripción SLA
        try:
            sanity_audit = SanityGateEngine.audit_and_reinforce_case(report, docs)
        except Exception:
            sanity_audit = None

        try:
            sla_status = DisputeSlaWatchdog.evaluate_case_sla(report.case_id, report=report)
        except Exception:
            sla_status = None

        # Identificar partidas físicas faltantes
        missing_details: List[str] = []
        if deliv and hasattr(deliv, "items") and deliv.items:
            for it in deliv.items:
                if getattr(it, "missing_quantity", 0) > 0:
                    missing_details.append(f"{it.missing_quantity}x {it.item_id}")
                elif getattr(it, "damaged_quantity", 0) > 0:
                    missing_details.append(f"{it.damaged_quantity}x {it.item_id} (dañado)")

        # Identificar códigos de retención aplicados
        deduction_codes: List[str] = []
        if pay and hasattr(pay, "deductions") and pay.deductions:
            for d in pay.deductions:
                deduction_codes.append(f"{d.code} (${d.amount:,.2f})")

        # Identificar cláusulas contractuales
        contract_clauses: List[str] = []
        if ctr and hasattr(ctr, "clauses") and ctr.clauses:
            for c in ctr.clauses:
                contract_clauses.append(f"Cláusula {c.clause_id}")

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
            missing_text = f" ({', '.join(missing_details)})" if missing_details else ""
            # El Fiscal ataca con la constancia de entrega
            prosecutor_args.append(AdversarialArgument(
                role=AdversarialRole.PROSECUTOR,
                speaker_name=cls.PROSECUTOR_NAME,
                topic="Faltante Físico en Muelle",
                argument_text=(
                    f"El comprador reportó válidamente un faltante de mercancía valorado en "
                    f"${justified_total:,.2f} USD{missing_text} en la remisión {delivery_folio} ({warehouse_loc}). "
                    f"Las unidades recibidas en patio fueron inferiores a las amparadas en factura {invoice_folio}."
                ),
                legal_or_contractual_ground=contract_clauses[0] if contract_clauses else "Cláusula de Recepción e Integridad de Entrega",
                strength_score=0.95,
                evidence_referenced=[delivery_folio, invoice_folio]
            ))

            # El Defensor allana y reconoce la deducción justificada
            defender_args.append(AdversarialArgument(
                role=AdversarialRole.DEFENDER,
                speaker_name=cls.DEFENDER_NAME,
                topic="Allanamiento de Faltante Acreditado",
                argument_text=(
                    f"Verificada la remisión {delivery_folio} con sello y firma física de recepción en {warehouse_loc} con discrepancia asentada{missing_text}, "
                    f"reconocemos la exactitud del faltante de ${justified_total:,.2f} USD y allanamos la "
                    f"deducción mediante emisión de Nota de Crédito comercial conforme a la ley."
                ),
                legal_or_contractual_ground="Art. 1043 Código de Comercio (Reconocimiento Expreso)",
                strength_score=0.98,
                evidence_referenced=[f"Remisión {delivery_folio} con salvedad en muelle", invoice_folio]
            ))
            sustained.append(f"Deducción de faltante físico por ${justified_total:,.2f} USD amparada en {delivery_folio} declarada PROCEDENTE.")
        else:
            # Si no hubo faltante justificado
            if has_delivery and delivery_signed and not discrepancy_reported:
                defender_args.append(AdversarialArgument(
                    role=AdversarialRole.DEFENDER,
                    speaker_name=cls.DEFENDER_NAME,
                    topic="Prueba Plena de Entrega Íntegra",
                    argument_text=(
                        f"La remisión {delivery_folio} fue firmada de plena conformidad en muelle {warehouse_loc} sin sello de salvedad ni faltantes. "
                        f"Cualquier reclamo posterior de faltante carece de valor probatorio conforme a la ley comercial."
                    ),
                    legal_or_contractual_ground="Eficacia Probatoria de Remisión Limpia (Prueba Plena Art. 88 CCom)",
                    strength_score=0.95,
                    evidence_referenced=[delivery_folio]
                ))

        # ---------------------------------------------------------
        # RONDA 2: Deducciones Unilaterales, Multas ASN y Pronto Pago
        # ---------------------------------------------------------
        precedent_citations = []
        if claimable_total > Decimal("0.00"):
            ded_str = f" bajo conceptos {', '.join(deduction_codes)}" if deduction_codes else ""
            # El Fiscal intenta defender la deducción del comprador con guías internas
            prosecutor_args.append(AdversarialArgument(
                role=AdversarialRole.PROSECUTOR,
                speaker_name=cls.PROSECUTOR_NAME,
                topic="Aplicación de Políticas Operativas y Guías del Comprador",
                argument_text=(
                    f"El retailer retuvo ${claimable_total:,.2f} USD{ded_str} en liquidación {payment_folio} con base en sus manuales internos de logística, "
                    f"penalizaciones por aviso anticipado ASN o descuentos comerciales por pronto pago."
                ),
                legal_or_contractual_ground="Manual Operativo de Proveedores del Retailer & Portal B2B",
                strength_score=0.15,
                evidence_referenced=[f"Comprobante de Retención {payment_folio}"]
            ))

            # Consultar precedentes aplicables en la Red de Memoria
            if precedent_matcher:
                try:
                    retailer_name = str(getattr(inv, "customer_id", getattr(ctr, "retailer_name", "RETAILER")))
                    matches = precedent_matcher.find_relevant_precedents(
                        retailer_id=retailer_name,
                        dispute_type=report.root_cause,
                        top_k=1
                    )
                    if matches:
                        precedent_citations.append(matches[0].formal_citation_text)
                except Exception:
                    pass

            precedent_ref_text = f" Reforzado por jurisprudencia vinculante: {precedent_citations[0]}." if precedent_citations else ""

            # Defensas especiales periciales derivadas de Sanity Gate y Watchdog SLA
            extemp_defense = ""
            if sanity_audit and not sanity_audit.notice_window_passed and sanity_audit.notice_window_days_allowed is not None:
                extemp_defense = f" PRECLUSIÓN TEMPORAL: Notificación extemporánea a los {sanity_audit.notice_window_days_elapsed} días (máximo contractual: {sanity_audit.notice_window_days_allowed} días), extinguiendo el derecho de retención."

            double_penalty_defense = ""
            if sanity_audit and sanity_audit.double_penalty_detected:
                double_penalty_defense = f" DOBLE PENALIZACIÓN ILEGAL: Multiplicidad de cargos ({', '.join(sanity_audit.double_penalty_details)}) sobre el mismo hecho operativo, nulos de pleno derecho (Non Bis In Idem)."

            cap_defense = ""
            if sanity_audit and sanity_audit.contractual_cap_enforced:
                cap_defense = f" TOPE CONTRACTUAL DE PENALIDAD REBASADO: Se retuvo en exceso de la cláusula de responsabilidad; excedente de ${sanity_audit.contractual_cap_excess_claimed:,.2f} USD es nulo."

            sla_defense = ""
            if sla_status:
                sla_defense = f" RELOJ SLA: Restan {sla_status.days_to_expiration} días de ventana perentoria ({sla_status.urgency_level})."

            # El Defensor destruye la pretensión unilateral
            defender_args.append(AdversarialArgument(
                role=AdversarialRole.DEFENDER,
                speaker_name=cls.DEFENDER_NAME,
                topic="Nulidad Absoluta de Cargos Unilaterales",
                argument_text=(
                    f"Objeción perentoria sobre factura {invoice_folio} y liquidación {payment_folio}: El contrato marco bilateral {contract_folio} prevalece jerárquicamente "
                    f"sobre cualquier guía o portal unilateral del comprador. No existe adenda bilateral suscrita "
                    f"que habilite retener ${claimable_total:,.2f} USD. La retención constituye incumplimiento de pago."
                    f"{extemp_defense}{double_penalty_defense}{cap_defense}{sla_defense}{precedent_ref_text}"
                ),
                legal_or_contractual_ground="Art. 88 del Código de Comercio & Cláusula de Prohibición de Penalidades Unilaterales",
                strength_score=0.99,
                evidence_referenced=[contract_folio, invoice_folio, payment_folio] + ([precedent_citations[0]] if precedent_citations else [])
            ))
            dismissed.append(f"Retención unilateral de ${claimable_total:,.2f} USD en {payment_folio} declarada IMPROCEDENTE y 100% RECLAMABLE.")

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
            if sanity_audit and (not sanity_audit.notice_window_passed or sanity_audit.double_penalty_detected or sanity_audit.contractual_cap_enforced):
                contested_def += Decimal("0.05")
            if not has_delivery:
                contested_def -= Decimal("0.15")
            probative_force = float(round((contested_def / (contested_def + contested_pros)) * Decimal("100"), 1))
            probative_force = min(98.5, max(15.0, probative_force))
        else:
            # Caso 100% justificado: no hay litigio, allanamiento pleno
            probative_force = 95.0

        sla_note = f" Reloj SLA: {sla_status.days_to_expiration} días restantes ({sla_status.urgency_level})." if sla_status else ""

        magistrate_summary = (
            f"VISTO el careo de autos en el expediente {report.case_id} (Factura: {invoice_folio}, Remisión: {delivery_folio}, Liquidación: {payment_folio}): "
            f"Se condena al comprador al reintegro inmediato de ${claimable_total:,.2f} USD por carecer de título legal habilitante en {contract_folio}, "
            f"y se valida la emisión de Nota de Crédito por ${justified_total:,.2f} USD al existir prueba física plena de muelle. "
            f"Fuerza probatoria de la defensa: {probative_force}%.{sla_note}"
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
