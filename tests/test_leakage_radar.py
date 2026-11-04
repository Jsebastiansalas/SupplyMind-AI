"""
tests/test_leakage_radar.py
Suite de pruebas periciales para el Radar de Fuga de Capital y Perfilado de Retailers (Eje 4).

Valida:
1. Escaneo de cartera institucional y consistencia matemática en Decimal ($0.00 MAE).
2. Perfilado predictivo de retailers (Walmart, Amazon, Cisco, Home Depot, Soriana, Liverpool, Chedraui, DataCo).
3. Cálculo del Deduction Vulnerability Index (DVI) e identificación de salvaguardas pre-despacho.
4. Exportación formal de reportes en Markdown y JSON.
5. Invocación de la herramienta ReAct 'audit_retailer_leakage_radar'.
6. Endpoints de la API REST (/api/analytics/leakage-radar, /hubs, /evaluate-po).
"""

from decimal import Decimal
import os
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from api.main import app
from agent.core.fx_and_leakage_engine import (
    RetailerLeakageProfiler,
    INCOTERM_RULES_REGISTRY,
)
from agent.predictive.leakage_radar import PreDispatchLeakageRadar
from agent.tools.registry import TOOL_DEFINITIONS, ToolExecutor
from agent.core.state import DisputeState
from agent.memory.audit_logger import AuditLogger
from data.models import PortfolioLeakageRadarReport

client = TestClient(app)


def test_portfolio_leakage_radar_scanning_and_exact_decimal_math():
    """Valida el escaneo de cartera y la precisión estricta de partida doble en Decimal."""
    report = RetailerLeakageProfiler.scan_portfolio_leakage_radar()

    assert isinstance(report, PortfolioLeakageRadarReport)
    assert report.total_cases_scanned >= 30
    assert report.total_disputed_volume > Decimal("0.00")
    assert report.total_recovered_capital > Decimal("0.00")

    # Invariante contable exacto: disputado == recuperado + en riesgo
    diff = abs(report.total_disputed_volume - (report.total_recovered_capital + report.total_leakage_at_risk))
    assert diff <= Decimal("0.05")

    # Win rate en rango legal
    assert 0.0 <= report.portfolio_win_rate_pct <= 100.0

    # Al menos 7 retailers representados
    assert len(report.retailer_summaries) >= 7

    retailer_ids = [r.retailer_id for r in report.retailer_summaries]
    for expected_r in ["AMAZON", "WALMART", "CISCO", "HOMEDEPOT", "SORIANA", "LIVERPOOL", "CHEDRAUI"]:
        assert expected_r in retailer_ids


def test_retailer_profiles_expansion():
    """Valida los perfiles predictivos y patrones sistemáticos de las cadenas comerciales."""
    # 1. Walmart
    wmt = RetailerLeakageProfiler.get_profile("WALMART")
    assert wmt.risk_tier == "PREDATORIO"
    assert wmt.recommended_incoterm == "FOB"
    assert any("PAT-WMT-01" in p.pattern_id for p in wmt.systematic_patterns)

    # 2. Soriana
    sor = RetailerLeakageProfiler.get_profile("SORIANA")
    assert sor.risk_tier == "ALTO"
    assert any("REBATE" in r for r in sor.top_deduction_reasons)
    assert len(sor.pre_dispatch_checklist) >= 2

    # 3. Liverpool
    liv = RetailerLeakageProfiler.get_profile("LIVERPOOL")
    assert liv.risk_tier == "MEDIO"
    assert any("COLGADO" in r for r in liv.top_deduction_reasons)

    # 4. DataCo Global
    dco = RetailerLeakageProfiler.get_profile("DATACO_GLOBAL")
    assert dco.risk_tier == "MEDIO"
    assert dco.win_rate_pct >= 90.0


