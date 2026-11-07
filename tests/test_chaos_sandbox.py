"""
tests/test_chaos_sandbox.py
Pruebas de Integración y Validación del Laboratorio de Caos y Resiliencia en Vivo.
"""

from fastapi.testclient import TestClient
import pytest
from api.main import app

client = TestClient(app)


def test_get_chaos_scenarios_catalog():
    """Valida que el catálogo de escenarios de caos retorne los 6 vectores de ataque."""
    res = client.get("/api/sandbox/chaos/scenarios")
    assert res.status_code == 200
    data = res.json()
    assert data["total_scenarios"] >= 6
    scenario_ids = [s["id"] for s in data["scenarios"]]
    assert "PROMPT_INJECTION_REMARK" in scenario_ids
    assert "CORRUPT_JSON_SYNTAX" in scenario_ids
    assert "IRRECONCILABLE_MISSING_POD" in scenario_ids
    assert "NETWORK_RATE_LIMIT_429" in scenario_ids
    assert "PRICE_DISCREPANCY_OVERCHARGE" in scenario_ids
    assert "PROCESS_INTERRUPTION_RESUME" in scenario_ids


def test_inject_prompt_injection_chaos():
    """Valida la detección y auto-cuarentena de inyección de prompt."""
    res = client.post("/api/sandbox/chaos/inject", json={
        "scenario_id": "PROMPT_INJECTION_REMARK",
        "retailer_id": "WALMART_MX",
        "disputed_amount": 4200.0
    })
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "RECOVERED_QUARANTINE"
    assert data["mae_zero_verified"] is True
    assert data["financial_delta"] == 0.00
    assert len(data["timeline"]) >= 4
    stages = [step["stage"] for step in data["timeline"]]
    assert "INGESTION" in stages
    assert "DETECTION" in stages
    assert "AUTO_QUARANTINE" in stages
    assert "INVARIANT_VERIFIED" in stages


def test_inject_corrupt_json_chaos():
    """Valida la auto-reparación de sintaxis corrupta en disco."""
    res = client.post("/api/sandbox/chaos/inject", json={
        "scenario_id": "CORRUPT_JSON_SYNTAX",
        "retailer_id": "AMAZON_MX",
        "disputed_amount": 3100.0
    })
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "RECOVERED_QUARANTINE"
    assert data["mae_zero_verified"] is True
    stages = [step["stage"] for step in data["timeline"]]
    assert "SYNTAX_ERROR_CAUGHT" in stages
    assert "AUTO_HEALING" in stages


def test_inject_missing_pod_honest_failure():
    """Valida la honestidad técnica: FAILED con FileNotFoundError sin alucinación."""
    res = client.post("/api/sandbox/chaos/inject", json={
        "scenario_id": "IRRECONCILABLE_MISSING_POD",
        "retailer_id": "LIVERPOOL_MX",
        "disputed_amount": 1950.0
    })
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "FAILED"
    assert data["mae_zero_verified"] is True
    assert "FileNotFoundError" in data["error_diagnosed"]
    stages = [step["stage"] for step in data["timeline"]]
    assert "HONEST_ESCALATION" in stages


def test_inject_network_rate_limit_backoff():
    """Valida la mitigación de fallas de red HTTP 429 con Exponential Backoff."""
    res = client.post("/api/sandbox/chaos/inject", json={
        "scenario_id": "NETWORK_RATE_LIMIT_429",
        "retailer_id": "SORIANA_MX",
        "disputed_amount": 5000.0
    })
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "AUTO_HEALED"
    assert data["mae_zero_verified"] is True
    assert "retroceso exponencial" in data["recovery_action_taken"]


def test_inject_process_interruption_resume():
    """Valida la reanudación idempotente sin duplicación de tareas."""
    res = client.post("/api/sandbox/chaos/inject", json={
        "scenario_id": "PROCESS_INTERRUPTION_RESUME",
        "disputed_amount": 2500.0
    })
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "IDEMPOTENT_RESUMED"
    assert data["mae_zero_verified"] is True
    stages = [step["stage"] for step in data["timeline"]]
    assert "IDEMPOTENT_RESUME" in stages
