"""
tests/test_predictive_radar.py
Suite de pruebas automatizadas para el Radar Preventivo Pre-Despacho (DVI)
y el Generador de Dossier Institucional para Arbitraje ICC/CANACO.
Sprint 5.4 (Frontera 4 de Superinteligencia).
"""

from decimal import Decimal
import pytest
from fastapi.testclient import TestClient

from api.main import app
from agent.predictive.leakage_radar import (
    DviRiskFactor,
    DviPredictionResult,
    PreDispatchLeakageRadar,
    HIGH_RISK_DC_PROFILES,
)
from agent.legal.arbitration_dossier import (
    ArbitrationEvidenceItem,
    ArbitrationDossier,
    ArbitrationDossierGenerator,
)
from data.models import DisputeAnalysisReport


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def sample_report():
    return DisputeAnalysisReport(
        case_id="case_001",
        billed_amount=Decimal("50000.00"),
        received_amount=Decimal("35000.00"),
        difference=Decimal("15000.00"),
        root_cause="Deducción unilateral controvertida",
        evidence=["Contrato Marco", "Factura FAC-001", "Remisión sellada"],
        justified_amount=Decimal("0.00"),
        claimable_amount=Decimal("15000.00"),
        confidence=0.95,
        recommended_action="Reclamar la totalidad del importe retenido indebidamente.",
        resolution_notes=["Entrega satisfecha en su totalidad según POD sellado."]
    )


# ==============================================================================
# 1. Pruebas del Radar Preventivo Pre-Despacho (DVI Engine)
# ==============================================================================

def test_radar_dvi_critical_risk():
    """Valida la detección de riesgo crítico por ventana de cita asimétrica e historial de merma."""
    res = PreDispatchLeakageRadar.evaluate_purchase_order(
        po_reference="PO-WM-994820",
        retailer_id="WALMART_MEXICO",
        destination_dc="WALMART_DC_6014",
        total_amount=Decimal("85000.00"),
        estimated_transit_hours=4.5,   # Tránsito largo
        appointment_window_hours=2.0,  # Ventana corta
        agreed_catalog_price_match=False,  # Discrepancia de precio
        contract_has_unilateral_penalty=True
    )

    assert isinstance(res, DviPredictionResult)
    assert res.po_reference == "PO-WM-994820"
    assert res.dvi_score >= 75.0
    assert res.risk_level == "CRITICAL"
    assert res.predicted_leakage_amount > Decimal("0.00")
    assert res.estimated_leakage_pct >= 5.0
    assert len(res.risk_factors) >= 3

    # Validar salvaguardas mandatorias inyectadas
    safeguards_text = " ".join(res.pre_dispatch_safeguards)
    assert "C-TPAT" in safeguards_text
    assert "EDI 856" in safeguards_text
    assert "reprogramar" in safeguards_text.lower() or "despachar" in safeguards_text.lower()
    assert "🚨 ALERTA CRÍTICA PRE-DESPACHO" in res.binding_executive_directive


def test_radar_dvi_low_risk():
    """Valida la evaluación de una orden de compra rutinaria con bajo riesgo."""
    res = PreDispatchLeakageRadar.evaluate_purchase_order(
        po_reference="PO-LOCAL-1002",
        retailer_id="CLIENTE_REGIONAL",
        destination_dc="ALMACEN_LOCAL_CDMX",
        total_amount=Decimal("20000.00"),
        estimated_transit_hours=1.0,
        appointment_window_hours=4.0,
        agreed_catalog_price_match=True,
        contract_has_unilateral_penalty=False
    )

    assert res.dvi_score < 30.0
    assert res.risk_level == "LOW"
    assert res.predicted_leakage_amount < Decimal("500.00")
    assert "✅ RIESGO BAJO" in res.binding_executive_directive


def test_radar_high_risk_destinations_catalog():
    """Verifica el catálogo topológico de centros de distribución de alta merma."""
    catalog = PreDispatchLeakageRadar.get_high_risk_destinations_catalog()
    assert "WALMART_DC_6014" in catalog
    assert "AMAZON_FC_DFW" in catalog
    assert "SORIANA_DC_TULTITLAN" in catalog
    assert "LIVERPOOL_CUAUTITLAN" in catalog

    wm = catalog["WALMART_DC_6014"]
    assert wm["risk_rating"] == "CRITICAL"
    assert wm["min_lead_hours_asn"] == 4.0


# ==============================================================================
# 2. Pruebas del Generador de Dossier Arbitral ICC/CANACO
# ==============================================================================

