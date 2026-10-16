"""
tests/test_api.py
Pruebas automatizadas para la API REST FastAPI de SupplyMind AI Enterprise.
"""

from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def test_api_health_endpoint():
    """Valida el endpoint de salud del sistema."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert data["version"] == "2.0.0"
    assert "grok" in data["model_name"].lower()


def test_api_list_cases():
    """Valida la obtención del catálogo de casos clasificados."""
    response = client.get("/api/cases")
    assert response.status_code == 200
    cases = response.json()
    assert len(cases) >= 3
    case_ids = [c["case_id"] for c in cases]
    assert "case_001" in case_ids
    assert "case_002" in case_ids
    assert "case_003" in case_ids


def test_api_get_case_details():
    """Valida la obtención de metadatos y documentos de un expediente."""
    response = client.get("/api/cases/case_001")
    assert response.status_code == 200
    data = response.json()
    assert data["case_id"] == "case_001"
    assert data["files_count"] >= 4
    file_names = [f["filename"] for f in data["files"]]
    assert "invoice.json" in file_names


def test_api_analyze_case():
    """Valida la ejecución de análisis agéntico vía API."""
    payload = {"fast_path": True, "use_cache": True}
    response = client.post("/api/cases/case_001/analyze", json=payload)
    assert response.status_code == 200
    report = response.json()
    assert report["billed_amount"] == 9000.0
    assert report["received_amount"] == 8200.0
    assert report["difference"] == -800.0
    assert report["justified_amount"] == 800.0
    assert report["claimable_amount"] == 0.0


def test_api_tribunal_evaluation():
    """Valida la auditoría colegiada de 100 puntos vía API."""
    response = client.get("/api/tribunal/case_001")
    assert response.status_code == 200
    data = response.json()
    assert data["total_score"] >= 90.0
    assert data["passed_mastery"] is True
    assert "cfo_evaluation" in data
    assert "legal_evaluation" in data
    assert "operations_evaluation" in data


def test_api_chat():
    """Valida el endpoint conversacional interactivo básico."""
    payload = {"message": "¿Cuál es la causa raíz de la discrepancia?"}
    response = client.post("/api/cases/case_001/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert len(data["reply"]) > 10


def test_api_chat_judge_auditor_role():
    """Valida el endpoint conversacional con rol de Jurado & Auditor."""
    payload = {
        "message": "¿Cómo se garantiza cero alucinación y qué evaluó el Tribunal Colegiado?",
        "role": "judge_auditor"
    }
    response = client.post("/api/cases/case_002/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert "role" in data
    assert data["role"] == "judge_auditor"
    assert len(data.get("sources", [])) > 0


def test_api_chat_product_breakdown():
    """Valida la consulta de desglose producto por producto."""
    payload = {
        "message": "Desglósame producto por producto qué se facturó y qué se entregó",
        "role": "senior_analyst"
    }
    response = client.post("/api/cases/case_002/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert "PROD-" in data["reply"] or "Facturado" in data["reply"] or "Desglose" in data["reply"]


def test_api_export_email_draft():
    """Valida la generación de borradores de correo B2B."""
    response = client.get("/api/cases/case_001/email-draft")
    assert response.status_code == 200
    data = response.json()
    assert "subject" in data
    assert "body" in data


def test_api_sandbox_simulate():
    """Valida la simulación interactiva instantánea (<50ms) del Sandbox."""
    # Caso 1: Faltante físico amparado en remisión -> Justificado
    payload_physical = {
        "case_id": "case_001",
        "billed_amount": 50000.0,
        "received_amount": 35000.0,
        "missing_amount": 15000.0,
        "damaged_amount": 0.0,
        "days_to_claim": 12,
        "delivery_signed_conforme": True
    }
    response = client.post("/api/sandbox/simulate", json=payload_physical)
    assert response.status_code == 200
    data = response.json()
    assert data["resolution"]["justified_amount"] == 15000.0
    assert data["resolution"]["claimable_amount"] == 0.0
    assert data["tribunal_scores"]["total_score"] >= 80.0
    assert data["latency_ms"] < 200

    # Caso 2: Reclamo extemporáneo (45 días > 30 días) -> 100% Reclamable por caducidad
    payload_expired = {
        "case_id": "case_001",
        "billed_amount": 50000.0,
        "received_amount": 35000.0,
        "missing_amount": 15000.0,
        "damaged_amount": 0.0,
        "days_to_claim": 45,
        "delivery_signed_conforme": True
    }
    res_exp = client.post("/api/sandbox/simulate", json=payload_expired)
    assert res_exp.status_code == 200
    data_exp = res_exp.json()
    assert data_exp["resolution"]["claimable_amount"] == 15000.0
    assert data_exp["resolution"]["justified_amount"] == 0.0
    assert data_exp["resolution"]["statute_of_limitations_applied"] is True



def test_api_telemetry_unit_economics():
    """Valida el cálculo de Unit Economics y ROI corporate."""
    response = client.get("/api/telemetry/unit-economics")
    assert response.status_code == 200
    data = response.json()
    assert data["per_case_metrics"]["agent_cost_usd"] < 0.01
    assert data["per_case_metrics"]["human_auditor_cost_usd"] == 45.0
    assert data["per_case_metrics"]["cost_reduction_percent"] > 99.0
    assert "roi_multiple" in data["enterprise_scale_projection"]


