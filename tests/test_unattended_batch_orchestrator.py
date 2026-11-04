"""
tests/test_unattended_batch_orchestrator.py
Suite de pruebas para el Orquestador Desatendido de 12 Horas y Generador de Bitácoras.

Valida:
1. Carga determinista y slicing de unidades de trabajo.
2. Procesamiento nominal de punta a punta con balance contable estricto ($0.00 MAE).
3. Detección y auto-recuperación de anomalías en cuarentena forense.
4. Resiliencia de streaming JSONL y reanudación automática sin duplicación de tareas.
5. Generación íntegra de bitácoras en CSV, JSON y Resumen Ejecutivo en Markdown.
"""

from decimal import Decimal
from pathlib import Path
import json
import pytest

from tools.batch_processor.unattended_batch_orchestrator import (
    UnattendedBatchOrchestrator,
    TaskExecutionRecord,
)
from tools.batch_processor.work_unit_queue_generator import WorkUnit, WorkUnitQueueGenerator


def test_orchestrator_initialization(tmp_path):
    """Verifica la configuración inicial del orquestador."""
    orchestrator = UnattendedBatchOrchestrator(
        output_dir=tmp_path,
        total_units=50,
        target_duration_hours=12.0,
        dry_run=True,
    )
    assert orchestrator.total_units == 50
    assert orchestrator.target_duration_hours == 12.0
    assert orchestrator.target_duration_seconds == 43200.0
    assert orchestrator.stream_path.name == "unattended_batch_execution_stream.jsonl"
    assert orchestrator.csv_log_path.name == "unattended_batch_execution_log.csv"
    assert orchestrator.json_log_path.name == "unattended_batch_execution_log.json"


def test_orchestrator_queue_loading_and_slicing(tmp_path):
    """Valida que la cola se cargue y respete el límite de unidades solicitado."""
    manifest_paths = WorkUnitQueueGenerator.export_queue_manifest(
        WorkUnitQueueGenerator.generate_queue(total_units=20, seed=2026),
        output_dir=tmp_path,
    )

    orchestrator = UnattendedBatchOrchestrator(
        queue_manifest_path=Path(manifest_paths["json_manifest"]),
        output_dir=tmp_path,
        total_units=10,
        dry_run=True,
    )
    queue = orchestrator.load_queue()
    assert len(queue) == 10
    assert queue[0].task_id == "work_unit_0001"
    assert queue[9].task_id == "work_unit_0010"


def test_orchestrator_process_unit_nominal(tmp_path):
    """Valida la ejecución de una unidad nominal sin anomalías."""
    orchestrator = UnattendedBatchOrchestrator(
        output_dir=tmp_path,
        total_units=5,
        dry_run=True,
    )
    unit = WorkUnit(
        unit_index=1,
        task_id="work_unit_0001",
        case_id="case_test_nominal_001",
        source_origin="RETAILER_CATALOG",
        retailer_id="WALMART_MX",
        retailer_name="Walmart México y Centroamérica",
        category="PRICING_DISCREPANCY",
        billed_amount=Decimal("10000.00"),
        received_amount=Decimal("8000.00"),
        disputed_amount=Decimal("2000.00"),
        expected_claimable=Decimal("1500.00"),
        expected_justified=Decimal("500.00"),
        expected_action="DEMAND_FULL_RECOVERY_PO_MATCH",
        has_anomaly=False,
    )

    record = orchestrator.process_work_unit(unit)

    assert isinstance(record, TaskExecutionRecord)
    assert record.task_id == "work_unit_0001"
    assert record.status == "SUCCESS"
    assert record.financial_delta == 0.00
    assert record.cost_usd > 0.0
    assert record.tokens_total > 0
    assert "Walmart" in record.retailer_name
    assert record.recovered_amount == 1500.00
    assert record.justified_amount == 500.00


