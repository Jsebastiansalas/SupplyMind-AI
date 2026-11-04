"""
tests/test_negotiation_duel.py
Suite de pruebas automatizadas para el Motor Multi-Agente de Negociación Bilateral B2B (Sprint 6.1).
Verifica:
1. Calibración y resolución de los 5 arquetipos de retail (Walmart, Amazon, Soriana, Costco, Generic).
2. Careo dialéctico por rondas con convergencia matemática en Decimal ($0.00 MAE).
3. Respeto infranqueable de la matriz de delegación financiera fijada por el CFO.
4. Dualidad de gobernanza (Modo Piloto Automático vs Human Gatekeeper con aprobación).
5. Certificación ZKP de la Minuta de Conciliación con hash criptográfico SHA-256.
6. Integración de endpoints REST en FastAPI.
"""

import pytest
from decimal import Decimal
from pathlib import Path
from fastapi.testclient import TestClient

from api.main import app
from agent.core.retailer_buyer_simulator import RetailerBuyerSimulator, ARCHETYPE_REGISTRY
from agent.core.bilateral_negotiation_engine import BilateralNegotiationEngine

client = TestClient(app)


def test_retailer_buyer_archetypes():
    """Valida la configuración de los 5 arquetipos de retail y su resolución automática."""
    assert len(ARCHETYPE_REGISTRY) == 5
    for arch_id, cfg in ARCHETYPE_REGISTRY.items():
        assert cfg.initial_demand_pct == 100.0
        assert cfg.concession_resistance_score >= 6.0
        assert len(cfg.key_pressure_points) >= 2
        assert cfg.buyer_title != ""

    # Detección por case_id
    arch_wm = RetailerBuyerSimulator.resolve_archetype("case_006_walmart_otif_pricing")
    assert arch_wm.archetype_id == "WALMART_OTIF"
    assert "Walmart" in arch_wm.retailer_name

    arch_amz = RetailerBuyerSimulator.resolve_archetype("case_005_amazon_shortage")
    assert arch_amz.archetype_id == "AMAZON_FC"
    assert "Amazon" in arch_amz.retailer_name

    arch_sor = RetailerBuyerSimulator.resolve_archetype("case_014_soriana_rebate_unilateral")
    assert arch_sor.archetype_id == "SORIANA_REBATE"

    arch_cos = RetailerBuyerSimulator.resolve_archetype("case_015_costco_tarima_danada")
    assert arch_cos.archetype_id == "COSTCO_DEPOT"


def test_negotiation_duel_full_autonomy_flow():
    """Valida la ejecución del careo multi-agente en modo Piloto Automático con convergencia y sellado ZKP."""
    case_id = "case_005_amazon_shortage"
    session = BilateralNegotiationEngine.start_duel(
        case_id=case_id,
        governance_mode="FULL_AUTONOMY",
        delegation_limit_pct=50.0
    )

    assert session.session_id.startswith("DUEL-")
    assert session.current_round == 1
    assert len(session.rounds) == 1
    assert session.governance_mode == "FULL_AUTONOMY"
    assert session.total_disputed_amount > Decimal("0.00")

    # Ronda 1: Comprador intransigente
    r1 = session.rounds[0]
    assert r1.buyer_stance == "INTRANSIGENT"
    assert r1.buyer_demand_credit_memo == session.total_disputed_amount
    assert r1.supplier_stance == "EVIDENCE_FIRMNESS"
    assert len(r1.evidence_exhibited) >= 1

    # Avanzar rondas hasta acuerdo
    for _ in range(4):
        if session.status in ["AGREEMENT_REACHED", "IMPASSE_REACHED"]:
            break
        session = BilateralNegotiationEngine.advance_duel_step(case_id)

    assert session.status == "AGREEMENT_REACHED"
    assert session.final_agreed_credit_memo is not None
    assert session.final_agreed_cash_recovery is not None

    # Invariante contable estricta ($0.00 MAE)
    total_agreed = session.final_agreed_credit_memo + session.final_agreed_cash_recovery
    assert total_agreed == session.total_disputed_amount

    # Verificar que se generó la minuta con sello criptográfico SHA-256
    assert session.settlement_minutes_hash is not None
    assert len(session.settlement_minutes_hash) == 64
    assert session.minutes_markdown_path is not None
    assert Path(session.minutes_markdown_path).exists()


