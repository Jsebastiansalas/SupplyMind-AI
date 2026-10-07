"""
Tests exhaustivos para la Fase 2: Modelos Pydantic de SupplyMind AI.

Verifica:
1. Instanciación y tipos correctos en todos los modelos.
2. Uso de Decimal para precisión financiera (nunca float).
3. Rechazo estricto de campos adicionales no esperados (extra='forbid').
4. Restricciones numéricas (cantidades >= 0, precios >= 0, confianza en [0.0, 1.0]).
5. Requisito de listas no vacías (min_length=1).
6. Alias para compatibilidad con LLM (evidence_used, confidence_score).
7. Formato visual del reporte final (formatted_display).
"""
from decimal import Decimal
import pytest
from pydantic import ValidationError

from data.models import (
    Invoice,
    InvoiceItem,
    PurchaseOrder,
    PurchaseOrderItem,
    DeliveryNote,
    DeliveryItem,
    PaymentReceipt,
    PaymentDeduction,
    CommercialContract,
    ContractClause,
    DisputeAnalysisReport,
)


class TestInvoiceModels:
    """Pruebas para Factura (Invoice) e InvoiceItem."""

    def test_valid_invoice(self):
        invoice = Invoice(
            invoice_id="INV-001",
            vendor_id="VEND-01",
            customer_id="CUST-01",
            po_reference="PO-100",
            issue_date="2026-10-01",
            currency="USD",
            items=[
                InvoiceItem(
                    item_id="ITEM-A",
                    description="Café Premium 1kg",
                    quantity=100,
                    unit_price=Decimal("10.00"),
                    total_price=Decimal("1000.00"),
                )
            ],
            subtotal=Decimal("1000.00"),
            tax=Decimal("0.00"),
            total_amount=Decimal("1000.00"),
        )
        assert invoice.invoice_id == "INV-001"
        assert invoice.total_amount == Decimal("1000.00")
        assert isinstance(invoice.items[0].unit_price, Decimal)

    def test_invoice_item_negative_quantity_fails(self):
        with pytest.raises(ValidationError) as exc:
            InvoiceItem(
                item_id="ITEM-A",
                description="Café",
                quantity=-5,
                unit_price=Decimal("10.00"),
                total_price=Decimal("0.00"),
            )
        assert "greater than or equal to 0" in str(exc.value)

    def test_invoice_item_negative_price_fails(self):
        with pytest.raises(ValidationError) as exc:
            InvoiceItem(
                item_id="ITEM-A",
                description="Café",
                quantity=10,
                unit_price=Decimal("-10.00"),
                total_price=Decimal("-100.00"),
            )
        assert "greater than or equal to 0" in str(exc.value)

    def test_invoice_empty_items_fails(self):
        with pytest.raises(ValidationError) as exc:
            Invoice(
                invoice_id="INV-002",
                vendor_id="VEND-01",
                customer_id="CUST-01",
                issue_date="2026-10-01",
                items=[],
                subtotal=Decimal("0.00"),
                total_amount=Decimal("0.00"),
            )
        assert "at least 1 item" in str(exc.value)

    def test_invoice_extra_field_forbidden(self):
        raw_payload = {
            "invoice_id": "INV-003",
            "vendor_id": "VEND-01",
            "customer_id": "CUST-01",
            "issue_date": "2026-10-01",
            "items": [
                {
                    "item_id": "ITEM-A",
                    "description": "Café",
                    "quantity": 1,
                    "unit_price": Decimal("1.00"),
                    "total_price": Decimal("1.00"),
                }
            ],
            "subtotal": Decimal("1.00"),
            "total_amount": Decimal("1.00"),
            "campo_no_autorizado": "hacker",
        }
        with pytest.raises(ValidationError) as exc:
            Invoice.model_validate(raw_payload)
        assert "extra_forbidden" in str(exc.value)


