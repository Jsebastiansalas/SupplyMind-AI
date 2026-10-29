"""
tests/test_erp_bidirectional.py
Suite de pruebas para la simulación bidireccional ERP (SAP S/4HANA y Oracle NetSuite)
correspondiente al Sprint 4.8.
"""

import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def test_sap_document_posting_simulation():
    """Valida la contabilización simulada en SAP S/4HANA vía BAPI_ACC_DOCUMENT_POST."""
    res = client.post("/api/cases/case_001/erp/sap/post-document")
    assert res.status_code == 200
    data = res.json()

    assert data["status"] == "SUCCESS_POSTED"
    assert data["system"] == "SAP S/4HANA Cloud / On-Premise"
    assert data["protocol"] == "RFC_BAPI_ACC_DOCUMENT_POST"
    assert data["case_id"] == "case_001"

    conf = data["confirmation"]
    assert conf["sap_document_number"].startswith("1000")
    assert conf["company_code"] == "1000"
    assert conf["fiscal_year"] == "2026"
    assert conf["posting_status"] == "CLEARED_IN_SUBLEDGER"
    assert conf["total_posted_usd"] == 800.0
    assert conf["lines_posted_count"] >= 2
    assert len(conf["bapi_return"]) >= 1
    assert any("605" in str(msg.get("number")) for msg in conf["bapi_return"])


def test_netsuite_journal_posting_simulation():
    """Valida la emisión de JournalEntry en Oracle NetSuite vía SuiteTalk REST Web Services."""
    res = client.post("/api/cases/case_002/erp/netsuite/post-journal")
    assert res.status_code == 200
    data = res.json()

    assert data["status"] == "APPROVED_POSTED"
    assert data["system"] == "Oracle NetSuite ERP"
    assert data["protocol"] == "SuiteTalk REST Web Services (v1)"
    assert data["case_id"] == "case_002"

    conf = data["confirmation"]
    assert conf["internal_id"].isdigit()
    assert conf["tran_id"].startswith("JE-2026-")
    assert conf["posting_status"] == "APPROVED"
    assert conf["total_posted_usd"] > 0
    assert "netsuite.com" in conf["audit_trail_url"]


def test_erp_posting_nonexistent_case():
    """Valida el manejo defensivo de error 404 ante un caso inexistente."""
    res_sap = client.post("/api/cases/case_999_fake_invalid/erp/sap/post-document")
    assert res_sap.status_code == 404

    res_ns = client.post("/api/cases/case_999_fake_invalid/erp/netsuite/post-journal")
    assert res_ns.status_code == 404
