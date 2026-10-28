"""
tests/test_batch_processor.py
Suite de pruebas para el Procesador Batch Masivo Desatendido (Semana 4 - Sprint 4.2).
Valida la ejecución concurrente, agregación macroeconómica, certificación MAE $0.00
y endpoints API REST.
"""

from decimal import Decimal
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from tools.batch_processor.batch_runner import EnterpriseBatchProcessor
from tools.batch_processor.models import BatchExecutionSummary, BatchCaseResult
from api.main import app

client = TestClient(app)


def test_batch_processor_execution_and_invariants():
    """Valida la ejecución de un lote y la preservación de la ecuación de balance macroeconómica."""
    summary: BatchExecutionSummary = EnterpriseBatchProcessor.execute_batch(
        case_ids=["case_001", "case_002", "case_003"],
        max_workers=2
    )

    assert isinstance(summary, BatchExecutionSummary)
    assert summary.batch_id.startswith("BATCH-")
    assert summary.total_cases_submitted == 3
    assert summary.total_cases_processed == 3
    assert summary.successful_cases >= 1

    # Invarianza aritmética de balance global
    assert summary.arithmetic_error_rate_pct == 0.0
    assert summary.mean_absolute_error_usd == Decimal("0.00")
    assert summary.total_volume_disputed_usd == summary.total_volume_justified_usd + summary.total_volume_claimable_usd

    # Verificación de que cada resultado individual contenga datos válidos
    for r in summary.results:
        assert isinstance(r, BatchCaseResult)
        assert r.billed_amount >= Decimal("0.00")
        assert r.execution_time_ms >= 0.0


def test_batch_summary_export_artifacts(tmp_path):
    """Valida la exportación de reportes JSON y Markdown ejecutivos."""
    summary = EnterpriseBatchProcessor.execute_batch(
        case_ids=["case_001", "case_002"],
        max_workers=2
    )

    json_path, md_path = EnterpriseBatchProcessor.export_batch_summary(summary, output_dir=tmp_path)

    assert json_path.exists()
    assert md_path.exists()

    md_content = md_path.read_text(encoding="utf-8")
    assert "Resumen Ejecutivo de Cartera — Procesamiento Batch Masivo" in md_content
    assert "Métricas Macroeconómicas de Cartera Auditada" in md_content
    assert "Error Absoluto Medio (MAE)" in md_content
    assert "$0.00 USD" in md_content


def test_batch_api_endpoints():
    """Valida los endpoints REST /api/batch/run y /api/batch/latest."""
    # 1. Ejecutar batch vía API
    res_run = client.post("/api/batch/run", json={"cases_count": 5, "workers": 2})
    assert res_run.status_code == 200
    data = res_run.json()

    assert "batch_id" in data
    assert data["total_cases_processed"] == 5
    assert data["mean_absolute_error_usd"] == 0.0
    assert "report_json_path" in data
    assert "report_md_path" in data

    # 2. Consultar último batch ejecutado
    res_latest = client.get("/api/batch/latest")
    assert res_latest.status_code == 200
    latest_data = res_latest.json()
    assert "batch_id" in latest_data
    assert "total_volume_billed_usd" in latest_data
