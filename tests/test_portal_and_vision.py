"""
tests/test_portal_and_vision.py
Pruebas unitarias e integración para el Motor RPA de Portales y Visión Multimodal (Sprints 6.1 y 6.2).
"""

from decimal import Decimal
import pytest
from fastapi.testclient import TestClient

from api.main import app
from agent.portal.retailer_portal_agent import RetailerPortalAgent
from agent.vision.pallet_vision_auditor import PalletVisionAuditor

client = TestClient(app)


# ==============================================================================
# Pruebas Unitarias: RPA Portales Retailer (Sprint 6.1)
# ==============================================================================

def test_retailer_portal_catalog():
    """Valida el catálogo de portales soportados."""
    portals = RetailerPortalAgent.get_supported_portals()
    portal_ids = [p["portal_id"] for p in portals]
    assert "WALMART_RETAIL_LINK" in portal_ids
    assert "AMAZON_VENDOR_CENTRAL" in portal_ids
    assert "SORIANA_B2B" in portal_ids
    assert "LIVERPOOL_B2B" in portal_ids


def test_sync_walmart_retail_link():
    """Valida la extracción desatendida de notas de débito de Walmart."""
    res = RetailerPortalAgent.sync_retailer_portal("WALMART_RETAIL_LINK", max_items=2)
    assert res.portal_type == "WALMART_RETAIL_LINK"
    assert res.total_deductions_found >= 1
    assert res.total_disputed_amount > Decimal("0.00")
    assert res.currency == "MXN"
    assert len(res.log_trace) >= 4
    for d in res.deductions:
        assert isinstance(d.amount, Decimal)
        assert d.dispute_status == "PENDING_ANALYSIS"


def test_sync_amazon_vendor_central():
    """Valida la extracción de deducciones en USD de Amazon Vendor Central."""
    res = RetailerPortalAgent.sync_retailer_portal("AMAZON_VENDOR_CENTRAL", max_items=2)
    assert res.portal_type == "AMAZON_VENDOR_CENTRAL"
    assert res.currency == "USD"
    assert any("SHORTAGE" in d.deduction_code for d in res.deductions)


def test_submit_dispute_to_portal():
    """Valida la carga y obtención de ticket de apelación en el portal."""
    sub = RetailerPortalAgent.submit_dispute_to_portal(
        portal_type="WALMART_RETAIL_LINK",
        deduction_id="DED-WM-9011",
        case_id="case_001",
        claimable_amount=Decimal("18500.00")
    )
    assert sub.portal_type == "WALMART_RETAIL_LINK"
    assert "TICKET-WAL" in sub.tracking_ticket
    assert sub.portal_response_status == "ACCEPTED_FOR_REVIEW"
    assert len(sub.attached_evidence_files) >= 3
    assert "SEAL-SHA256" in sub.confirmation_seal


# ==============================================================================
# Pruebas Unitarias: Visión Multimodal en Muelle & C-TPAT (Sprint 6.2)
# ==============================================================================

def test_inspect_pallet_clean():
    """Valida el peritaje de una tarima prístina con precinto C-TPAT verificado."""
    cert = PalletVisionAuditor.inspect_pallet(
        image_name="tarima_pristina.jpg",
        expected_seal="CTPAT-MX-982144",
        po_reference="PO-994820",
        case_id="case_001",
        simulate_damage=False
    )
    assert cert.overall_verdict == "CARGO_PRISTINE_ACCEPTED"
    assert cert.seal_audit.is_seal_matched is True
    assert cert.seal_audit.seal_status == "INTACT_AUTHENTIC"
    assert cert.pallet_audit.damaged_boxes_count == 0
    assert cert.pallet_audit.total_boxes_detected == 48
    assert len(cert.bounding_boxes) >= 4
    assert len(cert.forensic_sha256_hash) == 64


def test_inspect_pallet_damage_detection():
    """Valida la detección de anomalías (emplaye roto, caja aplastada, precinto violado)."""
    cert = PalletVisionAuditor.inspect_pallet(
        image_name="tarima_danada.jpg",
        expected_seal="CTPAT-MX-982144",
        po_reference="PO-AMZ-881290",
        case_id="case_005_amazon_shortage",
        simulate_damage=True
    )
    assert cert.overall_verdict == "IRREGULARITY_FLAGGED"
    assert cert.seal_audit.is_seal_matched is False
    assert cert.pallet_audit.damaged_boxes_count > 0
    assert any(b.status == "ANOMALY_FLAGGED" for b in cert.bounding_boxes)


# ==============================================================================
# Pruebas de Integración Endpoints REST API
# ==============================================================================

def test_api_portal_sync_endpoint():
    """Valida el endpoint POST /api/portal/sync-retailer."""
    response = client.post("/api/portal/sync-retailer", json={"portal_type": "WALMART_RETAIL_LINK", "max_items": 2})
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["portal_type"] == "WALMART_RETAIL_LINK"
    assert Decimal(str(data["total_disputed_amount"])) > Decimal("0.00")


def test_api_portal_upload_dispute_endpoint():
    """Valida el endpoint POST /api/portal/upload-dispute."""
    payload = {
        "portal_type": "WALMART_RETAIL_LINK",
        "deduction_id": "DED-WM-2026-90",
        "case_id": "case_001",
        "claimable_amount": 18500.00
    }
    response = client.post("/api/portal/upload-dispute", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()
    assert "tracking_ticket" in data


def test_api_vision_inspect_endpoint():
    """Valida el endpoint POST /api/vision/inspect-pallet."""
    payload = {
        "expected_seal": "CTPAT-MX-982144",
        "po_reference": "PO-994820",
        "case_id": "case_001",
        "simulate_damage": False
    }
    response = client.post("/api/vision/inspect-pallet", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["overall_verdict"] == "CARGO_PRISTINE_ACCEPTED"
    assert len(data["bounding_boxes"]) >= 4


def test_api_vision_samples_endpoint():
    """Valida el endpoint GET /api/vision/samples."""
    response = client.get("/api/vision/samples")
    assert response.status_code == 200, response.text
    data = response.json()
    assert len(data["samples"]) >= 2
