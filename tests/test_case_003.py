import json
from pathlib import Path
from decimal import Decimal
from data.models import (
    Invoice,
    PurchaseOrder,
    DeliveryNote,
    PaymentReceipt,
    CommercialContract
)
from tools.reconciliation_engine.engine import reconcile_dispute_data
from tools.contract_analyzer.rules import evaluate_contract_compliance
from tools.report_generator.generator import build_dispute_report

CASE_DIR = Path(__file__).resolve().parent.parent / "data" / "cases" / "case_003"

def test_case_003_files_exist():
    assert (CASE_DIR / "invoice.json").exists()
    assert (CASE_DIR / "purchase_order.json").exists()
    assert (CASE_DIR / "delivery.json").exists()
    assert (CASE_DIR / "payment.json").exists()
    assert (CASE_DIR / "contract.json").exists()

def test_case_003_invoice_validates():
    with open(CASE_DIR / "invoice.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    invoice = Invoice.model_validate(data)
    assert invoice.invoice_id == "INV-99402"
    assert invoice.total_amount == Decimal("15000.00")
    assert invoice.items[0].unit_price == Decimal("150.00")

def test_case_003_purchase_order_validates():
    with open(CASE_DIR / "purchase_order.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    po = PurchaseOrder.model_validate(data)
    assert po.po_id == "PO-55100"
    assert po.total_amount == Decimal("12000.00")
    assert po.items[0].agreed_unit_price == Decimal("120.00")

def test_case_003_delivery_validates():
    with open(CASE_DIR / "delivery.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    delivery = DeliveryNote.model_validate(data)
    assert delivery.delivery_id == "DEL-33019"
    assert delivery.signed is True
    assert delivery.items[0].missing_quantity == 0
    assert delivery.items[0].damaged_quantity == 0

def test_case_003_payment_validates():
    with open(CASE_DIR / "payment.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    payment = PaymentReceipt.model_validate(data)
    assert payment.payment_id == "PAY-4401"
    assert payment.amount_paid == Decimal("12000.00")
    assert len(payment.deductions) == 1
    assert payment.deductions[0].amount == Decimal("3000.00")

def test_case_003_contract_validates():
    with open(CASE_DIR / "contract.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    contract = CommercialContract.model_validate(data)
    assert contract.contract_id == "CTR-SUPERTIENDAS-2026"
    assert any(c.clause_id == "CLAUSE-3.1" for c in contract.clauses)

def test_case_003_deterministic_reconciliation():
    with open(CASE_DIR / "invoice.json", "r", encoding="utf-8") as f:
        invoice = Invoice.model_validate(json.load(f))
    with open(CASE_DIR / "purchase_order.json", "r", encoding="utf-8") as f:
        po = PurchaseOrder.model_validate(json.load(f))
    with open(CASE_DIR / "delivery.json", "r", encoding="utf-8") as f:
        delivery = DeliveryNote.model_validate(json.load(f))
    with open(CASE_DIR / "payment.json", "r", encoding="utf-8") as f:
        payment = PaymentReceipt.model_validate(json.load(f))
    with open(CASE_DIR / "contract.json", "r", encoding="utf-8") as f:
        contract = CommercialContract.model_validate(json.load(f))

    summary = reconcile_dispute_data(invoice, po, delivery, payment)
    assert summary.billed_amount == Decimal("15000.00")
    assert summary.received_amount == Decimal("12000.00")
    assert summary.difference == Decimal("-3000.00")
    assert summary.total_price_discrepancy_amount == Decimal("3000.00")
    assert summary.total_missing_amount == Decimal("0.00")
    assert summary.total_damaged_amount == Decimal("0.00")
    assert summary.justified_deductions_amount == Decimal("3000.00")
    assert summary.unjustified_deductions_amount == Decimal("0.00")
    assert summary.primary_discrepancy_type == "DIFERENCIA_DE_PRECIO"

    evaluation = evaluate_contract_compliance(contract, summary)
    assert evaluation.contractual_justification_valid is True
    assert any(m.clause_id == "CLAUSE-3.1" and m.is_deduction_authorized for m in evaluation.matches)

    report = build_dispute_report("case_003", summary, evaluation)
    assert report.case_id == "case_003"
    assert report.billed_amount == Decimal("15000.00")
    assert report.received_amount == Decimal("12000.00")
    assert report.difference == Decimal("-3000.00")
    assert report.justified_amount == Decimal("3000.00")
    assert report.claimable_amount == Decimal("0.00")
    assert report.confidence >= 0.90
    assert "precio" in report.root_cause.lower()

def test_case_003_skynet_runner_ask_simulated():
    from agent.core.skynet_runner import SkynetRunner
    runner = SkynetRunner(case_id="case_003")
    runner._ensure_case_loaded()
    
    ans_precio = runner._simulated_ask("¿Qué sobreprecio hubo en la factura?")
    assert "PROD-301" in ans_precio
    assert "150.00" in ans_precio
    assert "120.00" in ans_precio
    assert "3,000.00" in ans_precio

    ans_contrato = runner._simulated_ask("¿Qué cláusula del contrato autoriza la deducción?")
    assert "3.1" in ans_contrato

    ans_reclamable = runner._simulated_ask("¿Cuánto dinero podemos reclamar?")
    assert "0.00" in ans_reclamable

    ans_accion = runner._simulated_ask("¿Qué acción se debe tomar?")
    assert "nota de crédito" in ans_accion.lower() or "nota de credito" in ans_accion.lower()
