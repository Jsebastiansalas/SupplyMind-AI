"""
tests/test_evidence_binding.py
Suite de pruebas para el Pilar 3: Anclaje Fáctico Estricto y Certificación Zero Uncited Claims.
Verifica que cada centavo justificado, reclamable o deducido tenga un puntero fáctico
verificable (Factura, POD firmado, Orden de Compra o Cláusula Contractual).
"""

from decimal import Decimal
import pytest
from fastapi.testclient import TestClient

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
    EvidenceBindingManifest,
)
from tools.reconciliation_engine.engine import reconcile_dispute_data
from tools.contract_analyzer.rules import evaluate_contract_compliance
from tools.report_generator.generator import build_dispute_report
from agent.guardrails.evidence_binder import StrictEvidenceBinder
from agent.core.skynet_runner import SkynetRunner
from api.main import app


def _create_sample_case_documents(signed_delivery: bool = True, with_contract_clause: bool = True):
    invoice = Invoice(
        invoice_id="INV-TEST-301",
        vendor_id="VEN-ACME",
        customer_id="CUST-B2B",
        po_reference="PO-TEST-301",
        issue_date="2026-02-01",
        currency="USD",
        items=[
            InvoiceItem(item_id="SKU-A", description="Producto Alfa", quantity=100, unit_price=Decimal("100.00"), total_price=Decimal("10000.00")),
            InvoiceItem(item_id="SKU-B", description="Producto Beta", quantity=50, unit_price=Decimal("50.00"), total_price=Decimal("2500.00")),
        ],
        subtotal=Decimal("12500.00"),
        tax=Decimal("0.00"),
        total_amount=Decimal("12500.00")
    )

    po = PurchaseOrder(
        po_id="PO-TEST-301",
        vendor_id="VEN-ACME",
        customer_id="CUST-B2B",
        order_date="2026-01-25",
        currency="USD",
        items=[
            PurchaseOrderItem(item_id="SKU-A", description="Producto Alfa", ordered_quantity=100, agreed_unit_price=Decimal("100.00"), total_price=Decimal("10000.00")),
            PurchaseOrderItem(item_id="SKU-B", description="Producto Beta", ordered_quantity=50, agreed_unit_price=Decimal("50.00"), total_price=Decimal("2500.00")),
        ],
        total_amount=Decimal("12500.00")
    )

    delivery = DeliveryNote(
        delivery_id="DEL-TEST-301",
        po_reference="PO-TEST-301",
        delivery_date="2026-02-05",
        received_by="Almacenero Certificado",
        warehouse_location="CEDIS-NORTE",
        signed=signed_delivery,
        discrepancy_reported=True,
        items=[
            DeliveryItem(item_id="SKU-A", quantity_delivered=100, quantity_received=95, missing_quantity=5, damaged_quantity=0),
            DeliveryItem(item_id="SKU-B", quantity_delivered=50, quantity_received=50, missing_quantity=0, damaged_quantity=0),
        ]
    )

    payment = PaymentReceipt(
        payment_id="PAY-TEST-301",
        invoice_reference="INV-TEST-301",
        payment_date="2026-02-15",
        currency="USD",
        amount_paid=Decimal("10750.00"),
        deductions=[
            PaymentDeduction(code="SHORTAGE_SKU_A", reason="Faltante 5 uds SKU-A", amount=Decimal("500.00"), reference_doc="DEL-TEST-301"),
            PaymentDeduction(code="PENALTY_ASN_01", reason="Penalidad ASN Accuracy", amount=Decimal("1250.00"), reference_doc="ASN-SYS"),
        ]
    )

    clauses = []
    if with_contract_clause:
        clauses.append(
            ContractClause(
                clause_id="CLAUSE-ASN",
                title="Exactitud ASN",
                text="Penalidad por discrepancia ASN sobre entregas de proveedor.",
                policy="ASN_ACCURACY",
                tolerance_percentage=Decimal("0.00")
            )
        )
    else:
        clauses.append(
            ContractClause(
                clause_id="CLAUSE-GENERIC",
                title="Cláusula General",
                text="Términos generales sin políticas de penalización comercial.",
                policy="STANDARD",
                tolerance_percentage=Decimal("0.00")
            )
        )

    contract = CommercialContract(
        contract_id="CTR-TEST-301",
        vendor_id="VEN-ACME",
        customer_id="CUST-B2B",
        valid_from="2026-01-01",
        valid_to="2026-12-31",
        clauses=clauses
    )

    return invoice, po, delivery, payment, contract


