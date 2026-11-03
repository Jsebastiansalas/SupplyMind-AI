"""
tests/test_phase9_omniscience.py
Suite de verificación de integración y regresión formal para la Fase 9:
- HU 9.6.1: Optimizador C-Level de Portafolio y Capital de Trabajo (WorkingCapitalPortfolioOptimizer).
- HU 9.6.2: Expansión de 15 a 18 Herramientas ReAct Nativas en TOOL_DEFINITIONS y Endpoints API.
- HU 9.6.3: Integración completa de WACC/NPV, Régimen Fiscal SAT y MAE $0.00.
"""

from decimal import Decimal
import pytest
from fastapi.testclient import TestClient

from agent.core.portfolio_optimizer import (
    WorkingCapitalPortfolioOptimizer,
    PortfolioOptimizationSummary,
    PortfolioItemPriority,
)
from agent.tools.registry import TOOL_DEFINITIONS, ToolExecutor
from agent.core.state import DisputeState
from agent.memory.audit_logger import AuditLogger
from api.main import app

client = TestClient(app)


def test_working_capital_portfolio_optimizer_metrics():
    """Valida la agregación macroeconómica, cálculo de NPV descontado y VaR de prescripción."""
    summary = WorkingCapitalPortfolioOptimizer.optimize_portfolio(target_count=10, wacc_annual=0.12)

    assert isinstance(summary, PortfolioOptimizationSummary)
    assert summary.total_cases_analyzed >= 5
    assert summary.wacc_annual_applied_pct == 12.0
    assert summary.total_claimable_usd >= Decimal("0.00")
    assert summary.total_npv_usd >= Decimal("0.00")
    # El valor presente neto descontado por WACC y costos legales debe ser <= valor nominal bruto
    assert summary.total_claimable_usd >= summary.total_npv_usd
    assert summary.value_at_risk_prescription_usd >= Decimal("0.00")

    # Validar agenda ejecutiva de War-Room
    assert len(summary.recommended_war_room_agenda) >= 3
    assert "WAR-ROOM AGENDA" in summary.recommended_war_room_agenda[0]

    # Validar que los casos estén ordenados por prelación (Priority Score descendente)
    ranked = summary.ranked_cases
    assert len(ranked) >= 5
    for i in range(len(ranked) - 1):
        assert ranked[i].priority_execution_score >= ranked[i + 1].priority_execution_score

    for item in ranked:
        assert isinstance(item, PortfolioItemPriority)
        assert 0.0 <= item.priority_execution_score <= 100.0
        assert item.action_type in ("INTERRUPT_PRESCRIPTION", "EXPRESS_SETTLEMENT", "ARBITRATION", "POST_ERP")
        assert len(item.recommended_action) > 10


def test_batch_action_execution_prescription_interruption():
    """Valida la ejecución en lote de avisos de interrupción Art. 1041 CCom."""
    case_ids = ["case_005_amazon_shortage", "case_006_walmart_otif_pricing"]
    batch_res = WorkingCapitalPortfolioOptimizer.execute_batch_action(
        case_ids=case_ids,
        action_type="INTERRUPT_PRESCRIPTION",
        operator_name="Lic. Roberto Villarreal (Director Jurídico)"
    )

    assert batch_res["status"] == "success"
    assert batch_res["action_type"] == "INTERRUPT_PRESCRIPTION"
    assert batch_res["total_cases_requested"] == 2
    assert batch_res["total_success"] >= 1
    assert any("INT-1041" in r.get("notice_id", "") for r in batch_res["results"] if r["status"] == "SUCCESS")


