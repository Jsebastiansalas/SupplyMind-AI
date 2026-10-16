import io
import json
from pathlib import Path
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def test_api_create_guided_case_and_delete():
    # 1. Crear caso guiado
    payload = {
        "case_id": "test_guided_case_999",
        "display_name": "Caso de Prueba Guiado",
        "category": "Personalizado",
        "description": "Prueba de creación paramétrica",
        "vendor_id": "VEN-TEST",
        "customer_id": "CUST-TEST",
        "po_reference": "PO-TEST-123",
        "items": [
            {
                "item_id": "ITEM-01",
                "description": "Caja de prueba",
                "ordered_quantity": 100,
                "delivered_quantity": 90,
                "missing_quantity": 10,
                "agreed_unit_price": 50.0
            }
        ],
        "unauthorized_penalty": 200.0,
        "delivery_signed": True,
        "days_to_claim": 10
    }
    res_create = client.post("/api/cases/create-guided", json=payload)
    assert res_create.status_code == 200
    data = res_create.json()
    assert data["status"] == "success"
    cid = data["case_id"]
    assert cid == "case_test_guided_case_999"

    # 2. Verificar que list_cases lo detecta
    res_list = client.get("/api/cases")
    assert res_list.status_code == 200
    c_ids = [c["case_id"] for c in res_list.json()]
    assert cid in c_ids

    # 3. Analizar el caso recién creado
    res_analyze = client.post(f"/api/cases/{cid}/analyze", json={"fast_path": True, "use_cache": False})
    assert res_analyze.status_code == 200
    report = res_analyze.json()
    assert report["billed_amount"] == 5000.0
    assert report["justified_amount"] == 500.0
    assert report["claimable_amount"] == 200.0

    # 4. Eliminar el caso creado de prueba
    res_del = client.delete(f"/api/cases/{cid}")
    assert res_del.status_code == 200
    assert res_del.json()["status"] == "success"


def test_api_upload_case_and_delete():
    # 1. Preparar archivos simulados
    invoice_content = json.dumps({
        "invoice_id": "INV-UP-001",
        "vendor_id": "VEN-001",
        "customer_id": "CUST-001",
        "po_reference": "PO-UP-001",
        "issue_date": "2026-09-01",
        "currency": "USD",
        "items": [
            {
                "item_id": "SKU-UP-1",
                "description": "Producto Upload",
                "quantity": 10,
                "unit_price": 100.0,
                "total_price": 1000.0
            }
        ],
        "subtotal": 1000.0,
        "tax": 0.0,
        "total_amount": 1000.0
    }).encode("utf-8")

    files = [
        ("files", ("invoice.json", io.BytesIO(invoice_content), "application/json"))
    ]
    data = {
        "case_id": "test_upload_case_999",
        "display_name": "Caso Upload Test",
        "description": "Prueba de carga de archivos"
    }

    res_upload = client.post("/api/cases/upload", data=data, files=files)
    assert res_upload.status_code == 200
    res_data = res_upload.json()
    assert res_data["status"] == "success"
    cid = res_data["case_id"]
    assert cid == "case_test_upload_case_999"

    # Verificar que el archivo existe
    res_details = client.get(f"/api/cases/{cid}")
    assert res_details.status_code == 200
    assert res_details.json()["files_count"] >= 1

    # Limpiar
    res_del = client.delete(f"/api/cases/{cid}")
    assert res_del.status_code == 200