def test_pristine_case_evidence_binding():
    """Valida el anclaje fáctico perfecto al 100% de un caso respaldado."""
    inv, po, deliv, pay, ctr = _create_sample_case_documents(signed_delivery=True, with_contract_clause=True)
    rec = reconcile_dispute_data(inv, po, deliv, pay)
    ev = evaluate_contract_compliance(ctr, rec)

    report = build_dispute_report(
        case_id="case_test_p3_pristine",
        reconciliation=rec,
        contract_evaluation=ev,
        loaded_documents={"invoice": inv, "purchase_order": po, "delivery": deliv, "payment": pay, "contract": ctr}
    )

    manifest = report.evidence_manifest
    assert manifest is not None
    assert isinstance(manifest, EvidenceBindingManifest)
    assert manifest.binding_verdict == "FULL_EVIDENCE_BINDING_VERIFIED"
    assert manifest.backing_ratio_pct == 100.0
    assert manifest.unbacked_claims_count == 0
    assert len(manifest.cautelar_items) == 0
    assert manifest.total_backed_amount > Decimal("0.00")

    # Verificar que los punteros incluyan Factura, Pago, Remisión y Contrato
    doc_types = {p.doc_type for p in manifest.evidence_pointers}
    assert "INVOICE" in doc_types
    assert "PAYMENT" in doc_types
    assert "DELIVERY" in doc_types
    assert "CONTRACT" in doc_types


def test_unbacked_deduction_cautelar_detection():
    """Detecta partidas cautelares cuando el retailer retiene montos sin cláusula contractual habilitante."""
    inv, po, deliv, pay, ctr = _create_sample_case_documents(signed_delivery=True, with_contract_clause=False)
    rec = reconcile_dispute_data(inv, po, deliv, pay)
    ev = evaluate_contract_compliance(ctr, rec)

    initial_confidence = 0.98
    report = build_dispute_report(
        case_id="case_test_p3_unbacked",
        reconciliation=rec,
        contract_evaluation=ev,
        confidence=initial_confidence,
        loaded_documents={"invoice": inv, "purchase_order": po, "delivery": deliv, "payment": pay, "contract": ctr}
    )

    manifest = report.evidence_manifest
    assert manifest is not None
    assert manifest.binding_verdict in ["CAUTIONARY_ITEMS_DETECTED", "CRITICAL_UNBACKED_DEFICIT"]
    assert manifest.unbacked_claims_count > 0
    assert len(manifest.cautelar_items) > 0
    assert any("PENALTY_ASN" in c for c in manifest.cautelar_items)

    # Debe penalizar la confianza del dictamen
    assert report.confidence < initial_confidence
    assert manifest.confidence_penalty > 0.0


def test_unsigned_pod_delivery_cautelar_flag():
    """Detecta que una remisión sin firma física de muelle genera partida cautelar probatoria."""
    inv, po, deliv, pay, ctr = _create_sample_case_documents(signed_delivery=False, with_contract_clause=True)
    rec = reconcile_dispute_data(inv, po, deliv, pay)
    ev = evaluate_contract_compliance(ctr, rec)

    report = build_dispute_report(
        case_id="case_test_p3_unsigned",
        reconciliation=rec,
        contract_evaluation=ev,
        loaded_documents={"invoice": inv, "purchase_order": po, "delivery": deliv, "payment": pay, "contract": ctr}
    )

    manifest = report.evidence_manifest
    assert manifest is not None
    assert any("POD" in c or "firma" in c for c in manifest.cautelar_items)
    
    # El puntero del faltante físico debe estar marcado como no respaldado físicamente
    del_pointers = [p for p in manifest.evidence_pointers if p.doc_type == "DELIVERY"]
    assert len(del_pointers) > 0
    assert del_pointers[0].is_backed_by_physical_proof is False
    assert del_pointers[0].status == "CAUTELAR_NO_ACREDITADA"


def test_missing_documents_binding_resilience():
    """Tolera expedientes donde falta la factura o el pago original imputando estatus cautelar."""
    inv, po, deliv, pay, ctr = _create_sample_case_documents()
    rec = reconcile_dispute_data(inv, po, deliv, pay)
    ev = evaluate_contract_compliance(ctr, rec)

    # Pasar documentos sin factura
    report = build_dispute_report(
        case_id="case_test_p3_no_inv",
        reconciliation=rec,
        contract_evaluation=ev,
        loaded_documents={"purchase_order": po, "delivery": deliv, "payment": pay, "contract": ctr}
    )

    manifest = report.evidence_manifest
    assert manifest is not None
    assert manifest.unbacked_claims_count > 0
    assert any("Factura" in c for c in manifest.cautelar_items)


def test_skynet_runner_fast_path_evidence_manifest():
    """Verifica que el corredor Skynet produce e integra el EvidenceBindingManifest end-to-end."""
    runner = SkynetRunner(case_id="case_001", fast_path=True, use_cache=False)
    report = runner.run()

    assert report is not None
    assert report.evidence_manifest is not None
    manifest = report.evidence_manifest
    assert isinstance(manifest, EvidenceBindingManifest)
    assert manifest.case_id == "case_001"
    assert manifest.backing_ratio_pct > 0.0
    assert len(manifest.evidence_pointers) > 0


def test_evidence_manifest_api_endpoint():
    """Verifica que el endpoint GET /api/cases/{case_id}/evidence-manifest responda 200 con el manifiesto completo."""
    client = TestClient(app)
    response = client.get("/api/cases/case_001/evidence-manifest")
    assert response.status_code == 200
    data = response.json()

    assert data["case_id"] == "case_001"
    assert "binding_verdict" in data
    assert "backing_ratio_pct" in data
    assert "evidence_pointers" in data
    assert isinstance(data["evidence_pointers"], list)
    assert len(data["evidence_pointers"]) > 0