def test_arbitration_dossier_generation_icc(sample_report):
    """Valida la compilación de un expediente arbitral formal ante la ICC."""
    dossier = ArbitrationDossierGenerator.generate_dossier(
        report=sample_report,
        claimant_name="PROVEEDOR INDUSTRIAL ALIMENTICIO S.A. DE C.V.",
        claimant_tax_id="PRO920101XYZ",
        respondent_name="NUEVA WAL MART DE MEXICO S. DE R.L. DE C.V.",
        respondent_tax_id="NWM9709244W4",
        institution="ICC",
        days_in_arrears=120
    )

    assert isinstance(dossier, ArbitrationDossier)
    assert dossier.case_id == "case_001"
    assert "ARB-ICC-" in dossier.dossier_folio
    assert "Cámara de Comercio Internacional (ICC Paris)" in dossier.arbitral_institution
    assert "Reglamento de Arbitraje de la Cámara de Comercio Internacional" in dossier.governing_rules

    # Aritmética financiera ($0.00 MAE)
    assert dossier.principal_amount_claimed == Decimal("15000.00")
    assert dossier.accrued_interest_amount > Decimal("0.00")
    assert dossier.arbitration_costs_claimed == Decimal("5000.00")
    expected_total = (dossier.principal_amount_claimed + dossier.accrued_interest_amount + dossier.arbitration_costs_claimed).quantize(Decimal("0.01"))
    assert dossier.total_demand_amount == expected_total

    # Verificación de foliación y catálogo de pruebas
    assert dossier.total_pages_foliated >= 20
    assert len(dossier.evidence_catalog) == 7
    first_ev = dossier.evidence_catalog[0]
    assert "Fojas 001 a" in first_ev.foja_range
    assert len(first_ev.sha256_hash) > 10

    # Verificación de los 7 capítulos en Markdown
    md = dossier.full_dossier_markdown
    assert "CAPÍTULO I: RESUMEN EJECUTIVO Y LIQUIDACIÓN PATRIMONIAL" in md
    assert "CAPÍTULO II: IDENTIFICACIÓN DE LAS PARTES Y COMPETENCIA ARBITRAL" in md
    assert "CAPÍTULO III: RELACIÓN CIRCUNSTANCIADA DE LOS HECHOS" in md
    assert "CAPÍTULO IV: TABLA MAESTRA DE EVIDENCIAS PERICIALES FOLIADAS" in md
    assert "CAPÍTULO V: FUNDAMENTACIÓN JURÍDICA IMPERATIVA" in md
    assert "CAPÍTULO VI: PETITORIO FORMAL Y ACCIONES SOLICITADAS" in md
    assert "Convención de las Naciones Unidas sobre Contratos de Compraventa Internacional (CISG)" in md
    assert "T-MEC / USMCA" in md


def test_arbitration_dossier_generation_canaco(sample_report):
    """Valida la generación de dossier arbitral ante CANACO (México)."""
    dossier = ArbitrationDossierGenerator.generate_dossier(
        report=sample_report,
        institution="CANACO",
        days_in_arrears=60
    )

    assert "ARB-CANACO-" in dossier.dossier_folio
    assert "CANACO" in dossier.arbitral_institution
    assert dossier.total_pages_foliated >= 20


# ==============================================================================
# 3. Pruebas Endpoints API REST (/api/radar/...)
# ==============================================================================

def test_api_radar_dvi_evaluate_endpoint(client):
    """Prueba el endpoint /api/radar/dvi-evaluate."""
    response = client.post(
        "/api/radar/dvi-evaluate",
        json={
            "po_reference": "PO-TEST-8812",
            "retailer_id": "AMAZON_FULFILLMENT",
            "destination_dc": "AMAZON_FC_DFW",
            "total_amount": 50000.0,
            "estimated_transit_hours": 4.0,
            "appointment_window_hours": 2.0,
            "agreed_catalog_price_match": True,
            "contract_has_unilateral_penalty": True
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["po_reference"] == "PO-TEST-8812"
    assert "dvi_score" in data
    assert data["dvi_score"] >= 50.0
    assert len(data["risk_factors"]) >= 2
    assert len(data["pre_dispatch_safeguards"]) > 0


def test_api_radar_generate_arbitration_dossier_endpoint(client):
    """Prueba el endpoint /api/radar/generate-arbitration-dossier sobre case_001."""
    response = client.post(
        "/api/radar/generate-arbitration-dossier",
        json={
            "case_id": "case_001",
            "institution": "ICC",
            "days_in_arrears": 90
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["case_id"] == "case_001"
    assert "dossier_folio" in data
    assert "ARB-ICC-" in data["dossier_folio"]
    assert data["total_pages_foliated"] >= 20
    assert len(data["evidence_catalog"]) == 7
    assert "CAPÍTULO I:" in data["full_dossier_markdown"]


def test_api_radar_high_risk_destinations_endpoint(client):
    """Prueba la consulta del catálogo de centros de distribución de alto riesgo."""
    response = client.get("/api/radar/high-risk-destinations")
    assert response.status_code == 200
    data = response.json()
    assert "WALMART_DC_6014" in data
    assert "AMAZON_FC_DFW" in data
