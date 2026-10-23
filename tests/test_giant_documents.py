"""
tests/test_giant_documents.py
Batería de pruebas automatizadas para validar la ingesta y resolución
de expedientes B2B masivos / gigantes (40+ SKUs, > $350k USD).
"""

from decimal import Decimal
from agent.core.skynet_runner import SkynetRunner
from data.models import DisputeAnalysisReport
from tools.document_reader.reader import load_case_documents
from tools.reconciliation_engine.engine import reconcile_dispute_data
from tools.sku_matcher import perform_sku_level_matching


def test_mega_case_document_ingestion():
    """Valida la carga completa de los 5 documentos del caso gigante (40 SKUs)."""
    docs = load_case_documents("case_009_mega_retailer_dispute")
    assert "invoice" in docs
    assert "purchase_order" in docs
    assert "delivery" in docs
    assert "payment" in docs
    assert "contract" in docs

    assert len(docs["invoice"].items) == 40
    assert len(docs["purchase_order"].items) == 40
    assert len(docs["delivery"].items) == 40
    assert docs["invoice"].total_amount == Decimal("385000.00")
    assert docs["payment"].amount_paid == Decimal("360000.00")


def test_mega_case_deterministic_reconciliation():
    """Valida la conciliación matemática sin margen de error en 40 SKUs."""
    docs = load_case_documents("case_009_mega_retailer_dispute")
    summary = reconcile_dispute_data(
        invoice=docs["invoice"],
        purchase_order=docs["purchase_order"],
        delivery=docs["delivery"],
        payment=docs["payment"],
    )

    assert summary.billed_amount == Decimal("385000.00")
    assert summary.received_amount == Decimal("360000.00")
    assert summary.difference == Decimal("-25000.00")
    assert summary.total_missing_amount == Decimal("12000.00")
    assert summary.justified_deductions_amount == Decimal("12000.00")
    assert summary.unjustified_deductions_amount == Decimal("13000.00")


def test_mega_case_sku_matcher_and_vat():
    """Valida el motor SKU x SKU y el cálculo fiscal sobre 40 SKUs."""
    docs = load_case_documents("case_009_mega_retailer_dispute")
    sku_res = perform_sku_level_matching(
        invoice_data=docs["invoice"].model_dump(),
        delivery_data=docs["delivery"].model_dump(),
        po_data=docs["purchase_order"].model_dump(),
    )

    assert sku_res.total_skus_audited == 40
    assert sku_res.skus_with_discrepancies == 3
    assert sku_res.total_short_amount == Decimal("12000.00")
    assert sku_res.credit_note_recommended_subtotal == Decimal("12000.00")
    # IVA 16% de 12,000 = 1,920.00
    assert sku_res.credit_note_recommended_vat == Decimal("1920.00")
    assert sku_res.credit_note_recommended_total == Decimal("13920.00")


def test_mega_case_skynet_runner_resolution():
    """Valida la resolución integral por SkynetRunner con reporte formal."""
    runner = SkynetRunner("case_009_mega_retailer_dispute", fast_path=True, use_cache=False)
    report = runner.run()

    assert isinstance(report, DisputeAnalysisReport)
    assert report.case_id == "case_009_mega_retailer_dispute"
    assert report.billed_amount == Decimal("385000.00")
    assert report.received_amount == Decimal("360000.00")
    assert report.difference == Decimal("-25000.00")
    assert report.justified_amount == Decimal("12000.00")
    assert report.claimable_amount == Decimal("13000.00")
    assert report.confidence == 0.98
    assert "Faltante físico" in report.root_cause
    assert "13,000.00" in report.root_cause
