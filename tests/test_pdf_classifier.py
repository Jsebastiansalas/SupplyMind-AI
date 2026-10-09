"""
Pruebas unitarias del Clasificador y Segmentador Autónomo de Documentos B2B.
Verifica que el agente procese documentos de gran extensión (miles de caracteres)
y archivos con nombres arbitrarios sin requerir la convención estándar 'invoice.pdf'.
"""

from pathlib import Path
from decimal import Decimal
import pytest

from tools.document_reader.classifier import DocumentClassifier
from tools.document_reader.reader import load_case_documents
from tools.reconciliation_engine.engine import reconcile_dispute_data
from data.models import (
    Invoice,
    PurchaseOrder,
    DeliveryNote,
    PaymentReceipt,
    CommercialContract
)

CASE_007_DIR = Path("data/cases/case_007_cisco_large_bundle")

def test_classify_arbitrary_filename_invoice():
    inv_file = CASE_007_DIR / "DOC_FISCAL_CFDI_SERIE_B_NO_99214.pdf"
    doc_type, conf = DocumentClassifier.classify_pdf(inv_file)
    assert doc_type == "invoice"
    assert conf > 0.50

def test_classify_arbitrary_filename_po():
    po_file = CASE_007_DIR / "ORDEN_COMPRA_CORPORATIVA_GLOBAL_PO8810.pdf"
    doc_type, conf = DocumentClassifier.classify_pdf(po_file)
    assert doc_type == "purchase_order"
    assert conf > 0.50

def test_classify_arbitrary_filename_delivery():
    del_file = CASE_007_DIR / "REMITO_RECEPCION_LOGISTICA_ALMACEN_DALLAS.pdf"
    doc_type, conf = DocumentClassifier.classify_pdf(del_file)
    assert doc_type == "delivery"
    assert conf > 0.50

def test_classify_arbitrary_filename_payment():
    pay_file = CASE_007_DIR / "AVISO_PAGO_Y_LIQUIDACION_BANCARIA_WIRE.pdf"
    doc_type, conf = DocumentClassifier.classify_pdf(pay_file)
    assert doc_type == "payment"
    assert conf > 0.50

def test_classify_arbitrary_filename_contract():
    con_file = CASE_007_DIR / "CONVENIO_MARCO_PROVEEDORES_MSA_GLOBAL_2026.pdf"
    doc_type, conf = DocumentClassifier.classify_pdf(con_file)
    assert doc_type == "contract"
    assert conf > 0.50

def test_classify_directory_mapping_case_007():
    mapped = DocumentClassifier.classify_and_map_case_directory(CASE_007_DIR)
    assert set(mapped.keys()) == {"invoice", "purchase_order", "delivery", "payment", "contract"}
    assert mapped["invoice"].name == "DOC_FISCAL_CFDI_SERIE_B_NO_99214.pdf"
    assert mapped["purchase_order"].name == "ORDEN_COMPRA_CORPORATIVA_GLOBAL_PO8810.pdf"
    assert mapped["delivery"].name == "REMITO_RECEPCION_LOGISTICA_ALMACEN_DALLAS.pdf"
    assert mapped["payment"].name == "AVISO_PAGO_Y_LIQUIDACION_BANCARIA_WIRE.pdf"
    assert mapped["contract"].name == "CONVENIO_MARCO_PROVEEDORES_MSA_GLOBAL_2026.pdf"

def test_load_case_documents_arbitrary_names():
    docs = load_case_documents("case_007_cisco_large_bundle")
    assert isinstance(docs["invoice"], Invoice)
    assert isinstance(docs["purchase_order"], PurchaseOrder)
    assert isinstance(docs["delivery"], DeliveryNote)
    assert isinstance(docs["payment"], PaymentReceipt)
    assert isinstance(docs["contract"], CommercialContract)
    assert docs["invoice"].total_amount == Decimal("125000.00")
    assert docs["purchase_order"].total_amount == Decimal("117500.00")
    assert docs["payment"].amount_paid == Decimal("98000.00")

def test_full_text_extraction_large_documents():
    con_file = CASE_007_DIR / "CONVENIO_MARCO_PROVEEDORES_MSA_GLOBAL_2026.pdf"
    full_text, pages = DocumentClassifier.extract_full_text(con_file)
    assert len(full_text) > 1500 # Muy por encima de los 500 caracteres, abarcando documento completo
    assert len(pages) >= 1
    assert "CLÁUSULA" in full_text.upper() or "CLAUSULA" in full_text.upper()

def test_reconciliation_case_007_large():
    docs = load_case_documents("case_007_cisco_large_bundle")
    rec = reconcile_dispute_data(
        invoice=docs["invoice"],
        purchase_order=docs["purchase_order"],
        delivery=docs["delivery"],
        payment=docs["payment"]
    )
    assert rec.billed_amount == Decimal("125000.00")
    assert rec.received_amount == Decimal("98000.00")
    assert rec.difference == Decimal("-27000.00")
    assert rec.total_missing_amount == Decimal("4000.00")
    assert rec.total_damaged_amount == Decimal("1500.00")
    assert rec.total_price_discrepancy_amount == Decimal("7500.00")
    assert rec.justified_deductions_amount == Decimal("13000.00")
    assert rec.unjustified_deductions_amount == Decimal("14000.00")
