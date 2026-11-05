"""
tests/test_view_task_detail.py
Suite de pruebas para el Visor Detallado de Expedientes de la Corrida Desatendida.

Valida:
1. Carga íntegra de registros desde stream JSONL o manifiesto.
2. Búsqueda exacta por índice numérico y por Task ID.
3. Comportamiento ante consultas no encontradas.
"""

from pathlib import Path
import pytest

from scripts.view_task_detail import (
    load_all_records,
    find_record,
)


def test_load_all_records_from_stream_or_manifest():
    """Valida que siempre haya registros disponibles para inspección."""
    records = load_all_records()
    assert len(records) > 0
    assert "task_id" in records[0]
    assert "retailer_name" in records[0]


def test_find_record_by_index():
    """Valida la búsqueda por índice numérico (ej. '1')."""
    records = load_all_records()
    r = find_record(records, "1")
    assert r is not None
    assert r["unit_index"] == 1


def test_find_record_by_task_id():
    """Valida la búsqueda por Task ID (ej. 'work_unit_0001')."""
    records = load_all_records()
    r = find_record(records, "work_unit_0001")
    assert r is not None
    assert r["task_id"] == "work_unit_0001"


def test_find_record_not_found():
    """Valida que una consulta inexistente retorne None."""
    records = load_all_records()
    r = find_record(records, "non_existent_unit_999999")
    assert r is None
