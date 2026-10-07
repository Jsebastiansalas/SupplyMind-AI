from decimal import Decimal
from agent.core.hermes_runner import HermesRunner
from agent.memory.audit_logger import AuditLogger
from agent.core.state import DisputeState, ProcessStatus
from agent.tools.registry import TOOL_DEFINITIONS, ToolExecutor

def test_hermes_tool_definitions_schema():
    assert len(TOOL_DEFINITIONS) == 4
    names = [t["function"]["name"] for t in TOOL_DEFINITIONS]
    assert "read_dispute_documents" in names
    assert "execute_reconciliation" in names
    assert "evaluate_contract_terms" in names
    assert "generate_final_report" in names

def test_audit_logger_records_and_persists():
    logger = AuditLogger("test_case_audit")
    step = logger.log_step(
        phase="TEST_PHASE",
        action_type="THOUGHT",
        name="TestStep",
        details={"key": "val"},
        rationale="Prueba de auditoria"
    )
    assert step.step_number == 1
    assert step.name == "TestStep"
    assert logger.log_file.exists()
    
    # Limpiar archivo de prueba
    if logger.log_file.exists():
        logger.log_file.unlink()

def test_hermes_runner_resolves_case_001_simulated():
    runner = HermesRunner(case_id="case_001")
    report = runner._run_simulated_hermes()
    
    assert report.case_id == "case_001"
    assert report.billed_amount == Decimal("9000.00")
    assert report.received_amount == Decimal("8200.00")
    assert report.difference == Decimal("-800.00")
    assert report.justified_amount == Decimal("800.00")
    assert report.claimable_amount == Decimal("0.00")
    assert report.confidence >= 0.90
    assert "faltante" in report.root_cause.lower()
    assert len(report.evidence) >= 2
    assert "nota de crédito" in report.recommended_action.lower() or "nota de credito" in report.recommended_action.lower()
    
    # Verificar bitácora auditable generada
    assert runner.audit_logger.log_file.exists()

def test_hermes_runner_ask_simulated():
    runner = HermesRunner(case_id="case_001")
    
    # Pregunta sobre faltantes
    ans_faltante = runner._simulated_ask("¿Qué faltante de cajas hubo?")
    assert "PROD-002" in ans_faltante
    assert "10 cajas" in ans_faltante
    assert "800" in ans_faltante
    
    # Pregunta sobre contrato
    ans_contrato = runner._simulated_ask("¿Qué cláusula del contrato autoriza la deducción?")
    assert "4.2" in ans_contrato
    
    # Pregunta sobre monto reclamable
    ans_reclamable = runner._simulated_ask("¿Cuánto dinero podemos reclamar?")
    assert "0.00" in ans_reclamable
    
    # Pregunta sobre recomendación
    ans_accion = runner._simulated_ask("¿Qué acción se debe tomar?")
    assert "nota de crédito" in ans_accion.lower() or "nota de credito" in ans_accion.lower()

def test_calibrated_prompts_contain_expert_criteria():
    from agent.planner.prompts import SYSTEM_PROMPT, INTERACTIVE_CHAT_PROMPT
    assert "JERARQUÍA PROBATORIA" in SYSTEM_PROMPT
    assert "MATRIZ DE CAUSA RAÍZ" in SYSTEM_PROMPT
    assert "CONFIDENCE SCORING" in SYSTEM_PROMPT
    assert "JERARQUÍA PROBATORIA" in INTERACTIVE_CHAT_PROMPT

def test_agent_trainer_budget_limit_and_calculation():
    from agent.training.trainer import AgentTrainer
    trainer = AgentTrainer(budget_limit_usd=1.00)
    assert trainer.budget_limit_usd == 1.00
    assert trainer.total_spent_usd == 0.0
    
    # Prueba de cálculo de costo con tarifas Grok
    cost = trainer._calc_cost(tokens_in=1000, tokens_out=1000)
    assert cost == 0.012  # (1*0.002) + (1*0.010)
    
    # Validación de verificación presupuestaria
    assert trainer._check_budget() is True
    trainer.total_spent_usd = 1.05
    assert trainer._check_budget() is False

def test_hermes_runner_inspection_and_menu_methods():
    runner = HermesRunner(case_id="case_001")
    runner._ensure_case_loaded()
    
    # Verificar que los métodos de inspección corran sin excepciones
    runner._display_menu()
    runner._display_documents_inspection()
    runner._display_reconciliation_details()
    runner._display_contract_evaluation()
    runner._display_audit_log_tail()

