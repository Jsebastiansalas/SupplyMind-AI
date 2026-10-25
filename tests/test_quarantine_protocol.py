"""
tests/test_quarantine_protocol.py
Suite de pruebas para el Pilar 4: Semáforo de Integridad y Protocolo Forense de Cuarentena Documental.
Verifica que casos con contaminación cruzada de entidades, anacronismos o corrupción
crítica sean aislados preventivamente bajo el ForensicQuarantineDocket.
"""

from decimal import Decimal
from datetime import datetime, timezone
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
    DocumentHealthAudit,
    ForensicQuarantineDocket,
    DisputeAnalysisReport,
)
from agent.guardrails.quarantine_manager import QuarantineManager
from tools.report_generator.generator import build_dispute_report
from tools.reconciliation_engine.engine import reconcile_dispute_data
from tools.contract_analyzer.rules import evaluate_contract_compliance
from api.main import app


def _build_base_pristine_docs():
    invoice = Invoice(
        invoice_id="INV-Q4-001",
        vendor_id="VEN-GLOBAL",
        customer_id="WALMART-CORP",
        po_reference="PO-Q4-001",
        issue_date="2026-03-05",
        currency="USD",
        items=[InvoiceItem(item_id="SKU-1", description="Item 1", quantity=100, unit_price=Decimal("50.00"), total_price=Decimal("5000.00"))],
        subtotal=Decimal("5000.00"),
        tax=Decimal("0.00"),
        total_amount=Decimal("5000.00")
    )
    po = PurchaseOrder(
        po_id="PO-Q4-001",
        vendor_id="VEN-GLOBAL",
        customer_id="WALMART-CORP",
        order_date="2026-03-01",
        currency="USD",
        items=[PurchaseOrderItem(item_id="SKU-1", description="Item 1", ordered_quantity=100, agreed_unit_price=Decimal("50.00"), total_price=Decimal("5000.00"))],
        total_amount=Decimal("5000.00")
    )
    delivery = DeliveryNote(
        delivery_id="DEL-Q4-001",
        po_reference="PO-Q4-001",
        delivery_date="2026-03-08",
        received_by="Walmart CEDIS Central",
        warehouse_location="CEDIS-01",
        signed=True,
        discrepancy_reported=False,
        items=[DeliveryItem(item_id="SKU-1", quantity_delivered=100, quantity_received=100, missing_quantity=0, damaged_quantity=0)]
    )
    payment = PaymentReceipt(
        payment_id="PAY-Q4-001",
        invoice_reference="INV-Q4-001",
        payment_date="2026-03-20",
        currency="USD",
        amount_paid=Decimal("5000.00"),
        deductions=[]
    )
    contract = CommercialContract(
        contract_id="CTR-Q4-001",
        vendor_id="VEN-GLOBAL",
        customer_id="WALMART-CORP",
        valid_from="2026-01-01",
        valid_to="2026-12-31",
        clauses=[ContractClause(clause_id="C-1", title="Estándar", text="Términos estándar.", policy="STD", tolerance_percentage=Decimal("0.00"))]
    )
    return invoice, po, delivery, payment, contract


def test_cross_entity_contamination_triggers_quarantine():
    """Detecta contaminación cruzada si la remisión de entrega corresponde a otro cliente."""
    inv, po, deliv, pay, ctr = _build_base_pristine_docs()

    # Contaminación intencional: la remisión fue recibida y firmada por AMAZON FBA en vez de WALMART
    deliv_contaminated = DeliveryNote(
        delivery_id="DEL-CONTAMINATED-99",
        po_reference="PO-AMAZON-888",
        delivery_date="2026-03-08",
        received_by="Amazon Fulfillment Center DFW7",
        warehouse_location="AMZ-DFW7",
        signed=True,
        discrepancy_reported=False,
        items=[DeliveryItem(item_id="SKU-1", quantity_delivered=100, quantity_received=100, missing_quantity=0, damaged_quantity=0)]
    )

    docs = {"invoice": inv, "purchase_order": po, "delivery": deliv_contaminated, "payment": pay, "contract": ctr}
    health = DocumentHealthAudit(
        case_id="case_cross_entity",
        health_score=100.0,
        status="PRISTINE",
        is_healthy=True
    )

    updated_health, docket = QuarantineManager.evaluate_quarantine("case_cross_entity", docs, health)

    assert updated_health.status == "QUARANTINE"
    assert updated_health.is_healthy is False
    assert docket is not None
    assert docket.is_settlement_blocked is True
    assert docket.severity == "CRITICAL_CONTAMINATION"
    assert docket.operator_override_permitted is False
    assert any("Amazon" in r or "Contaminación cruzada" in r for r in docket.blocking_reasons)
    assert "CROSS_ENTITY_CUSTOMER_INVARIANT_VIOLATED" in docket.violated_invariants


