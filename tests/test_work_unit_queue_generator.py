"""
tests/test_work_unit_queue_generator.py
Suite de pruebas para el Generador de Cola de Unidades de Trabajo de Carga Masiva (1,000+ Unidades).

Valida:
1. Generación determinista de 1,024 unidades con semilla reproducible.
2. Cumplimiento del invariante matemático en Decimal ($0.00 MAE) en el 100% de las tareas.
3. Distribución diversificada entre DataCo Real, Retailers Comerciales y Anomalías controladas.
4. Exportación exitosa del manifiesto en JSON y CSV.
5. Materialización física de expedientes en disco con los 5 documentos comerciales.
"""

from decimal import Decimal
from pathlib import Path
import pytest

from tools.batch_processor.work_unit_queue_generator import WorkUnitQueueGenerator, WorkUnit


def test_work_unit_queue_generation_and_invariants():
    """Verifica que se generen exactamente 1,024 unidades con balance contable estricto."""
    queue = WorkUnitQueueGenerator.generate_queue(total_units=1024, seed=2026)

    assert len(queue) == 1024

    for u in queue:
        assert isinstance(u, WorkUnit)
        assert u.task_id.startswith("work_unit_")
        assert u.unit_index >= 1
        assert u.billed_amount > Decimal("0.00")
        assert u.received_amount >= Decimal("0.00")
        assert u.disputed_amount >= Decimal("0.00")

        # Invariante financiero: Facturado == Pagado + Disputado ($0.00 MAE)
        diff = abs(u.billed_amount - (u.received_amount + u.disputed_amount))
        assert diff == Decimal("0.00"), f"Invariante roto en unidad {u.task_id}"


def test_work_unit_queue_reproducibility():
    """Valida que la misma semilla genere idénticos expedientes."""
    q1 = WorkUnitQueueGenerator.generate_queue(total_units=50, seed=2026)
    q2 = WorkUnitQueueGenerator.generate_queue(total_units=50, seed=2026)

    assert len(q1) == len(q2)
    for u1, u2 in zip(q1, q2):
        assert u1.task_id == u2.task_id
        assert u1.case_id == u2.case_id
        assert u1.billed_amount == u2.billed_amount
        assert u1.disputed_amount == u2.disputed_amount


def test_work_unit_queue_distribution():
    """Valida la distribución realista entre DataCo, Retailers y Anomalías controladas."""
    queue = WorkUnitQueueGenerator.generate_queue(total_units=1024, seed=2026)

    origins = {}
    for u in queue:
        origins[u.source_origin] = origins.get(u.source_origin, 0) + 1

    assert origins.get("DATACO_REAL", 0) >= 300      # ~35%
    assert origins.get("RETAILER_CATALOG", 0) >= 550  # ~60%
    assert origins.get("ANOMALY_CONTROLLED", 0) >= 15 # ~3%

    # Diversidad de cadenas comerciales
    retailers = set(u.retailer_id for u in queue)
    assert len(retailers) >= 8
    for expected in ["WALMART_MX", "AMAZON_MX", "SORIANA_MX", "HOMEDEPOT_MX", "DATACO_GLOBAL"]:
        assert expected in retailers


def test_work_unit_manifest_export(tmp_path):
    """Valida la exportación de los manifiestos JSON y CSV."""
    queue = WorkUnitQueueGenerator.generate_queue(total_units=100, seed=2026)
    paths = WorkUnitQueueGenerator.export_queue_manifest(queue, output_dir=tmp_path)

    json_p = Path(paths["json_manifest"])
    csv_p = Path(paths["csv_manifest"])

    assert json_p.exists()
    assert csv_p.exists()
    assert json_p.stat().st_size > 1000
    assert csv_p.stat().st_size > 1000

    # Validar líneas del CSV
    lines = csv_p.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 101  # Header + 100 registros


def test_work_unit_task_materialization(tmp_path):
    """Valida que una unidad de trabajo se materialice en disco con los 5 archivos requeridos."""
    queue = WorkUnitQueueGenerator.generate_queue(total_units=10, seed=2026)
    unit = queue[0]

    case_dir = WorkUnitQueueGenerator.materialize_task_to_disk(unit, tmp_path)
    assert case_dir.exists()

    required_files = ["invoice.json", "purchase_order.json", "delivery.json", "payment.json", "contract.json"]
    for rf in required_files:
        fp = case_dir / rf
        assert fp.exists(), f"Falta archivo {rf} en {case_dir}"
        assert fp.stat().st_size > 50
