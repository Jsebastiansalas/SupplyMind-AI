"""
tests/test_portal_dispatcher.py
Suite de pruebas automatizadas para el Despachador Robótico a Portales B2B (Sprint 6.3).
Verifica:
1. Empaquetador forense de evidencias (CFDI 4.0, remisión sellada, EDI 856/997, C-TPAT, Convenio ZKP).
2. Adaptadores de payload específicos para los 4 portales (Walmart, Amazon, Soriana, Liverpool).
3. Máquina de estados de radicación, generación de ticket oficial y bitácora de auditoría.
4. Integración y respuesta en endpoints REST de FastAPI.
"""

import pytest
from decimal import Decimal
from fastapi.testclient import TestClient

from api.main import app
from agent.portal.portal_dispatcher_engine import PortalDispatcherEngine
from data.models import PortalDispatchDossier, PortalDispatchReceipt

client = TestClient(app)


def test_build_dispatch_dossier_manifest():
    """Valida la generación del expediente forense con hashes SHA-256 e índice de evidencias."""
    case_id = "case_005_amazon_shortage"
    dossier = PortalDispatcherEngine.build_dispatch_dossier(case_id)

    assert isinstance(dossier, PortalDispatchDossier)
    assert dossier.case_id == case_id
    assert dossier.portal_type == "AMAZON_VENDOR_CENTRAL"
    assert len(dossier.manifest_items) >= 4

    # Verificar integridad de cada documento
    doc_types = [item.doc_type for item in dossier.manifest_items]
    assert "CFDI_40_XML" in doc_types
    assert "REMISSION_STAMPED_POD" in doc_types
    assert "ASN_EDI_856" in doc_types
    assert "CTPAT_SEAL_CERTIFICATE" in doc_types

    for item in dossier.manifest_items:
        assert len(item.sha256_hash) == 64
        assert item.status == "VERIFIED_VALID"
        assert item.file_size_bytes > 0

    assert len(dossier.zkp_dossier_digest) == 64


def test_portal_adapters_payload_formatting():
    """Valida los adaptadores específicos para Walmart, Amazon, Soriana y Liverpool."""
    # 1. Walmart Retail Link
    wm_dossier = PortalDispatcherEngine.build_dispatch_dossier("case_006_walmart_otif_pricing", portal_type="WALMART_RETAIL_LINK")
    assert wm_dossier.adapter_payload is not None
    assert wm_dossier.adapter_payload.portal_type == "WALMART_RETAIL_LINK"
    assert "21" in wm_dossier.adapter_payload.claim_code or "Shortage" in wm_dossier.adapter_payload.claim_code
    assert "6014" in wm_dossier.adapter_payload.dc_or_fc_code
    assert wm_dossier.adapter_payload.portal_specific_fields["luminate_supplier_id"] == "VN-77291-WAL"

    # 2. Amazon Vendor Central
    amz_dossier = PortalDispatcherEngine.build_dispatch_dossier("case_005_amazon_shortage", portal_type="AMAZON_VENDOR_CENTRAL")
    assert amz_dossier.adapter_payload.portal_type == "AMAZON_VENDOR_CENTRAL"
    assert "SHORTAGE" in amz_dossier.adapter_payload.claim_code
    assert "DAL3" in amz_dossier.adapter_payload.dc_or_fc_code
    assert amz_dossier.adapter_payload.portal_specific_fields["vendor_code"] == "AMZMX-4401"

    # 3. Soriana B2B
    sor_dossier = PortalDispatcherEngine.build_dispatch_dossier("case_005_amazon_shortage", portal_type="SORIANA_B2B")
    assert sor_dossier.adapter_payload.portal_type == "SORIANA_B2B"
    assert "DED-MERMA" in sor_dossier.adapter_payload.claim_code
    assert "201" in sor_dossier.adapter_payload.dc_or_fc_code
    assert "clave_proveedor_soriana" in sor_dossier.adapter_payload.portal_specific_fields

    # 4. Liverpool B2B
    liv_dossier = PortalDispatcherEngine.build_dispatch_dossier("case_005_amazon_shortage", portal_type="LIVERPOOL_B2B")
    assert liv_dossier.adapter_payload.portal_type == "LIVERPOOL_B2B"
    assert "DED-04" in liv_dossier.adapter_payload.claim_code
    assert "Galerías" in liv_dossier.adapter_payload.dc_or_fc_code
    assert "partners_portal_id" in liv_dossier.adapter_payload.portal_specific_fields


def test_dispatch_lifecycle_and_ticket_generation():
    """Valida la ejecución desatendida del despacho y la bitácora auditable de radicación."""
    case_id = "case_005_amazon_shortage"
    receipt = PortalDispatcherEngine.dispatch_case_to_portal(
        case_id=case_id,
        operator_name="Ing. Alejandro Garza (SupplyMind Lead Dispatcher)"
    )

    assert isinstance(receipt, PortalDispatchReceipt)
    assert receipt.status == "CONFIRMED_ACCEPTED"
    assert receipt.http_status_code == 201
    assert receipt.tracking_ticket.startswith("AMZN-CASE-2026-")
    assert len(receipt.confirmation_seal_sha256) == 64
    assert receipt.estimated_sla_days == 10

    # Bitácora paso a paso
    assert len(receipt.log_trace) >= 7
    assert any("[INIT]" in log for log in receipt.log_trace)
    assert any("[AUTH]" in log for log in receipt.log_trace)
    assert any("[DOSSIER]" in log for log in receipt.log_trace)
    assert any("[UPLOAD]" in log for log in receipt.log_trace)
    assert any("[SUBMIT]" in log for log in receipt.log_trace)
    assert any("[CONFIRMED]" in log for log in receipt.log_trace)

    # Recuperación posterior
    stored_receipt = PortalDispatcherEngine.get_dispatch_receipt(case_id)
    assert stored_receipt is not None
    assert stored_receipt.tracking_ticket == receipt.tracking_ticket


def test_rest_api_portal_dispatch_endpoints():
    """Valida los endpoints REST para generación de dossier y radicación en portales."""
    case_id = "case_005_amazon_shortage"

    # 1. GET /api/cases/{case_id}/portal/dossier
    dossier_res = client.get(f"/api/cases/{case_id}/portal/dossier")
    assert dossier_res.status_code == 200
    d_data = dossier_res.json()
    assert d_data["status"] == "success"
    assert "manifest_items" in d_data["dossier"]
    assert len(d_data["dossier"]["manifest_items"]) >= 4

    # 2. POST /api/cases/{case_id}/portal/dispatch
    post_res = client.post(
        f"/api/cases/{case_id}/portal/dispatch",
        json={"portal_type": "AMAZON_VENDOR_CENTRAL", "operator_name": "Auditor Test"}
    )
    assert post_res.status_code == 200
    p_data = post_res.json()
    assert p_data["status"] == "success"
    assert p_data["receipt"]["status"] == "CONFIRMED_ACCEPTED"
    assert "AMZN-CASE-2026-" in p_data["receipt"]["tracking_ticket"]

    # 3. GET /api/cases/{case_id}/portal/receipt
    rcpt_res = client.get(f"/api/cases/{case_id}/portal/receipt")
    assert rcpt_res.status_code == 200
    r_data = rcpt_res.json()
    assert r_data["status"] == "success"
    assert r_data["receipt"]["tracking_ticket"] == p_data["receipt"]["tracking_ticket"]

    # 4. GET /api/portal/dispatches
    all_res = client.get("/api/portal/dispatches")
    assert all_res.status_code == 200
    all_data = all_res.json()
    assert all_data["status"] == "success"
    assert all_data["total_dispatches"] >= 1
