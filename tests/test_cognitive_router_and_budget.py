"""
Suite de Pruebas de Enrutamiento Cognitivo Neuro-Simbólico, Presupuesto Real de Pasarela y Auditoría de Invariantes.
====================================================================================================================
Verifica:
1. CognitiveRouter: Decisión autónoma entre Ejecución Simbólica (Python) y Razonamiento Híbrido (Grok-4.7 + Python Tools),
   además de la delegación estricta de sub-tareas aritméticas a Python.
2. TaskBudgetGuard: Telemetría calibrada al consumo real medido en la pasarela Platica ($10.66 USD / 940 peticiones)
   y corte duro (Circuit Cutoff) cuando una tarea excede su presupuesto máximo o límite de llamadas LLM.
3. CryptographicInvariantAuditor: Verificación honesta de invariantes contables de partida doble y sello SHA-256.
"""
from decimal import Decimal
from pathlib import Path

from agent.planner.cognitive_router import (
    CognitiveRouter,
    ExecutionEngineMode,
)
from agent.guardrails.budget_guard import (
    TaskBudgetGuard,
    GATEWAY_HISTORICAL_SPEND_USD,
    GATEWAY_HISTORICAL_REQUESTS,
    GATEWAY_MEASURED_AVG_COST_PER_REQUEST_USD,
)
from agent.guardrails.arithmetic_verifier import (
    CryptographicInvariantAuditor,
    ZKPFinancialAuditor,
    generate_cryptographic_proof_token,
)
from data.models import DisputeAnalysisReport


