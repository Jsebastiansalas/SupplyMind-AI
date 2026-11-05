"""
tests/test_unattended_batch_api_routes.py
Pruebas de Integración para los Endpoints de la Jornada Desatendida de 1,024 Unidades.
"""

from fastapi.testclient import TestClient
import pytest
from api.main import app

client = TestClient(app)


def test_get_unattended_summary():
    """Valida que el endpoint de resumen retorne métricas y la cuota de 1,024 unidades."""
    res = client.get("/api/batch/unattended/summary")
    assert res.status_code == 200
    data = res.json()
    assert "total_units" in data
    assert data["total_units"] == 1024
    assert "status_breakdown" in data
    assert "telemetry" in data
    assert "cryptographic_seal" in data
    assert data["cryptographic_seal"]["merkle_root"] != "UNSEALED"


def test_get_unattended_heartbeat():
    """Valida el endpoint de heartbeat / latido del proceso."""
    res = client.get("/api/batch/unattended/heartbeat")
    assert res.status_code == 200
    data = res.json()
    assert "status" in data
    assert data["total_units"] == 1024


def test_verify_unattended_seal():
    """Valida la verificación criptográfica del árbol de Merkle desde la API."""
    res = client.post("/api/batch/unattended/verify-seal")
    assert res.status_code == 200
    data = res.json()
    assert "is_valid" in data
    assert data["is_valid"] is True
    assert data["total_records_verified"] == 1024
    assert data["mae_zero_invariant_passed"] is True


def test_list_unattended_cases():
    """Valida la paginación y filtrado de casos."""
    res = client.get("/api/batch/unattended/cases?page=1&page_size=10")
    assert res.status_code == 200
    data = res.json()
    assert data["total_items"] == 1024
    assert len(data["records"]) == 10
    assert data["page"] == 1

    # Filtrar por status FAILED
    res_failed = client.get("/api/batch/unattended/cases?page=1&page_size=10&status=FAILED")
    assert res_failed.status_code == 200
    data_failed = res_failed.json()
    assert data_failed["total_items"] > 0
    for r in data_failed["records"]:
        assert r["status"] == "FAILED"


def test_run_small_batch_smoke_test_endpoint():
    """Valida la ejecución del smoke test interactivo desde la API."""
    res = client.post("/api/batch/unattended/run-smoke-test", json={"units": 3, "dry_run": True})
    assert res.status_code == 200
    data = res.json()
    assert "batch_result" in data
    assert "records" in data
    assert len(data["records"]) == 3
    assert data["seal_verification"]["is_valid"] is True
    assert data["dossiers_verified"] == 3


def test_get_unattended_case_dossier():
    """Valida la recuperación de los 5 documentos físicos de un expediente en disco."""
    res = client.get("/api/batch/unattended/cases?page=1&page_size=5")
    assert res.status_code == 200
    first_case_id = res.json()["records"][0]["case_id"]

    dossier_res = client.get(f"/api/batch/unattended/dossier/{first_case_id}")
    assert dossier_res.status_code == 200
    dossier_data = dossier_res.json()
    assert dossier_data["case_id"] == first_case_id
    assert "documents" in dossier_data
    docs = dossier_data["documents"]
    assert "invoice" in docs
    assert "purchase_order" in docs
    assert "delivery" in docs
    assert "payment" in docs
    assert "contract" in docs
    assert "audit_resolution_docket" in docs
