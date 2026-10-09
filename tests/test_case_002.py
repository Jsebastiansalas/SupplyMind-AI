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

CASE_DIR = Path(__file__).resolve().parent.parent / "data" / "cases" / "case_002"

def test_case_002_files_exist():
    assert (CASE_DIR / "invoice.json").exists()
    assert (CASE_DIR / "purchase_order.json").exists()
    assert (CASE_DIR / "delivery.json").exists()
    assert (CASE_DIR / "payment.json").exists()
    assert (CASE_DIR / "contract.json").exists()

def test_case_002_invoice_validates():
    with open(CASE_DIR / "invoice.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    invoice = Invoice.model_validate(data)
    assert invoice.invoice_id == "INV-88301"
    assert invoice.total_amount == Decimal("54200.00")
    assert len(invoice.items) == 4

def test_case_002_purchase_order_validates():
    with open(CASE_DIR / "purchase_order.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    po = PurchaseOrder.model_validate(data)
    assert po.po_id == "PO-44120"
    assert po.total_amount == Decimal("54200.00")
    assert len(po.items) == 4

def test_case_002_delivery_validates():
    with open(CASE_DIR / "delivery.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    delivery = DeliveryNote.model_validate(data)
    assert delivery.delivery_id == "DEL-12044"
    assert delivery.signed is True
    assert delivery.discrepancy_reported is True
    assert len(delivery.items) == 4
    # PROD-102 tiene 50 cajas faltantes
    assert delivery.items[1].item_id == "PROD-102"
    assert delivery.items[1].missing_quantity == 50

def test_case_002_payment_validates():
    with open(CASE_DIR / "payment.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    payment = PaymentReceipt.model_validate(data)
    assert payment.payment_id == "PAY-9931"
    assert payment.amount_paid == Decimal("37700.00")
    assert len(payment.deductions) == 3
    # Total de deducciones: $4000 + $6500 + $6000 = $16500
    total_ded = sum(d.amount for d in payment.deductions)
    assert total_ded == Decimal("16500.00")

def test_case_002_contract_validates():
    with open(CASE_DIR / "contract.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    contract = CommercialContract.model_validate(data)
    assert contract.contract_id == "CTR-MEGAMARKET-2026"
    clause_ids = [c.clause_id for c in contract.clauses]
    assert "CLAUSE-4.2" in clause_ids
    assert "CLAUSE-5.1" in clause_ids
    assert "CLAUSE-7.3" in clause_ids

def test_case_002_deterministic_reconciliation():
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
    assert summary.billed_amount == Decimal("54200.00")
    assert summary.received_amount == Decimal("37700.00")
    assert summary.difference == Decimal("-16500.00")
    assert summary.total_missing_amount == Decimal("4000.00")  # 50 * $80
    assert summary.total_damaged_amount == Decimal("0.00")
    assert summary.justified_deductions_amount == Decimal("4000.00")
    assert summary.unjustified_deductions_amount == Decimal("12500.00")  # $16500 - $4000

    evaluation = evaluate_contract_compliance(contract, summary)
    assert evaluation.contractual_justification_valid is True
    assert "12,500.00" in evaluation.summary_legal_assessment

    report = build_dispute_report("case_002", summary, evaluation)
    assert report.case_id == "case_002"
    assert report.billed_amount == Decimal("54200.00")
    assert report.received_amount == Decimal("37700.00")
    assert report.difference == Decimal("-16500.00")
    assert report.justified_amount == Decimal("4000.00")
    assert report.claimable_amount == Decimal("12500.00")
    assert report.confidence >= 0.90

def test_case_002_skynet_runner_ask_simulated():
    from agent.core.skynet_runner import SkynetRunner
    runner = SkynetRunner(case_id="case_002")
    runner._ensure_case_loaded()
    
    ans_faltante = runner._simulated_ask("¿Qué faltante de cajas hubo?")
    assert "PROD-102" in ans_faltante
    assert "50 cajas" in ans_faltante
    assert "4,000.00" in ans_faltante

    ans_contrato = runner._simulated_ask("¿Qué cláusula del contrato autoriza la deducción?")
    assert "4.2" in ans_contrato
    assert "5.1" in ans_contrato
    assert "7.3" in ans_contrato

    ans_reclamable = runner._simulated_ask("¿Cuánto dinero podemos reclamar?")
    assert "12,500.00" in ans_reclamable

    ans_monto = runner._simulated_ask("¿Cuánto pagó y cuánto se retuvo?")
    assert "37,700.00" in ans_monto
    assert "16,500.00" in ans_monto
    assert "4,000.00" in ans_monto
