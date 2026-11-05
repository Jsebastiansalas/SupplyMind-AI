"""
tests/test_small_batch_smoke_test.py
Pruebas unitarias para el Ejecutor de Lote Pequeño Pre-Corrida (Mejora 3).
"""

from __future__ import annotations

from pathlib import Path

from scripts.run_small_batch_smoke_test import (
    build_representative_small_queue,
    run_small_batch_smoke_test,
)


def test_build_representative_small_queue() -> None:
    """Verifica que la cola de lote pequeño incluya casos nominales, JSON corrupto y falta física de POD."""
    queue = build_representative_small_queue(total_units=6)
    assert len(queue) == 6
    assert queue[0].task_id == "smoke_unit_0001"
    assert queue[5].task_id == "smoke_unit_0006"

    anom_types = [u.anomaly_type for u in queue if u.has_anomaly]
    assert "CORRUPT_JSON_SYNTAX" in anom_types
    assert "IRRECONCILABLE_MISSING_POD" in anom_types


def test_run_small_batch_smoke_test_end_to_end(tmp_path: Path) -> None:
    """Verifica que el smoke test ejecute los 3 estados (SUCCESS, RECOVERED_QUARANTINE, FAILED) y selle con SHA-256."""
    res = run_small_batch_smoke_test(output_dir=tmp_path, units_count=6, dry_run=True)
    records = res["records"]
    assert len(records) == 6
    assert res["dossiers_verified"] == 6
    assert res["seal_verification"]["is_valid"] is True
    assert res["distinct_token_counts"] >= 3

    statuses = {r["status"] for r in records}
    assert "SUCCESS" in statuses
    assert "RECOVERED_QUARANTINE" in statuses
    assert "FAILED" in statuses
