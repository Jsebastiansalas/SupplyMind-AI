"""
tests/test_phase10_case_ledger.py
Fuente Única de Verdad: CaseLedger, cuarentena en el optimizador y guardas batch.
"""

import json
import re
from decimal import Decimal
from pathlib import Path

import pytest

from agent.core.case_ledger import CaseLedger, is_report_quarantined
from agent.core.portfolio_optimizer import WorkingCapitalPortfolioOptimizer

ROOT = Path(__file__).resolve().parent.parent
QUARANTINE_CASES = [
    "case_031_adversarial_prompt_injection",
    "case_032_quarantine_cross_contamination",
    "case_033_quarantine_anachronistic_dates",
    "case_049_adversarial_deep_prompt_injection",
]
PRODUCTION_DIRS = ["agent/core", "agent/portal", "agent/vision", "agent/predictive",
                   "agent/courtroom", "agent/fiscal", "agent/guardrails", "agent/planner",
                   "agent/tools", "api", "tools/reconciliation_engine", "tools/contract_analyzer"]


def test_production_code_never_reads_ground_truth():
    """La hoja de respuestas del benchmark no puede ser leída por código de producción."""
    offenders = []
    pattern = re.compile(r"""["']ground_truth\.json["']""")
    for d in PRODUCTION_DIRS:
        for py in (ROOT / d).rglob("*.py"):
            for n, line in enumerate(py.read_text(encoding="utf-8").splitlines(), 1):
                if pattern.search(line) and not line.lstrip().startswith("#"):
                    offenders.append(f"{py.relative_to(ROOT)}:{n}")
    assert offenders == [], f"Lecturas de ground_truth.json en producción: {offenders}"


def test_quarantine_detection_criteria():
    assert is_report_quarantined({"recommended_action": "PROTOCOLO FORENSE ACTIVADO ..."})
    assert is_report_quarantined({"quarantine_docket": {"x": 1}})
    assert is_report_quarantined({"health_audit": {"status": "QUARANTINE"}})
    assert not is_report_quarantined({"recommended_action": "Emitir nota de crédito"})


def test_ledger_zeroes_quarantined_amounts():
    canon = CaseLedger.from_report({
        "case_id": "X", "claimable_amount": "10000.00", "justified_amount": "5.00",
        "quarantine_docket": {"reason": "prompt injection"},
    })
    assert canon.is_quarantined
    assert canon.claimable_amount == Decimal("0.00")
    assert canon.justified_amount == Decimal("0.00")
    assert not canon.is_actionable


@pytest.mark.parametrize("cid", QUARANTINE_CASES)
def test_ledger_marks_real_quarantine_cases(cid):
    canon = CaseLedger.get(cid)
    assert canon.is_quarantined, f"{cid} debería estar en cuarentena"
    assert canon.claimable_amount == Decimal("0.00")


def test_ledger_matches_canonical_report_for_all_cases():
    """Las cifras del ledger coinciden al centavo con el reporte canónico persistido."""
    for rep in sorted((ROOT / "reports").glob("dispute_report_case_*.json")):
        data = json.loads(rep.read_text(encoding="utf-8"))
        if data.get("concessions"):
            continue  # estado negociado, no línea base
        cid = data["case_id"]
        canon = CaseLedger.get(cid)
        if canon.is_quarantined:
            assert canon.claimable_amount == Decimal("0.00")
            continue
        assert canon.claimable_amount == Decimal(str(data["claimable_amount"])).quantize(Decimal("0.01")), cid
        assert canon.justified_amount == Decimal(str(data["justified_amount"])).quantize(Decimal("0.01")), cid


def test_optimizer_excludes_quarantine_and_matches_ledger():
    summary = WorkingCapitalPortfolioOptimizer.optimize_portfolio()
    ledger_total = sum((CaseLedger.get(i.case_id).claimable_amount for i in summary.ranked_cases), Decimal("0.00"))
    assert summary.total_claimable_usd == ledger_total

    q_items = [i for i in summary.ranked_cases if i.is_quarantined]
    assert {i.case_id for i in q_items} >= set(QUARANTINE_CASES) & {i.case_id for i in summary.ranked_cases}
    for i in q_items:
        assert i.claimable_amount == Decimal("0.00")
        assert i.npv_payoff == Decimal("0.00")
        assert i.action_type == "FORENSIC_REVIEW"
        assert i.priority_execution_score == 0.0
    assert summary.quarantined_cases_count == len(q_items)


def test_optimizer_total_matches_crucible_benchmark():
    """El War-Room y el benchmark Crucible reportan el mismo capital reclamable."""
    bench_file = ROOT / "reports" / "crucible_benchmark_50_cases_report.json"
    if not bench_file.exists():
        pytest.skip("Benchmark Crucible no ejecutado")
    bench = json.loads(bench_file.read_text(encoding="utf-8"))
    bench_by_case = {c["case_id"]: Decimal(str(c["claimable_pred"])).quantize(Decimal("0.01"))
                     for c in bench["cases_results"]}
    summary = WorkingCapitalPortfolioOptimizer.optimize_portfolio(case_ids=list(bench_by_case))
    for item in summary.ranked_cases:
        assert item.claimable_amount == bench_by_case[item.case_id], item.case_id
    assert summary.total_claimable_usd == sum(bench_by_case.values(), Decimal("0.00"))


@pytest.mark.parametrize("action", ["INTERRUPT_PRESCRIPTION", "POST_ERP"])
def test_batch_blocks_quarantined_cases(action):
    res = WorkingCapitalPortfolioOptimizer.execute_batch_action(QUARANTINE_CASES[:2], action)
    assert res["total_blocked"] == 2
    assert res["total_success"] == 0
    assert all(r["status"] == "BLOCKED" for r in res["results"])


def test_batch_post_erp_succeeds_on_actionable_case():
    """Regresión: POST_ERP fallaba siempre por NameError de ConcessionEngine."""
    res = WorkingCapitalPortfolioOptimizer.execute_batch_action(["case_002"], "POST_ERP")
    assert res["total_success"] == 1, res["results"]
