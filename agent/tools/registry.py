from typing import Dict, Any, List
from agent.core.state import DisputeState, ProcessStatus
from agent.memory.audit_logger import AuditLogger
from tools.document_reader.reader import load_case_documents, load_case_documents_with_health
from tools.reconciliation_engine.engine import reconcile_dispute_data
from tools.contract_analyzer.rules import evaluate_contract_compliance
from tools.report_generator.generator import build_dispute_report
from tools.sku_matcher import perform_sku_level_matching
from tools.notice_window_auditor import audit_notice_window

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
    },
    {
        "type": "function",
        "function": {
            "name": "audit_notice_window",
            "description": "Audita la validez temporal del reclamo contra la cláusula de plazos de notificación (Notice Window, típicamente 30 días). Si el comprador notificó fuera de plazo, el reclamo es extemporáneo y nulo de pleno derecho s/ Art. 1043 del Código de Comercio.",
            "parameters": {
                "type": "object",
                "properties": {
                    "case_id": {
                        "type": "string",
                        "description": "Identificador del caso."
                    },
                    "notice_window_days": {
                        "type": "integer",
                        "description": "Plazo límite pactado en días naturales (por defecto 30)."
                    }
                },
                "required": ["case_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "match_skus_and_calculate_tax",
            "description": "Ejecuta el cotejo matemático determinístico línea a línea por cada SKU individual entre Factura, Remisión y Orden de Compra, calculando faltantes, averías, variaciones de precio y la base gravable con IVA al 16% para emitir la Nota de Crédito correspondiente.",
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
                docs, health_audit = load_case_documents_with_health(case_id)
                self.state.loaded_documents = docs
                self.state.health_audit = health_audit
                
                if health_audit.status == "QUARANTINE" or not health_audit.is_healthy or len(docs) < 5:
                    from tools.document_reader.reader import DocumentReaderError
                    raise DocumentReaderError(
                        f"Expediente '{case_id}' en cuarentena documental (salud: {health_audit.health_score}%): "
                        f"Archivos corruptos o faltantes críticos."
                    )
                
                invoice_items_count = len(docs["invoice"].items)
                if invoice_items_count >= 50:
                    self.state.is_massive_scale = True

                result = {
                    "status": "success",
                    "documents_found": list(docs.keys()),
                    "invoice_total": float(docs["invoice"].total_amount),
                    "po_total": float(docs["purchase_order"].total_amount),
                    "invoice_items_count": invoice_items_count,
                    "delivery_items": len(docs["delivery"].items),
                    "payment_received": float(docs["payment"].amount_paid),
                    "deductions_count": len(docs["payment"].deductions),
                    "health_score": health_audit.health_score,
                    "health_status": health_audit.status,
                    "execution_safety_level": health_audit.execution_safety_level,
                    "is_massive_scale": self.state.is_massive_scale
                }
                
            elif tool_name == "execute_reconciliation":
                self.state.current_status = ProcessStatus.RECONCILING
                if not self.state.loaded_documents:
                    docs = load_case_documents(case_id)
                    self.state.loaded_documents = docs
                else:
                    docs = self.state.loaded_documents
                    
                invoice_items_count = len(docs["invoice"].items)
                if invoice_items_count >= 50 or self.state.is_massive_scale:
                    from tools.reconciliation_engine.batch_map_reduce import MassiveBatchReconciliationEngine
                    manifest = MassiveBatchReconciliationEngine.map_reduce_reconcile(
                        invoice=docs["invoice"],
                        purchase_order=docs["purchase_order"],
                        delivery=docs["delivery"],
                        payment=docs["payment"],
                        batch_size=50
                    )
                    self.state.hierarchical_manifest = manifest
                    summary = manifest.summary
                    self.state.reconciliation_summary = summary
                    
                    compact_discrepancies = [
                        {
                            "item_id": d.item_id,
                            "desc": d.description,
                            "missing_qty": d.missing_quantity,
                            "damaged_qty": d.damaged_quantity,
                            "price_diff": float(d.price_difference),
                            "impact": float(d.total_impact)
                        }
                        for d in summary.discrepancies[:25]
                    ]
                    
                    result = {
                        "status": "success",
                        "is_massive_scale": True,
                        "total_skus_processed": manifest.total_skus_processed,
                        "total_batches_count": manifest.total_batches_count,
                        "merkle_root_hash": manifest.merkle_root_hash,
                        "invariant_conserved": manifest.invariant_conserved,
                        "billed_amount": float(summary.billed_amount),
                        "received_amount": float(summary.received_amount),
                        "difference": float(summary.difference),
                        "primary_discrepancy_type": summary.primary_discrepancy_type,
                        "total_missing_amount": float(summary.total_missing_amount),
                        "total_damaged_amount": float(summary.total_damaged_amount),
                        "total_price_discrepancy_amount": float(summary.total_price_discrepancy_amount),
                        "justified_deductions": float(summary.justified_deductions_amount),
                        "unjustified_deductions": float(summary.unjustified_deductions_amount),
                        "discrepancies_count": len(summary.discrepancies),
                        "discrepancies": compact_discrepancies,
                        "evidence_trail": summary.evidence_trail
                    }
                else:
                    summary = reconcile_dispute_data(
                        invoice=docs["invoice"],
                        purchase_order=docs["purchase_order"],
                        delivery=docs["delivery"],
                        payment=docs["payment"]
                    )
                    self.state.reconciliation_summary = summary
                    
                    compact_discrepancies = [
                        {
                            "item_id": d.item_id,
                            "desc": d.description,
                            "missing_qty": d.missing_quantity,
                            "damaged_qty": d.damaged_quantity,
                            "price_diff": float(d.price_difference),
                            "impact": float(d.total_impact)
                        }
                        for d in summary.discrepancies
                    ]
                    
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
                        "discrepancies": compact_discrepancies,
                        "evidence_trail": summary.evidence_trail
                    }
                
            elif tool_name == "evaluate_contract_terms":
                self.state.current_status = ProcessStatus.EVALUATING_CONTRACT
                if not self.state.loaded_documents:
                    self.state.loaded_documents = load_case_documents(case_id)
                if not self.state.reconciliation_summary:
                    docs = self.state.loaded_documents
                    self.state.reconciliation_summary = reconcile_dispute_data(
                        invoice=docs["invoice"],
                        purchase_order=docs["purchase_order"],
                        delivery=docs["delivery"],
                        payment=docs["payment"]
                    )
                    
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
                
                # Si el contrato es extenso o jerárquico, enriquecer con cláusulas indexadas BM25
                contract_text = getattr(contract, "raw_content", "") or ""
                if not contract_text and hasattr(contract, "clauses") and contract.clauses:
                    contract_text = "\n\n".join([f"CLÁUSULA {c.clause_id}: {c.text}" for c in contract.clauses])
                if len(contract_text.split()) > 300:
                    try:
                        from tools.document_reader.hierarchical_segmenter import HierarchicalDocumentSegmenter
                        hierarchy = HierarchicalDocumentSegmenter.segment_text(contract_text, document_name=f"contrato_{case_id}")
                        query_term = self.state.reconciliation_summary.primary_discrepancy_type or "penalizacion"
                        top_clauses = HierarchicalDocumentSegmenter.query_relevant_clauses(hierarchy, query=query_term, top_k=3)
                        result["indexed_hierarchical_clauses"] = [
                            {"title": c.title, "clause_id": c.clause_id, "excerpt": c.content[:200]}
                            for c in top_clauses
                        ]
                    except Exception:
                        pass

                
            elif tool_name == "generate_final_report":
                self.state.current_status = ProcessStatus.SYNTHESIZING
                if not self.state.loaded_documents:
                    self.state.loaded_documents = load_case_documents(case_id)
                if not self.state.reconciliation_summary:
                    docs = self.state.loaded_documents
                    self.state.reconciliation_summary = reconcile_dispute_data(
                        invoice=docs["invoice"],
                        purchase_order=docs["purchase_order"],
                        delivery=docs["delivery"],
                        payment=docs["payment"]
                    )
                if not self.state.contract_evaluation:
                    contract = self.state.loaded_documents["contract"]
                    self.state.contract_evaluation = evaluate_contract_compliance(
                        contract=contract,
                        summary=self.state.reconciliation_summary
                    )
                    
                root_cause = arguments.get("root_cause_explanation")
                recommended_action = arguments.get("recommended_action")
                
                report = build_dispute_report(
                    case_id=case_id,
                    reconciliation=self.state.reconciliation_summary,
                    contract_evaluation=self.state.contract_evaluation,
                    root_cause_explanation=root_cause,
                    recommended_action=recommended_action,
                    confidence=0.98,
                    health_audit=self.state.health_audit,
                    loaded_documents=self.state.loaded_documents
                )
                self.state.final_report = report
                self.state.current_status = ProcessStatus.COMPLETED
                
                result = {
                    "status": "success",
                    "report": report.model_dump(mode="json")
                }

            elif tool_name == "audit_notice_window":
                if not self.state.loaded_documents:
                    self.state.loaded_documents = load_case_documents(case_id)
                docs = self.state.loaded_documents
                deliv_dict = docs["delivery"].model_dump() if hasattr(docs["delivery"], "model_dump") else docs["delivery"].__dict__
                pay_dict = docs["payment"].model_dump() if hasattr(docs["payment"], "model_dump") else docs["payment"].__dict__
                contract_dict = docs["contract"].model_dump() if hasattr(docs["contract"], "model_dump") else docs["contract"].__dict__

                limit_days = arguments.get("notice_window_days", 30)
                notice_audit = audit_notice_window(
                    delivery_data=deliv_dict,
                    payment_data=pay_dict,
                    contract_data=contract_dict,
                    default_limit_days=limit_days
                )
                result = {
                    "status": "success",
                    "notice_audit": notice_audit.model_dump()
                }

            elif tool_name == "match_skus_and_calculate_tax":
                if not self.state.loaded_documents:
                    self.state.loaded_documents = load_case_documents(case_id)
                docs = self.state.loaded_documents
                inv_dict = docs["invoice"].model_dump() if hasattr(docs["invoice"], "model_dump") else docs["invoice"].__dict__
                deliv_dict = docs["delivery"].model_dump() if hasattr(docs["delivery"], "model_dump") else docs["delivery"].__dict__
                po_dict = docs["purchase_order"].model_dump() if hasattr(docs["purchase_order"], "model_dump") else docs["purchase_order"].__dict__

                sku_res = perform_sku_level_matching(
                    invoice_data=inv_dict,
                    delivery_data=deliv_dict,
                    po_data=po_dict
                )
                result = {
                    "status": "success",
                    "sku_matching": sku_res.model_dump()
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