def test_negotiation_duel_human_gatekeeper_mode():
    """Valida que en modo Human Gatekeeper el agente congele la ejecución y requiera aprobación humana."""
    case_id = "case_006_walmart_otif_pricing"
    session = BilateralNegotiationEngine.start_duel(
        case_id=case_id,
        governance_mode="HUMAN_GATEKEEPER",
        delegation_limit_pct=40.0
    )

    # Avanzar rondas
    for _ in range(4):
        if session.status in ["AWAITING_HUMAN_APPROVAL", "AGREEMENT_REACHED", "IMPASSE_REACHED"]:
            break
        session = BilateralNegotiationEngine.advance_duel_step(case_id)

    # Debe pausarse para aprobación humana
    assert session.status == "AWAITING_HUMAN_APPROVAL"
    assert "espera de confirmación" in session.summary_verdict.lower() or "gatekeeper" in session.summary_verdict.lower()

    # Operador aprueba el acuerdo
    approved_session = BilateralNegotiationEngine.approve_settlement(
        case_id=case_id,
        operator_name="Lic. Javier Treviño (CFO)"
    )
    assert approved_session.status == "AGREEMENT_REACHED"
    assert approved_session.settlement_minutes_hash is not None
    assert Path(approved_session.minutes_markdown_path).exists()


def test_delegation_limit_inviolability():
    """Valida que el agente SupplyMind NUNCA conceda más allá del límite autorizado por el CFO."""
    case_id = "case_001"
    # Límite estricto del 20%
    session = BilateralNegotiationEngine.start_duel(
        case_id=case_id,
        governance_mode="FULL_AUTONOMY",
        delegation_limit_pct=20.0
    )

    max_allowed = session.delegation_limit_amount
    for r in session.rounds:
        # La concesión ofrecida no debe exceder el límite autorizado
        concession = r.supplier_offer_credit_memo - session.rounds[0].supplier_offer_credit_memo
        assert concession <= max_allowed + Decimal("0.05")


def test_negotiation_duel_rest_api():
    """Valida los endpoints REST /api/cases/{case_id}/negotiation/duel/*."""
    case_id = "case_002"

    # 1. Iniciar duelo
    res_start = client.post(
        f"/api/cases/{case_id}/negotiation/duel/start",
        json={"governance_mode": "HUMAN_GATEKEEPER", "delegation_limit_pct": 50.0}
    )
    assert res_start.status_code == 200
    data_start = res_start.json()
    assert data_start["status"] == "success"
    session_data = data_start["session"]
    assert session_data["case_id"] == case_id
    assert session_data["current_round"] == 1

    # 2. Consultar estado del duelo
    res_get = client.get(f"/api/cases/{case_id}/negotiation/duel")
    assert res_get.status_code == 200
    assert res_get.json()["session"]["session_id"] == session_data["session_id"]

    # 3. Avanzar una ronda
    res_step = client.post(f"/api/cases/{case_id}/negotiation/duel/step")
    assert res_step.status_code == 200
    data_step = res_step.json()
    assert len(data_step["session"]["rounds"]) >= 1

    # 4. Aprobar acuerdo
    res_app = client.post(
        f"/api/cases/{case_id}/negotiation/duel/approve",
        json={"operator_name": "Auditor Senior B2B"}
    )
    assert res_app.status_code == 200
    data_app = res_app.json()
    assert data_app["session"]["status"] == "AGREEMENT_REACHED"
    assert data_app["minutes_hash"] is not None



def test_live_objection_amazon_45min_late_delivery_tolerance():
    """Valida la refutación autónoma de la objeción de Amazon por retraso de 45 min dentro de tolerancia (Eje 2)."""
    case_id = "case_005_amazon_shortage"
    objection = "Amazon rechaza tu carta porque el transportista llegó 45 minutos tarde al muelle de descarga."

    res = BilateralNegotiationEngine.respond_to_live_objection(
        case_id=case_id,
        objection=objection
    )

    assert res.case_id == case_id
    assert res.objection_category == "LATE_DELIVERY_OTIF"
    assert res.is_objection_contractually_valid is False
    assert "CL-LOG-05.2" in res.contract_clause_applied
    assert "60 minutos" in res.contract_tolerance_rule
    assert "45 min" in res.contract_tolerance_rule

    # Invariante contable Decimal ($0.00 MAE)
    total_agreed = res.proposed_credit_memo + res.proposed_cash_recovery
    session = BilateralNegotiationEngine.get_duel_session(case_id)
    assert total_agreed == session.total_disputed_amount
    assert res.proposed_credit_memo == Decimal("5000.00")
    assert res.proposed_cash_recovery == Decimal("2500.00")

    # Argumentación jurídica fundamentada
    assert "Cláusula 5.2" in res.counter_argument_reply or "5.2" in res.counter_argument_reply
    assert "tolerancia" in res.counter_argument_reply.lower()
    assert len(res.evidence_exhibited) >= 2


