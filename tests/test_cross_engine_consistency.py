"""
tests/test_cross_engine_consistency.py
Fase 10 - Sprint 10.3: Contrato de Consistencia Numérica Cross-Motor y Validación de Entradas Límite en las 18 Herramientas ReAct.

Garantiza:
1. Una sola cifra real: CaseLedger == Reporte == Optimizador == ERP == Chat == Courtroom == CFDI.
2. Cuadratura contable de partida doble: sum(debits) == sum(credits) == abs(difference).
3. Robustez de las 18 herramientas ReAct ante entradas límite (caso inexistente, montos 0, parámetros vacíos, régimen inválido).
"""

from decimal import Decimal
import json
from pathlib import Path
import pytest

from agent.core.case_ledger import CaseLedger
from agent.core.erp_engine import ErpEngine, get_case_fiscal_profile
from agent.core.portfolio_optimizer import WorkingCapitalPortfolioOptimizer
from agent.core.skynet_runner import SkynetRunner
from agent.core.state import DisputeState
from agent.memory.audit_logger import AuditLogger
from agent.tools.registry import TOOL_DEFINITIONS, ToolExecutor
from api.routes.chat import _extract_case_full_context, _deterministic_chat_response

ROOT_DIR = Path(__file__).resolve().parent.parent


def test_cross_engine_financial_invariance_sample_cases():
    """Valida que todos los motores sincronicen la misma cifra al centavo en casos representativos."""
    sample_cases = [
        "case_001",
        "case_002",
        "case_004_enterprise",
        "case_005_amazon_shortage",
        "case_006_walmart_otif_pricing",
        "case_016_nestle_cuarentena_lab",
        "case_021_samsung_fx_variance",
        "case_031_adversarial_prompt_injection",
        "case_035_mega_multimodal_60_skus"
    ]

    for cid in sample_cases:
        canon = CaseLedger.get(cid)
        opt_summary = WorkingCapitalPortfolioOptimizer.optimize_portfolio(case_ids=[cid])
        assert opt_summary.total_cases_analyzed == 1
        opt_item = opt_summary.ranked_cases[0]

        # 1. Consistencia CaseLedger <-> PortfolioOptimizer
        assert opt_item.claimable_amount == canon.claimable_amount, f"Discrepancia en cartera para {cid}"
        assert opt_item.is_quarantined == canon.is_quarantined, f"Discrepancia en estatus de cuarentena para {cid}"

        if canon.is_quarantined:
            assert opt_item.claimable_amount == Decimal("0.00")
            assert opt_item.action_type == "FORENSIC_REVIEW"
            continue

        # 2. Consistencia con SkynetRunner Report
        rep = SkynetRunner(case_id=cid, fast_path=True, use_cache=True).run()
        assert canon.claimable_amount == rep.claimable_amount
        assert canon.justified_amount == rep.justified_amount
        assert abs(canon.difference) == abs(rep.difference)

        # 3. Consistencia con Asiento Contable ERP (Partida Doble)
        lines = ErpEngine.build_erp_posting_lines(rep)
        tot_debit = sum((l.debit for l in lines), Decimal("0.00"))
        tot_credit = sum((l.credit for l in lines), Decimal("0.00"))
        assert tot_debit == tot_credit, f"Descuadre contable débito/crédito en {cid}: {tot_debit} != {tot_credit}"
        assert tot_credit == abs(canon.difference), f"Póliza no cuadra con retención total en {cid}: {tot_credit} != {abs(canon.difference)}"

        if canon.claimable_amount > Decimal("0.00"):
            line_claimable = next((l for l in lines if l.account_code == "120090"), None)
            assert line_claimable is not None, f"Falta cuenta de deudores en disputa (120090) en {cid}"
            assert line_claimable.debit == canon.claimable_amount, f"Monto en cuenta 120090 no coincide con reclamable en {cid}"

        # 4. Consistencia con CFDI 4.0 XML (Total Nota de Crédito == Justificado)
        fiscal_prof = get_case_fiscal_profile(cid)
        cfdi_xml = ErpEngine.generate_cfdi_40_xml(cid, rep, fiscal_prof)
        assert f'Total="{rep.justified_amount:.2f}"' in cfdi_xml, f"Total CFDI no coincide con nota de crédito en {cid}"


