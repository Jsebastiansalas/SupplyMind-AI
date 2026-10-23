"""
tests/test_sprint_2_2.py
Batería de pruebas automatizadas para certificar las historias de usuario del Sprint 2.2:
- US-2.2.1: Ingesta y conciliación de datos reales en PDF (Amazon Vendor Central y Walmart).
- US-2.2.2: Ingesta de remisión física escaneada con sellos y OCR de visión (Home Depot).
- US-2.2.3: Demostración de resiliencia y captura de fallos (JSON corrupto y esquema inválido).
"""

from decimal import Decimal
from agent.core.skynet_runner import SkynetRunner
from data.models import DisputeAnalysisReport


def test_us_2_2_1_amazon_real_pdf_resolution():
    """Valida la resolución completa sobre los 5 PDFs reales de Amazon (Caso 005)."""
    runner = SkynetRunner("case_005_amazon_shortage", fast_path=True)
    report = runner.run()

    assert isinstance(report, DisputeAnalysisReport)
    assert report.case_id == "case_005_amazon_shortage"
    assert report.billed_amount == Decimal("48000.00")
    assert report.received_amount == Decimal("40500.00")
    assert report.difference == Decimal("-7500.00")
    assert report.justified_amount == Decimal("5000.00")
    assert report.claimable_amount == Decimal("2500.00")
    assert report.confidence == 0.98
    assert "Amazon" in report.root_cause or "Faltante" in report.root_cause or "case_005" in report.root_cause
    assert len(report.evidence) >= 2


def test_us_2_2_1_walmart_real_pdf_resolution():
    """Valida la resolución completa sobre los PDFs reales de Walmart OTIF (Caso 006)."""
    runner = SkynetRunner("case_006_walmart_otif_pricing", fast_path=True)
    report = runner.run()

    assert isinstance(report, DisputeAnalysisReport)
    assert report.case_id == "case_006_walmart_otif_pricing"
    assert report.billed_amount == Decimal("64500.00")
    assert report.received_amount == Decimal("56500.00")
    assert report.difference == Decimal("-8000.00")
    assert report.justified_amount == Decimal("4500.00")
    assert report.claimable_amount == Decimal("3500.00")
    assert report.confidence == 0.98


def test_us_2_2_2_homedepot_ocr_scanned_resolution():
    """Valida la ingesta y conciliación de remisión física escaneada con OCR (Caso 008)."""
    from tools.document_reader.reader import load_case_documents
    from tools.reconciliation_engine.engine import reconcile_dispute_data

    docs = load_case_documents("case_008_homedepot_damaged_scanned")
    assert "delivery" in docs
    assert len(docs["delivery"].items) > 0

    reconciliation = reconcile_dispute_data(
        invoice=docs["invoice"],
        purchase_order=docs["purchase_order"],
        delivery=docs["delivery"],
        payment=docs["payment"]
    )
    assert reconciliation.billed_amount > Decimal("0.00")
    assert reconciliation.total_damaged_amount > Decimal("0.00")


def test_us_2_2_3_corrupt_json_resilience():
    """Valida que ante sintaxis JSON rota, el agente no crashee y emita informe de resiliencia."""
    runner = SkynetRunner("test_corrupt_json", fast_path=True)
    report = runner.run()

    assert isinstance(report, DisputeAnalysisReport)
    assert report.case_id == "test_corrupt_json"
    assert report.confidence == 0.0
    assert "TECHNICAL_ERROR" in report.root_cause
    assert "corruptos" in report.root_cause.lower() or "inválido" in report.root_cause.lower()


def test_us_2_2_3_bad_schema_resilience():
    """Valida que ante un esquema inválido, el agente capture la excepción de forma controlada."""
    runner = SkynetRunner("test_bad_schema", fast_path=True)
    report = runner.run()

    assert isinstance(report, DisputeAnalysisReport)
    assert report.case_id == "test_bad_schema"
    assert report.confidence == 0.0
    assert "TECHNICAL_ERROR" in report.root_cause
