"""
tests/test_phase9_mcts_financial.py
Suite de Pruebas Automatizadas para el Motor MCTSNegotiator Financiero (Fase 9).
Valida:
1. HU 9.4.1: Descuento de flujos por WACC, Costos Legales Directos, Interés Moratorio (Art. 362 CCom),
   Capital Cost Drag, DSO Savings y NPV con precisión Decimal ($0.00 MAE).
2. HU 9.4.2: Acoplamiento Dinámico con RelationalHealthEngine (RHI Score, Modos de Modulación y Ponderaciones).
3. Caso de Negocio CFO: Trade-off entre Liquidación Express vs Litigio Coactivo a tasas elevadas de costo de capital.
4. Interoperabilidad REST API (/api/meta-cognition/mcts-simulate).
"""

from decimal import Decimal
import pytest
from fastapi.testclient import TestClient

from api.main import app
from agent.planner.mcts_negotiator import (
    MCTSNegotiator,
    MCTSPlanResult,
    NegotiationTrajectory
)


@pytest.fixture
def client():
    return TestClient(app)


# ==============================================================================
# 1. PRUEBAS DE CÁLCULO FINANCIERO Y NPV CON PRECISIÓN DECIMAL ($0.00 MAE)
# ==============================================================================

def test_mcts_calculate_trajectory_npv_exactness():
    """Valida la exactitud aritmética en Decimal de la fórmula NPV para las tres rutas."""
    claimable = Decimal("100000.00")
    wacc_pct = 12.0

    # 1. Litigio Agresivo (100% nominal, 67 días promedio, costas legales e intereses moratorios)
    lit = MCTSNegotiator.calculate_trajectory_npv(
        claimable_amount=claimable,
        recovery_pct=1.00,
        duration_days=67,
        wacc_annual_pct=wacc_pct,
        is_litigation=True
    )
    assert lit["nominal_recovered"] == Decimal("100000.00")
    assert lit["capital_cost_drag"] > Decimal("0.00")
    assert lit["direct_legal_cost"] == Decimal("4500.00")  # 4% ($4,000) + $500 cuota
    assert lit["expected_moratory_interest"] > Decimal("0.00")  # 9% anual Art. 362 CCom
    # Cuadratura exacta: NPV = Descontado - Costas + Intereses
    assert lit["npv_payoff"] == (lit["discounted_cash_flow"] - lit["direct_legal_cost"] + lit["expected_moratory_interest"])
    assert lit["dso_savings_days"] == (90 - 67)

    # 2. Liquidación Express (92% nominal, 7 días promedio, cero costas ni intereses)
    exp = MCTSNegotiator.calculate_trajectory_npv(
        claimable_amount=claimable,
        recovery_pct=0.92,
        duration_days=7,
        wacc_annual_pct=wacc_pct,
        is_litigation=False
    )
    assert exp["nominal_recovered"] == Decimal("92000.00")
    assert exp["direct_legal_cost"] == Decimal("0.00")
    assert exp["expected_moratory_interest"] == Decimal("0.00")
    assert exp["capital_cost_drag"] < lit["capital_cost_drag"]  # Mucho menor costo de arrastre
    assert exp["npv_payoff"] == exp["discounted_cash_flow"]
    assert exp["dso_savings_days"] == (90 - 7)

    # 3. Preservación de Relación (85% nominal, 22 días promedio)
    rel = MCTSNegotiator.calculate_trajectory_npv(
        claimable_amount=claimable,
        recovery_pct=0.85,
        duration_days=22,
        wacc_annual_pct=wacc_pct,
        is_litigation=False
    )
    assert rel["nominal_recovered"] == Decimal("85000.00")
    assert rel["direct_legal_cost"] == Decimal("0.00")
    assert rel["expected_moratory_interest"] == Decimal("0.00")
    assert rel["dso_savings_days"] == (90 - 22)


def test_mcts_wacc_impact_on_capital_cost_drag():
    """Demuestra que a mayor WACC, el arrastre de capital penaliza severamente el litigio prolongado."""
    claimable = Decimal("50000.00")
    days = 75

    # WACC bajo (6%) vs WACC alto (24%)
    fin_low_wacc = MCTSNegotiator.calculate_trajectory_npv(claimable, 1.0, days, wacc_annual_pct=6.0, is_litigation=True)
    fin_high_wacc = MCTSNegotiator.calculate_trajectory_npv(claimable, 1.0, days, wacc_annual_pct=24.0, is_litigation=True)

    assert fin_high_wacc["capital_cost_drag"] > fin_low_wacc["capital_cost_drag"] * Decimal("3.5")
    assert fin_high_wacc["npv_payoff"] < fin_low_wacc["npv_payoff"]


def test_mcts_direct_legal_cost_override():
    """Permite sobrescribir el presupuesto de costas arbitrales de litigio."""
    claimable = Decimal("80000.00")
    custom_cost = Decimal("8500.00")

    fin = MCTSNegotiator.calculate_trajectory_npv(
        claimable_amount=claimable,
        recovery_pct=1.00,
        duration_days=60,
        wacc_annual_pct=10.0,
        is_litigation=True,
        direct_legal_cost_override=custom_cost
    )
    assert fin["direct_legal_cost"] == custom_cost


# ==============================================================================
# 2. PRUEBAS DE ACOPLAMIENTO DINÁMICO CON RELATIONAL HEALTH ENGINE (HU 9.4.2)
# ==============================================================================