def test_date_anachronism_triggers_quarantine():
    """Detecta un anacronismo temporal si la fecha de entrega antecede a la emisión de la orden de compra."""
    inv, po, deliv, pay, ctr = _build_base_pristine_docs()

    # Entrega registrada 40 días antes de que se emitiera la orden de compra
    deliv_anachronistic = DeliveryNote(
        delivery_id="DEL-ANACHRONIC-01",
        po_reference="PO-Q4-001",
        delivery_date="2026-01-15",
        received_by="Walmart CEDIS Central",
        warehouse_location="CEDIS-01",
        signed=True,
        discrepancy_reported=False,
        items=[DeliveryItem(item_id="SKU-1", quantity_delivered=100, quantity_received=100, missing_quantity=0, damaged_quantity=0)]
    )

    docs = {"invoice": inv, "purchase_order": po, "delivery": deliv_anachronistic, "payment": pay, "contract": ctr}
    health = DocumentHealthAudit(
        case_id="case_anachronism",
        health_score=95.0,
        status="AUTO_REPAIRED",
        is_healthy=True
    )

    updated_health, docket = QuarantineManager.evaluate_quarantine("case_anachronism", docs, health)

    assert updated_health.status == "QUARANTINE"
    assert docket is not None
    assert docket.severity == "ANACHRONISM_RISK"
    assert any("Anacronismo temporal" in r for r in docket.blocking_reasons)
    assert "TEMPORAL_CAUSALITY_INVARIANT_VIOLATED" in docket.violated_invariants


def test_low_health_score_triggers_quarantine():
    """Expedientes con salud documental crítica (<50%) entran automáticamente en cuarentena."""
    inv, po, deliv, pay, ctr = _build_base_pristine_docs()
    docs = {"invoice": inv}  # Faltan 4 documentos primarios

    health = DocumentHealthAudit(
        case_id="case_severe_deficit",
        health_score=35.0,
        status="QUARANTINE",
        is_healthy=False,
        documents_missing=["delivery", "payment", "contract", "purchase_order"]
    )

    updated_health, docket = QuarantineManager.evaluate_quarantine("case_severe_deficit", docs, health)

    assert updated_health.status == "QUARANTINE"
    assert docket is not None
    assert docket.severity == "SEVERE_DOCUMENT_DEFICIT"
    assert any("Salud documental deficiente" in r for r in docket.blocking_reasons)
    assert len(docket.remediation_steps) > 0


def test_pristine_case_passes_quarantine_cleanly():
    """Un caso íntegro no genera expediente de cuarentena y mantiene estatus PRISTINE."""
    inv, po, deliv, pay, ctr = _build_base_pristine_docs()
    docs = {"invoice": inv, "purchase_order": po, "delivery": deliv, "payment": pay, "contract": ctr}

    health = DocumentHealthAudit(
        case_id="case_pristine_clean",
        health_score=100.0,
        status="PRISTINE",
        is_healthy=True
    )

    updated_health, docket = QuarantineManager.evaluate_quarantine("case_pristine_clean", docs, health)

    assert updated_health.status == "PRISTINE"
    assert updated_health.is_healthy is True
    assert docket is None


def test_quarantine_enforcement_on_report():
    """Verifica que el informe final bloquee la acción de emisión de nota de crédito si está en cuarentena."""
    inv, po, deliv, pay, ctr = _build_base_pristine_docs()
    rec = reconcile_dispute_data(inv, po, deliv, pay)
    ev = evaluate_contract_compliance(ctr, rec)

    docket = ForensicQuarantineDocket(
        quarantine_id="FRQ-TEST-ISOLATION-01",
        case_id="case_test_block",
        severity="CRITICAL_CONTAMINATION",
        is_settlement_blocked=True,
        blocking_reasons=["Contaminación cruzada de cliente con entidad no relacionada."],
        remediation_steps=["Cargar el POD correcto."]
    )

    health_quarantined = DocumentHealthAudit(
        case_id="case_test_block",
        health_score=40.0,
        status="QUARANTINE",
        is_healthy=False,
        quarantine_docket=docket
    )

    report = build_dispute_report(
        case_id="case_test_block",
        reconciliation=rec,
        contract_evaluation=ev,
        confidence=0.95,
        health_audit=health_quarantined,
        loaded_documents={"invoice": inv, "purchase_order": po, "delivery": deliv, "payment": pay, "contract": ctr}
    )

    assert report.quarantine_docket is not None
    assert report.confidence <= 0.20
    assert "BLOQUEADA" in report.recommended_action or "BLOQUEADAS" in report.recommended_action
    assert "PROTOCOLO FORENSE" in report.recommended_action


def test_quarantine_docket_api_endpoints():
    """Prueba que el endpoint GET /api/cases/{case_id}/quarantine-docket responda adecuadamente."""
    client = TestClient(app)

    # 1. Caso base PRISTINE (case_001) -> NOT_QUARANTINED
    resp_clean = client.get("/api/cases/case_001/quarantine-docket")
    assert resp_clean.status_code == 200
    data_clean = resp_clean.json()
    assert data_clean["status"] == "NOT_QUARANTINED"
    assert data_clean["is_settlement_blocked"] is False

    # 2. Caso con archivos corruptos (test_corrupt_json) -> QUARANTINED
    resp_corrupt = client.get("/api/cases/test_corrupt_json/quarantine-docket")
    assert resp_corrupt.status_code == 200
    data_corrupt = resp_corrupt.json()
    assert data_corrupt["status"] == "QUARANTINED"
    assert data_corrupt["is_settlement_blocked"] is True
    assert "docket" in data_corrupt
    assert data_corrupt["docket"]["severity"] is not None
