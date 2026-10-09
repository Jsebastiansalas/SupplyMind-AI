from typing import Dict, Any, List
from agent.core.state import DisputeState, ProcessStatus
from agent.memory.audit_logger import AuditLogger
from tools.document_reader.reader import load_case_documents
from tools.reconciliation_engine.engine import reconcile_dispute_data
from tools.contract_analyzer.rules import evaluate_contract_compliance
from tools.report_generator.generator import build_dispute_report

# Especificación formal JSON-Schema para SKYNET y Grok
TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "read_dispute_documents",
            "description": "Carga y valida los documentos del expediente comercial de la disputa (factura, orden de compra, remisión de entrega, comprobante de pago y contrato).",
            "parameters": {
                "type": "object",
                "properties": {
                    "case_id": {
                        "type": "string",
                        "description": "Identificador del caso a analizar (ejemplo: 'case_001')."
                    }
                },
                "required": ["case_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "execute_reconciliation",
            "description": "Ejecuta el motor determinístico de conciliación línea a línea y financiera. Compara cantidades recibidas vs facturadas, coteja precios con la orden de compra y calcula con precisión matemática exacta el monto faltante, averiado y deducciones aplicadas.",
            "parameters": {
                "type": "object",
                "properties": {
                    "case_id": {
                        "type": "string",
                        "description": "Identificador del caso cuyos documentos ya fueron leídos."
                    }
                },
                "required": ["case_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "evaluate_contract_terms",
            "description": "Analiza las cláusulas y condiciones comerciales del contrato contra los hallazgos de conciliación física. Determina si las penalizaciones o deducciones aplicadas por el comprador están legal y contractualmente amparadas.",
            "parameters": {
                "type": "object",
                "properties": {
                    "case_id": {
                        "type": "string",
                        "description": "Identificador del caso."
                    }
                },
                "required": ["case_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_final_report",
            "description": "Genera formalmente el Dispute Analysis Report final con el monto facturado, recibido, diferencia, causa encontrada, evidencia utilizada, monto justificado, monto reclamable, nivel de confianza y acción recomendada.",
            "parameters": {
                "type": "object",
                "properties": {
                    "case_id": {
                        "type": "string",
                        "description": "Identificador del caso."
                    },
                    "root_cause_explanation": {
                        "type": "string",
                        "description": "Explicación detallada de la causa raíz encontrada basada en la evidencia documental y conciliación física."
                    },
                    "recommended_action": {
                        "type": "string",
                        "description": "Acción recomendada para el equipo de operaciones/cartera (ej. emitir nota de crédito, iniciar cobro coactivo, solicitar inspección)."
                    }
                },
                "required": ["case_id", "root_cause_explanation", "recommended_action"]
            }
        }
    }
]

class ToolExecutor:
    """Ejecutor y despachador de herramientas para el bucle agéntico SKYNET."""
    def __init__(self, state: DisputeState, audit_logger: AuditLogger):
        self.state = state
        self.audit_logger = audit_logger

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        case_id = arguments.get("case_id", self.state.case_id)
        
        self.audit_logger.log_step(
            phase=self.state.current_status.value,
            action_type="TOOL_CALL",
            name=tool_name,
            details={"arguments": arguments}
        )
        
        try:
            if tool_name == "read_dispute_documents":
                self.state.current_status = ProcessStatus.READING_DOCUMENTS
                docs = load_case_documents(case_id)
                self.state.loaded_documents = docs
                
                result = {
                    "status": "success",
                    "documents_found": list(docs.keys()),
                    "invoice_total": float(docs["invoice"].total_amount),
                    "po_total": float(docs["purchase_order"].total_amount),
                    "delivery_items": len(docs["delivery"].items),
                    "payment_received": float(docs["payment"].amount_paid),
                    "deductions_count": len(docs["payment"].deductions)
                }
                
            elif tool_name == "execute_reconciliation":
                self.state.current_status = ProcessStatus.RECONCILING
                if not self.state.loaded_documents:
                    docs = load_case_documents(case_id)
                    self.state.loaded_documents = docs
                else:
                    docs = self.state.loaded_documents
                    
                summary = reconcile_dispute_data(
                    invoice=docs["invoice"],
                    purchase_order=docs["purchase_order"],
                    delivery=docs["delivery"],
                    payment=docs["payment"]
                )
                self.state.reconciliation_summary = summary
                
                result = {
                    "status": "success",
                    "billed_amount": float(summary.billed_amount),
                    "received_amount": float(summary.received_amount),
                    "difference": float(summary.difference),
                    "primary_discrepancy_type": summary.primary_discrepancy_type,
                    "total_missing_amount": float(summary.total_missing_amount),
                    "total_damaged_amount": float(summary.total_damaged_amount),
                    "total_price_discrepancy_amount": float(summary.total_price_discrepancy_amount),
                    "justified_deductions": float(summary.justified_deductions_amount),
                    "unjustified_deductions": float(summary.unjustified_deductions_amount),
                    "discrepancies": [d.model_dump(mode="json") for d in summary.discrepancies],
                    "evidence_trail": summary.evidence_trail
                }
                
            elif tool_name == "evaluate_contract_terms":
                self.state.current_status = ProcessStatus.EVALUATING_CONTRACT
                if not self.state.loaded_documents or not self.state.reconciliation_summary:
                    raise ValueError("Se requiere ejecutar lectura y conciliación antes de evaluar contrato.")
                    
                contract = self.state.loaded_documents["contract"]
                evaluation = evaluate_contract_compliance(
                    contract=contract,
                    summary=self.state.reconciliation_summary
                )
                self.state.contract_evaluation = evaluation
                
                result = {
                    "status": "success",
                    "contract_id": evaluation.contract_id,
                    "contractual_justification_valid": evaluation.contractual_justification_valid,
                    "summary_legal_assessment": evaluation.summary_legal_assessment,
                    "recommended_contract_action": evaluation.recommended_contract_action,
                    "matches": [m.model_dump() for m in evaluation.matches]
                }
                
            elif tool_name == "generate_final_report":
                self.state.current_status = ProcessStatus.SYNTHESIZING
                if not self.state.reconciliation_summary or not self.state.contract_evaluation:
                    raise ValueError("Se requiere conciliación y evaluación de contrato previas para generar reporte.")
                    
                root_cause = arguments.get("root_cause_explanation")
                recommended_action = arguments.get("recommended_action")
                
                report = build_dispute_report(
                    case_id=case_id,
                    reconciliation=self.state.reconciliation_summary,
                    contract_evaluation=self.state.contract_evaluation,
                    root_cause_explanation=root_cause,
                    recommended_action=recommended_action,
                    confidence=0.98
                )
                self.state.final_report = report
                self.state.current_status = ProcessStatus.COMPLETED
                
                result = {
                    "status": "success",
                    "report": report.model_dump(mode="json")
                }
            else:
                result = {"status": "error", "message": f"Herramienta desconocida: {tool_name}"}

        except Exception as e:
            result = {"status": "error", "message": str(e)}
            self.state.error_message = str(e)
            self.state.current_status = ProcessStatus.FAILED

        self.audit_logger.log_step(
            phase=self.state.current_status.value,
            action_type="TOOL_OUTPUT",
            name=tool_name,
            details={"result": result}
        )
        return result