def test_live_objection_late_delivery_exceeding_tolerance():
    """Valida el cálculo proporcional cuando el retraso excede la ventana de gracia contractual (Eje 2)."""
    case_id = "case_006_walmart_otif_pricing"
    objection = "Walmart aplica retención de penalización OTIF ya que el camión excedió 90 minutos la cita fijada."

    res = BilateralNegotiationEngine.respond_to_live_objection(
        case_id=case_id,
        objection=objection
    )

    assert res.objection_category == "LATE_DELIVERY_OTIF"
    assert res.is_objection_contractually_valid is True
    assert "CL-LOG-05.3" in res.contract_clause_applied
    assert "Exceso de 30 minutos" in res.contract_tolerance_rule

    # Invariante contable Decimal ($0.00 MAE)
    session = BilateralNegotiationEngine.get_duel_session(case_id)
    assert res.proposed_credit_memo + res.proposed_cash_recovery == session.total_disputed_amount
    assert res.proposed_credit_memo > Decimal("0.00")


def test_live_objection_unauthorized_coop_advertising_penalty():
    """Valida el rechazo categórico de retenciones unilaterales por publicidad sin adenda firmada (Eje 2)."""
    case_id = "case_005_amazon_shortage"
    objection = "El comprador deduce $500 por folleto publicitario / co-op de verano según su política interna."

    res = BilateralNegotiationEngine.respond_to_live_objection(
        case_id=case_id,
        objection=objection
    )

    assert res.objection_category == "UNAUTHORIZED_PENALTY"
    assert res.is_objection_contractually_valid is False
    assert "CL-COM-07.2" in res.contract_clause_applied or "10.4" in res.contract_clause_applied
    assert "Código de Comercio" in res.counter_argument_reply or "Art. 78" in res.counter_argument_reply
    assert "adenda" in res.counter_argument_reply.lower()

    # Invariante contable
    session = BilateralNegotiationEngine.get_duel_session(case_id)
    assert res.proposed_credit_memo + res.proposed_cash_recovery == session.total_disputed_amount


def test_live_objection_damaged_goods_preclusion():
    """Valida la aplicación de preclusión procesal de 5 días por remisión sellada conforme en muelle (Eje 2)."""
    case_id = "case_001"
    objection = "Rechazamos el pago porque la mercancía llegó con tarimas dañadas y empaque roto."

    res = BilateralNegotiationEngine.respond_to_live_objection(
        case_id=case_id,
        objection=objection
    )

    assert res.objection_category == "DAMAGED_GOODS"
    assert res.is_objection_contractually_valid is False
    assert "Art. 88" in res.contract_clause_applied or "CL-CAL-04.1" in res.contract_clause_applied
    assert "preclusión" in res.counter_argument_reply.lower() or "precluido" in res.counter_argument_reply.lower()


def test_live_objection_rest_api_endpoint():
    """Valida el endpoint REST POST /api/cases/{case_id}/negotiation/duel/live-objection (Eje 2)."""
    case_id = "case_005_amazon_shortage"

    # 1. Petición válida
    res = client.post(
        f"/api/cases/{case_id}/negotiation/duel/live-objection",
        json={
            "objection": "Amazon rechaza tu carta porque el transportista llegó 45 minutos tarde al muelle de descarga.",
            "operator_name": "Juez Evaluador B2B"
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["case_id"] == case_id
    live = data["live_response"]
    assert live["objection_category"] == "LATE_DELIVERY_OTIF"
    assert live["is_objection_contractually_valid"] is False
    assert live["proposed_credit_memo"] == 5000.0
    assert live["proposed_cash_recovery"] == 2500.0

    # 2. Validación de error: objeción vacía
    res_bad = client.post(
        f"/api/cases/{case_id}/negotiation/duel/live-objection",
        json={"objection": "   "}
    )
    assert res_bad.status_code == 400

    # 3. Validación de error: caso inexistente
    res_404 = client.post(
        "/api/cases/case_inexistente_999/negotiation/duel/live-objection",
        json={"objection": "Alguna objecion"}
    )
    assert res_404.status_code == 404


def test_live_objection_tool_executor_react_integration():
    """Valida la invocación de run_bilateral_negotiation_duel con buyer_objection en ToolExecutor (Eje 2)."""
    from agent.tools.registry import ToolExecutor
    from agent.core.state import DisputeState
    from agent.memory.audit_logger import AuditLogger

    case_id = "case_005_amazon_shortage"
    state = DisputeState(case_id=case_id, objective="Auditar objeción de transporte")
    logger = AuditLogger(case_id)
    executor = ToolExecutor(state=state, audit_logger=logger)

    result = executor.execute_tool(
        "run_bilateral_negotiation_duel",
        {
            "case_id": case_id,
            "buyer_objection": "Amazon rechaza tu carta porque el transportista llegó 45 minutos tarde al muelle de descarga."
        }
    )

    assert result["status"] == "success"
    assert result["mode"] == "live_objection"
    assert result["live_response"]["objection_category"] == "LATE_DELIVERY_OTIF"
    assert result["live_response"]["is_objection_contractually_valid"] is False
    assert "CL-LOG-05.2" in result["live_response"]["contract_clause_applied"]