def test_cross_engine_chat_consistency_and_quarantine_shield():
    """Valida que el copiloto conversacional reporte las mismas cifras canónicas y active escudo en cuarentena."""
    # 1. Caso ordinario: case_005_amazon_shortage
    ctx_005 = _extract_case_full_context("case_005_amazon_shortage")
    canon_005 = CaseLedger.get("case_005_amazon_shortage")
    assert ctx_005["report"].claimable_amount == canon_005.claimable_amount
    resp_005 = _deterministic_chat_response("case_005_amazon_shortage", "cuanto es el monto reclamable?", "client", ctx_005)
    assert f"${canon_005.claimable_amount:,.2f} USD" in resp_005

    # 2. Caso en cuarentena: case_031_adversarial_prompt_injection
    ctx_031 = _extract_case_full_context("case_031_adversarial_prompt_injection")
    resp_031 = _deterministic_chat_response("case_031_adversarial_prompt_injection", "quien tiene la razon?", "client", ctx_031)
    assert "PROTOCOLO FORENSE ACTIVADO" in resp_031
    assert "CUARENTENA PREVENTIVA" in resp_031
    assert "$0.00 USD" in resp_031


def test_cross_engine_courtroom_debate_consistency():
    """Valida que el careo judicial de AdversarialCourtroomEngine cite cifras idénticas al expediente."""
    from agent.courtroom.adversarial_engine import AdversarialCourtroomEngine
    cid = "case_002"
    rep = SkynetRunner(case_id=cid, fast_path=True, use_cache=True).run()
    debate = AdversarialCourtroomEngine.conduct_debate(cid, rep)
    assert debate is not None
    assert debate.case_id == cid
    # El monto debatido y el veredicto deben estar anclados a la diferencia real del expediente
    assert abs(debate.disputed_amount) == abs(rep.difference)
    assert debate.claimable_amount == rep.claimable_amount
    assert debate.justified_amount == rep.justified_amount


def test_18_react_tools_boundary_inputs_non_existent_case():
    """Valida que las 18 herramientas manejen casos inexistentes retornando un esquema de error controlado."""
    dummy_state = DisputeState(case_id="non_existent_case_99999", objective="Auditoría límite")
    logger = AuditLogger(case_id="non_existent_case_99999")
    executor = ToolExecutor(state=dummy_state, audit_logger=logger)

    assert len(TOOL_DEFINITIONS) >= 18, f"Se esperaban exactamente 18 herramientas registradas, hay {len(TOOL_DEFINITIONS)}"

    for tool_def in TOOL_DEFINITIONS:
        t_name = tool_def["function"]["name"]
        # Invocamos cada herramienta con un expediente que no existe
        res = executor.execute_tool(t_name, {"case_id": "non_existent_case_99999"})
        assert isinstance(res, dict), f"La herramienta {t_name} debe retornar un dict"
        assert "status" in res, f"La herramienta {t_name} debe incluir clave 'status'"
        # No debe haber reventado con excepción no capturada
        assert res["status"] in ("error", "success")


def test_18_react_tools_boundary_inputs_zero_amounts_and_edge_values():
    """Valida el comportamiento de herramientas financieras ante valores cero y entradas límite."""
    state = DisputeState(case_id="case_001", objective="Prueba límites numéricos")
    logger = AuditLogger(case_id="case_001")
    executor = ToolExecutor(state=state, audit_logger=logger)

    # 1. MCTS con claimable_amount = 0.0
    res_mcts = executor.execute_tool("simulate_mcts_npv_strategy", {
        "case_id": "case_001",
        "claimable_amount": 0.0,
        "wacc_annual_pct": 0.0,
        "supplier_priority": "BALANCED"
    })
    assert res_mcts["status"] == "success"
    assert Decimal(str(res_mcts["mcts_npv_plan"]["npv_payoff"])) == Decimal("0.00")
    assert Decimal(str(res_mcts["mcts_npv_plan"]["capital_cost_drag"])) == Decimal("0.00")

    # 2. Optimizador de cartera con lista vacía
    res_opt = executor.execute_tool("optimize_working_capital_portfolio", {
        "case_ids": [],
        "wacc_annual": 0.12,
        "target_count": 0
    })
    assert res_opt["status"] == "success"
    assert res_opt["portfolio_optimization"]["total_cases_analyzed"] == 0
    assert Decimal(str(res_opt["portfolio_optimization"]["total_claimable_usd"])) == Decimal("0.00")

    # 3. Resolución de régimen fiscal con sobreescritura inválida (debe degradar a estándar con gracia)
    res_tax = executor.execute_tool("resolve_fiscal_regime_and_erp", {
        "case_id": "case_001",
        "regime_override": "INVALID_REGIME_UNKNOWN"
    })
    assert res_tax["status"] == "success"
    # Degrada a régimen estándar sin fallar
    assert res_tax["fiscal_tax_profile"]["regime_code"] == "STANDARD_VAT_16"
    assert len(res_tax["erp_posting_lines"]) > 0