class TestPurchaseOrderModels:
    """Pruebas para PurchaseOrder y PurchaseOrderItem."""

    def test_valid_purchase_order(self):
        po = PurchaseOrder(
            po_id="PO-500",
            vendor_id="VEND-01",
            customer_id="CUST-01",
            order_date="2026-09-28",
            currency="USD",
            items=[
                PurchaseOrderItem(
                    item_id="ITEM-1",
                    description="Harina 25kg",
                    ordered_quantity=50,
                    agreed_unit_price=Decimal("20.00"),
                    total_price=Decimal("1000.00"),
                )
            ],
            total_amount=Decimal("1000.00"),
        )
        assert po.po_id == "PO-500"
        assert po.items[0].ordered_quantity == 50

    def test_po_empty_items_fails(self):
        with pytest.raises(ValidationError):
            PurchaseOrder(
                po_id="PO-501",
                vendor_id="VEND-01",
                customer_id="CUST-01",
                order_date="2026-09-28",
                items=[],
                total_amount=Decimal("0.00"),
            )


class TestDeliveryNoteModels:
    """Pruebas para DeliveryNote y DeliveryItem."""

    def test_valid_delivery_note_defaults(self):
        delivery = DeliveryNote(
            delivery_id="DEL-101",
            po_reference="PO-500",
            delivery_date="2026-10-02",
            received_by="Carlos Gómez (Almacén Central)",
            warehouse_location="Bodega BOG-01",
            items=[
                DeliveryItem(
                    item_id="ITEM-1",
                    quantity_delivered=50,
                    quantity_received=40,
                    missing_quantity=10,
                )
            ],
        )
        assert delivery.signed is True
        assert delivery.discrepancy_reported is False
        assert delivery.items[0].damaged_quantity == 0
        assert delivery.items[0].missing_quantity == 10

    def test_delivery_negative_missing_quantity_fails(self):
        with pytest.raises(ValidationError):
            DeliveryItem(
                item_id="ITEM-1",
                quantity_delivered=50,
                quantity_received=50,
                missing_quantity=-2,
            )


class TestPaymentReceiptModels:
    """Pruebas para PaymentReceipt y PaymentDeduction."""

    def test_valid_payment_with_deductions(self):
        receipt = PaymentReceipt(
            payment_id="PAY-880",
            invoice_reference="INV-001",
            payment_date="2026-10-05",
            currency="USD",
            amount_paid=Decimal("800.00"),
            deductions=[
                PaymentDeduction(
                    code="DED-FALTANTE",
                    reason="Deducción por 10 unidades no recibidas",
                    amount=Decimal("200.00"),
                    reference_doc="DEL-101",
                )
            ],
        )
        assert receipt.amount_paid == Decimal("800.00")
        assert len(receipt.deductions) == 1
        assert receipt.deductions[0].amount == Decimal("200.00")

    def test_valid_payment_empty_deductions_default(self):
        receipt = PaymentReceipt(
            payment_id="PAY-881",
            invoice_reference="INV-001",
            payment_date="2026-10-05",
            amount_paid=Decimal("1000.00"),
        )
        assert receipt.deductions == []


class TestCommercialContractModels:
    """Pruebas para CommercialContract y ContractClause."""

    def test_valid_contract(self):
        contract = CommercialContract(
            contract_id="CTR-2026-01",
            vendor_id="VEND-01",
            customer_id="CUST-01",
            valid_from="2026-01-01",
            valid_to="2026-12-31",
            clauses=[
                ContractClause(
                    clause_id="CLAUSE-4.2",
                    title="Deducciones por faltantes en entrega",
                    text="El comprador podrá deducir del pago el valor acordado de unidades faltantes si la remisión está firmada con novedad.",
                    policy="allow_shortage_deduction_if_signed",
                    tolerance_percentage=Decimal("0.00"),
                )
            ],
        )
        assert contract.contract_id == "CTR-2026-01"
        assert contract.clauses[0].policy == "allow_shortage_deduction_if_signed"


