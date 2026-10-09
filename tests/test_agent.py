from decimal import Decimal
from agent.core.skynet_runner import SkynetRunner
from agent.memory.audit_logger import AuditLogger
from agent.core.state import DisputeState, ProcessStatus
from agent.tools.registry import TOOL_DEFINITIONS, ToolExecutor

def test_skynet_tool_definitions_schema():
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

def test_skynet_runner_resolves_case_001_simulated():
    runner = SkynetRunner(case_id="case_001")
    report = runner._run_simulated_skynet()
    
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

def test_skynet_runner_ask_simulated():
    runner = SkynetRunner(case_id="case_001")
    
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

def test_skynet_runner_inspection_and_menu_methods():
    runner = SkynetRunner(case_id="case_001")
    runner._ensure_case_loaded()
    
    # Verificar que los métodos de inspección corran sin excepciones
    runner._display_menu()
    runner._display_documents_inspection()
    runner._display_reconciliation_details()
    runner._display_contract_evaluation()
    runner._display_audit_log_tail()
    runner._display_all_cases_comparison()

def test_skynet_runner_multi_case_features():
    runner = SkynetRunner(case_id="case_001")
    
    # 1. Prueba de cambio con alias '2'
    runner._switch_case("2")
    assert runner.case_id == "case_002"
    assert runner.state.case_id == "case_002"
    
    # 2. Prueba de cambio con alias '3'
    runner._switch_case("c3")
    assert runner.case_id == "case_003"
    
    # 3. Pregunta comparativa multi-caso
    ans_comp = runner._simulated_ask("compara los 3 casos de la cartera")
    assert "case_001" in ans_comp
    assert "case_002" in ans_comp
    assert "case_003" in ans_comp
    assert "12,500" in ans_comp
    
    # 4. Pregunta cruzada hacia caso 2 estando en caso 3
    ans_cross_2 = runner._simulated_ask("¿Cuánto dinero es reclamable en el caso 2?")
    assert "12,500.00" in ans_cross_2
    
    # 5. Volver a caso 1 con alias '1'
    runner._switch_case("caso 1")
    assert runner.case_id == "case_001"


