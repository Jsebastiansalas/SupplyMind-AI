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

CASE_DIR = Path(__file__).resolve().parent.parent / "data" / "cases" / "case_001"

def test_case_001_files_exist():
    assert (CASE_DIR / "invoice.json").exists()
    assert (CASE_DIR / "purchase_order.json").exists()
    assert (CASE_DIR / "delivery.json").exists()
    assert (CASE_DIR / "payment.json").exists()
    assert (CASE_DIR / "contract.json").exists()

def test_case_001_invoice_validates():
    with open(CASE_DIR / "invoice.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    invoice = Invoice.model_validate(data)
    assert invoice.invoice_id == "INV-40102"
    assert invoice.total_amount == Decimal("9000.00")
    assert len(invoice.items) == 2

def test_case_001_purchase_order_validates():
    with open(CASE_DIR / "purchase_order.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    po = PurchaseOrder.model_validate(data)
    assert po.po_id == "PO-8821"
    assert po.total_amount == Decimal("9000.00")
    assert len(po.items) == 2

def test_case_001_delivery_validates():
    with open(CASE_DIR / "delivery.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    delivery = DeliveryNote.model_validate(data)
    assert delivery.delivery_id == "DEL-9912"
    assert delivery.signed is True
    assert delivery.discrepancy_reported is True
    assert delivery.items[1].missing_quantity == 10

def test_case_001_payment_validates():
    with open(CASE_DIR / "payment.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    payment = PaymentReceipt.model_validate(data)
    assert payment.payment_id == "PAY-7710"
    assert payment.amount_paid == Decimal("8200.00")
    assert len(payment.deductions) == 1
    assert payment.deductions[0].amount == Decimal("800.00")

def test_case_001_contract_validates():
    with open(CASE_DIR / "contract.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    contract = CommercialContract.model_validate(data)
    assert contract.contract_id == "CTR-RETAIL-2026"
    assert any(c.clause_id == "CLAUSE-4.2" for c in contract.clauses)