def test_pre_dispatch_dvi_evaluation_high_risk():
    """Valida el cálculo del DVI y prescripción de salvaguardas para un despacho de alto riesgo."""
    dvi_res = RetailerLeakageProfiler.evaluate_pre_dispatch_order(
        po_reference="PO-TEST-WMT-9921",
        retailer_id="WALMART",
        destination_dc="WALMART_DC_6014",
        total_amount=Decimal("50000.00"),
        estimated_transit_hours=4.5,
        appointment_window_hours=2.0,
        agreed_catalog_price_match=False,
        contract_has_unilateral_penalty=True
    )

    assert dvi_res.po_reference == "PO-TEST-WMT-9921"
    assert dvi_res.dvi_score >= 50.0
    assert dvi_res.risk_level in ["HIGH", "CRITICAL"]
    assert dvi_res.predicted_leakage_amount > Decimal("0.00")
    assert len(dvi_res.risk_factors) >= 3
    assert len(dvi_res.pre_dispatch_safeguards) >= 3
    assert "🚨" in dvi_res.binding_executive_directive or "⚠️" in dvi_res.binding_executive_directive


def test_export_portfolio_radar_report(tmp_path):
    """Valida la generación y persistencia de los reportes en Markdown y JSON."""
    report = RetailerLeakageProfiler.scan_portfolio_leakage_radar()
    paths = RetailerLeakageProfiler.export_portfolio_radar_report(report, output_dir=str(tmp_path))

    json_file = Path(paths["json_report"])
    md_file = Path(paths["markdown_report"])

    assert json_file.exists()
    assert md_file.exists()

    md_text = md_file.read_text(encoding="utf-8")
    assert "# 🛰️ Radar de Fuga de Capital y Perfilado de Retailers" in md_text
    assert "Métricas Consolidadas de Capital" in md_text
    assert "Ranking de Riesgo y Perfilado" in md_text
    assert "Centros de Distribución (CEDIS)" in md_text


def test_leakage_radar_react_tool():
    """Valida la ejecución de la herramienta ReAct 'audit_retailer_leakage_radar'."""
    logger = AuditLogger("test_case_radar_exec")
    state = DisputeState(case_id="case_005_amazon_shortage", objective="Audit leakage radar")
    executor = ToolExecutor(state, logger)

    # 1. Modo retailer individual
    res_single = executor.execute_tool("audit_retailer_leakage_radar", {"retailer_id": "AMAZON"})
    assert res_single["status"] == "success"
    assert res_single["mode"] == "SINGLE_RETAILER_PROFILE"
    assert res_single["retailer_id"] == "AMAZON"
    assert len(res_single["pre_dispatch_checklist"]) >= 2

    # 2. Modo escaneo de cartera
    res_port = executor.execute_tool("audit_retailer_leakage_radar", {"scan_portfolio": True})
    assert res_port["status"] == "success"
    assert res_port["mode"] == "PORTFOLIO_SCAN"
    assert res_port["total_cases_scanned"] >= 30
    assert res_port["total_disputed_volume_usd"] > 0
    assert len(res_port["top_retailers"]) >= 3


def test_leakage_radar_api_endpoints():
    """Valida los endpoints REST del radar en FastAPI."""
    # 1. GET /api/analytics/leakage-radar
    r1 = client.get("/api/analytics/leakage-radar")
    assert r1.status_code == 200
    data1 = r1.json()
    assert data1["status"] == "success"
    assert data1["total_cases_scanned"] >= 30
    assert data1["total_disputed_volume_usd"] > 0
    assert len(data1["retailer_summaries"]) >= 7

    # 2. GET /api/analytics/leakage-radar/hubs
    r2 = client.get("/api/analytics/leakage-radar/hubs")
    assert r2.status_code == 200
    data2 = r2.json()
    assert data2["status"] == "success"
    assert data2["count"] >= 3

    # 3. POST /api/analytics/leakage-radar/evaluate-po
    r3 = client.post(
        "/api/analytics/leakage-radar/evaluate-po",
        json={
            "po_reference": "PO-TEST-API-001",
            "retailer_id": "WALMART",
            "destination_dc": "WALMART_DC_6014",
            "total_amount": 35000.0,
            "estimated_transit_hours": 3.0,
            "appointment_window_hours": 2.0,
            "sku_list": ["SKU-001", "SKU-002"],
            "agreed_catalog_price_match": True,
            "contract_has_unilateral_penalty": False
        }
    )
    assert r3.status_code == 200
    data3 = r3.json()
    assert data3["status"] == "success"
    assert "dvi_result" in data3
    assert data3["dvi_result"]["dvi_score"] > 0
