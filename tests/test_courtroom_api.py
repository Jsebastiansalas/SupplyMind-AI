"""
tests/test_courtroom_api.py
Pruebas unitarias para el endpoint de Estrado Dialéctico Adversarial (Sprint 5.5).
"""

from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def test_get_adversarial_courtroom_case_001():
    """Valida la generación del careo dialéctico adversarial para case_001."""
    response = client.get("/api/cases/case_001/adversarial-courtroom")
    assert response.status_code == 200, response.text
    data = response.json()

    assert data["case_id"] == "case_001"
    assert "retailer_name" in data
    assert "supplier_name" in data
    assert data["disputed_amount"] >= 0.0
    assert "courtroom_session_id" in data

    # Validar partes del careo
    assert data["prosecutor"]["role"] == "PROSECUTOR"
    assert data["defense"]["role"] == "DEFENSE_COUNSEL"
    assert data["judge"]["role"] == "MAGISTRATE_JUDGE"
    assert data["judge"]["verdict_status"] in ["REEMBOLSO_TOTAL_ORDENADO", "DEDUCCION_CONFIRMADA"]
    assert data["judge"]["moratory_interest_rate_annual"] == 9.0
    assert "statutory_precedents" in data["judge"]
    assert len(data["judge"]["statutory_precedents"]) >= 3

    # Validar 3 rondas dialécticas
    assert len(data["rounds"]) == 3
    for r in data["rounds"]:
        assert "round_number" in r
        assert "title" in r
        assert "prosecutor_claim" in r
        assert "defense_counter" in r
        assert "exhibited_evidence" in r

    # Validar integración MCTS
    assert "mcts_strategy" in data
    assert "recommended_trajectory" in data["mcts_strategy"]
    assert "confidence_score" in data["mcts_strategy"]
    assert "trajectories" in data["mcts_strategy"]


def test_get_adversarial_courtroom_not_found():
    """Valida el manejo de error 404 para casos inexistentes."""
    response = client.get("/api/cases/non_existent_case_9999/adversarial-courtroom")
    assert response.status_code == 404