def test_cognitive_router_distinguishes_symbolic_vs_neuro_symbolic(tmp_path: Path):
    """
    Verifica que el CognitiveRouter enrute automáticamente:
    - Casos tabulares estructurados (.json / .csv) -> SYMBOLIC_PYTHON (0 llamadas LLM).
    - Casos con evidencia no estructurada compleja (.png, textos extensos o disputas interactivas) -> HYBRID_NEURO_SYMBOLIC.
    """
    # 1. Caso tabular estructurado puro -> SYMBOLIC_PYTHON
    tabular_case = tmp_path / "case_tabular_structured"
    tabular_case.mkdir()
    (tabular_case / "invoice.json").write_text('{"id": "INV-01"}', encoding="utf-8")
    (tabular_case / "po.json").write_text('{"id": "PO-01"}', encoding="utf-8")
    (tabular_case / "payment.json").write_text('{"id": "PAY-01"}', encoding="utf-8")

    decision_tabular = CognitiveRouter.evaluate_routing(tabular_case, interactive_query=None)
    assert decision_tabular.mode == ExecutionEngineMode.SYMBOLIC_PYTHON
    assert decision_tabular.use_llm is False
    assert decision_tabular.estimated_cost_usd == Decimal("0.000000")
    assert len(decision_tabular.python_symbolic_tasks) >= 3
    assert len(decision_tabular.grok_neural_tasks) == 0

    # 2. Caso con evidencia manuscrita (.png) y cláusula no estructurada extensa -> HYBRID_NEURO_SYMBOLIC
    complex_case = tmp_path / "case_unstructured_dispute"
    complex_case.mkdir()
    (complex_case / "invoice.pdf").write_bytes(b"%PDF-1.4 dummy")
    (complex_case / "scanned_dock_note.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    (complex_case / "carrier_dispute_email.txt").write_text("A" * 600, encoding="utf-8")

    decision_complex = CognitiveRouter.evaluate_routing(complex_case, interactive_query=None)
    assert decision_complex.mode == ExecutionEngineMode.HYBRID_NEURO_SYMBOLIC
    assert decision_complex.use_llm is True
    assert decision_complex.arithmetic_lock_active is True
    assert decision_complex.estimated_cost_usd > Decimal("0.00")
    assert len(decision_complex.grok_neural_tasks) >= 2
    assert len(decision_complex.python_symbolic_tasks) >= 3

    # 3. Consulta interactiva con requerimiento de argumentación legal -> HYBRID_NEURO_SYMBOLIC
    decision_interactive = CognitiveRouter.evaluate_routing(
        tabular_case,
        interactive_query="Redacta un alegato de arbitraje citando la cláusula de fuerza mayor y merma contractual."
    )
    assert decision_interactive.mode == ExecutionEngineMode.HYBRID_NEURO_SYMBOLIC
    assert decision_interactive.use_llm is True


def test_cognitive_router_subtask_delegation_and_directive():
    """
    Verifica que las sub-tareas matemáticas, contables o de conciliación se deleguen
    obligatoriamente a Python Symbolic Tools, mientras que las semánticas permitan Grok-4.7.
    """
    assert CognitiveRouter.should_delegate_subtask_to_python("calculate_decimal_reconciliation") is True
    assert CognitiveRouter.should_delegate_subtask_to_python("verify_double_entry_ledger") is True
    assert CognitiveRouter.should_delegate_subtask_to_python("lookup_deduction_code_in_catalog") is True
    assert CognitiveRouter.should_delegate_subtask_to_python("interpret_ambiguous_email_clause") is False

    directive = CognitiveRouter.get_neuro_symbolic_system_directive()
    assert "DIRECTIVA DE ARQUITECTURA NEURO-SIMBÓLICA" in directive
    assert "ESTRICTAMENTE PROHIBIDO realizar sumas" in directive
    assert "Decimal" in directive


def test_task_budget_guard_real_gateway_calibration_and_hard_cutoff():
    """
    Verifica que TaskBudgetGuard:
    1. Esté calibrado con la tarifa real medida de la pasarela ($10.66 USD / 940 peticiones = $0.011340 USD/req).
    2. Acumule costos reales por tarea y bloquee llamadas adicionales cuando se alcance el tope presupuestario ($0.03 USD)
       o el límite de llamadas por expediente.
    """
    TaskBudgetGuard.reset_all()

    assert GATEWAY_HISTORICAL_SPEND_USD == Decimal("10.66")
    assert GATEWAY_HISTORICAL_REQUESTS == 940
    assert GATEWAY_MEASURED_AVG_COST_PER_REQUEST_USD == Decimal("0.011340")

    # Configurar un tope estricto de $0.025 USD y máximo 2 peticiones para el caso de prueba
    case_id = "test_case_budget_cutoff"
    TaskBudgetGuard.configure_case(
        case_id=case_id,
        budget_cap_usd=Decimal("0.025000"),
        max_requests=2
    )

    assert TaskBudgetGuard.can_invoke_llm(case_id) is True

    # Primera petición a Grok-4.7 (ej. 1200 prompt tokens, 400 completion tokens -> $0.006 + $0.006 = $0.012 USD)
    summary_1 = TaskBudgetGuard.record_llm_call(
        case_id=case_id,
        prompt_tokens=1200,
        completion_tokens=400,
        model="grok-4.7",
        purpose="react_step_1"
    )
    assert summary_1.requests_count == 1
    assert summary_1.measured_cost_usd == Decimal("0.012000")
    assert summary_1.was_throttled is False
    assert TaskBudgetGuard.can_invoke_llm(case_id) is True

    # Segunda petición a Grok-4.7 (1500 prompt tokens, 500 completion tokens -> $0.0075 + $0.0075 = $0.015 USD)
    # Acumulado = $0.027 USD >= $0.025 USD tope y 2/2 peticiones -> debe activar corte duro
    summary_2 = TaskBudgetGuard.record_llm_call(
        case_id=case_id,
        prompt_tokens=1500,
        completion_tokens=500,
        model="grok-4.7",
        purpose="react_step_2"
    )
    assert summary_2.requests_count == 2
    assert summary_2.measured_cost_usd == Decimal("0.027000")
    assert summary_2.was_throttled is True
    assert summary_2.status == "THROTTLED_CAP_REACHED"
    assert TaskBudgetGuard.can_invoke_llm(case_id) is False

    telemetry = TaskBudgetGuard.get_global_session_telemetry()
    assert telemetry["session_total_requests"] == 2
    assert telemetry["session_measured_cost_usd"] == 0.027
    assert telemetry["throttled_cases_count"] == 1


def test_cryptographic_invariant_auditor_and_backward_compatibility():
    """
    Verifica que CryptographicInvariantAuditor valide la identidad de partida doble
    y el sello SHA-256 sin depender de terminología inflada, manteniendo retrocompatibilidad.
    """
    report = DisputeAnalysisReport(
        case_id="case_001",
        billed_amount=Decimal("25000.00"),
        received_amount=Decimal("21250.00"),
        difference=Decimal("-3750.00"),
        justified_amount=Decimal("1250.00"),
        claimable_amount=Decimal("2500.00"),
        confidence_score=0.98,
        root_cause="Conciliación verificada con herramientas simbólicas en Python.",
        recommended_action="Reclamar $2,500.00 USD por cargo sin soporte.",
        evidence=["invoice.pdf", "delivery_note.pdf", "payment_receipt.pdf"]
    )
    seal = generate_cryptographic_proof_token(
        case_id=report.case_id,
        billed=report.billed_amount,
        received=report.received_amount,
        diff=report.difference,
        justified=report.justified_amount,
        claimable=report.claimable_amount,
        timestamp="2026-11-03T20:00:00Z"
    )
    assert seal.startswith("SM-PROOF-SHA256-")

    audit_result = CryptographicInvariantAuditor.audit_report(report)
    assert audit_result.audit_status == "MATHEMATICALLY_PROVEN"
    assert audit_result.text_hallucination_detected is False
    assert audit_result.invariant_conservation_ok is True
    assert audit_result.invariant_deductions_ok is True

    # Verificar alias retrocompatible
    assert ZKPFinancialAuditor is CryptographicInvariantAuditor