def test_mcts_auto_queries_rhi_for_tier1_retailer():
    """Valida que MCTS consulte automáticamente el RHI del caso Tier-1 (Walmart) activando DIPLOMATIC_PRESERVATION."""
    case_id = "case_006_walmart_otif_pricing"
    result = MCTSNegotiator.simulate_negotiation(
        case_id=case_id,
        claimable_amount=Decimal("35000.00"),
        num_simulations=300
    )

    assert isinstance(result, MCTSPlanResult)
    assert result.rhi_score_applied is not None
    assert result.rhi_score_applied >= 80.0
    assert result.rhi_modulation_mode == "DIPLOMATIC_PRESERVATION"
    assert result.recommended_trajectory == "PRESERVACION_RELACION"
    assert result.relationship_retention_index >= 0.90


def test_mcts_auto_queries_rhi_for_low_margin_distributor():
    """Valida que MCTS consulte automáticamente el RHI de distribuidor de bajo margen (<50 pts) activando ASSERTIVE_LITIGIOUS."""
    case_id = "case_002"
    result = MCTSNegotiator.simulate_negotiation(
        case_id=case_id,
        claimable_amount=Decimal("40000.00"),
        num_simulations=300
    )

    assert isinstance(result, MCTSPlanResult)
    assert result.rhi_score_applied is not None
    assert result.rhi_score_applied < 50.0
    assert result.rhi_modulation_mode == "ASSERTIVE_LITIGIOUS"
    # Al ser cuenta prescindible y RHI bajo, no prioriza concesiones blandas
    assert result.recommended_trajectory in ("LITIGIO_AGRESIVO", "LIQUIDACION_EXPRESS")


def test_mcts_explicit_rhi_score_override():
    """Permite sobrescribir el RHI score en tiempo de ejecución para pruebas o simulaciones ad-hoc."""
    # RHI forzado a 95 puntos -> fuerza preservación
    res_high = MCTSNegotiator.simulate_negotiation(
        case_id="case_sme_test",
        claimable_amount=Decimal("25000.00"),
        rhi_score=95.0,
        num_simulations=200
    )
    assert res_high.rhi_score_applied == 95.0
    assert res_high.rhi_modulation_mode == "DIPLOMATIC_PRESERVATION"
    assert res_high.recommended_trajectory == "PRESERVACION_RELACION"

    # RHI forzado a 20 puntos -> fuerza litigio o liquidación express
    res_low = MCTSNegotiator.simulate_negotiation(
        case_id="case_sme_test",
        claimable_amount=Decimal("25000.00"),
        rhi_score=20.0,
        num_simulations=200
    )
    assert res_low.rhi_score_applied == 20.0
    assert res_low.rhi_modulation_mode == "ASSERTIVE_LITIGIOUS"


# ==============================================================================
# 3. CASO DE NEGOCIO CFO: TRADE-OFF DE VALOR PRESENTE NETO
# ==============================================================================

def test_mcts_cfo_tradeoff_elevated_cost_of_capital():
    """
    Escenario CFO Corporativo:
    Con un WACC alto (20%) y prioridad de liquidez inmediata,
    Liquidación Express (92% a 7 días) supera en NPV al Litigio (100% nominal a 67 días con costas).
    """
    claimable = Decimal("100000.00")
    result = MCTSNegotiator.simulate_negotiation(
        case_id="case_cfo_liquidity_crunch",
        claimable_amount=claimable,
        retailer_account_weight_pct=10.0,
        supplier_cashflow_priority="CASH_URGENT",
        wacc_annual_pct=20.0,
        num_simulations=400
    )

    assert result.recommended_trajectory == "LIQUIDACION_EXPRESS"
    assert result.dso_savings_days >= 80  # Ahorro masivo de días en calle
    assert result.npv_payoff > Decimal("90000.00")

    # Verificar que el synthesis mencione NPV y DSO
    assert "NPV" in result.executive_synthesis
    assert "DSO" in result.executive_synthesis
    assert "WACC 20.0%" in result.executive_synthesis


# ==============================================================================
# 4. PRUEBAS DE ENDPOINT REST (/api/meta-cognition/mcts-simulate)
# ==============================================================================

def test_api_meta_cognition_mcts_simulate_financial(client):
    """Valida que el endpoint REST retorne los nuevos campos financieros y relacionales."""
    response = client.post(
        "/api/meta-cognition/mcts-simulate",
        json={
            "case_id": "case_006_walmart_otif_pricing",
            "claimable_amount": 50000.00,
            "wacc_annual_pct": 14.5,
            "rhi_score": 85.0,
            "num_simulations": 150
        }
    )
    assert response.status_code == 200
    data = response.json()

    assert data["case_id"] == "case_006_walmart_otif_pricing"
    assert "npv_payoff" in data
    assert "capital_cost_drag" in data
    assert data["wacc_annual_pct"] == 14.5
    assert data["dso_savings_days"] > 0
    assert data["rhi_score_applied"] == 85.0
    assert data["rhi_modulation_mode"] == "DIPLOMATIC_PRESERVATION"
    assert len(data["trajectories_evaluated"]) == 3

    # Validar que cada trayectoria tenga las métricas financieras
    for t in data["trajectories_evaluated"]:
        assert "npv_payoff" in t
        assert "capital_cost_drag" in t
        assert "dso_savings_days" in t
        assert Decimal(str(t["npv_payoff"])) > Decimal("0.00")
