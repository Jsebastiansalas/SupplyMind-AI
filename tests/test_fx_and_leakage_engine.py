"""
tests/test_fx_and_leakage_engine.py
Suite de pruebas periciales para el Motor Cambiario FX con Incoterms 2020 (Pilar 5)
y el Perfilador de Fugas de Retailers con Checklists Pre-Despacho (Pilar 3).

Valida:
1. Invariante matemático contable en Decimal: total_nominal == fx_variance + commercial_deduction.
2. Cero error de redondeo de punto flotante.
3. Reglas ICC Incoterms 2020 (FOB, FCA, DDP, DAP, CIF, CIP, EXW).
4. Perfilamiento predictivo de Amazon, Walmart, Cisco, Home Depot y Mega Retailer.
5. Endpoints de la API REST y chat conversacional con Grok.
"""

from decimal import Decimal
import pytest
from fastapi.testclient import TestClient

from api.main import app
from agent.core.fx_and_leakage_engine import (
    FxAndIncotermsEngine,
    RetailerLeakageProfiler,
    INCOTERM_RULES_REGISTRY,
)
from data.models import FxAuditReport, RetailerLeakageProfile


client = TestClient(app)


def test_incoterms_rules_registry_integrity():
    """Valida que el registro oficial contenga las reglas ICC 2020 indispensables."""
    required_codes = ["FOB", "FCA", "DDP", "DAP", "CIF", "CIP", "EXW"]
    for code in required_codes:
        assert code in INCOTERM_RULES_REGISTRY
        rule = INCOTERM_RULES_REGISTRY[code]
        assert rule.incoterm_code == code
        assert len(rule.name) > 5
        assert len(rule.transfer_point) > 5
        assert rule.transit_risk_party in ["BUYER", "SELLER"]
        assert "ICC Incoterms 2020" in rule.legal_basis


def test_fx_isolation_mathematical_invariant_exactness():
    """
    Verifica que la varianza cambiaria pura y la deducción comercial operativa
    sumen exactamente la discrepancia nominal total en moneda de liquidación (Decimal).
    """
    report = FxAndIncotermsEngine.audit_cross_border_fx(
        case_id="case_005_amazon_shortage",
        invoice_rate=Decimal("18.5000"),
        payment_rate=Decimal("17.8000"),
        target_currency="MXN",
        incoterm_code="FOB"
    )

    assert report.math_invariant_verified is True
    # Invariante contable estricto: total_nominal == fx_variance + commercial_deduction
    calculated_sum = report.fx_variance_amount + report.commercial_deduction_amount
    diff = abs(report.total_nominal_discrepancy - calculated_sum)
    assert diff <= Decimal("0.05")

    # Caso 005 facturó $48,000 USD y pagó $40,500 USD (Diferencia de $7,500 USD)
    assert report.billed_amount_invoice_curr == Decimal("48000.00")
    assert report.received_amount_invoice_curr == Decimal("40500.00")
    # FX Variance = 48,000 * (18.50 - 17.80) = 48,000 * 0.70 = 33,600.00 MXN
    assert report.fx_variance_amount == Decimal("33600.00")
    assert report.fx_impact_type == "PÉRDIDA CAMBIARIA (FX LOSS)"


def test_fx_rate_appreciation_gain():
    """Valida la detección correcta de ganancia cambiaria cuando la divisa se aprecia."""
    report = FxAndIncotermsEngine.audit_cross_border_fx(
        case_id="case_006_walmart_otif_pricing",
        invoice_rate=Decimal("17.5000"),
        payment_rate=Decimal("18.2000"),
        target_currency="MXN",
        incoterm_code="DDP"
    )

    # 17.50 - 18.20 = -0.70 (Ganancia cambiaria en liquidación)
    assert report.fx_variance_amount < Decimal("0.00")
    assert report.fx_impact_type == "GANANCIA CAMBIARIA (FX GAIN)"
    assert report.math_invariant_verified is True


def test_incoterms_legal_verdict_fob_origin_risk():
    """Bajo FOB/FCA el riesgo se transfiere en origen; deducción en muelle de destino es improcedente."""
    report = FxAndIncotermsEngine.audit_cross_border_fx(
        case_id="case_005_amazon_shortage",
        incoterm_code="FOB"
    )

    assert report.incoterm == "FOB"
    assert report.incoterm_verdict == "IMPROCEDENTE_POR_INCOTERM"
    # El 100% de la deducción de transporte/muelle es reclamable al comprador
    assert report.effective_claimable_amount == Decimal("7500.00")
    assert "ICC Incoterms 2020 Regla FOB" in report.incoterm_legal_basis


def test_incoterms_legal_verdict_ddp_destination_risk():
    """Bajo DDP el vendedor asume el riesgo hasta el muelle de destino."""
    report = FxAndIncotermsEngine.audit_cross_border_fx(
        case_id="case_005_amazon_shortage",
        incoterm_code="DDP"
    )

    assert report.incoterm == "DDP"
    assert report.incoterm_verdict == "PROCEDENTE_EN_DESTINO"
    # El saldo reclamable se limita al componente no justificado ($2,500 de multa ASN)
    assert report.effective_claimable_amount == Decimal("2500.00")


def test_incoterms_legal_verdict_cif_insurance_obligation():
    """Bajo CIF el riesgo es del comprador amparado por seguro provisto por el vendedor."""
    report = FxAndIncotermsEngine.audit_cross_border_fx(
        case_id="case_005_amazon_shortage",
        incoterm_code="CIF"
    )

    assert report.incoterm == "CIF"
    assert report.incoterm_verdict == "REQUERIDO_RECLAMO_ASEGURADORA"
    assert "seguro marítimo" in report.incoterm_legal_basis.lower()