def test_orchestrator_process_anomaly_and_quarantine(tmp_path):
    """Valida que una unidad con anomalía sea recuperada mediante cuarentena forense."""
    orchestrator = UnattendedBatchOrchestrator(
        output_dir=tmp_path,
        total_units=5,
        dry_run=True,
    )
    anomaly_unit = WorkUnit(
        unit_index=2,
        task_id="work_unit_0002",
        case_id="case_test_anomaly_002",
        source_origin="ANOMALY_CONTROLLED",
        retailer_id="AMAZON_MX",
        retailer_name="Amazon México",
        category="ADVERSARIAL_ANOMALY_TEST",
        billed_amount=Decimal("5000.00"),
        received_amount=Decimal("3000.00"),
        disputed_amount=Decimal("2000.00"),
        expected_claimable=Decimal("0.00"),
        expected_justified=Decimal("2000.00"),
        expected_action="QUARANTINE_ISOLATE",
        has_anomaly=True,
        anomaly_type="SYNTAX_CORRUPT",
        anomaly_description="Inyección de caracteres espurios en bloque de totales fiscales",
    )

    record = orchestrator.process_work_unit(anomaly_unit)

    assert record.status == "RECOVERED_QUARANTINE"
    assert "SYNTAX_CORRUPT" in record.error_encountered
    assert "Auto-cuarentena forense" in record.recovery_action
    assert record.financial_delta == 0.00
    assert record.erp_action == "QUARANTINE_DOCKET_CREATED"


def test_orchestrator_streaming_and_resumption(tmp_path):
    """Valida la persistencia en streaming y la reanudación sin duplicación."""
    orchestrator = UnattendedBatchOrchestrator(
        output_dir=tmp_path,
        total_units=6,
        dry_run=True,
        resume=True,
    )

    # Simular ejecución de primeras 3 tareas
    res1 = orchestrator.run_unattended_batch()
    assert res1["total_processed"] == 6
    assert orchestrator.stream_path.exists()

    # Verificar que el streaming contiene exactamente 6 líneas
    lines = orchestrator.stream_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 6

    # Crear una segunda instancia con resume=True
    orchestrator2 = UnattendedBatchOrchestrator(
        output_dir=tmp_path,
        total_units=6,
        dry_run=True,
        resume=True,
    )
    orchestrator2.load_completed_stream()
    assert len(orchestrator2.completed_task_ids) == 6

    # Al ejecutar de nuevo, no debe procesar ninguna adicional
    res2 = orchestrator2.run_unattended_batch()
    assert res2["total_processed"] == 6


def test_orchestrator_export_artifacts(tmp_path):
    """Valida la exportación de bitácoras CSV, JSON y Resumen Ejecutivo en Markdown."""
    orchestrator = UnattendedBatchOrchestrator(
        output_dir=tmp_path,
        total_units=8,
        dry_run=True,
    )
    result = orchestrator.run_unattended_batch()

    csv_path = Path(result["export_paths"]["csv_log"])
    json_path = Path(result["export_paths"]["json_log"])
    md_path = Path(result["export_paths"]["summary_md"])

    assert csv_path.exists()
    assert json_path.exists()
    assert md_path.exists()

    # Validar CSV
    csv_lines = csv_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(csv_lines) == 9  # Header + 8 registros
    assert "unit_index,task_id,case_id" in csv_lines[0]
    assert "financial_delta" in csv_lines[0]

    # Validar JSON
    with open(json_path, "r", encoding="utf-8") as f:
        json_data = json.load(f)
    assert json_data["batch_metadata"]["total_units_recorded"] == 8
    assert len(json_data["records"]) == 8

    # Validar Markdown
    md_text = md_path.read_text(encoding="utf-8")
    assert "# Resumen Ejecutivo" in md_text
    assert "Tasa de Éxito Operativo" in md_text
    assert "Costo Total Acumulado" in md_text
    assert "$0.00 MAE" in md_text
