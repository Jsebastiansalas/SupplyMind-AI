import pytest
from decimal import Decimal
from tools.document_reader.reader import load_case_documents, DocumentReaderError
from tools.reconciliation_engine.engine import reconcile_dispute_data
from tools.contract_analyzer.rules import evaluate_contract_compliance
from tools.report_generator.generator import build_dispute_report

class TestDocumentReader:
    def test_load_valid_case_001(self):
        docs = load_case_documents("case_001")
        assert "invoice" in docs
        assert "purchase_order" in docs
        assert "delivery" in docs
        assert "payment" in docs
        assert "contract" in docs
        assert docs["invoice"].invoice_id == "INV-40102"

    def test_load_non_existent_case_fails(self):
        with pytest.raises(DocumentReaderError):
            load_case_documents("caso_inexistente_999")

class TestReconciliationEngine:
    def test_deterministic_reconciliation_case_001(self):
        docs = load_case_documents("case_001")
        summary = reconcile_dispute_data(
            invoice=docs["invoice"],
            purchase_order=docs["purchase_order"],
            delivery=docs["delivery"],
            payment=docs["payment"]
        )
        
        # Exactitud matemática
        assert summary.billed_amount == Decimal("9000.00")
        assert summary.received_amount == Decimal("8200.00")
        assert summary.difference == Decimal("-800.00")
        assert summary.total_deductions_applied == Decimal("800.00")
        
        # Hallazgo físico
        assert summary.primary_discrepancy_type == "FALTANTE_DE_MERCANCIA"
        assert summary.total_missing_amount == Decimal("800.00")
        assert summary.total_damaged_amount == Decimal("0.00")
        assert summary.total_price_discrepancy_amount == Decimal("0.00")
        
        # Justificación matemática
        assert summary.justified_deductions_amount == Decimal("800.00")
        assert summary.unjustified_deductions_amount == Decimal("0.00")
        
        # Detalle de la línea afectada
        assert len(summary.discrepancies) == 1
        disc = summary.discrepancies[0]
        assert disc.item_id == "PROD-002"
        assert disc.missing_quantity == 10
        assert disc.missing_amount == Decimal("800.00")

class TestContractAnalyzer:
    def test_evaluate_contract_compliance_case_001(self):
        docs = load_case_documents("case_001")
        summary = reconcile_dispute_data(
            invoice=docs["invoice"],
            purchase_order=docs["purchase_order"],
            delivery=docs["delivery"],
            payment=docs["payment"]
        )
        contract_eval = evaluate_contract_compliance(
            contract=docs["contract"],
            summary=summary
        )
        
        assert contract_eval.contractual_justification_valid is True
        assert any(m.clause_id == "CLAUSE-4.2" and m.is_deduction_authorized for m in contract_eval.matches)
        assert "justificada" in contract_eval.summary_legal_assessment.lower()
        assert "Nota de Crédito" in contract_eval.recommended_contract_action

class TestReportGenerator:
    def test_build_dispute_report_case_001(self):
        docs = load_case_documents("case_001")
        summary = reconcile_dispute_data(
            invoice=docs["invoice"],
            purchase_order=docs["purchase_order"],
            delivery=docs["delivery"],
            payment=docs["payment"]
        )
        contract_eval = evaluate_contract_compliance(
            contract=docs["contract"],
            summary=summary
        )
        report = build_dispute_report(
            case_id="case_001",
            reconciliation=summary,
            contract_evaluation=contract_eval,
            confidence=0.98
        )
        
        assert report.case_id == "case_001"
        assert report.billed_amount == Decimal("9000.00")
        assert report.received_amount == Decimal("8200.00")
        assert report.difference == Decimal("-800.00")
        assert report.justified_amount == Decimal("800.00")
        assert report.claimable_amount == Decimal("0.00")
        assert report.confidence == 0.98
        assert "Faltante físico" in report.root_cause
        assert len(report.evidence) >= 2
        
        # Probar renderizado
        display_str = report.formatted_display()
        assert "DISPUTE ANALYSIS REPORT" in display_str
        assert "$9,000.00 USD" in display_str
        assert "$-800.00 USD" in display_str


class TestToolExecutorNewTools:
    def test_execute_audit_notice_window_tool(self):
        from agent.core.state import DisputeState
        from agent.memory.audit_logger import AuditLogger
        from agent.tools.registry import ToolExecutor

        state = DisputeState(case_id="case_001", objective="Auditar disputa case_001")
        logger = AuditLogger("test_notice_tool")
        executor = ToolExecutor(state=state, audit_logger=logger)

        res = executor.execute_tool("audit_notice_window", {"case_id": "case_001", "notice_window_days": 30})
        assert res["status"] == "success"
        assert "notice_audit" in res
        assert "is_timely" in res["notice_audit"]

    def test_execute_match_skus_and_calculate_tax_tool(self):
        from agent.core.state import DisputeState
        from agent.memory.audit_logger import AuditLogger
        from agent.tools.registry import ToolExecutor

        state = DisputeState(case_id="case_001", objective="Auditar disputa case_001")
        logger = AuditLogger("test_sku_tax_tool")
        executor = ToolExecutor(state=state, audit_logger=logger)

        res = executor.execute_tool("match_skus_and_calculate_tax", {"case_id": "case_001"})
        assert res["status"] == "success"
        assert "sku_matching" in res
        assert "total_skus_audited" in res["sku_matching"]
        assert "credit_note_recommended_vat" in res["sku_matching"]

    def test_tool_executor_self_healing_prerequisite(self):
        """Valida US-2.1.2: Si execute_reconciliation se llama sin cargar documentos antes, auto-sana cargándolos."""
        from agent.core.state import DisputeState
        from agent.memory.audit_logger import AuditLogger
        from agent.tools.registry import ToolExecutor

        state = DisputeState(case_id="case_001", objective="Prueba auto-sanacion")
        assert not state.loaded_documents
        logger = AuditLogger("test_self_healing")
        executor = ToolExecutor(state=state, audit_logger=logger)

        res = executor.execute_tool("execute_reconciliation", {"case_id": "case_001"})
        assert res["status"] == "success"
        assert state.loaded_documents is not None
        assert state.reconciliation_summary is not None
        assert res["billed_amount"] == 9000.0

    def test_tool_executor_graceful_error_handling(self):
        """Valida US-2.1.2: Herramientas desconocidas o errores de archivo no crashean y retornan status error."""
        from agent.core.state import DisputeState, ProcessStatus
        from agent.memory.audit_logger import AuditLogger
        from agent.tools.registry import ToolExecutor

        state = DisputeState(case_id="case_001", objective="Prueba errores")
        logger = AuditLogger("test_errors")
        executor = ToolExecutor(state=state, audit_logger=logger)

        # 1. Herramienta desconocida
        res_unk = executor.execute_tool("herramienta_fantasma", {})
        assert res_unk["status"] == "error"
        assert "desconocida" in res_unk["message"].lower()

        # 2. Caso inexistente
        res_fail = executor.execute_tool("read_dispute_documents", {"case_id": "caso_inexistente_999"})
        assert res_fail["status"] == "error"
        assert state.current_status == ProcessStatus.FAILED


