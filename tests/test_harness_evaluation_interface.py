"""
tests/test_harness_evaluation_interface.py
Suite de pruebas para el Modo Harness de Evaluación de Platica (CLI --json y Endpoint POST /api/evaluate).
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from api.main import app
from config.settings import settings
from agent.core.harness_adapter import HarnessAdapter

client = TestClient(app)


@pytest.fixture(autouse=True)
def cleanup_temp_harness_cases():
    yield
    for cname in ["case_harness_blind_01", "case_caso_externo_jurado", "case_harness_api_02"]:
        p = settings.DATA_DIR / cname
        if p.exists() and p.is_dir():
            shutil.rmtree(p, ignore_errors=True)
        for ext in ["json", "md"]:
            rep = Path("reports") / f"dispute_report_{cname}.{ext}"
            if rep.exists():
                rep.unlink(missing_ok=True)
            let = Path("reports") / f"carta_reclamacion_{cname}.{ext}"
            if let.exists():
                let.unlink(missing_ok=True)


def test_harness_cli_existing_case_pure_json():
    """Verifica que `python main.py --input case_001 --json --fast` emita JSON 100% puro en stdout."""
    proc = subprocess.run(
        [sys.executable, "main.py", "--input", "case_001", "--json", "--fast"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )
    data = json.loads(proc.stdout.strip())
    assert data["status"] == "SUCCESS"
    assert data["case_id"] == "case_001"
    assert data["mae_invariant_verified"] is True
    assert data["financial_delta_mae"] == 0.0
    assert data["billed_amount"] == 9000.0
    assert data["received_amount"] == 8200.0
    assert data["difference"] == 800.0
    assert "telemetry" in data


def test_harness_adapter_custom_json_file(tmp_path: Path):
    """Verifica que el adaptador procese un archivo JSON externo inédito enviado por el Harness."""
    custom_payload = {
        "case_id": "case_harness_blind_01",
        "currency": "USD",
        "items": [
            {
                "item_id": "SKU-900",
                "description": "Servidor Rack Industrial",
                "ordered_quantity": 20,
                "delivered_quantity": 18,
                "missing_quantity": 2,
                "agreed_unit_price": 500.0,
            }
        ],
        "amount_paid": 7500.0,
        "unauthorized_penalty": 1500.0,
        "unauthorized_penalty_reason": "Cargo unilateral por promoción no pactada",
    }
    json_file = tmp_path / "blind_case.json"
    json_file.write_text(json.dumps(custom_payload), encoding="utf-8")

    res = HarnessAdapter.evaluate(target=json_file, fast_path=True, silent_stdout=True)
    assert res["status"] == "SUCCESS"
    assert res["mae_invariant_verified"] is True
    assert res["financial_delta_mae"] == 0.0
    assert res["billed_amount"] == 10000.0
    assert res["received_amount"] == 7500.0
    assert res["difference"] == 2500.0
    assert res["justified_amount"] == 1000.0
    assert res["claimable_amount"] == 1500.0


def test_harness_adapter_external_folder_spanish_aliases(tmp_path: Path):
    """Verifica que el adaptador normalice carpetas externas con nombres en español (factura.json, etc.)."""
    ext_dir = tmp_path / "caso_externo_jurado"
    ext_dir.mkdir(parents=True, exist_ok=True)

    (ext_dir / "factura.json").write_text(
        json.dumps({
            "invoice_id": "INV-EXT-01",
            "vendor_id": "PROV-01",
            "customer_id": "RET-01",
            "po_reference": "PO-EXT-01",
            "issue_date": "2026-10-01",
            "currency": "USD",
            "items": [{"item_id": "A1", "description": "Caja", "quantity": 50, "unit_price": 100.0, "total_price": 5000.0}],
            "subtotal": 5000.0,
            "tax": 0.0,
            "total_amount": 5000.0,
        }),
        encoding="utf-8",
    )
    (ext_dir / "pago.json").write_text(
        json.dumps({
            "payment_id": "PAY-EXT-01",
            "invoice_reference": "INV-EXT-01",
            "payment_date": "2026-10-15",
            "currency": "USD",
            "amount_paid": 4200.0,
            "deductions": [
                {"code": "DED-ARB", "reason": "Penalización administrativa unilateral sin soporte", "amount": 800.0}
            ],
        }),
        encoding="utf-8",
    )

    res = HarnessAdapter.evaluate(target=ext_dir, fast_path=True, silent_stdout=True)
    assert res["status"] == "SUCCESS"
    assert res["mae_invariant_verified"] is True
    assert res["billed_amount"] == 5000.0
    assert res["received_amount"] == 4200.0
    assert res["difference"] == 800.0
    assert res["claimable_amount"] == 800.0


def test_api_evaluate_endpoint():
    """Verifica los endpoints POST /api/evaluate y POST /evaluate para el Harness REST."""
    resp1 = client.post("/api/evaluate", json={"case_id": "case_002", "fast_path": True})
    assert resp1.status_code == 200
    body1 = resp1.json()
    assert body1["status"] == "SUCCESS"
    assert body1["case_id"] == "case_002"
    assert body1["mae_invariant_verified"] is True
    assert body1["claimable_amount"] == 12500.0

    resp2 = client.post(
        "/evaluate",
        json={
            "case_id": "case_harness_api_02",
            "billed_amount": 20000.0,
            "amount_paid": 18000.0,
            "unauthorized_penalty": 2000.0,
            "fast_path": True,
        },
    )
    assert resp2.status_code == 200
    body2 = resp2.json()
    assert body2["status"] == "SUCCESS"
    assert body2["mae_invariant_verified"] is True
    assert body2["claimable_amount"] == 2000.0