def test_18_react_tool_definitions_and_names():
    """Valida la expansión del arsenal ReAct a exactamente 18 super-herramientas nativas."""
    assert len(TOOL_DEFINITIONS) == 18

    tool_names = [t["function"]["name"] for t in TOOL_DEFINITIONS]

    # Verificar que existan las 3 nuevas herramientas de Fase 9
    assert "optimize_working_capital_portfolio" in tool_names
    assert "simulate_mcts_npv_strategy" in tool_names
    assert "resolve_fiscal_regime_and_erp" in tool_names

    # Verificar herramientas previas clave
    assert "read_dispute_documents" in tool_names
    assert "execute_reconciliation" in tool_names
    assert "evaluate_contract_terms" in tool_names
    assert "evaluate_dispute_sla_and_interrupt_prescription" in tool_names
    assert "run_bilateral_negotiation_duel" in tool_names
    assert "dispatch_dossier_to_retailer_portal" in tool_names


def test_tool_executor_new_phase9_tools():
    """Valida que ToolExecutor despache correctamente las 3 nuevas herramientas de Fase 9."""
    state = DisputeState(case_id="case_001", objective="Auditoría integral")
    audit_logger = AuditLogger(case_id="case_001")
    executor = ToolExecutor(state, audit_logger)

    # 1. Herramienta 16: optimize_working_capital_portfolio
    res16 = executor.execute_tool("optimize_working_capital_portfolio", {"target_count": 3, "wacc_annual": 0.14})
    assert res16["status"] == "success"
    assert "portfolio_optimization" in res16
    assert res16["portfolio_optimization"]["total_cases_analyzed"] == 3

    # 2. Herramienta 17: simulate_mcts_npv_strategy
    res17 = executor.execute_tool("simulate_mcts_npv_strategy", {
        "case_id": "case_001",
        "claimable_amount": 25000.0,
        "wacc_annual_pct": 12.0,
        "supplier_priority": "BALANCED"
    })
    assert res17["status"] == "success"
    assert "mcts_npv_plan" in res17
    plan = res17["mcts_npv_plan"]
    assert float(plan["npv_payoff"]) > 0.0
    assert float(plan["capital_cost_drag"]) > 0.0
    assert plan["wacc_annual_pct"] == 12.0

    # 3. Herramienta 18: resolve_fiscal_regime_and_erp
    res18 = executor.execute_tool("resolve_fiscal_regime_and_erp", {"case_id": "case_001"})
    assert res18["status"] == "success"
    assert "fiscal_tax_profile" in res18
    assert res18["fiscal_tax_profile"]["regime_code"] == "STANDARD_VAT_16"
    assert len(res18["erp_posting_lines"]) >= 2

    # Validar partida doble contable: Débitos == Créditos
    lines = res18["erp_posting_lines"]
    tot_debit = sum(Decimal(str(l["debit"])) for l in lines)
    tot_credit = sum(Decimal(str(l["credit"])) for l in lines)
    assert tot_debit == tot_credit


def test_portfolio_optimization_api_endpoints():
    """Valida los endpoints REST expuestos en /api/batch para War-Room de Capital de Trabajo."""
    # 1. POST /api/batch/optimize-portfolio
    res_post = client.post("/api/batch/optimize-portfolio", json={
        "target_count": 5,
        "wacc_annual": 0.12
    })
    assert res_post.status_code == 200
    data = res_post.json()
    assert data["total_cases_analyzed"] == 5
    assert len(data["ranked_cases"]) == 5
    assert data["wacc_annual_applied_pct"] == 12.0

    # 2. GET /api/batch/portfolio-summary
    res_get = client.get("/api/batch/portfolio-summary?target_count=4&wacc=0.10")
    assert res_get.status_code == 200
    data_get = res_get.json()
    assert data_get["total_cases_analyzed"] == 4
    assert data_get["wacc_annual_applied_pct"] == 10.0

    # 3. POST /api/batch/execute-action
    res_action = client.post("/api/batch/execute-action", json={
        "case_ids": ["case_005_amazon_shortage"],
        "action_type": "INTERRUPT_PRESCRIPTION",
        "operator_name": "Lic. Roberto Villarreal (Director Jurídico)"
    })
    assert res_action.status_code == 200
    data_act = res_action.json()
    assert data_act["status"] == "success"
    assert data_act["total_success"] == 1
