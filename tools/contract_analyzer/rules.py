from typing import List
from decimal import Decimal
from pydantic import BaseModel, ConfigDict
from data.models import CommercialContract
from tools.reconciliation_engine.engine import ReconciliationSummary

class ClauseMatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    clause_id: str
    title: str
    is_applicable: bool
    is_deduction_authorized: bool
    explanation: str

class ContractEvaluationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    contract_id: str
    matches: List[ClauseMatch]
    contractual_justification_valid: bool
    summary_legal_assessment: str
    recommended_contract_action: str

def evaluate_contract_compliance(
    contract: CommercialContract,
    summary: ReconciliationSummary
) -> ContractEvaluationResult:
    """
    Analiza las cláusulas contractuales contra los hallazgos de conciliación física.
    Determina si las deducciones aplicadas por el comprador están legal y contractualmente amparadas.
    """
    matches: List[ClauseMatch] = []
    is_valid = False
    
    for clause in contract.clauses:
        # Cláusula de faltantes físicos
        if clause.policy == "DEDUCTION_ALLOWED_ON_SIGNED_DISCREPANCY" or "4.2" in clause.clause_id:
            if summary.total_missing_amount > Decimal("0.00"):
                matches.append(
                    ClauseMatch(
                        clause_id=clause.clause_id,
                        title=clause.title,
                        is_applicable=True,
                        is_deduction_authorized=True,
                        explanation=(
                            f"La {clause.clause_id} ({clause.title}) autoriza la deducción del 100% "
                            f"del valor unitario cuando exista constancia firmada en la remisión."
                        )
                    )
                )
                is_valid = True
                
        # Cláusula de averías
        elif clause.policy == "PHOTO_EVIDENCE_REQUIRED" or "5.1" in clause.clause_id:
            if summary.total_damaged_amount > Decimal("0.00"):
                matches.append(
                    ClauseMatch(
                        clause_id=clause.clause_id,
                        title=clause.title,
                        is_applicable=True,
                        is_deduction_authorized=False,
                        explanation=f"Requiere notificación dentro de 48 horas y acta fotográfica según {clause.clause_id}."
                    )
                )

        # Cláusula de precios
        elif clause.policy == "STRICT_MATCH" or "3.1" in clause.clause_id:
            if summary.total_price_discrepancy_amount != Decimal("0.00"):
                matches.append(
                    ClauseMatch(
                        clause_id=clause.clause_id,
                        title=clause.title,
                        is_applicable=True,
                        is_deduction_authorized=True,
                        explanation=f"Los precios facturados deben ajustarse a la Orden de Compra según {clause.clause_id}."
                    )
                )

    if is_valid and summary.unjustified_deductions_amount == Decimal("0.00"):
        assessment = (
            f"La deducción de ${summary.justified_deductions_amount:,.2f} aplicada por el cliente "
            f"se encuentra plenamente justificada conforme a las cláusulas comerciales del contrato {contract.contract_id}."
        )
        action = "Aceptar la deducción en cartera y emitir Nota de Crédito comercial por el importe correspondiente para sanear la cuenta."
    elif summary.unjustified_deductions_amount > Decimal("0.00"):
        assessment = (
            f"Existe un monto no justificado de ${summary.unjustified_deductions_amount:,.2f} que no cuenta con "
            f"respaldo contractual ni físico en las remisiones de entrega."
        )
        action = f"Exigir el pago complementario de ${summary.unjustified_deductions_amount:,.2f} mediante requerimiento formal."
    else:
        assessment = "No se detectaron causales contractuales válidas para las diferencias registradas."
        action = "Solicitar aclaración inmediata al equipo comercial y de cartera del cliente."

    return ContractEvaluationResult(
        contract_id=contract.contract_id,
        matches=matches,
        contractual_justification_valid=is_valid,
        summary_legal_assessment=assessment,
        recommended_contract_action=action
    )
