"""
tests/test_phase9_chat_omniscience.py
Pruebas exhaustivas para el Sprint 9.1:
Copiloto Conversacional Omnisciente con Tool-Calling ReAct, Consultas de Portafolio
e Inyección de Motores de Fases 7 y 8.
"""

import pytest
from decimal import Decimal
from fastapi.testclient import TestClient

from api.main import app
from agent.tools.registry import TOOL_DEFINITIONS, ToolExecutor
from api.routes.chat import (
    parse_portfolio_query,
    generate_portfolio_overview,
    parse_sla_query,
    parse_rhi_query,
    parse_bank_remittance_query,
    parse_root_cause_query,
    parse_liability_cap_query,
)

client = TestClient(app)


def test_tool_definitions_structure():
    """Valida que el registro de herramientas cumpla el estándar OpenAI Function Calling."""
    assert len(TOOL_DEFINITIONS) >= 15
    for tool in TOOL_DEFINITIONS:
        assert tool["type"] == "function"
        fn = tool["function"]
        assert "name" in fn
        assert "description" in fn
        assert "parameters" in fn
        assert fn["parameters"]["type"] == "object"


def test_intent_parsers_detection():
    """Valida la detección precisa de intenciones en lenguaje natural."""
    # Portafolio
    assert parse_portfolio_query("¿Cuál es el estado del portafolio y los casos más críticos?") is True
    assert parse_portfolio_query("Dame un resumen de cartera general") is True
    assert parse_portfolio_query("Ranking de la flota") is True
    assert parse_portfolio_query("¿Cuánto es la factura de este caso?") is False

    # SLA Watchdog
    assert parse_sla_query("¿Cuántos días faltan para la prescripción del SLA y el Art. 1041?") is True
    assert parse_sla_query("¿Cuál es el DTP y caducidad?") is True
    assert parse_sla_query("Hola buen día") is False

    # Salud Relacional RHI
    assert parse_rhi_query("¿Cuál es el puntaje RHI de salud relacional con Walmart?") is True
    assert parse_rhi_query("¿Qué riesgo de churn o deserción existe?") is True

    # Remesa Bancaria 3-Way
    assert parse_bank_remittance_query("Revisa la remesa bancaria y el depósito neto 3-way") is True
    assert parse_bank_remittance_query("Muéstrame el certificado de cierre de cartera") is True

    # Causa Raíz & CAPA
    assert parse_root_cause_query("¿Qué departamento es responsable según causa raíz?") is True
    assert parse_root_cause_query("Genera el ticket CAPA para almacén") is True

    # Topes Contractuales
    assert parse_liability_cap_query("¿Hay un tope máximo de penalización o límite de responsabilidad?") is True
    assert parse_liability_cap_query("¿Existe algún exceso sobre el cap?") is True


def test_portfolio_overview_endpoint():
    """Valida el endpoint GET /api/cases/portfolio/overview de inteligencia de cartera."""
    res = client.get("/api/cases/portfolio/overview")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    overview = data["overview"]
    assert overview["total_cases"] >= 50
    assert overview["total_billed"] > 0
    assert overview["total_disputed"] > 0
    assert overview["total_claimable"] > 0
    assert "recovery_ratio_pct" in overview
    assert "prescription_var_amount" in overview
    assert "CRITICAL_EXPIRED" in overview["urgency_counts"]
    assert "HIGH_IMMINENT" in overview["urgency_counts"]
    assert len(overview["top_critical_cases"]) <= 5
    assert len(overview["top_critical_cases"]) > 0

    assert "markdown_report" in data
    assert "Cross-Portfolio War-Room" in data["markdown_report"]


def test_chat_cross_portfolio_query_in_case():
    """Valida que una consulta de portafolio formulada dentro de un chat de caso sea interceptada y respondida."""
    res = client.post(
        "/api/cases/case_001/chat",
        json={"message": "¿Cómo está el portafolio global y cuáles son los casos críticos?"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["mode"] == "portfolio_intelligence"
    assert "Cross-Portfolio War-Room" in data["reply"]
    assert "portfolio_overview" in data
    assert data["portfolio_overview"]["total_cases"] >= 50


def test_chat_portfolio_virtual_case_id():
    """Valida que /api/cases/portfolio/chat responda con el análisis de cartera sin dar 404."""
    res = client.post(
        "/api/cases/portfolio/chat",
        json={"message": "Resumen ejecutivo de cartera"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["mode"] == "portfolio_intelligence"
    assert "War-Room" in data["reply"]


def test_chat_sla_watchdog_query():
    """Valida que la consulta sobre prescripción SLA retorne el dictamen temporal Art. 1041 CCom."""
    res = client.post(
        "/api/cases/case_001/chat",
        json={"message": "¿Cuál es la ventana de prescripción SLA y cuántos días quedan para este caso según el Art. 1041?"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["mode"] in ["sla_watchdog", "live"]
    reply = data["reply"]
    assert any(term in reply.lower() for term in ["prescripción", "prescripcion", "sla", "1041", "días", "dtp"])


def test_chat_relational_health_query():
    """Valida que la consulta sobre RHI devuelva los indicadores de salud y postura comercial."""
    res = client.post(
        "/api/cases/case_001/chat",
        json={"message": "¿Cuál es el Relationship Health Index (RHI) y qué postura comercial debemos adoptar?"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["mode"] in ["relational_health", "live"]
    reply = data["reply"]
    assert any(term in reply.lower() for term in ["rhi", "salud relacional", "postura", "churn", "ltv", "wallet"])


def test_chat_bank_remittance_3way_query():
    """Valida que la consulta sobre remesas y 3-way match entregue la cuadratura $0.00 MAE."""
    res = client.post(
        "/api/cases/case_001/chat",
        json={"message": "¿Cómo quedó la conciliación bancaria 3-way y el depósito neto verificado?"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["mode"] in ["bank_remittance_3way", "live"]
    reply = data["reply"]
    assert any(term in reply.lower() for term in ["3-way", "bancario", "depósito", "deposito", "remesa", "mae"])


def test_chat_root_cause_capa_query():
    """Valida que la consulta sobre causa raíz entregue el departamento responsable y checklist CAPA."""
    res = client.post(
        "/api/cases/case_001/chat",
        json={"message": "¿Cuál es la causa raíz de este caso, a qué departamento se atribuye y qué ticket CAPA procede?"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["mode"] in ["root_cause_capa", "live"]
    reply = data["reply"]
    assert any(term in reply.lower() for term in ["departamento", "capa", "responsable", "protocolo", "almacén", "transporte", "cedis"])


def test_chat_liability_cap_query():
    """Valida que la consulta sobre topes contractuales evalúe los límites de responsabilidad."""
    res = client.post(
        "/api/cases/case_001/chat",
        json={"message": "¿Existe un tope de responsabilidad contractual o penalidad máxima pactada?"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["mode"] in ["contractual_caps", "live"]
    reply = data["reply"]
    assert any(term in reply.lower() for term in ["tope", "responsabilidad", "límite", "limite", "cláusula", "cap"])


def test_chat_response_structure_has_tools_executed():
    """Valida que la respuesta del chat incluya tools_executed de forma estándar."""
    res = client.post(
        "/api/cases/case_001/chat",
        json={"message": "¿Cuál es la causa raíz oficial?"}
    )
    assert res.status_code == 200
    data = res.json()
    assert "tools_executed" in data
    assert isinstance(data["tools_executed"], list)