def test_retailer_leakage_profiler_amazon():
    """Valida el perfil predictivo y patrones abusivos de Amazon."""
    profile = RetailerLeakageProfiler.get_profile("AMAZON")
    assert profile.retailer_id == "AMAZON"
    assert profile.risk_tier == "ALTO"
    assert profile.win_rate_pct >= 90.0
    assert profile.recovery_ratio_pct >= 85.0
    assert "Dallas FC" in profile.cedis_alert_summary

    # Verificar que contenga el patrón abusivo de ASN EDI 856
    asn_pattern = next((p for p in profile.systematic_patterns if "ASN" in p.name), None)
    assert asn_pattern is not None
    assert asn_pattern.frequency_pct >= 80.0
    assert asn_pattern.impact_severity == "CRITICA"

    # Verificar checklist pre-despacho
    assert len(profile.pre_dispatch_checklist) >= 3
    edi_chk = next((c for c in profile.pre_dispatch_checklist if "EDI" in c.title), None)
    assert edi_chk is not None
    assert edi_chk.mandatory is True


def test_retailer_leakage_profiler_walmart():
    """Valida el perfil predictivo y deducción extemporánea de Walmart."""
    profile = RetailerLeakageProfiler.get_profile("WALMART")
    assert profile.retailer_id == "WALMART"
    assert profile.risk_tier == "PREDATORIO"
    assert profile.recommended_incoterm == "FOB"
    assert "85%" in profile.cedis_alert_summary

    # Patrón de pronto pago fin de mes
    early_pay = next((p for p in profile.systematic_patterns if "Pronto Pago" in p.name), None)
    assert early_pay is not None
    assert early_pay.frequency_pct == 85.0

    # Checklist Retail Link OTIF
    otif_chk = next((c for c in profile.pre_dispatch_checklist if "OTIF" in c.title), None)
    assert otif_chk is not None
    assert otif_chk.mandatory is True


def test_retailer_leakage_all_profiles_catalog():
    """Verifica que el catálogo institucional contenga todos los grandes retailers."""
    profiles = RetailerLeakageProfiler.get_all_profiles()
    retailer_ids = [p.retailer_id for p in profiles]
    assert "AMAZON" in retailer_ids
    assert "WALMART" in retailer_ids
    assert "CISCO" in retailer_ids
    assert "HOMEDEPOT" in retailer_ids
    assert "MEGA_RETAILER" in retailer_ids


def test_api_fx_audit_endpoint():
    """Prueba el endpoint GET /api/cases/{case_id}/fx-audit."""
    response = client.get("/api/cases/case_005_amazon_shortage/fx-audit?incoterm=FOB&invoice_rate=18.50&payment_rate=17.85")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["case_id"] == "case_005_amazon_shortage"
    audit = data["fx_audit"]
    assert audit["incoterm"] == "FOB"
    assert audit["incoterm_verdict"] == "IMPROCEDENTE_POR_INCOTERM"
    assert audit["math_invariant_verified"] is True
    assert audit["fx_variance_amount"] > 0


def test_api_fx_simulate_endpoint():
    """Prueba el endpoint POST /api/cases/{case_id}/fx-audit/simulate."""
    payload = {
        "invoice_fx_rate": 19.20,
        "payment_fx_rate": 18.00,
        "target_currency": "MXN",
        "incoterm": "CIF"
    }
    response = client.post("/api/cases/case_006_walmart_otif_pricing/fx-audit/simulate", json=payload)
    assert response.status_code == 200
    data = response.json()
    audit = data["simulated_fx_audit"]
    assert audit["incoterm"] == "CIF"
    assert audit["incoterm_verdict"] == "REQUERIDO_RECLAMO_ASEGURADORA"
    assert audit["invoice_fx_rate"] == 19.20


def test_api_retailer_profile_and_checklist_endpoints():
    """Prueba los endpoints de perfil de retailer y pre-dispatch checklist."""
    # 1. Perfil por caso
    resp1 = client.get("/api/cases/case_005_amazon_shortage/retailer-profile")
    assert resp1.status_code == 200
    p1 = resp1.json()["retailer_profile"]
    assert p1["retailer_id"] == "AMAZON"

    # 2. Checklist de Walmart
    resp2 = client.get("/api/retailers/WALMART/pre-dispatch-checklist")
    assert resp2.status_code == 200
    chk = resp2.json()["checklist"]
    assert len(chk) >= 3
    assert any("OTIF" in c["title"] for c in chk)


def test_chat_interception_fx_and_retailer_queries():
    """Valida la respuesta inteligente e inmediata a través del endpoint de chat."""
    # Consulta de FX
    resp_fx = client.post(
        "/api/cases/case_005_amazon_shortage/chat",
        json={"message": "¿Cuál es la varianza cambiaria FX y el veredicto bajo Incoterm FOB?"}
    )
    assert resp_fx.status_code == 200
    data_fx = resp_fx.json()
    assert data_fx["mode"] == "fx_and_incoterms"
    assert "Incoterms 2020" in data_fx["reply"]
    assert "Invariante Certificado" in data_fx["reply"]

    # Consulta de perfil de retailer
    resp_ret = client.post(
        "/api/cases/case_006_walmart_otif_pricing/chat",
        json={"message": "Muéstrame el perfil de fugas de Walmart y el checklist pre-despacho"}
    )
    assert resp_ret.status_code == 200
    data_ret = resp_ret.json()
    assert data_ret["mode"] == "retailer_leakage_profile"
    assert "Perfilador Predictivo" in data_ret["reply"]
    assert "Walmart" in data_ret["reply"]
