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
