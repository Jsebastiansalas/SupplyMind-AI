"""
tests/test_official_dossier_export.py
Pruebas para el exportador de Dossier Foliado Oficial con Código QR Merkle y Sello Digital SAT.
"""

from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def test_get_official_dossier_case_001():
    response = client.get("/api/cases/case_001/official-dossier")
    assert response.status_code == 200, f"Expected 200 but got {response.status_code}: {response.text}"
    data = response.json()

    # Validar campos clave de la estructura oficial
    assert data["case_id"] == "case_001"
    assert data["folio_number"].startswith("FOL-SAT-2026-CASE_001")
    assert "merkle_root" in data and len(data["merkle_root"]) == 64
    assert "digital_signature" in data and len(data["digital_signature"]) == 64
    assert "<svg" in data["qr_code_svg"] and "</svg>" in data["qr_code_svg"]
    assert data["invariante_mae_zero"] is True

    # Conciliación Three-Way Match
    twm = data["three_way_match"]
    assert twm["billed_amount"] > 0
    assert twm["received_amount"] > 0
    assert twm["claimable_amount"] >= 0
    assert twm["reconciliation_delta"] == 0.0

    # Póliza contable NIF C-3
    erp = data["erp_journal_entry"]
    assert erp["asiento_tipo"] == "Póliza de Diario NIF C-3"
    assert erp["balance_cuadrado"] is True
    assert len(erp["debe_cuentas"]) >= 2
    assert len(erp["haber_cuentas"]) >= 1

    # Base Legal
    legal = data["legal_basis"]
    assert "Art. 1043 CCom" in legal["statute_of_limitations"]
    assert "Art. 383 CCom" in legal["notice_window_status"]
