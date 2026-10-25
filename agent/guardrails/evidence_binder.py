"""
agent/guardrails/evidence_binder.py
Pilar 3: Anclaje Fáctico Estricto y Certificación Probatoria (Evidence Binding & Zero Uncited Claims).

Objetivo:
Garantizar que CADA centavo declarado como justificado, reclamable o deducido
esté estrictamente vinculado a un puntero fáctico verificable (Factura, POD firmado,
Orden de Compra o Cláusula Contractual).
Cualquier concepto no respaldado se clasifica como 'Partida Cautelar no Acreditada',
penaliza el nivel de confianza y activa advertencia de verificación física.
"""

from decimal import Decimal
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Union

from data.models import (
    DisputeAnalysisReport,
    EvidencePointer,
    EvidenceBindingManifest,
    Invoice,
    DeliveryNote,
    PurchaseOrder,
    PaymentReceipt,
    CommercialContract,
)
from tools.reconciliation_engine.engine import ReconciliationSummary


class StrictEvidenceBinder:
    """
    Auditor y enlazador de evidencia probatoria de grado pericial contable.
    Inspecciona cada partida monetaria y certifica su respaldo documental físico.
    """

    @classmethod
    def audit_and_bind(
        cls,
        report: DisputeAnalysisReport,
        reconciliation: Optional[ReconciliationSummary] = None,
        loaded_documents: Optional[Dict[str, Any]] = None,
        contract_evaluation: Optional[Any] = None,
    ) -> DisputeAnalysisReport:
        """
        Ejecuta el cotejo de cada partida monetaria contra los documentos del caso,
        genera los EvidencePointers y ensambla el EvidenceBindingManifest.
        """
        case_id = report.case_id
        docs = loaded_documents or {}

        invoice = docs.get("invoice")
        delivery = docs.get("delivery")
        po = docs.get("purchase_order") or docs.get("po")
        payment = docs.get("payment")
        contract = docs.get("contract")

        pointers: List[EvidencePointer] = []
        cautelar_items: List[str] = []
        canonical_citations: List[str] = []

        # ======================================================================
        # 1. Anclaje del Monto Facturado (Invoice Binding)
        # ======================================================================
        inv_id = getattr(invoice, "invoice_id", None) or (invoice.get("invoice_id") if isinstance(invoice, dict) else None) or "INV-N/A"
        inv_total = getattr(invoice, "total_amount", None) or (Decimal(str(invoice.get("total_amount", 0))) if isinstance(invoice, dict) else None)

        if invoice is not None and inv_total is not None and abs(inv_total - report.billed_amount) <= Decimal("0.05"):
            ptr_inv = EvidencePointer(
                pointer_id=f"PTR-INV-{inv_id}-TOTAL",
                doc_type="INVOICE",
                doc_id=inv_id,
                field_ref="total_amount",
                amount=report.billed_amount,
                citation_tag=f"[Factura {inv_id} §Total ${report.billed_amount:,.2f} {report.currency}]",
                is_backed_by_physical_proof=True,
                status="ACREDITADO",
                detail=f"Factura comercial fiscalmente válida por ${report.billed_amount:,.2f} {report.currency}."
            )
            pointers.append(ptr_inv)
            canonical_citations.append(ptr_inv.citation_tag)
        else:
            ptr_inv = EvidencePointer(
                pointer_id=f"PTR-INV-{inv_id}-UNVERIFIED",
                doc_type="INVOICE",
                doc_id=inv_id,
                field_ref="total_amount",
                amount=report.billed_amount,
                citation_tag=f"[Factura {inv_id} §IMPUTADA_O_DIFERIDA]",
                is_backed_by_physical_proof=False,
                status="CAUTELAR_NO_ACREDITADA",
                detail="Factura no suministrada originalmente o monto facturado discrepa del total declarado."
            )
            pointers.append(ptr_inv)
            cautelar_items.append(f"Monto Facturado (${report.billed_amount:,.2f}): Soporte de factura original ausente o con discrepancia.")

        # ======================================================================
        # 2. Anclaje del Pago Recibido (Payment Receipt Binding)
        # ======================================================================
        pay_id = getattr(payment, "payment_id", None) or (payment.get("payment_id") if isinstance(payment, dict) else None) or "PAY-N/A"
        pay_paid = getattr(payment, "amount_paid", None) or (Decimal(str(payment.get("amount_paid", 0))) if isinstance(payment, dict) else None)

        if payment is not None and pay_paid is not None and abs(pay_paid - report.received_amount) <= Decimal("0.05"):
            ptr_pay = EvidencePointer(
                pointer_id=f"PTR-PAY-{pay_id}-AMOUNT",
                doc_type="PAYMENT",
                doc_id=pay_id,
                field_ref="amount_paid",
                amount=report.received_amount,
                citation_tag=f"[Comprobante {pay_id} §Liquidación ${report.received_amount:,.2f} {report.currency}]",
                is_backed_by_physical_proof=True,
                status="ACREDITADO",
                detail=f"Depósito / Remesa bancaria verificada en estado de cuenta por ${report.received_amount:,.2f}."
            )
            pointers.append(ptr_pay)
            canonical_citations.append(ptr_pay.citation_tag)
        else:
            ptr_pay = EvidencePointer(
                pointer_id=f"PTR-PAY-{pay_id}-UNVERIFIED",
                doc_type="PAYMENT",
                doc_id=pay_id,
                field_ref="amount_paid",
                amount=report.received_amount,
                citation_tag=f"[Comprobante {pay_id} §NO_ACREDITADO]",
                is_backed_by_physical_proof=False,
                status="CAUTELAR_NO_ACREDITADA",
                detail="Liquidación bancaria sin comprobante original de transferencia/remesa."
            )
            pointers.append(ptr_pay)
            cautelar_items.append(f"Monto Recibido (${report.received_amount:,.2f}): Comprobante de pago bancario no verificado.")

        # ======================================================================
        # 3. Anclaje de Entregas y Remisiones (Delivery POD & Physical Inspection)
        # ======================================================================
        del_id = getattr(delivery, "delivery_id", None) or (delivery.get("delivery_id") if isinstance(delivery, dict) else None) or "DEL-N/A"
        del_signed = getattr(delivery, "signed", True) if delivery else False
        if isinstance(delivery, dict):
            del_signed = delivery.get("signed", True)

        # Si hay remisión y está firmada:
        has_delivery_doc = delivery is not None
        if has_delivery_doc:
            if not del_signed:
                cautelar_items.append(f"Remisión {del_id}: Carece de firma o sello físico de muelle (POD no certificado).")

        # ======================================================================
        # 4. Anclaje de Deducciones Aplicadas por el Retailer vs Cláusulas Contractuales
        # ======================================================================
        deductions_raw = []
        if payment:
            if isinstance(payment, dict):
                deductions_raw = payment.get("deductions", [])
            else:
                deductions_raw = getattr(payment, "deductions", [])

        # Indexar cláusulas del contrato si existen
        contract_id = getattr(contract, "contract_id", None) or (contract.get("contract_id") if isinstance(contract, dict) else None) or "CTR-S/N"
        contract_clauses = []
        if contract:
            if isinstance(contract, dict):
                contract_clauses = contract.get("clauses", [])
            else:
                contract_clauses = getattr(contract, "clauses", [])

        for idx, ded in enumerate(deductions_raw, 1):
            if isinstance(ded, dict):
                d_code = str(ded.get("code", f"DED-{idx}"))
                d_reason = str(ded.get("reason", "Deducción comercial"))
                d_amt = Decimal(str(ded.get("amount", 0)))
                d_ref = ded.get("reference_doc")
            else:
                d_code = str(getattr(ded, "code", f"DED-{idx}"))
                d_reason = str(getattr(ded, "reason", "Deducción comercial"))
                d_amt = Decimal(str(getattr(ded, "amount", 0)))
                d_ref = getattr(ded, "reference_doc", None)

            # Buscar si el contrato contempla esta política
            matching_clause = None
            d_lower = f"{d_code} {d_reason}".lower()
            for c in contract_clauses:
                c_text = (c.get("text", "") if isinstance(c, dict) else getattr(c, "text", "")).lower()
                c_title = (c.get("title", "") if isinstance(c, dict) else getattr(c, "title", "")).lower()
                c_policy = (c.get("policy", "") if isinstance(c, dict) else getattr(c, "policy", "")).lower()
                if any(w in c_text or w in c_title or w in c_policy for w in [d_code.lower(), "asn", "otif", "pronto pago", "damage", "shortage", "avería", "faltante"]):
                    matching_clause = c
                    break

            # Determinar si la deducción está acreditada físicamente o es arbitraria
            if matching_clause:
                c_id = matching_clause.get("clause_id") if isinstance(matching_clause, dict) else getattr(matching_clause, "clause_id", "CLAUSE")
                c_title_val = matching_clause.get("title") if isinstance(matching_clause, dict) else getattr(matching_clause, "title", "Política")
                ptr_ded = EvidencePointer(
                    pointer_id=f"PTR-DED-{d_code}-{idx}",
                    doc_type="CONTRACT",
                    doc_id=contract_id,
                    field_ref=f"clause_{c_id}",
                    amount=d_amt,
                    citation_tag=f"[Contrato {contract_id} §Cláusula {c_id} '{c_title_val}' | Deducción {d_code} ${d_amt:,.2f}]",
                    is_backed_by_physical_proof=True,
                    status="ACREDITADO",
                    detail=f"Deducción '{d_code}' normada por la cláusula {c_id} de {contract_id}."
                )
                pointers.append(ptr_ded)
                canonical_citations.append(ptr_ded.citation_tag)
            else:
                # Deducción sin cláusula contractual que la autorice
                ptr_ded = EvidencePointer(
                    pointer_id=f"PTR-DED-{d_code}-{idx}-UNBACKED",
                    doc_type="PAYMENT",
                    doc_id=pay_id,
                    field_ref=f"deduction_{d_code}",
                    amount=d_amt,
                    citation_tag=f"[Comprobante {pay_id} §Deducción Unilateral {d_code} | ${d_amt:,.2f} SIN CLÁUSULA EN {contract_id}]",
                    is_backed_by_physical_proof=False,
                    status="CAUTELAR_NO_ACREDITADA",
                    detail=f"El retailer retuvo ${d_amt:,.2f} bajo el código '{d_code}', pero el contrato {contract_id} no contiene cláusula habilitante."
                )
                pointers.append(ptr_ded)
                cautelar_items.append(f"Deducción {d_code} (${d_amt:,.2f}): Sin cláusula contractual que autorice retención.")

        # ======================================================================
        # 5. Anclaje de Discrepancias Físicas por SKU (Reconciliation Line Items)
        # ======================================================================
        if reconciliation and reconciliation.discrepancies:
            for d in reconciliation.discrepancies:
                sku = d.item_id
                if d.missing_quantity > 0:
                    status_flag = "ACREDITADO" if del_signed else "CAUTELAR_NO_ACREDITADA"
                    tag = f"[Remisión {del_id} §SKU {sku} | Faltante: {d.missing_quantity} uds | ${d.missing_amount:,.2f}]"
                    ptr_sku = EvidencePointer(
                        pointer_id=f"PTR-DEL-{del_id}-{sku}-SHORT",
                        doc_type="DELIVERY",
                        doc_id=del_id,
                        field_ref="missing_quantity",
                        item_sku=sku,
                        amount=d.missing_amount,
                        citation_tag=tag,
                        is_backed_by_physical_proof=del_signed,
                        status=status_flag,
                        detail=f"Faltante físico de {d.missing_quantity} unidades registrado en remisión {del_id} (Firma POD: {'Sí' if del_signed else 'No'})."
                    )
                    pointers.append(ptr_sku)
                    canonical_citations.append(tag)

                if d.damaged_quantity > 0:
                    status_flag = "ACREDITADO" if del_signed else "CAUTELAR_NO_ACREDITADA"
                    tag = f"[Remisión {del_id} §SKU {sku} | Avería: {d.damaged_quantity} uds | ${d.damaged_amount:,.2f}]"
                    ptr_dam = EvidencePointer(
                        pointer_id=f"PTR-DEL-{del_id}-{sku}-DAMAGED",
                        doc_type="DELIVERY",
                        doc_id=del_id,
                        field_ref="damaged_quantity",
                        item_sku=sku,
                        amount=d.damaged_amount,
                        citation_tag=tag,
                        is_backed_by_physical_proof=del_signed,
                        status=status_flag,
                        detail=f"Mercancía averiada ({d.damaged_quantity} unidades) en remisión {del_id}."
                    )
                    pointers.append(ptr_dam)
                    canonical_citations.append(tag)

                if d.price_difference != Decimal("0.00"):
                    po_id = getattr(po, "po_id", "PO-N/A") if po else "PO-N/A"
                    tag = f"[PO {po_id} vs Factura {inv_id} §SKU {sku} | Varianza Precio: ${d.price_difference:,.2f}/ud]"
                    ptr_pr = EvidencePointer(
                        pointer_id=f"PTR-PO-{po_id}-{sku}-PRICE",
                        doc_type="PURCHASE_ORDER",
                        doc_id=po_id,
                        field_ref="agreed_unit_price",
                        item_sku=sku,
                        amount=abs(d.price_difference * Decimal(d.billed_quantity)),
                        citation_tag=tag,
                        is_backed_by_physical_proof=True,
                        status="ACREDITADO",
                        detail=f"Discrepancia entre precio pactado en PO ({d.agreed_unit_price}) y facturado ({d.invoiced_unit_price})."
                    )
                    pointers.append(ptr_pr)
                    canonical_citations.append(tag)

        # ======================================================================
        # 6. Cálculo del Ratio de Respaldo y Penalización de Confianza
        # ======================================================================
        backed_pointers = [p for p in pointers if p.status == "ACREDITADO"]
        unbacked_pointers = [p for p in pointers if p.status == "CAUTELAR_NO_ACREDITADA"]

        total_backed_amt = sum((p.amount for p in backed_pointers), Decimal("0.00"))
        total_unbacked_amt = sum((p.amount for p in unbacked_pointers), Decimal("0.00"))
        tot_claims_amt = total_backed_amt + total_unbacked_amt

        if tot_claims_amt > Decimal("0.00"):
            backing_ratio = float((total_backed_amt / tot_claims_amt) * Decimal("100.0"))
        else:
            backing_ratio = 100.0

        confidence_penalty = 0.0
        if len(unbacked_pointers) > 0:
            confidence_penalty = round(min(0.35, 0.08 * len(unbacked_pointers) + (float(total_unbacked_amt / max(Decimal("1.00"), report.billed_amount)) * 0.15)), 2)
            report.confidence = max(0.20, round(report.confidence - confidence_penalty, 3))

            if backing_ratio < 70.0:
                verdict = "CRITICAL_UNBACKED_DEFICIT"
            else:
                verdict = "CAUTIONARY_ITEMS_DETECTED"
        else:
            verdict = "FULL_EVIDENCE_BINDING_VERIFIED"

        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        manifest = EvidenceBindingManifest(
            case_id=case_id,
            total_claims_audited=len(pointers),
            backed_claims_count=len(backed_pointers),
            unbacked_claims_count=len(unbacked_pointers),
            total_backed_amount=total_backed_amt,
            total_unbacked_amount=total_unbacked_amt,
            backing_ratio_pct=round(backing_ratio, 2),
            evidence_pointers=pointers,
            cautelar_items=cautelar_items,
            binding_verdict=verdict,
            confidence_penalty=confidence_penalty,
            generated_at=timestamp
        )

        # ======================================================================
        # 7. Actualización de report.evidence con Citas Canónicas
        # ======================================================================
        if canonical_citations:
            existing = list(report.evidence)
            # Agregar citas canónicas que no estén ya en la evidencia
            for cit in canonical_citations:
                if not any(cit in e for e in existing):
                    existing.append(cit)
            report.evidence = existing

        report.evidence_manifest = manifest
        return report
