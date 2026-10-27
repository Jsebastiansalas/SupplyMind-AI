"""
Sintetizador Paramétrico de Casos Comerciales B2B Reales (Sprint 3.1 - US-301).

Genera expedientes comerciales completos y coherentes con:
1. Factura Comercial (Invoice) con sellos fiscales y desglose al centavo.
2. Orden de Compra (Purchase Order) con términos y precios pactados.
3. Remisión de Entrega (Delivery Note) con sellos de muelle y firmas.
4. Comprobante de Pago (Payment Receipt) con retenciones y códigos de deducción.
5. Contrato Marco Comercial (Commercial Contract) con cláusulas y tolerancias.
6. Ground Truth Pericial inmutable con invariantes matemáticas al 100%.

Todas las operaciones numéricas emplean estrictamente Decimal con redondeo ROUND_HALF_UP.
Todos los documentos son validados contra sus esquemas Pydantic oficiales antes de persistir.
"""

import json
import uuid
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union

from data.models import (
    Invoice, InvoiceItem,
    PurchaseOrder, PurchaseOrderItem,
    DeliveryNote, DeliveryItem,
    PaymentReceipt, PaymentDeduction,
    CommercialContract, ContractClause
)
from agent.training.factory.ground_truth import (
    GroundTruth,
    GroundTruthLineItem,
    GroundTruthDeductionAssessment,
    DiscrepancyCategory,
    CommercialActionType
)
from tools.real_data_generator.retailer_catalog import (
    BuyerEnterpriseProfile,
    RETAILER_CATALOG,
    DEFAULT_SUPPLIER_PROFILE,
    get_retailer_profile
)

TWO_PLACES = Decimal("0.01")


def _quantize(val: Union[Decimal, int, float, str]) -> Decimal:
    """Asegura redondeo financiero a dos decimales sin punto flotante."""
    if not isinstance(val, Decimal):
        val = Decimal(str(val))
    return val.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


class CaseDossier:
    """Contenedor de los 5 documentos comerciales y el Ground Truth pericial."""
    def __init__(
        self,
        case_id: str,
        invoice: Invoice,
        purchase_order: PurchaseOrder,
        delivery: DeliveryNote,
        payment: PaymentReceipt,
        contract: CommercialContract,
        ground_truth: GroundTruth,
        raw_ground_truth_dict: Optional[Dict[str, Any]] = None
    ):
        self.case_id = case_id
        self.invoice = invoice
        self.purchase_order = purchase_order
        self.delivery = delivery
        self.payment = payment
        self.contract = contract
        self.ground_truth = ground_truth
        self.raw_ground_truth_dict = raw_ground_truth_dict or {}

    def save_to_directory(self, target_dir: Path) -> Dict[str, Path]:
        """Escribe todos los documentos en formato JSON en el directorio destino."""
        target_dir.mkdir(parents=True, exist_ok=True)
        created_files = {}

        # 1. Factura
        inv_path = target_dir / "invoice.json"
        with open(inv_path, "w", encoding="utf-8") as f:
            json.dump(self.invoice.model_dump(mode="json"), f, indent=2, ensure_ascii=False)
        created_files["invoice"] = inv_path

        # 2. Orden de Compra
        po_path = target_dir / "purchase_order.json"
        with open(po_path, "w", encoding="utf-8") as f:
            json.dump(self.purchase_order.model_dump(mode="json"), f, indent=2, ensure_ascii=False)
        created_files["purchase_order"] = po_path

        # 3. Remisión de Entrega
        del_path = target_dir / "delivery.json"
        with open(del_path, "w", encoding="utf-8") as f:
            json.dump(self.delivery.model_dump(mode="json"), f, indent=2, ensure_ascii=False)
        created_files["delivery"] = del_path

        # 4. Comprobante de Pago
        pay_path = target_dir / "payment.json"
        with open(pay_path, "w", encoding="utf-8") as f:
            json.dump(self.payment.model_dump(mode="json"), f, indent=2, ensure_ascii=False)
        created_files["payment"] = pay_path

        # 5. Contrato
        ctr_path = target_dir / "contract.json"
        with open(ctr_path, "w", encoding="utf-8") as f:
            json.dump(self.contract.model_dump(mode="json"), f, indent=2, ensure_ascii=False)
        created_files["contract"] = ctr_path

        # 6. Ground Truth
        gt_path = target_dir / "ground_truth.json"
        with open(gt_path, "w", encoding="utf-8") as f:
            gt_dict = self.raw_ground_truth_dict if self.raw_ground_truth_dict else self.ground_truth.model_dump(mode="json")
            json.dump(gt_dict, f, indent=2, ensure_ascii=False)
        created_files["ground_truth"] = gt_path

        return created_files


