"""
Pruebas unitarias determinísticas de ingesta y parseo de documentos PDF.
Valida la conversión de PDF a modelos estrictos Pydantic y su conciliación.
"""

from pathlib import Path
from decimal import Decimal
import pytest

from tools.document_reader.pdf_parser import PDFCaseParser
from tools.document_reader.reader import load_case_documents
from tools.reconciliation_engine.engine import reconcile_dispute_data
from tools.contract_analyzer.rules import evaluate_contract_compliance
from data.models import (
    Invoice,
    PurchaseOrder,
    DeliveryNote,
    PaymentReceipt,
    CommercialContract
)

CASE_005_DIR = Path("data/cases/case_005_amazon_shortage")
CASE_006_DIR = Path("data/cases/case_006_walmart_otif_pricing")

def test_parse_invoice_pdf_case_005():
    inv = PDFCaseParser.parse_invoice(CASE_005_DIR / "invoice.pdf")
    assert isinstance(inv, Invoice)
    assert inv.invoice_id == "INV-PAC-2026-4402"
    assert inv.total_amount == Decimal("48000.00")
    assert len(inv.items) == 2

def test_parse_purchase_order_pdf_case_005():
    po = PDFCaseParser.parse_purchase_order(CASE_005_DIR / "purchase_order.pdf")
    assert isinstance(po, PurchaseOrder)
    assert po.po_id == "PO-AMZ-2026-9041"
    assert po.total_amount == Decimal("48000.00")

def test_parse_delivery_pdf_case_005():
    deliv = PDFCaseParser.parse_delivery_note(CASE_005_DIR / "delivery.pdf")
    assert isinstance(deliv, DeliveryNote)
    assert deliv.delivery_id == "BOL-POD-77319"
    assert deliv.discrepancy_reported is True
    assert deliv.items[0].missing_quantity == 20

def test_parse_payment_pdf_case_005():
    pay = PDFCaseParser.parse_payment_receipt(CASE_005_DIR / "payment.pdf")
    assert isinstance(pay, PaymentReceipt)
    assert pay.payment_id == "REM-AMZ-99120"
    assert pay.amount_paid == Decimal("40500.00")
    assert len(pay.deductions) == 2
    assert pay.deductions[0].amount == Decimal("5000.00")
    assert pay.deductions[1].amount == Decimal("2500.00")

def test_parse_contract_pdf_case_005():
    contract = PDFCaseParser.parse_contract(CASE_005_DIR / "contract.pdf")
    assert isinstance(contract, CommercialContract)
    assert contract.contract_id == "MSA-AMZ-PAC-2026"
    assert len(contract.clauses) == 2

def test_load_case_documents_pure_pdf():
    docs5 = load_case_documents("case_005_amazon_shortage")
    assert "invoice" in docs5
    assert "purchase_order" in docs5
    assert "delivery" in docs5
    assert "payment" in docs5
    assert "contract" in docs5

def test_reconciliation_case_005_pdf():
    docs = load_case_documents("case_005_amazon_shortage")
    rec = reconcile_dispute_data(
        invoice=docs["invoice"],
        purchase_order=docs["purchase_order"],
        delivery=docs["delivery"],
        payment=docs["payment"]
    )
    assert rec.billed_amount == Decimal("48000.00")
    assert rec.received_amount == Decimal("40500.00")
    assert rec.difference == Decimal("-7500.00")
    assert rec.justified_deductions_amount == Decimal("5000.00")
    assert rec.unjustified_deductions_amount == Decimal("2500.00")
    assert rec.primary_discrepancy_type == "FALTANTE_DE_MERCANCIA"

def test_reconciliation_case_006_pdf():
    docs = load_case_documents("case_006_walmart_otif_pricing")
    rec = reconcile_dispute_data(
        invoice=docs["invoice"],
        purchase_order=docs["purchase_order"],
        delivery=docs["delivery"],
        payment=docs["payment"]
    )
    assert rec.billed_amount == Decimal("64500.00")
    assert rec.received_amount == Decimal("56500.00")
    assert rec.difference == Decimal("-8000.00")
    assert rec.justified_deductions_amount == Decimal("4500.00")
    assert rec.unjustified_deductions_amount == Decimal("3500.00")
    assert rec.primary_discrepancy_type == "DIFERENCIA_DE_PRECIO"

def test_contract_evaluation_pdf_cases():
    docs5 = load_case_documents("case_005_amazon_shortage")
    rec5 = reconcile_dispute_data(docs5["invoice"], docs5["purchase_order"], docs5["delivery"], docs5["payment"])
    ev5 = evaluate_contract_compliance(docs5["contract"], rec5)
    assert ev5.contractual_justification_valid is True

    docs6 = load_case_documents("case_006_walmart_otif_pricing")
    rec6 = reconcile_dispute_data(docs6["invoice"], docs6["purchase_order"], docs6["delivery"], docs6["payment"])
    ev6 = evaluate_contract_compliance(docs6["contract"], rec6)
    assert ev6.contractual_justification_valid is True
