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
    """Valida el endpoint conversacional interactivo."""
    payload = {"message": "¿Cuál es la causa raíz de la discrepancia?"}
    response = client.post("/api/cases/case_001/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert len(data["reply"]) > 10


def test_api_export_email_draft():
    """Valida la generación de borradores de correo B2B."""
    response = client.get("/api/cases/case_001/email-draft")
    assert response.status_code == 200
    data = response.json()
    assert "subject" in data
    assert "body" in data
