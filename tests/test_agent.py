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
    report = runner.run()
    
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