class EnterpriseCaseSynthesizer:
    """
    Sintetizador maestro de expedientes de auditoría comercial B2B.
    Garantiza invarianza contable exacta: Facturado - Recibido = Deducciones = Justificado + Reclamable.
    """

    @classmethod
    def synthesize_custom_case(
        cls,
        case_id: str,
        buyer_id: str,
        category: DiscrepancyCategory,
        items_spec: List[Dict[str, Any]],
        deductions_spec: List[Dict[str, Any]],
        currency: str = "USD",
        order_date: str = "2026-08-20",
        issue_date: str = "2026-08-28",
        delivery_date: str = "2026-09-02",
        payment_date: str = "2026-09-25",
        tax_rate: Decimal = Decimal("0.00"),
        custom_clauses: Optional[List[Dict[str, Any]]] = None
    ) -> CaseDossier:
        """
        Genera un expediente completo a partir de especificaciones paramétricas detalladas.
        
        items_spec: Lista de dicts con:
            - sku: str
            - description: str
            - ordered_qty: int
            - invoiced_qty: int
            - delivered_qty: int
            - received_qty: int
            - damaged_qty: int (default 0)
            - agreed_price: Decimal
            - invoiced_price: Decimal (default equal to agreed_price)
            - notes: str

        deductions_spec: Lista de dicts con:
            - code: str
            - reason: str
            - amount: Decimal
            - is_justified: bool
            - clause_ref: str
            - reference_doc: str
        """
        buyer = get_retailer_profile(buyer_id)
        if not buyer:
            raise ValueError(f"Comprador no registrado en catálogo: '{buyer_id}'")

        supplier = DEFAULT_SUPPLIER_PROFILE
        vendor_id = supplier["vendor_id"]
        customer_id = f"CUST-{buyer.buyer_id}"
        po_id = f"PO-{case_id.upper()[:8]}-{uuid.uuid4().hex[:4].upper()}"
        invoice_id = f"INV-{case_id.upper()[:8]}-{uuid.uuid4().hex[:4].upper()}"
        delivery_id = f"DEL-{case_id.upper()[:8]}-{uuid.uuid4().hex[:4].upper()}"
        payment_id = f"PAY-{case_id.upper()[:8]}-{uuid.uuid4().hex[:4].upper()}"
        contract_id = f"CTR-{buyer.buyer_id}-2026"

        # 1. Procesar items y totales
        po_items: List[PurchaseOrderItem] = []
        inv_items: List[InvoiceItem] = []
        del_items: List[DeliveryItem] = []
        gt_line_items: List[GroundTruthLineItem] = []

        po_total = Decimal("0.00")
        subtotal = Decimal("0.00")
        has_delivery_discrepancy = False

        for spec in items_spec:
            sku = spec["sku"]
            desc = spec.get("description", f"Producto {sku}")
            ord_qty = int(spec.get("ordered_qty", spec.get("invoiced_qty", 10)))
            inv_qty = int(spec.get("invoiced_qty", ord_qty))
            del_qty = int(spec.get("delivered_qty", inv_qty))
            rec_qty = int(spec.get("received_qty", del_qty))
            dam_qty = int(spec.get("damaged_qty", 0))
            miss_qty = max(0, inv_qty - rec_qty)

            agr_price = _quantize(spec.get("agreed_price", Decimal("100.00")))
            inv_price = _quantize(spec.get("invoiced_price", agr_price))

            po_line_total = _quantize(Decimal(ord_qty) * agr_price)
            inv_line_total = _quantize(Decimal(inv_qty) * inv_price)

            po_total += po_line_total
            subtotal += inv_line_total

            notes = spec.get("notes", "Recibido de conformidad en muelle")
            if miss_qty > 0 or dam_qty > 0:
                has_delivery_discrepancy = True
                if miss_qty > 0 and dam_qty > 0:
                    notes = f"Discrepancia en tarima: {miss_qty} faltantes y {dam_qty} averiados. Sello de muelle."
                elif miss_qty > 0:
                    notes = f"Faltante físico en muelle: {miss_qty} unidades ausentes. Anotado en remisión."
                elif dam_qty > 0:
                    notes = f"Mercancía averiada: {dam_qty} unidades rotas con acta fotográfica."

            po_items.append(PurchaseOrderItem(
                item_id=sku,
                description=desc,
                ordered_quantity=ord_qty,
                agreed_unit_price=agr_price,
                total_price=po_line_total
            ))

            inv_items.append(InvoiceItem(
                item_id=sku,
                description=desc,
                quantity=inv_qty,
                unit_price=inv_price,
                total_price=inv_line_total
            ))

            del_items.append(DeliveryItem(
                item_id=sku,
                quantity_delivered=del_qty,
                quantity_received=rec_qty,
                missing_quantity=miss_qty,
                damaged_quantity=dam_qty,
                notes=notes
            ))

            gt_line_items.append(GroundTruthLineItem(
                item_id=sku,
                description=desc,
                invoiced_qty=inv_qty,
                received_qty=rec_qty,
                missing_qty=miss_qty,
                damaged_qty=dam_qty,
                invoiced_price=inv_price,
                agreed_price=agr_price
            ))

        tax_amount = _quantize(subtotal * tax_rate)
        total_billed = subtotal + tax_amount

        # 2. Procesar Deducciones y Pagos
        pay_deductions: List[PaymentDeduction] = []
        gt_deductions: List[GroundTruthDeductionAssessment] = []
        total_deductions = Decimal("0.00")
        total_justified = Decimal("0.00")
        total_claimable = Decimal("0.00")
        justified_breakdown: Dict[str, str] = {}
        claimable_breakdown: Dict[str, str] = {}
        citations: List[str] = []

        for d_spec in deductions_spec:
            code = d_spec["code"]
            reason = d_spec["reason"]
            amount = _quantize(d_spec["amount"])
            is_justified = bool(d_spec["is_justified"])
            clause_ref = d_spec.get("clause_ref", "CLAUSE-GENERAL")
            ref_doc = d_spec.get("reference_doc", delivery_id)

            total_deductions += amount
            if is_justified:
                total_justified += amount
                justified_breakdown[code] = str(amount)
            else:
                total_claimable += amount
                claimable_breakdown[code] = str(amount)

            if clause_ref not in citations:
                citations.append(clause_ref)

            pay_deductions.append(PaymentDeduction(
                code=code,
                reason=reason,
                amount=amount,
                reference_doc=ref_doc
            ))

            gt_deductions.append(GroundTruthDeductionAssessment(
                code=code,
                amount=amount,
                reason=reason,
                is_justified=is_justified,
                governing_clause_id=clause_ref,
                factual_basis=reason,
                remedy_action="ACCEPT_AND_CREDIT" if is_justified else "REJECT_AND_CLAIM"
            ))

        amount_paid = total_billed - total_deductions
        if amount_paid < Decimal("0.00"):
            raise ValueError(f"Deducciones ({total_deductions}) exceden total facturado ({total_billed})")

        # 3. Construir Contrato
        clauses_list: List[ContractClause] = []
        if custom_clauses:
            for cc in custom_clauses:
                clauses_list.append(ContractClause(
                    clause_id=cc["clause_id"],
                    title=cc["title"],
                    text=cc["text"],
                    policy=cc.get("policy", "STANDARD"),
                    tolerance_percentage=_quantize(cc.get("tolerance_percentage", Decimal("0.00")))
                ))
        else:
            for rc in buyer.contract_clauses:
                clauses_list.append(ContractClause(
                    clause_id=rc.clause_id,
                    title=rc.title,
                    text=rc.text,
                    policy=rc.policy,
                    tolerance_percentage=rc.tolerance_percentage
                ))

        # Seleccionar almacén y supervisor
        warehouse_loc = buyer.primary_cedis_list[0] if buyer.primary_cedis_list else "CEDIS Central Muelle 1"
        supervisor_name = buyer.warehouse_supervisors[0] if buyer.warehouse_supervisors else "Jefe de Almacén General"

        # 4. Validar e Instanciar Modelos Pydantic
        invoice_obj = Invoice(
            invoice_id=invoice_id,
            vendor_id=vendor_id,
            customer_id=customer_id,
            po_reference=po_id,
            issue_date=issue_date,
            currency=currency,
            items=inv_items,
            subtotal=subtotal,
            tax=tax_amount,
            total_amount=total_billed
        )

        po_obj = PurchaseOrder(
            po_id=po_id,
            vendor_id=vendor_id,
            customer_id=customer_id,
            order_date=order_date,
            currency=currency,
            items=po_items,
            total_amount=po_total
        )

        delivery_obj = DeliveryNote(
            delivery_id=delivery_id,
            po_reference=po_id,
            delivery_date=delivery_date,
            received_by=supervisor_name,
            warehouse_location=warehouse_loc,
            signed=True,
            discrepancy_reported=has_delivery_discrepancy,
            items=del_items
        )

        payment_obj = PaymentReceipt(
            payment_id=payment_id,
            invoice_reference=invoice_id,
            payment_date=payment_date,
            currency=currency,
            amount_paid=amount_paid,
            deductions=pay_deductions
        )

        contract_obj = CommercialContract(
            contract_id=contract_id,
            vendor_id=vendor_id,
            customer_id=customer_id,
            valid_from="2026-01-01",
            valid_to="2026-12-31",
            clauses=clauses_list
        )

        # Determinar acción comercial
        if total_claimable > Decimal("0.00") and total_justified > Decimal("0.00"):
            action_type = CommercialActionType.MIXED_RESOLUTION
            recommended_action_str = "EMIT_CREDIT_NOTE_AND_RECOVERY_LETTER"
        elif total_claimable > Decimal("0.00"):
            action_type = CommercialActionType.COLLECTION_LETTER
            recommended_action_str = "REJECT_AND_CLAIM"
        else:
            action_type = CommercialActionType.CREDIT_NOTE
            recommended_action_str = "ACCEPT_AND_CREDIT"

        difference = amount_paid - total_billed  # Negativo si hubo deducción

        # 5. Instanciar Ground Truth con validación de invariante estricta
        ground_truth_obj = GroundTruth(
            case_id=case_id,
            category=category,
            expected_action_type=action_type,
            billed_amount=total_billed,
            received_amount=amount_paid,
            difference=difference,
            expected_justified_amount=total_justified,
            expected_claimable_amount=total_claimable,
            line_items=gt_line_items,
            deductions=gt_deductions,
            required_clause_citations=citations,
            scenario_tags=[buyer.industry, category.value]
        )

        # Diccionario enriquecido para máxima compatibilidad con frontend y evaluador
        raw_gt = {
            "case_id": case_id,
            "category": category.value,
            "buyer_id": buyer.buyer_id,
            "buyer_name": buyer.trade_name,
            "industry": buyer.industry,
            "currency": currency,
            "billed_amount": str(total_billed),
            "received_amount": str(amount_paid),
            "difference": str(difference),
            "expected_justified_amount": str(total_justified),
            "expected_claimable_amount": str(total_claimable),
            "expected_confidence": 0.98,
            "justified_breakdown": justified_breakdown,
            "claimable_breakdown": claimable_breakdown,
            "required_clause_citations": citations,
            "recommended_commercial_action": recommended_action_str,
            "deductions": [d.model_dump(mode="json") for d in gt_deductions]
        }

        return CaseDossier(
            case_id=case_id,
            invoice=invoice_obj,
            purchase_order=po_obj,
            delivery=delivery_obj,
            payment=payment_obj,
            contract=contract_obj,
            ground_truth=ground_truth_obj,
            raw_ground_truth_dict=raw_gt
        )