class TestDisputeAnalysisReportModel:
    """Pruebas para el reporte final de la disputa comercial."""

    def test_valid_dispute_report_direct_init(self):
        report = DisputeAnalysisReport(
            case_id="case_001",
            currency="USD",
            billed_amount=Decimal("9000.00"),
            received_amount=Decimal("8200.00"),
            difference=Decimal("-800.00"),
            root_cause="Faltante físico comprobado en remisión",
            evidence=[
                "Faltante de 10 unidades en remisión DEL-9912",
                "Cláusula contractual 4.2 autoriza deducción",
            ],
            justified_amount=Decimal("800.00"),
            claimable_amount=Decimal("0.00"),
            confidence=0.98,
            recommended_action="Aceptar deducción y emitir Nota de Crédito por $800.00 USD",
        )
        assert report.case_id == "case_001"
        assert report.difference == Decimal("-800.00")
        assert len(report.evidence) == 2
        assert report.confidence == 0.98

    def test_valid_dispute_report_with_aliases(self):
        raw_payload = {
            "case_id": "case_001",
            "currency": "USD",
            "billed_amount": Decimal("9000.00"),
            "received_amount": Decimal("8200.00"),
            "difference": Decimal("-800.00"),
            "root_cause": "Faltante físico comprobado en remisión",
            "evidence_used": [
                "Faltante de 10 unidades en remisión DEL-9912",
                "Cláusula contractual 4.2 autoriza deducción",
            ],
            "justified_amount": Decimal("800.00"),
            "claimable_amount": Decimal("0.00"),
            "confidence_score": 0.98,
            "recommended_action": "Aceptar deducción y emitir Nota de Crédito por $800.00 USD",
        }
        report = DisputeAnalysisReport.model_validate(raw_payload)
        assert report.case_id == "case_001"
        assert report.difference == Decimal("-800.00")
        assert len(report.evidence) == 2
        assert report.confidence == 0.98

    def test_confidence_out_of_bounds_fails(self):
        with pytest.raises(ValidationError):
            DisputeAnalysisReport(
                case_id="case_001",
                billed_amount=Decimal("9000.00"),
                received_amount=Decimal("9000.00"),
                difference=Decimal("0.00"),
                root_cause="Sin novedad",
                evidence=["Ninguna"],
                justified_amount=Decimal("0.00"),
                claimable_amount=Decimal("0.00"),
                confidence=1.5,  # Debe ser <= 1.0
                recommended_action="Cerrar",
            )

    def test_negative_claimable_amount_fails(self):
        with pytest.raises(ValidationError):
            DisputeAnalysisReport(
                case_id="case_001",
                billed_amount=Decimal("9000.00"),
                received_amount=Decimal("9000.00"),
                difference=Decimal("0.00"),
                root_cause="Sin novedad",
                evidence=["Ninguna"],
                justified_amount=Decimal("0.00"),
                claimable_amount=Decimal("-10.00"),  # ge=0
                confidence=0.95,
                recommended_action="Cerrar",
            )

    def test_formatted_display_string(self):
        report = DisputeAnalysisReport(
            case_id="case_001",
            currency="USD",
            billed_amount=Decimal("9000.00"),
            received_amount=Decimal("8200.00"),
            difference=Decimal("-800.00"),
            root_cause="Faltante físico comprobado",
            evidence=["Faltante en DEL-9912"],
            justified_amount=Decimal("800.00"),
            claimable_amount=Decimal("0.00"),
            confidence=0.98,
            recommended_action="Emitir Nota de Crédito",
        )
        output = report.formatted_display()
        assert "DISPUTE ANALYSIS REPORT" in output
        assert "case_001" in output
        assert "$9,000.00 USD" in output
        assert "$-800.00 USD" in output
        assert "98.0%" in output
        assert "Emitir Nota de Crédito" in output
