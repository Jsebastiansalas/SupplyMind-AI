from typing import Optional, Dict, Any
from data.models import DisputeAnalysisReport, DocumentHealthAudit
from tools.reconciliation_engine.engine import ReconciliationSummary
from tools.contract_analyzer.rules import ContractEvaluationResult

def build_dispute_report(
    case_id: str,
    reconciliation: ReconciliationSummary,
    contract_evaluation: ContractEvaluationResult,
    root_cause_explanation: Optional[str] = None,
    recommended_action: Optional[str] = None,
    confidence: float = 0.98,
    health_audit: Optional[DocumentHealthAudit] = None,
    loaded_documents: Optional[Dict[str, Any]] = None,
) -> DisputeAnalysisReport:
    """
    Construye y valida el modelo estricto de DisputeAnalysisReport combinando
    la precisión determinística de los cálculos con la evaluación contractual
    y el anclaje fáctico probatorio de cero alucinaciones.
    """
    # 1. Determinar causa raíz
    if root_cause_explanation:
        cause = root_cause_explanation
    elif reconciliation.primary_discrepancy_type == "FALTANTE_DE_MERCANCIA":
        items_str = ", ".join([f"{d.missing_quantity} uds de {d.description}" for d in reconciliation.discrepancies if d.missing_quantity > 0])
        cause = f"Faltante físico en entrega ({items_str}) por valor de ${reconciliation.total_missing_amount:,.2f} USD."
    elif reconciliation.primary_discrepancy_type == "MERCANCIA_AVERIADA":
        cause = f"Mercancía averiada durante recepción por valor de ${reconciliation.total_damaged_amount:,.2f} USD."
    elif reconciliation.primary_discrepancy_type == "DIFERENCIA_DE_PRECIO":
        cause = f"Discrepancia de precio unitario facturado vs acordado en PO por ${reconciliation.total_price_discrepancy_amount:,.2f} USD."
    else:
        cause = "Deducción comercial no justificada en recepción."
        
    # 2. Consolidar evidencia
    evidence = list(reconciliation.evidence_trail)
    for match in contract_evaluation.matches:
        if match.is_applicable:
            evidence.append(f"Respaldo contractual: {match.explanation}")
            
    # 3. Acción recomendada
    action = recommended_action or contract_evaluation.recommended_contract_action
    
    report = DisputeAnalysisReport(
        case_id=case_id,
        currency="USD",
        billed_amount=reconciliation.billed_amount,
        received_amount=reconciliation.received_amount,
        difference=reconciliation.difference,
        root_cause=cause,
        evidence=evidence,
        justified_amount=reconciliation.justified_deductions_amount,
        claimable_amount=reconciliation.unjustified_deductions_amount,
        confidence=confidence,
        recommended_action=action,
        health_audit=health_audit
    )

    # Auditoría ZKP e invariantes de cero alucinación (Pilar 2)
    from agent.guardrails.arithmetic_verifier import ZKPFinancialAuditor
    report = ZKPFinancialAuditor.audit_and_enforce(report, reconciliation)

    # Anclaje fáctico estricto y certificación probatoria Zero Uncited Claims (Pilar 3)
    from agent.guardrails.evidence_binder import StrictEvidenceBinder
    report = StrictEvidenceBinder.audit_and_bind(
        report=report,
        reconciliation=reconciliation,
        loaded_documents=loaded_documents,
        contract_evaluation=contract_evaluation
    )

    return report
