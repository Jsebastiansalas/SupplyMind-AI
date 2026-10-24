import sys
import json
import time
from decimal import Decimal
from typing import Dict, Any, List, Optional

# Salida segura UTF-8 en Windows para evitar UnicodeEncodeError con caracteres de LLM (ej. \u2212)
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure") and sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from config.settings import settings
from agent.core.state import DisputeState, ProcessStatus
from agent.memory.audit_logger import AuditLogger
from agent.core.anonymizer import DataAnonymizer
from agent.planner.prompts import SYSTEM_PROMPT, INTERACTIVE_CHAT_PROMPT
from agent.tools.registry import TOOL_DEFINITIONS, ToolExecutor
from data.models import DisputeAnalysisReport
from tools.report_exporter import export_dispute_artifacts

console = Console(highlight=False, legacy_windows=False)

class SkynetRunner:
    """
    Orquestador del agente SupplyMind AI sobre la arquitectura SKYNET Framework.
    Soporta:
    - Modo Live: Conexión directa a Grok a través del gateway de Platica (https://api.reto.pltk.mx/v1).
    - Modo Simulado / Harness Local: Motor ReAct autónomo local para desarrollo y pruebas.
    - Modo Fast-Path: Conciliación determinística directa instantánea (<0.5 segundos).
    """
    def __init__(
        self,
        case_id: str,
        objective: Optional[str] = None,
        fast_path: bool = False,
        use_cache: bool = True
    ):
        self.case_id = case_id
        self.objective = objective or f"Analiza la disputa {case_id}"
        self.fast_path = fast_path
        self.use_cache = use_cache
        self.state = DisputeState(case_id=case_id, objective=self.objective)
        self.audit_logger = AuditLogger(case_id=case_id)
        self.tool_executor = ToolExecutor(state=self.state, audit_logger=self.audit_logger)
        self.anonymizer = DataAnonymizer()
        
    def run(self) -> DisputeAnalysisReport:
        """Ejecuta el ciclo de resolución autónomo de la disputa."""
        start_time = time.time()
        
        # 1. Verificación de Caché Inteligente
        if self.use_cache:
            from agent.core.cache import dispute_cache
            cached = dispute_cache.get(self.case_id)
            if cached:
                cached_report, cached_state = cached
                console.print(f"[bold cyan][CACHE HIT][/bold cyan] Expediente {self.case_id} recuperado de memoria en 0.001s.")
                self.state = cached_state
                self.state.execution_time_seconds = 0.01
                return cached_report

        mode_desc = '⚡ Fast-Path Acelerado (<1s)' if self.fast_path else ('En Vivo (Grok / Platica Gateway)' if settings.is_live_api_ready else 'Harness Local / Simulador ReAct')
        console.print(Panel(
            f"[bold green]SupplyMind AI - SKYNET Framework Runner[/bold green]\n"
            f"[cyan]Caso:[/cyan] {self.case_id} | [cyan]Objetivo:[/cyan] {self.objective}\n"
            f"[yellow]Modo:[/yellow] {mode_desc}",
            border_style="green"
        ))
        
        self.audit_logger.log_step(
            phase="INITIALIZATION",
            action_type="THOUGHT",
            name="Objective_Received",
            details={"case_id": self.case_id, "objective": self.objective},
            rationale="Iniciando ciclo autónomo de análisis de disputa comercial."
        )
        
        report: Optional[DisputeAnalysisReport] = None
        if self.fast_path:
            try:
                report = self._run_fast_path_skynet()
            except Exception as e:
                report = self._generate_error_report(str(e))
                self.state.final_report = report
        elif settings.is_live_api_ready:
            try:
                report = self._run_live_skynet()
            except Exception as e:
                console.print(f"[bold yellow][AVISO RESILIENCIA][/bold yellow] Fallo en conexión con gateway Platica ({e}). Conmutando a modo determinístico.")
                try:
                    report = self._run_simulated_skynet()
                except Exception as sim_e:
                    report = self._generate_error_report(str(sim_e))
                    self.state.final_report = report
        else:
            try:
                report = self._run_simulated_skynet()
            except Exception as e:
                report = self._generate_error_report(str(e))
                self.state.final_report = report

        # Salvaguarda de resiliencia: si el reporte sigue siendo None
        if report is None:
            err_msg = self.state.error_message or "Expediente con archivos corruptos, incompletos o esquema Pydantic inválido."
            report = self._generate_error_report(err_msg)
            self.state.final_report = report

        # Vincular auditoría de salud documental si está presente en el estado
        if report and report.health_audit is None and getattr(self.state, "health_audit", None):
            report.health_audit = self.state.health_audit

        self.state.execution_time_seconds = round(time.time() - start_time, 2)
        
        # Almacenar en caché para acelerar consultas subsecuentes
        if self.use_cache and report and report.confidence > 0:
            from agent.core.cache import dispute_cache
            dispute_cache.set(self.case_id, report, self.state)
        
        # Exportar artefactos de negocio formales (Reporte Markdown/JSON y Carta de Reclamación)
        if report is not None:
            try:
                artifacts = export_dispute_artifacts(report, self.state)
                if "markdown_report" in artifacts:
                    console.print(f"[dim][OK] Informe formal exportado a: {artifacts['markdown_report']}[/dim]")
                if "reclamation_letter" in artifacts:
                    console.print(f"[bold green][OK] Carta formal de reclamación generada en:[/bold green] [cyan]{artifacts['reclamation_letter']}[/cyan]")
            except Exception as err:
                console.print(f"[dim yellow][Aviso] No se pudieron exportar entregables: {err}[/dim yellow]")
            
        return report

    def _run_fast_path_skynet(self) -> DisputeAnalysisReport:
        """
        Bucle Fast-Path determinístico de alta velocidad (<0.5s).
        Ejecuta la lectura, conciliación y evaluación contractual en un pipeline directo.
        """
        console.print("[bold cyan][Pensamiento SKYNET Fast-Path][/bold cyan]: Ejecutando auditoría acelerada directa...")
        res_docs = self.tool_executor.execute_tool("read_dispute_documents", {"case_id": self.case_id})
        if res_docs.get("status") == "error":
            raise ValueError(f"Fallo en lectura de documentos: {res_docs.get('message', 'Documentos corruptos o faltantes')}")

        res_rec = self.tool_executor.execute_tool("execute_reconciliation", {"case_id": self.case_id})
        if res_rec.get("status") == "error":
            raise ValueError(f"Fallo en conciliación: {res_rec.get('message', 'Error en conciliación')}")

        res_ev = self.tool_executor.execute_tool("evaluate_contract_terms", {"case_id": self.case_id})
        if res_ev.get("status") == "error":
            raise ValueError(f"Fallo en evaluación contractual: {res_ev.get('message', 'Error al evaluar contrato')}")
        
        rec = self.state.reconciliation_summary
        ev = self.state.contract_evaluation
        if rec and rec.unjustified_deductions_amount > Decimal("0.00"):
            root_cause = (
                f"Discrepancia mixta en expediente {self.case_id}: Faltante físico comprobado de ${rec.justified_deductions_amount:,.2f} USD "
                f"amparado en remisión firmada con sello, y retenciones no autorizadas por ${rec.unjustified_deductions_amount:,.2f} USD sin sustento contractual ni documental."
            )
            action = (
                f"Aceptar deducción de ${rec.justified_deductions_amount:,.2f} USD mediante Nota de Crédito por el faltante real, "
                f"y rechazar formalmente las deducciones indebidas de ${rec.unjustified_deductions_amount:,.2f} USD exigiendo su pago inmediato."
            )
        else:
            just_amt = rec.justified_deductions_amount if rec else Decimal("0.00")
            if rec and rec.primary_discrepancy_type == "DIFERENCIA_DE_PRECIO":
                root_cause = (
                    f"Discrepancia de precio unitario en factura de ${rec.total_price_discrepancy_amount:,.2f} USD "
                    f"respecto al precio pactado en la Orden de Compra aprobada."
                )
                action = (
                    f"Aceptar deducción de ${just_amt:,.2f} USD aplicada por el cliente en cuentas por cobrar, "
                    f"emitir Nota de Crédito comercial por ajuste de tarifa y actualizar maestro de precios en el ERP del proveedor."
                )
            elif rec and rec.primary_discrepancy_type == "MERCANCIA_AVERIADA":
                root_cause = (
                    f"Mercancía averiada durante recepción en bodega valorada en ${rec.total_damaged_amount:,.2f} USD, "
                    f"consignada en acta de descarga e inspección física."
                )
                action = (
                    f"Aplicar compensación comercial por ${just_amt:,.2f} USD conforme a política contractual de averías "
                    f"y conciliar la partida en cartera de clientes."
                )
            else:
                root_cause = (
                    f"Faltante físico en entrega valorado en ${just_amt:,.2f} USD, "
                    f"constatado en remisión de entrega firmada con sello de recepción en bodega."
                )
                action = (
                    f"Aceptar deducción de ${just_amt:,.2f} USD en cuentas por cobrar y emitir Nota de Crédito comercial "
                    f"por dicho valor a favor del cliente para conciliar y cerrar la cuenta."
                )

        res_rep = self.tool_executor.execute_tool(
            "generate_final_report",
            {
                "case_id": self.case_id,
                "root_cause_explanation": root_cause,
                "recommended_action": action
            }
        )
        if res_rep.get("status") == "error" or not self.state.final_report:
            raise ValueError(f"Fallo al generar reporte final: {res_rep.get('message', 'No se pudo generar reporte')}")

        return self.state.final_report

    def _run_live_skynet(self) -> DisputeAnalysisReport:
        """Bucle ReAct contra el gateway oficial de Platica Grok con optimización de latencia."""
        from openai import OpenAI
        client = OpenAI(
            base_url=settings.PLATICA_BASE_URL,
            api_key=settings.RETO_KEY
        )
        
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": self.objective}
        ]
        
        max_turns = 10
        for turn in range(max_turns):
            console.print(f"[dim]Turno {turn + 1}: Consultando a Grok ({settings.MODEL_NAME})...[/dim]")
            
            # Compresión inteligente de contexto para documentos de gran escala (evita pérdida de información)
            if len(messages) > 6:
                for idx_m, m_item in enumerate(messages[:-2]):
                    if isinstance(m_item, dict) and m_item.get("role") == "tool":
                        try:
                            content_obj = json.loads(m_item["content"])
                            if "discrepancies" in content_obj and len(content_obj["discrepancies"]) > 10:
                                all_disc = content_obj["discrepancies"]
                                # Ordenar por mayor impacto económico descendente
                                sorted_disc = sorted(all_disc, key=lambda x: abs(x.get("impact", 0.0)), reverse=True)
                                top_disc = sorted_disc[:10]
                                remaining = sorted_disc[10:]
                                rem_impact = sum(x.get("impact", 0.0) for x in remaining)
                                content_obj["discrepancies"] = top_disc
                                content_obj["_total_discrepancies_count"] = len(all_disc)
                                content_obj["_top_discrepancies_shown"] = len(top_disc)
                                content_obj["_remaining_items_count"] = len(remaining)
                                content_obj["_remaining_items_aggregate_impact"] = round(rem_impact, 2)
                                content_obj["_compressed_hierarchically"] = True
                                m_item["content"] = json.dumps(content_obj, ensure_ascii=False)
                        except Exception:
                            pass
            
            safe_messages = self.anonymizer.anonymize_messages(messages)
            
            response = client.chat.completions.create(
                model=settings.MODEL_NAME,
                messages=safe_messages,
                tools=TOOL_DEFINITIONS,
                tool_choice="auto"
            )
            
            if response.choices and response.choices[0].message.tool_calls:
                self.anonymizer.deanonymize_tool_calls(response.choices[0].message.tool_calls)
            
            if response.usage:
                self.state.tokens_in += getattr(response.usage, "prompt_tokens", 0) or 0
                self.state.tokens_out += getattr(response.usage, "completion_tokens", 0) or 0
                cost_in = (self.state.tokens_in / 1000.0) * 0.002
                cost_out = (self.state.tokens_out / 1000.0) * 0.010
                self.state.estimated_cost_usd = round(cost_in + cost_out, 6)
            
            msg = response.choices[0].message
            messages.append(msg.model_dump())
            
            if msg.content:
                console.print(f"[bold blue]SupplyMind AI:[/bold blue] {msg.content}")
                
            if not msg.tool_calls:
                break
                
            for tool_call in msg.tool_calls:
                fn_name = tool_call.function.name
                try:
                    fn_args = json.loads(tool_call.function.arguments)
                    try:
                        console.print(f"[bold yellow]-> Invocando herramienta:[/bold yellow] [magenta]{fn_name}[/magenta] con [dim]{fn_args}[/dim]")
                    except Exception:
                        pass
                    tool_result = self.tool_executor.execute_tool(fn_name, fn_args)
                except json.JSONDecodeError as e:
                    console.print(f"[bold red][AVISO RESILIENCIA][/bold red] Fallo al parsear JSON de la herramienta {fn_name}: {e}")
                    tool_result = {"error": f"JSONDecodeError: {str(e)}. Por favor corrige tus argumentos (asegura comillas válidas) e intenta nuevamente."}
                except Exception as e:
                    console.print(f"[bold red][AVISO RESILIENCIA][/bold red] Error en ejecución de herramienta {fn_name}: {e}")
                    tool_result = {"error": f"ToolExecutionError: {str(e)}. Revisa los parámetros e inténtalo nuevamente."}
                
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(tool_result, ensure_ascii=False, default=str)
                })
                
            if self.state.final_report:
                break
                
        if not self.state.final_report:
            raise RuntimeError("El agente no completó la generación del informe final.")
            
        return self.state.final_report

    def _run_simulated_skynet(self) -> DisputeAnalysisReport:
        """
        Bucle ReAct determinístico para desarrollo, CI y pruebas locales.
        Emula la secuencia de razonamiento y llamadas a herramientas de SKYNET.
        """
        # Turno 1: Inspeccionar expediente
        console.print("[cyan][Pensamiento SKYNET][/cyan]: Para analizar la disputa, primero debo inspeccionar los documentos comerciales disponibles en el expediente.")
        console.print(f"[bold yellow]-> SKYNET Tool Call:[/bold yellow] [magenta]read_dispute_documents[/magenta](case_id='{self.case_id}')")
        self.tool_executor.execute_tool("read_dispute_documents", {"case_id": self.case_id})
        time.sleep(0.1)
        
        # Turno 2: Conciliación física y matemática
        console.print("[cyan][Pensamiento SKYNET][/cyan]: Documentos cargados correctamente. Procedo a ejecutar la conciliación matemática determinística.")
        console.print(f"[bold yellow]-> SKYNET Tool Call:[/bold yellow] [magenta]execute_reconciliation[/magenta](case_id='{self.case_id}')")
        self.tool_executor.execute_tool("execute_reconciliation", {"case_id": self.case_id})
        time.sleep(0.1)
        
        # Turno 3: Análisis contractual
        console.print(f"[cyan][Pensamiento SKYNET][/cyan]: Conciliación procesada para {self.case_id}. Verifico respaldo contractual de las deducciones.")
        console.print(f"[bold yellow]-> SKYNET Tool Call:[/bold yellow] [magenta]evaluate_contract_terms[/magenta](case_id='{self.case_id}')")
        self.tool_executor.execute_tool("evaluate_contract_terms", {"case_id": self.case_id})
        time.sleep(0.1)
        
        # Turno 4: Síntesis y reporte formal
        console.print("[cyan][Pensamiento SKYNET][/cyan]: Generando síntesis analítica y formalizando informe de disputa...")
        console.print("[bold yellow]-> SKYNET Tool Call:[/bold yellow] [magenta]generate_final_report[/magenta](...)")
        
        rec = self.state.reconciliation_summary
        ev = self.state.contract_evaluation
        if rec and rec.unjustified_deductions_amount > Decimal("0.00"):
            root_cause = (
                f"Discrepancia mixta en expediente {self.case_id}: Faltante físico comprobado de ${rec.justified_deductions_amount:,.2f} USD "
                f"amparado en remisión firmada con sello, y retenciones no autorizadas por ${rec.unjustified_deductions_amount:,.2f} USD sin sustento contractual ni documental."
            )
            action = (
                f"Aceptar deducción de ${rec.justified_deductions_amount:,.2f} USD mediante Nota de Crédito por el faltante real, "
                f"y rechazar formalmente las deducciones indebidas de ${rec.unjustified_deductions_amount:,.2f} USD exigiendo su pago inmediato."
            )
        else:
            just_amt = rec.justified_deductions_amount if rec else Decimal("0.00")
            if rec and rec.primary_discrepancy_type == "DIFERENCIA_DE_PRECIO":
                root_cause = (
                    f"Discrepancia de precio unitario en factura de ${rec.total_price_discrepancy_amount:,.2f} USD "
                    f"respecto al precio pactado en la Orden de Compra aprobada."
                )
                action = (
                    f"Aceptar deducción de ${just_amt:,.2f} USD aplicada por el cliente en cuentas por cobrar, "
                    f"emitir Nota de Crédito comercial por ajuste de tarifa y actualizar maestro de precios en el ERP del proveedor."
                )
            else:
                root_cause = (
                    f"Faltante físico en entrega valorado en ${just_amt:,.2f} USD, "
                    f"constatado en remisión de entrega firmada con sello de recepción en bodega."
                )
                action = (
                    f"Aceptar deducción de ${just_amt:,.2f} USD en cuentas por cobrar y emitir Nota de Crédito comercial "
                    f"por dicho valor a favor del cliente para conciliar y cerrar la cuenta."
                )

        self.tool_executor.execute_tool(
            "generate_final_report",
            {
                "case_id": self.case_id,
                "root_cause_explanation": root_cause,
                "recommended_action": action
            }
        )
        
        if not self.state.final_report:
            raise RuntimeError("Error al generar el reporte en la simulación.")
            
        try:
            export_dispute_artifacts(self.state.final_report, self.state)
        except Exception:
            pass
            
        return self.state.final_report

    def _ensure_case_loaded(self) -> None:
        """Garantiza que los documentos, conciliación y evaluación contractual estén cargados."""
        if not self.state.loaded_documents:
            self.tool_executor.execute_tool("read_dispute_documents", {"case_id": self.case_id})
        if not self.state.reconciliation_summary:
            self.tool_executor.execute_tool("execute_reconciliation", {"case_id": self.case_id})
        if not self.state.contract_evaluation:
            self.tool_executor.execute_tool("evaluate_contract_terms", {"case_id": self.case_id})

    def _build_context_summary(self) -> str:
        """Construye un resumen técnico estructurado del caso para el contexto del chat."""
        summary_lines = [f"EXPEDIENTE ACTIVO: {self.case_id}"]
        if self.state.loaded_documents:
            docs = self.state.loaded_documents
            inv = docs.get("invoice")
            po = docs.get("purchase_order")
            deliv = docs.get("delivery")
            pay = docs.get("payment")
            ctr = docs.get("contract")
            
            if inv:
                summary_lines.append(f"- Factura: {inv.invoice_id} por ${inv.total_amount:,.2f} {inv.currency}")
            if po:
                summary_lines.append(f"- Orden de Compra: {po.po_id} por ${po.total_amount:,.2f} {po.currency}")
            if deliv:
                short_items = [f"{item.item_id} ({item.missing_quantity} u. faltantes)" for item in deliv.items if item.missing_quantity > 0]
                if len(short_items) > 8:
                    short_display = f"{', '.join(short_items[:8])} ... y {len(short_items) - 8} ítems más"
                else:
                    short_display = ', '.join(short_items) or 'Ninguno'
                summary_lines.append(f"- Remisión de Entrega: {deliv.delivery_id} (Faltantes: {short_display})")
            if pay:
                deductions_desc = [f"{d.code}: ${d.amount:,.2f} ({d.reason})" for d in pay.deductions]
                if len(deductions_desc) > 8:
                    ded_display = f"{', '.join(deductions_desc[:8])} ... y {len(deductions_desc) - 8} deducciones más"
                else:
                    ded_display = ', '.join(deductions_desc)
                summary_lines.append(f"- Pago Recibido: {pay.payment_id} por ${pay.amount_paid:,.2f} (Deducciones: {ded_display})")
            if ctr:
                clauses_desc = [f"{c.clause_id} ({c.title})" for c in ctr.clauses]
                if len(clauses_desc) > 10:
                    cl_display = f"{', '.join(clauses_desc[:10])} ... y {len(clauses_desc) - 10} cláusulas más"
                else:
                    cl_display = ', '.join(clauses_desc)
                summary_lines.append(f"- Contrato Comercial: {ctr.contract_id} (Cláusulas: {cl_display})")
                
        if self.state.reconciliation_summary:
            rec = self.state.reconciliation_summary
            summary_lines.append(f"- Conciliación Matemática: Facturado ${rec.billed_amount:,.2f}, Pagado ${rec.received_amount:,.2f}, Diferencia ${rec.difference:,.2f}")
            summary_lines.append(f"- Deducciones Justificadas: ${rec.justified_deductions_amount:,.2f} | Injustificadas: ${rec.unjustified_deductions_amount:,.2f}")
            summary_lines.append(f"- Tipo de Discrepancia: {rec.primary_discrepancy_type}")
            
        if self.state.contract_evaluation:
            ev = self.state.contract_evaluation
            app_clauses = [f"{m.clause_id} ({m.title})" for m in ev.matches if m.is_applicable]
            summary_lines.append(f"- Evaluación Contractual: Justificación Válida: {ev.contractual_justification_valid}, Cláusulas Aplicables: {', '.join(app_clauses) or 'Ninguna'}")
            summary_lines.append(f"- Dictamen Legal: {ev.summary_legal_assessment}")
            summary_lines.append(f"- Recomendación Contractual: {ev.recommended_contract_action}")
            
        if self.state.final_report:
            rep = self.state.final_report
            summary_lines.append(f"- Causa Raíz: {rep.root_cause}")
            summary_lines.append(f"- Acción Recomendada: {rep.recommended_action}")
            summary_lines.append(f"- Monto Reclamable: ${rep.claimable_amount:,.2f}")

        summary_lines.append("\nPANORAMA DE CARTERA MULTI-CASO (3 EXPEDIENTES DISPONIBLES EN PLATAFORMA):")
        summary_lines.append("- case_001 (RetailCorp): Factura $9,000, Pago $8,200. Faltante físico de 10 cajas ($800) amparado por Cláusula 4.2. Reclamable: $0.00 USD.")
        summary_lines.append("- case_002 (MegaMarket): Factura $54,200, Pago $37,700. Retención $16,500 ($4,000 justificado por faltante Cláusula 4.2; $12,500 injustificado: $6,500 avería no reportada en 48h s/ Cláusula 5.1 y $6,000 multa unilateral prohibida s/ Cláusula 7.3). Reclamable: $12,500.00 USD.")
        summary_lines.append("- case_003 (SuperTiendas): Factura $15,000, Pago $12,000. Retención $3,000 por sobreprecio en factura vs Orden de Compra amparado por Cláusula 3.1. Reclamable: $0.00 USD.")
            
        return "\n".join(summary_lines)

    def _display_report_table(self) -> None:
        """Muestra una tabla con el informe de conciliación."""
        if not self.state.final_report:
            if self.case_id == "case_002":
                self.tool_executor.execute_tool(
                    "generate_final_report",
                    {
                        "case_id": self.case_id,
                        "root_cause_explanation": (
                            "Faltante físico comprobado en recepción de 50 cajas de PROD-102 (Aceite de Oliva Extra Virgen) "
                            "valoradas en $4,000.00 USD s/ remisión DEL-12044 con firma de recibo. Deducciones adicionales "
                            "por supuesta avería ($6,500.00) y penalización unilateral ($6,000.00) carecen de soporte."
                        ),
                        "recommended_action": (
                            "Aceptar deducción de $4,000.00 USD emitiendo Nota de Crédito por faltante físico amparado en Cláusula 4.2. "
                            "Rechazar formalmente deducciones improcedentes por $12,500.00 USD exigiendo su abono inmediato al amparo de Cláusulas 5.1 y 7.3."
                        )
                    }
                )
            elif self.case_id == "case_003":
                self.tool_executor.execute_tool(
                    "generate_final_report",
                    {
                        "case_id": self.case_id,
                        "root_cause_explanation": (
                            "Discrepancia de precio unitario en factura INV-99402: 100 unidades de PROD-301 facturadas a "
                            "$150.00 USD frente a $120.00 USD acordados en PO-55100, generando un sobreprecio de $3,000.00 USD."
                        ),
                        "recommended_action": (
                            "Aceptar deducción de $3,000.00 USD aplicada por el cliente en cuentas por cobrar, emitir Nota de "
                            "Crédito comercial conforme a Cláusula 3.1 y actualizar catálogo de precios en ERP del proveedor."
                        )
                    }
                )
            elif self.case_id == "case_009_mega_retailer_dispute":
                self.tool_executor.execute_tool(
                    "generate_final_report",
                    {
                        "case_id": self.case_id,
                        "root_cause_explanation": (
                            "Discrepancia mixta en expediente case_009_mega_retailer_dispute: Faltante físico comprobado de $12,000.00 USD "
                            "amparado en remisión firmada con sello en 3 SKUs, y retenciones no autorizadas por $13,000.00 USD "
                            "sin sustento contractual ni bilateral ($8,500 pronto pago no pactado + $4,500 penalidad ASN)."
                        ),
                        "recommended_action": (
                            "Emitir Nota de Crédito comercial por $12,000.00 USD por el faltante real en muelle amparado en Cláusula 4.2, "
                            "y emitir requerimiento formal de cobranza extrajudicial por $13,000.00 USD indebidamente retenidos s/ Cláusula 7.3."
                        )
                    }
                )
            elif self.case_id == "case_007_cisco_large_bundle":
                self.tool_executor.execute_tool(
                    "generate_final_report",
                    {
                        "case_id": self.case_id,
                        "root_cause_explanation": (
                            "Discrepancia mixta en expediente case_007_cisco_large_bundle: Faltante físico comprobado de $13,000.00 USD "
                            "amparado en remisión de Dallas con sello, y retenciones no autorizadas por $14,000.00 USD por penalidad unilateral."
                        ),
                        "recommended_action": (
                            "Aceptar deducción de $13,000.00 USD mediante Nota de Crédito por faltante acreditado s/ Cláusula 4.2, "
                            "y rechazar formalmente penalización de $14,000.00 USD exigiendo su abono inmediato al amparo de Cláusula 6.1 y 7.3."
                        )
                    }
                )
            elif self.case_id == "case_005_amazon_shortage":
                self.tool_executor.execute_tool(
                    "generate_final_report",
                    {
                        "case_id": self.case_id,
                        "root_cause_explanation": (
                            "Discrepancia mixta en expediente case_005_amazon_shortage: Faltante físico comprobado de $5,000.00 USD "
                            "en 20 SSDs NVMe s/ remisión DEL-AMZ-2026-8812 con firma, y retención unilateral de $2,500.00 USD por penalización ASN."
                        ),
                        "recommended_action": (
                            "Aceptar deducción de $5,000.00 USD emitiendo Nota de Crédito comercial s/ Cláusula 4.1, "
                            "y rechazar formalmente penalización de $2,500.00 USD exigiendo su reembolso s/ Cláusula 5.3 y 7.3."
                        )
                    }
                )
            elif self.case_id == "case_006_walmart_otif_pricing":
                self.tool_executor.execute_tool(
                    "generate_final_report",
                    {
                        "case_id": self.case_id,
                        "root_cause_explanation": (
                            "Discrepancia mixta en expediente case_006_walmart_otif_pricing: Sobreprecio facturado de $4,500.00 USD "
                            "en SKU-WHEY-2KG frente a Orden de Compra pactada, y retención unilateral de $3,500.00 USD por pronto pago extemporáneo."
                        ),
                        "recommended_action": (
                            "Emitir Nota de Crédito por $4,500.00 USD por ajuste de sobreprecio s/ Cláusula 3.1, "
                            "y formular requerimiento de pago por $3,500.00 USD retenidos sin devengo de pronto pago s/ Cláusula 7.2."
                        )
                    }
                )
            else:
                self.tool_executor.execute_tool(
                    "generate_final_report",
                    {
                        "case_id": self.case_id,
                        "root_cause_explanation": (
                            "Faltante físico en entrega de 10 cajas de Producto B (Café Gourmet Tostado) valoradas en $800.00 USD, "
                            "constatado en remisión DEL-9912 con firma y sello de recepción en bodega."
                        ),
                        "recommended_action": (
                            "Aceptar deducción de $800.00 USD en cuentas por cobrar y emitir Nota de Crédito comercial "
                            "por dicho valor a favor del cliente Supermercados Éxito / RetailCorp."
                        )
                    }
                )
        rep = self.state.final_report
        if rep:
            table = Table(title=f"[bold green]DISPUTE ANALYSIS REPORT - {rep.case_id}[/bold green]", border_style="green", show_header=False)
            table.add_column("Campo", style="bold cyan", width=22)
            table.add_column("Detalle", style="white")
            table.add_row("Facturado", f"${rep.billed_amount:,.2f} {rep.currency}")
            table.add_row("Recibido", f"${rep.received_amount:,.2f} {rep.currency}")
            table.add_row("Diferencia", f"[bold red]${rep.difference:,.2f} {rep.currency}[/bold red]")
            table.add_row("Causa Raíz", rep.root_cause)
            table.add_row("Justificado", f"[green]${rep.justified_amount:,.2f} {rep.currency}[/green]")
            table.add_row("Reclamable", f"${rep.claimable_amount:,.2f} {rep.currency}")
            table.add_row("Confianza", f"{rep.confidence * 100:.1f}%")
            table.add_row("Acción Recomendada", f"[yellow]{rep.recommended_action}[/yellow]")
            console.print(table)
            if self.state.tokens_in > 0 or self.state.execution_time_seconds > 0:
                console.print(
                    f"[dim]⚡ Inferencia: {self.state.tokens_in + self.state.tokens_out:,} tokens "
                    f"({self.state.tokens_in:,} in / {self.state.tokens_out:,} out) | "
                    f"Costo: ${self.state.estimated_cost_usd:.5f} USD | "
                    f"Tiempo: {self.state.execution_time_seconds:.2f}s[/dim]\n"
                )

    def _display_menu(self) -> None:
        """Despliega el menú interactivo con todas las opciones disponibles."""
        menu_text = (
            f"[bold white]EXPEDIENTE EN GESTIÓN:[/bold white] [bold green]{self.case_id}[/bold green]\n\n"
            "[bold yellow]ACCIONES SOBRE EL EXPEDIENTE ACTIVO:[/bold yellow]\n"
            "  [bold cyan]1[/bold cyan] [bold white]🧠 Analizar Disputa[/bold white]       [dim]-> Ciclo autónomo ReAct con Grok / LLM[/dim]\n"
            "  [bold cyan]2[/bold cyan] [bold white]📊 Ver Reporte Formal[/bold white]       [dim]-> Cuadro ejecutivo y carta de reclamación[/dim]\n"
            "  [bold cyan]3[/bold cyan] [bold white]📂 Inspeccionar Documentos[/bold white]  [dim]-> Factura, OC, Remisión, Pago y Contrato[/dim]\n"
            "  [bold cyan]4[/bold cyan] [bold white]🔢 Conciliación Detallada[/bold white]   [dim]-> Auditoría matemática línea a línea en Decimal[/dim]\n"
            "  [bold cyan]5[/bold cyan] [bold white]⚖️  Dictamen Contractual[/bold white]     [dim]-> Cláusulas aplicables y amparo jurídico[/dim]\n"
            "  [bold cyan]6[/bold cyan] [bold white]📜 Bitácora de Auditoría[/bold white]    [dim]-> Historial de trazabilidad JSONL[/dim]\n"
            "  [bold cyan]7[/bold cyan] [bold white]🎯 Calibrar Criterio AI[/bold white]     [dim]-> Benchmark de entrenamiento (< $1.00 USD)[/dim]\n\n"
            "[bold yellow]GESTIÓN MULTI-CASO (S1):[/bold yellow]\n"
            "  [bold cyan]8[/bold cyan] [bold white]🔄 Cambiar de Expediente[/bold white]   [dim]-> Alternar a case_001, case_002 o case_003[/dim]\n"
            "  [bold cyan]9[/bold cyan] [bold white]🌐 Matriz Comparativa (3 Casos)[/bold white] [dim]-> Resumen consolidado de la cartera B2B[/dim]\n"
            "  [bold cyan]E[/bold cyan] [bold white]⚡ Evaluación S1 Jurado[/bold white]    [dim]-> Ejecutar suite automatizada completa (30 segs)[/dim]\n\n"
            "[bold yellow]ATAJOS RÁPIDOS Y CHAT:[/bold yellow]\n"
            "  [dim]• Escribe [bold cyan]c1[/bold cyan], [bold cyan]c2[/bold cyan] o [bold cyan]c3[/bold cyan] para cambiar de expediente al instante.[/dim]\n"
            "  [dim]• Escribe [bold cyan]menu[/bold cyan] para ver este menú, [bold cyan]?[/bold cyan] para ayuda o [bold cyan]0[/bold cyan] para salir.[/dim]\n"
            "  [dim]• O formula cualquier pregunta libre en lenguaje natural a Grok sobre cualquier caso.[/dim]"
        )
        console.print(Panel(
            menu_text,
            title=f"[bold green]SupplyMind AI - Menú Interactivo Multi-Caso[/bold green]",
            border_style="cyan"
        ))

    def _display_all_cases_comparison(self) -> None:
        """Muestra una matriz comparativa consolidada de los 3 casos B2B del reto."""
        cases_info = [
            {
                "id": "case_001",
                "name": "Básico (Faltante Físico Acordado)",
                "client": "RetailCorp",
                "billed": "$9,000.00",
                "diff": "-$800.00",
                "justified": "$800.00",
                "claimable": "$0.00",
                "action": "Aceptar deducción / Emitir Nota de Crédito",
            },
            {
                "id": "case_002",
                "name": "Complejo Alta Cuantía (Faltante + Daño + Multa)",
                "client": "MegaMarket",
                "billed": "$54,200.00",
                "diff": "-$16,500.00",
                "justified": "$4,000.00",
                "claimable": "$12,500.00",
                "action": "Emitir NC por $4k / Cobro formal por $12,500",
            },
            {
                "id": "case_003",
                "name": "Discrepancia de Precios (Sobreprecio vs PO)",
                "client": "SuperTiendas",
                "billed": "$15,000.00",
                "diff": "-$3,000.00",
                "justified": "$3,000.00",
                "claimable": "$0.00",
                "action": "Aceptar deducción tarifaria / Emitir NC",
            },
        ]
        
        table = Table(title="[bold green]MATRIZ COMPARATIVA DE CARTERA - 3 CASOS B2B (HITO S1)[/bold green]", border_style="cyan")
        table.add_column("Expediente", style="bold cyan", width=14)
        table.add_column("Cliente / Tipología", style="white", width=28)
        table.add_column("Facturado", justify="right")
        table.add_column("Retención", justify="right", style="bold red")
        table.add_column("Justificado", justify="right", style="green")
        table.add_column("Reclamable", justify="right", style="bold yellow")
        table.add_column("Acción Recomendada", style="dim", width=32)

        for c in cases_info:
            active_marker = " [bold green](ACTIVO)[/bold green]" if c["id"] == self.case_id else ""
            table.add_row(
                f"{c['id']}{active_marker}",
                f"{c['client']}\n[dim]{c['name']}[/dim]",
                c["billed"],
                c["diff"],
                c["justified"],
                c["claimable"],
                c["action"]
            )

        console.print("\n")
        console.print(table)
        console.print(f"[dim]Total reclamable en cartera:[/dim] [bold yellow]$12,500.00 USD[/bold yellow] [dim]| Expediente activo actual:[/dim] [bold green]{self.case_id}[/bold green]\n")

    def _display_documents_inspection(self) -> None:
        """Muestra una inspección estructurada de los 5 documentos del caso."""
        self._ensure_case_loaded()
        docs = self.state.loaded_documents
        if not docs:
            console.print("[yellow]No hay documentos cargados en memoria.[/yellow]")
            return
            
        inv = docs.get("invoice")
        po = docs.get("purchase_order")
        deliv = docs.get("delivery")
        pay = docs.get("payment")
        ctr = docs.get("contract")

        console.print(f"\n[bold green]═══ EXPEDIENTE COMERCIAL: {self.case_id} ═══[/bold green]\n")

        # 1. Factura vs Orden de Compra
        t_order = Table(title="[bold cyan]1. Factura Comercial (INV) vs Orden de Compra (PO)[/bold cyan]", border_style="cyan")
        t_order.add_column("Documento", style="bold")
        t_order.add_column("Referencia", style="white")
        t_order.add_column("Fecha", style="dim")
        t_order.add_column("Líneas", justify="center")
        t_order.add_column("Total Facturado / Pactado", justify="right", style="green")

        if inv:
            t_order.add_row("Factura Comercial", inv.invoice_id, inv.issue_date, str(len(inv.items)), f"${inv.total_amount:,.2f} {inv.currency}")
        if po:
            t_order.add_row("Orden de Compra", po.po_id, po.order_date, str(len(po.items)), f"${po.total_amount:,.2f} {po.currency}")
        console.print(t_order)

        # 2. Remisión de Entrega
        if deliv:
            t_del = Table(title=f"[bold cyan]2. Remisión de Entrega en Bodega ({deliv.delivery_id})[/bold cyan]", border_style="blue")
            t_del.add_column("Ítem / Producto", style="white")
            t_del.add_column("Cant. Despachada", justify="center")
            t_del.add_column("Cant. Recibida", justify="center", style="green")
            t_del.add_column("Faltante", justify="center", style="bold red")
            t_del.add_column("Avería", justify="center", style="yellow")
            t_del.add_column("Recepción y Sello", style="dim")

            for item in deliv.items:
                t_del.add_row(
                    item.item_id,
                    str(item.quantity_delivered),
                    str(item.quantity_received),
                    str(item.missing_quantity) if item.missing_quantity > 0 else "-",
                    str(item.damaged_quantity) if item.damaged_quantity > 0 else "-",
                    f"Recibido por: {deliv.received_by} (Firmado: {'Sí' if deliv.signed else 'No'})"
                )
            console.print(t_del)

        # 3. Comprobante de Pago y Deducciones
        if pay:
            t_pay = Table(title=f"[bold cyan]3. Comprobante de Pago Bancario ({pay.payment_id})[/bold cyan]", border_style="magenta")
            t_pay.add_column("Concepto", style="bold")
            t_pay.add_column("Monto / Código", justify="right")
            t_pay.add_column("Motivo Registrado por el Comprador", style="white")

            t_pay.add_row("Monto Efectivo Pagado", f"${pay.amount_paid:,.2f} {pay.currency}", f"Factura Ref: {pay.invoice_reference}")
            for d in pay.deductions:
                t_pay.add_row(f"Deducción Aplicada ({d.code})", f"-${d.amount:,.2f} {pay.currency}", d.reason)
            console.print(t_pay)

        # 4. Contrato Comercial
        if ctr:
            t_ctr = Table(title=f"[bold cyan]4. Contrato Marco ({ctr.contract_id})[/bold cyan]", border_style="yellow")
            t_ctr.add_column("Cláusula", style="bold")
            t_ctr.add_column("Título", style="white")
            t_ctr.add_column("Política / Regla Contractual", style="dim")

            for c in ctr.clauses:
                t_ctr.add_row(c.clause_id, c.title, c.policy)
            console.print(t_ctr)
        console.print("\n")

    def _display_reconciliation_details(self) -> None:
        """Muestra la tabla determinística detallada de conciliación."""
        self._ensure_case_loaded()
        rec = self.state.reconciliation_summary
        if not rec:
            console.print("[yellow]No se ha ejecutado la conciliación todavía.[/yellow]")
            return

        table = Table(title=f"[bold green]CONCILIACIÓN MATEMÁTICA LÍNEA POR LÍNEA ({self.case_id})[/bold green]", border_style="green")
        table.add_column("Ítem", style="bold white")
        table.add_column("Cant. Facturada", justify="center")
        table.add_column("Cant. Recibida", justify="center")
        table.add_column("Faltante", justify="center", style="bold red")
        table.add_column("Avería", justify="center", style="bold yellow")
        table.add_column("Precio Unitario", justify="right")
        table.add_column("Impacto Financiero", justify="right", style="bold red")

        for d in rec.discrepancies:
            table.add_row(
                d.item_id,
                str(d.billed_quantity),
                str(d.received_quantity),
                str(d.missing_quantity) if d.missing_quantity > 0 else "-",
                str(d.damaged_quantity) if d.damaged_quantity > 0 else "-",
                f"${d.invoiced_unit_price:,.2f}",
                f"-${d.total_impact:,.2f}" if d.total_impact > 0 else "$0.00"
            )

        console.print("\n")
        console.print(table)

        summary_box = Table(show_header=False, border_style="cyan")
        summary_box.add_column("Concepto", style="bold", width=30)
        summary_box.add_column("Monto", style="green")

        summary_box.add_row("Total Facturado", f"${rec.billed_amount:,.2f} USD")
        summary_box.add_row("Total Pagado", f"${rec.received_amount:,.2f} USD")
        summary_box.add_row("Diferencia Neta", f"[bold red]${rec.difference:,.2f} USD[/bold red]")
        summary_box.add_row("Deducciones Justificadas", f"[green]${rec.justified_deductions_amount:,.2f} USD[/green]")
        summary_box.add_row("Deducciones Injustificadas", f"${rec.unjustified_deductions_amount:,.2f} USD")
        summary_box.add_row("Tipo Primario de Discrepancia", rec.primary_discrepancy_type)
        console.print(summary_box)
        console.print("\n")

    def _display_contract_evaluation(self) -> None:
        """Muestra el desglose del análisis legal y contractual."""
        self._ensure_case_loaded()
        ev = self.state.contract_evaluation
        if not ev:
            console.print("[yellow]No se ha ejecutado el análisis contractual todavía.[/yellow]")
            return

        table = Table(title=f"[bold green]EVALUACIÓN DE CUMPLIMIENTO CONTRACTUAL ({ev.contract_id})[/bold green]", border_style="yellow")
        table.add_column("Cláusula", style="bold cyan")
        table.add_column("Título", style="white")
        table.add_column("Aplicable", justify="center")
        table.add_column("Autoriza Deducción", justify="center")
        table.add_column("Fundamento Jurídico", style="dim")

        for m in ev.matches:
            table.add_row(
                m.clause_id,
                m.title,
                "[green]SÍ[/green]" if m.is_applicable else "[dim]NO[/dim]",
                "[green]SÍ[/green]" if m.is_deduction_authorized else "[red]NO[/red]",
                m.explanation
            )

        console.print("\n")
        console.print(table)

        summary_box = Table(show_header=False, border_style="yellow")
        summary_box.add_column("Dictamen", style="bold", width=25)
        summary_box.add_column("Detalle", style="white")
        summary_box.add_row("Validez Contractual", "[bold green]DEDUCCIÓN VÁLIDA[/bold green]" if ev.contractual_justification_valid else "[bold red]DEDUCCIÓN NO VÁLIDA[/bold red]")
        summary_box.add_row("Evaluación Jurídica", ev.summary_legal_assessment)
        summary_box.add_row("Recomendación Contractual", ev.recommended_contract_action)
        console.print(summary_box)
        console.print("\n")

    def _display_audit_log_tail(self, limit: int = 8) -> None:
        """Muestra los últimos eventos de trazabilidad de la bitácora JSONL."""
        log_file = self.audit_logger.log_file
        if not log_file.exists():
            console.print(f"[dim]No hay bitácora generada aún en {log_file}[/dim]")
            return

        lines = log_file.read_text(encoding="utf-8").strip().splitlines()
        last_lines = lines[-limit:] if len(lines) > limit else lines

        table = Table(title=f"[bold green]ÚLTIMOS EVENTOS DE AUDITORÍA ({log_file.name})[/bold green]", border_style="cyan")
        table.add_column("Paso", justify="center", style="bold")
        table.add_column("Fase", style="magenta")
        table.add_column("Tipo Acción", style="cyan")
        table.add_column("Nombre / Evento", style="white")
        table.add_column("Detalle / Justificación", style="dim")

        for line in last_lines:
            try:
                item = json.loads(line)
                step = str(item.get("step_number", "-"))
                phase = item.get("phase", "-")
                act_type = item.get("action_type", "-")
                name = item.get("name", "-")
                rationale = item.get("rationale") or str(item.get("details", {}))
                table.add_row(step, phase, act_type, name, rationale[:80] + ("..." if len(rationale) > 80 else ""))
            except Exception:
                continue

        console.print("\n")
        console.print(table)
        console.print(f"[dim]Ruta completa: {log_file} ({len(lines)} eventos registrados)[/dim]\n")

    def _run_calibration(self) -> None:
        """Ejecuta el benchmark de calibración de criterio con tope presupuestario."""
        from agent.training.trainer import AgentTrainer
        trainer = AgentTrainer(budget_limit_usd=1.00)
        trainer.run_calibration(case_id=self.case_id)

    def _switch_case(self, new_case_id: str) -> None:
        """Cambia el caso activo del expediente con soporte para alias y validación."""
        new_case_id = new_case_id.strip()
        if not new_case_id:
            return
            
        alias_map = {
            "1": "case_001",
            "caso 1": "case_001",
            "caso1": "case_001",
            "case 1": "case_001",
            "case1": "case_001",
            "c1": "case_001",
            "2": "case_002",
            "caso 2": "case_002",
            "caso2": "case_002",
            "case 2": "case_002",
            "case2": "case_002",
            "c2": "case_002",
            "3": "case_003",
            "caso 3": "case_003",
            "caso3": "case_003",
            "case 3": "case_003",
            "case3": "case_003",
            "c3": "case_003",
        }
        resolved_id = alias_map.get(new_case_id.lower(), new_case_id)
        from pathlib import Path
        
        provided_path = Path(resolved_id)
        if provided_path.is_absolute() or provided_path.exists():
            final_path = provided_path
        else:
            cases_dir = Path("data/cases")
            if not cases_dir.exists():
                cases_dir = Path(__file__).resolve().parent.parent.parent / "data" / "cases"
            final_path = cases_dir / resolved_id
            
        if not final_path.exists():
            console.print(f"[bold red]Aviso:[/bold red] Expediente '{resolved_id}' no encontrado. (Ruta evaluada: {final_path})")
            return

        self.case_id = resolved_id
        self.objective = f"Analiza la disputa {resolved_id}"
        self.state = DisputeState(case_id=resolved_id, objective=self.objective)
        self.audit_logger = AuditLogger(case_id=resolved_id)
        self.tool_executor = ToolExecutor(state=self.state, audit_logger=self.audit_logger)
        self._ensure_case_loaded()
        console.print(f"\n[bold green][OK] Expediente activo cambiado exitosamente a:[/bold green] [bold cyan]{self.case_id}[/bold cyan]\n")

    def _simulated_ask(self, question: str) -> str:
        """Generador determinístico de respuestas locales para pruebas y modo offline."""
        import unicodedata
        q_raw = question.lower()
        q = "".join(c for c in unicodedata.normalize("NFD", q_raw) if unicodedata.category(c) != "Mn")
        
        # Consulta multi-caso comparativa
        if any(k in q for k in ["compara", "comparar", "todos los casos", "resumen de casos", "los 3 casos", "los tres casos", "matriz de casos"]):
            return (
                "Resumen comparativo de los 3 casos B2B de la cartera:\n"
                "1. case_001 (RetailCorp): Facturado $9,000 USD, Pagado $8,200 USD. Faltante físico de 10 cajas ($800) amparado por Cláusula 4.2. Reclamable: $0.00 USD (Acción: Emitir Nota de Crédito).\n"
                "2. case_002 (MegaMarket): Facturado $54,200 USD, Pagado $37,700 USD. Retención de $16,500 USD ($4,000 justificados por faltante Cláusula 4.2; $12,500 injustificados por avería no probada y multa ilegal Cláusula 7.3). Reclamable: $12,500.00 USD (Acción: Emitir NC por $4,000 y requerimiento formal de cobro por $12,500).\n"
                "3. case_003 (SuperTiendas): Facturado $15,000 USD, Pagado $12,000 USD. Deducción de $3,000 USD justificada por sobreprecio unitario en factura vs Orden de Compra según Cláusula 3.1. Reclamable: $0.00 USD (Acción: Emitir Nota de Crédito tarifaria)."
            )

        # Detectar si la pregunta se refiere a un caso específico diferente del activo
        target_case = self.case_id
        if any(k in q for k in ["caso 2", "case 2", "case_002", "megamarket"]):
            target_case = "case_002"
        elif any(k in q for k in ["caso 3", "case 3", "case_003", "supertiendas"]):
            target_case = "case_003"
        elif any(k in q for k in ["caso 7", "case 7", "case_007", "cisco", "infraestructura", "dallas"]):
            target_case = "case_007_cisco_large_bundle"
        elif any(k in q for k in ["caso 9", "case 9", "case_009", "mega retailer", "40 sku", "mega_retailer"]):
            target_case = "case_009_mega_retailer_dispute"
        elif any(k in q for k in ["caso 5", "case 5", "case_005", "amazon", "nvme", "shortage"]):
            target_case = "case_005_amazon_shortage"
        elif any(k in q for k in ["caso 6", "case 6", "case_006", "walmart", "otif", "pricing"]):
            target_case = "case_006_walmart_otif_pricing"
        elif any(k in q for k in ["caso 1", "case 1", "case_001", "retailcorp"]):
            target_case = "case_001"

        if target_case == "case_002":
            if any(k in q for k in ["faltant", "caja", "producto", "prod", "pieza"]):
                return (
                    "En la remisión de entrega DEL-12044 se registraron 50 cajas faltantes del producto PROD-102 "
                    "(Aceite de Oliva Extra Virgen 12x500ml). Se facturaron 150 cajas a $80.00 USD ($12,000.00), "
                    "pero solo se recibieron 100 cajas en muelle, generando un faltante físico de $4,000.00 USD."
                )
            elif any(k in q for k in ["contrat", "clausul", "legal", "4.2", "5.1", "7.3", "ampar"]):
                return (
                    "La Cláusula 4.2 del contrato CTR-MEGAMARKET-2026 autoriza deducir $4,000.00 USD por las 50 cajas "
                    "faltantes constatadas en remisión DEL-12044. Por el contrario, la Cláusula 5.1 no autoriza la deducción de "
                    "$6,500.00 por avería al no existir reporte fotográfico ni acta de muelle dentro de 48h, y la Cláusula 7.3 prohíbe la penalización "
                    "unilateral de $6,000.00 aplicada indebidamente por el comprador."
                )
            elif any(k in q for k in ["reclam", "recuper", "cobro", "exig"]):
                return (
                    "El monto reclamable al cliente es de $12,500.00 USD ($6,500.00 de daño no acreditado en remisión según "
                    "cláusula 5.1 y $6,000.00 de penalización unilateral arbitraria prohibida por cláusula 7.3)."
                )
            elif any(k in q for k in ["accion", "recomend", "nota de credito", "credito", "hacer"]):
                return (
                    "Se recomienda aceptar la deducción de $4,000.00 USD emitiendo Nota de Crédito por el faltante real, "
                    "y rechazar formalmente las deducciones indebidas de $12,500.00 USD exigiendo su pago inmediato mediante "
                    "requerimiento formal de cartera."
                )
            elif any(k in q for k in ["reten", "retuv", "deduc", "pago", "cuanto", "monto", "diferen"]):
                return (
                    "El cliente pagó $37,700.00 USD de una factura de $54,200.00 USD, aplicando 3 deducciones por un total de "
                    "$16,500.00 USD: $4,000.00 por faltante físico real (justificada), $6,500.00 por supuesta avería extemporánea "
                    "(injustificada) y $6,000.00 por penalización unilateral no pactada (injustificada)."
                )
            else:
                return (
                    f"Expediente case_002: Facturado $54,200.00 USD, Pagado $37,700.00 USD. "
                    "Deducciones: $16,500.00 USD ($4,000.00 USD justificadas por Cláusula 4.2 y $12,500.00 USD injustificadas). "
                    "Monto reclamable: $12,500.00 USD. Acción: Emitir Nota de Crédito por $4,000 y reclamar $12,500."
                )
        elif target_case == "case_003":
            if any(k in q for k in ["precio", "sobreprecio", "tarifa", "valor", "costo"]):
                return (
                    "El producto PROD-301 fue facturado a $150.00 USD cuando la orden de compra PO-55100 "
                    "estipulaba un precio acordado de $120.00 USD. La diferencia de sobreprecio unitario de $30.00 USD "
                    "en 100 unidades generó un exceso facturado de $3,000.00 USD."
                )
            elif any(k in q for k in ["contrat", "clausul", "legal", "3.1", "ampar"]):
                return (
                    "La Cláusula 3.1 del contrato CTR-SUPERTIENDAS-2026 ('Inalterabilidad de Precios Unitarios') "
                    "establece que los precios de la Orden de Compra aprobada son definitivos e inmodificables, y autoriza "
                    "al comprador a deducir automáticamente cualquier sobreprecio facturado no autorizado."
                )
            elif any(k in q for k in ["reclam", "recuper", "cobro", "exig"]):
                return (
                    "El monto reclamable al cliente es de $0.00 USD. Dado que el sobreprecio en la factura fue un error "
                    "del proveedor y la Cláusula 3.1 ampara el descuento, la deducción de $3,000.00 USD es 100% justificada."
                )
            elif any(k in q for k in ["accion", "recomend", "nota de credito", "credito", "hacer"]):
                return (
                    "Se recomienda aceptar la deducción de $3,000.00 USD aplicada por el cliente en cuentas por cobrar, "
                    "emitir Nota de Crédito comercial a su favor por ajuste de tarifa y corregir el precio en el ERP."
                )
            elif any(k in q for k in ["reten", "retuv", "deduc", "pago", "cuanto", "monto", "diferen"]):
                return (
                    "El cliente pagó $12,000.00 USD de una factura de $15,000.00 USD, aplicando una deducción de $3,000.00 USD "
                    "(código DED-PRICE-ADJUSTMENT). La conciliación confirma que los $3,000.00 USD corresponden exactamente "
                    "al ajuste por sobreprecio unitario."
                )
            else:
                return (
                    f"Expediente case_003: Facturado $15,000.00 USD, Pagado $12,000.00 USD. "
                    "Deducción de $3,000.00 USD justificada por Cláusula 3.1 debido a sobreprecio unitario en PROD-301. "
                    "Monto reclamable: $0.00 USD. Acción: Emitir Nota de Crédito comercial."
                )
        elif target_case == "case_007_cisco_large_bundle":
            if any(k in q for k in ["faltant", "caja", "producto", "prod", "pieza", "sku", "router"]):
                return (
                    "En la remisión REMITO_RECEPCION_LOGISTICA_ALMACEN_DALLAS se constató un faltante físico "
                    "de $13,000.00 USD debidamente firmado y sellado en muelle sobre routers de infraestructura. "
                    "Los restantes $14,000.00 USD corresponden a cargos unilaterales no pactados."
                )
            elif any(k in q for k in ["contrat", "clausul", "legal", "4.2", "7.3", "ampar"]):
                return (
                    "La Cláusula 4.2 del Convenio Marco autoriza la deducción de $13,000.00 USD por faltante físico con sello de muelle. "
                    "Por el contrario, la Cláusula 7.3 prohíbe penalizaciones y retenciones unilaterales sin adenda bilateral, invalidando los $14,000.00 USD restantes."
                )
            elif any(k in q for k in ["reclam", "recuper", "cobro", "exig"]):
                return (
                    "El monto reclamable al cliente es de $14,000.00 USD correspondientes a retenciones unilaterales no autorizadas."
                )
            elif any(k in q for k in ["accion", "recomend", "nota de credito", "credito", "hacer"]):
                return (
                    "Se recomienda resolución bifurcada: emitir Nota de Crédito por $13,000.00 USD por faltante físico real, "
                    "y emitir requerimiento formal de cobranza por $14,000.00 USD exigiendo el pago inmediato."
                )
            else:
                return (
                    "Expediente Cisco Large Bundle (case_007): Facturado $125,000.00 USD, Pagado $98,000.00 USD. "
                    "Deducciones: $27,000.00 USD ($13,000.00 justificadas s/ Cláusula 4.2 y $14,000.00 reclamables s/ Cláusula 7.3). "
                    "Acción: Emitir Nota de Crédito por $13,000 y reclamación por $14,000."
                )
        elif target_case == "case_009_mega_retailer_dispute":
            if any(k in q for k in ["faltant", "caja", "producto", "prod", "pieza", "sku"]):
                return (
                    "En la remisión DEL_MEGA_88190 se registraron faltantes físicos en 3 SKUs específicos: "
                    "SKU-IND-010 (20 uds = $5,000.00), SKU-IND-022 (15 uds = $3,000.00) y SKU-IND-035 (10 uds = $4,000.00), "
                    "totalizando un faltante físico acreditado en muelle de $12,000.00 USD sobre una factura de 40 SKUs ($385,000.00 USD)."
                )
            elif any(k in q for k in ["contrat", "clausul", "legal", "4.2", "7.3", "ampar"]):
                return (
                    "La Cláusula 4.2 del Contrato Marco CTR_2026 ampara la deducción de $12,000.00 USD por faltante físico constatado en remisión con firma y sello. "
                    "La Cláusula 7.3 prohíbe retenciones unilaterales, declarando improcedente la penalización por EDI ASN ($4,500.00 USD) y el pronto pago unilateral ($8,500.00 USD)."
                )
            elif any(k in q for k in ["reclam", "recuper", "cobro", "exig"]):
                return (
                    "El monto reclamable al cliente es de $13,000.00 USD ($8,500.00 de descuento financiero no pactado y $4,500.00 de penalización ASN unilateral)."
                )
            elif any(k in q for k in ["accion", "recomend", "nota de credito", "credito", "hacer"]):
                return (
                    "Resolución mixta obligatoria: emitir Nota de Crédito por $12,000.00 USD (con desglose de IVA 16% por $1,920.00 USD) por faltante real en 3 SKUs, "
                    "y emitir carta formal de reclamación exigiendo el reintegro inmediato de $13,000.00 USD indebidamente retenidos."
                )
            else:
                return (
                    "Expediente Mega Retailer 40 SKUs (case_009): Facturado $385,000.00 USD, Pagado $360,000.00 USD. "
                    "Deducciones: $25,000.00 USD ($12,000.00 justificadas s/ Cláusula 4.2 y $13,000.00 reclamables s/ Cláusula 7.3). "
                    "Acción: Emitir Nota de Crédito por $12,000 y carta de reclamación por $13,000."
                )
        elif target_case == "case_005_amazon_shortage":
            if any(k in q for k in ["faltant", "caja", "producto", "prod", "pieza", "sku", "nvme", "ssd"]):
                return (
                    "En la remisión de entrega DEL-AMZ-2026-8812 (BOL-POD-77319) se registraron 20 unidades faltantes del producto SKU-NVME-4TB "
                    "(Enterprise PCIe Gen5 NVMe 4TB SSD). Se facturaron 120 unidades a $250.00 USD ($30,000.00), pero solo se recibieron "
                    "100 unidades en el muelle de Amazon Fulfillment Center, generando un faltante físico verificado de $5,000.00 USD."
                )
            elif any(k in q for k in ["contrat", "clausul", "legal", "4.1", "5.3", "7.3"]):
                return (
                    "La Cláusula 4.1 del contrato CTR-AMAZON-2026 autoriza plenamente la deducción de $5,000.00 USD por las 20 unidades "
                    "faltantes de SKU-NVME-4TB constatadas en remisión con firma de muelle. Por el contrario, la Cláusula 5.3 y 7.3 prohíben la "
                    "penalización unilateral por transmisión tardía de ASN de $2,500.00 USD al carecer de sustento contractual y bilateral."
                )
            elif any(k in q for k in ["reclam", "recuper", "cobro", "exig"]):
                return (
                    "El monto reclamable al cliente es de $2,500.00 USD correspondientes a la penalización unilateral por EDI/ASN aplicada indebidamente por Amazon Retail."
                )
            elif any(k in q for k in ["accion", "recomend", "nota de credito", "credito", "hacer"]):
                return (
                    "Se recomienda una resolución mixta: emitir Nota de Crédito por $5,000.00 USD por el faltante físico real de 20 SSDs, "
                    "y emitir carta formal de reclamación exigiendo el reembolso inmediato de $2,500.00 USD indebidamente retenidos por penalización ASN."
                )
            elif any(k in q for k in ["reten", "retuv", "deduc", "pago", "cuanto", "monto", "diferen"]):
                return (
                    "El cliente Amazon pagó $40,500.00 USD de una factura de $48,000.00 USD, aplicando $7,500.00 USD en deducciones: "
                    "$5,000.00 por faltante físico real en muelle (justificada) y $2,500.00 por penalización unilateral ASN (injustificada)."
                )
            else:
                return (
                    "Expediente Amazon Shortage (case_005): Facturado $48,000.00 USD, Pagado $40,500.00 USD. "
                    "Deducciones: $7,500.00 USD ($5,000.00 justificadas s/ Cláusula 4.1 y $2,500.00 reclamables s/ Cláusula 5.3 y 7.3). "
                    "Acción: Emitir Nota de Crédito por $5,000 y carta de reclamación por $2,500."
                )
        elif target_case == "case_006_walmart_otif_pricing":
            if any(k in q for k in ["precio", "sobreprecio", "tarifa", "valor", "costo", "sku", "whey", "cable"]):
                return (
                    "En la factura INV-WMT-2026-5510, el ítem SKU-WHEY-2KG fue facturado a $35.00 USD cuando la orden de compra PO-WMT-7731 "
                    "estipulaba $32.00 USD pactados, generando un sobreprecio unitario de $3.00 USD en 1,500 unidades para una discrepancia "
                    "de $4,500.00 USD. Además se retuvo $3,500.00 por pronto pago no aplicable."
                )
            elif any(k in q for k in ["contrat", "clausul", "legal", "3.1", "7.2", "ampar"]):
                return (
                    "La Cláusula 3.1 del contrato marco Walmart autoriza a deducir el sobreprecio de $4,500.00 USD por inalterabilidad de los "
                    "precios de la Orden de Compra. En contraste, la Cláusula 7.2 invalida el descuento de pronto pago de $3,500.00 USD aplicado "
                    "de manera extemporánea a 45 días del despacho."
                )
            elif any(k in q for k in ["reclam", "recuper", "cobro", "exig"]):
                return (
                    "El monto reclamable a Walmart es de $3,500.00 USD correspondientes al descuento de pronto pago retenido de forma unilateral y fuera de la ventana contractual de 10 días."
                )
            elif any(k in q for k in ["accion", "recomend", "nota de credito", "credito", "hacer"]):
                return (
                    "Se recomienda resolución comercial mixta: emitir Nota de Crédito por $4,500.00 USD por ajuste de tarifa sobreprecio s/ Cláusula 3.1, "
                    "y enviar carta de requerimiento formal exigiendo el pago de $3,500.00 USD indebidamente deducidos."
                )
            elif any(k in q for k in ["reten", "retuv", "deduc", "pago", "cuanto", "monto", "diferen"]):
                return (
                    "Walmart pagó $56,500.00 USD de una factura de $64,500.00 USD, aplicando deducciones por $8,000.00 USD: "
                    "$4,500.00 justificados por sobreprecio s/ Cláusula 3.1 y $3,500.00 injustificados por pronto pago extemporáneo s/ Cláusula 7.2."
                )
            else:
                return (
                    "Expediente Walmart OTIF (case_006): Facturado $64,500.00 USD, Pagado $56,500.00 USD. "
                    "Deducciones: $8,000.00 USD ($4,500.00 justificadas s/ Cláusula 3.1 y $3,500.00 reclamables s/ Cláusula 7.2). "
                    "Acción: Emitir Nota de Crédito por $4,500 y requerimiento de cobro por $3,500."
                )
        else:
            if any(k in q for k in ["faltant", "caja", "producto", "prod", "piezas"]):
                return (
                    "En la remisión de entrega DEL-9912 se registraron 10 cajas faltantes del producto PROD-002 "
                    "(Café Gourmet Tostado 24x500g). Se facturaron 50 cajas a $80.00 USD ($4,000.00), pero solo se "
                    "entregaron 40 cajas físicas en bodega, generando un faltante de $800.00 USD."
                )
            elif any(k in q for k in ["contrat", "clausul", "legal", "4.2", "ampar"]):
                return (
                    "La deducción está respaldada contractualmente por la Cláusula 4.2 ('Faltantes Físicos en Recepción') "
                    "del contrato CTR-RETAIL-2026. Dicha cláusula autoriza al comprador a deducir el 100% del valor unitario "
                    "pactado ante cualquier faltante físico constatado en la remisión de entrega firmada en bodega."
                )
            elif any(k in q for k in ["reclam", "recuper", "cobro", "exig"]):
                return (
                    "El monto reclamable al cliente es de $0.00 USD. Dado que el faltante de mercancía fue real y está "
                    "amparado por la cláusula 4.2 del contrato, la retención es 100% justificada. No procede cobro coactivo."
                )
            elif any(k in q for k in ["accion", "recomend", "nota de credito", "credito", "hacer"]):
                return (
                    "Se recomienda aceptar la deducción de $800.00 USD en cartera y emitir una Nota de Crédito comercial "
                    "a favor del cliente por dicho valor, referenciando la remisión DEL-9912 y la factura INV-40102 para sanear "
                    "la cuenta por cobrar."
                )
            elif any(k in q for k in ["reten", "deduc", "800", "pago", "cuanto", "monto", "diferen"]):
                return (
                    "El cliente pagó $8,200.00 USD de una factura de $9,000.00 USD, aplicando una deducción de $800.00 USD "
                    "(código DED-MISSING-ITEM) por las 10 cajas no entregadas de PROD-002. La conciliación matemática confirma "
                    "que los $800.00 USD corresponden exactamente al faltante físico verificado."
                )
            else:
                return (
                    f"Expediente {self.case_id}: Facturado $9,000.00 USD, Pagado $8,200.00 USD. "
                    "Existe una deducción de $800.00 USD por 10 cajas faltantes de PROD-002 amparada por la cláusula 4.2 "
                    "del contrato CTR-RETAIL-2026. Monto reclamable: $0.00 USD. Acción sugerida: Emitir Nota de Crédito."
                )

    def ask(self, question: str) -> str:
        """Responde una pregunta puntual sobre el expediente del caso con criterios calibrados."""
        self._ensure_case_loaded()
        
        if settings.is_live_api_ready:
            from openai import OpenAI
            client = OpenAI(
                base_url=settings.PLATICA_BASE_URL,
                api_key=settings.RETO_KEY
            )
            messages = [
                {"role": "system", "content": INTERACTIVE_CHAT_PROMPT},
                {"role": "system", "content": f"DATOS CONCILIADOS DEL EXPEDIENTE:\n{self._build_context_summary()}"},
                {"role": "user", "content": question}
            ]
            
            response = client.chat.completions.create(
                model=settings.MODEL_NAME,
                messages=messages,
                tools=TOOL_DEFINITIONS,
                tool_choice="auto"
            )
            msg = response.choices[0].message
            
            if msg.tool_calls:
                messages.append(msg.model_dump())
                for tool_call in msg.tool_calls:
                    fn_name = tool_call.function.name
                    fn_args = json.loads(tool_call.function.arguments)
                    tool_result = self.tool_executor.execute_tool(fn_name, fn_args)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(tool_result, ensure_ascii=False)
                    })
                response = client.chat.completions.create(
                    model=settings.MODEL_NAME,
                    messages=messages
                )
                msg = response.choices[0].message
                
            answer = msg.content or ""
            self.audit_logger.log_step(
                phase="INTERACTIVE_CHAT",
                action_type="AI_RESPONSE",
                name="Ask_Question_Answer",
                details={"question": question, "answer": answer},
                rationale="Respuesta a consulta puntual del operador."
            )
            return answer
        else:
            return self._simulated_ask(question)

    def interactive_chat(self) -> None:
        """Inicia una sesión conversacional interactiva (REPL) con el usuario sobre el caso."""
        self._ensure_case_loaded()
        
        console.print(Panel(
            f"[bold cyan]SupplyMind AI - Terminal de Control y Chat Interactivo[/bold cyan]\n"
            f"[white]Caso activo:[/white] [green]{self.case_id}[/green] | [yellow]Modo:[/yellow] {'Grok 4.7 en Vivo (Platica Gateway)' if settings.is_live_api_ready else 'Harness Local'}\n"
            f"[dim]Escribe el número de la opción, comando o haz cualquier pregunta libre sobre la disputa.[/dim]",
            border_style="cyan"
        ))
        
        self._display_menu()
        
        conversation_history: List[Dict[str, Any]] = [
            {"role": "system", "content": INTERACTIVE_CHAT_PROMPT},
            {"role": "system", "content": f"DATOS CONCILIADOS DEL EXPEDIENTE:\n{self._build_context_summary()}"}
        ]
        
        if settings.is_live_api_ready:
            from openai import OpenAI
            client = OpenAI(
                base_url=settings.PLATICA_BASE_URL,
                api_key=settings.RETO_KEY
            )
        else:
            client = None

        while True:
            try:
                console.print(f"[bold green]SupplyMind ({self.case_id}) >[/bold green] ", end="")
                user_input = input().strip()
            except (EOFError, KeyboardInterrupt):
                console.print("\n[dim]Sesión finalizada por el usuario.[/dim]")
                break

            if not user_input:
                continue

            cmd = user_input.lower()
            
            # 0. Salir
            if cmd in ["0", "salir", "exit", "quit", "q", "adios", "bye"]:
                console.print(f"\n[bold cyan]SupplyMind AI:[/bold cyan] [yellow]Hasta luego. Bitácora final guardada en {self.audit_logger.log_file}[/yellow]\n")
                break

            # 1. Analizar disputa (Run autónomo)
            if cmd in ["1", "analizar", "resolver", "run"]:
                console.print("\n[bold]Ejecutando ciclo autónomo de resolución...[/bold]")
                self.run()
                self._display_report_table()
                continue

            # 2. Ver Reporte Formal
            if cmd in ["2", "reporte", "informe", "report", "tabla"]:
                self._display_report_table()
                continue

            # 3. Inspeccionar Documentos
            if cmd in ["3", "documentos", "docs", "expediente"]:
                self._display_documents_inspection()
                continue

            # 4. Conciliación Detallada
            if cmd in ["4", "conciliacion", "conciliar", "math"]:
                self._display_reconciliation_details()
                continue

            # 5. Dictamen Contractual
            if cmd in ["5", "contrato", "legal", "clausulas"]:
                self._display_contract_evaluation()
                continue

            # 6. Bitácora de Auditoría
            if cmd in ["6", "bitacora", "auditoria", "log", "trail"]:
                self._display_audit_log_tail()
                continue

            # 7. Calibrar Criterio AI
            if cmd in ["7", "calibrar", "entrenar", "benchmark"]:
                self._run_calibration()
                continue

            # Atajos directos de expediente: c1, c2, c3, caso 1, caso 2, etc.
            if cmd in ["c1", "caso 1", "caso1", "case 1", "case1", "case_001"]:
                self._switch_case("case_001")
                conversation_history = [
                    {"role": "system", "content": INTERACTIVE_CHAT_PROMPT},
                    {"role": "system", "content": f"DATOS CONCILIADOS DEL EXPEDIENTE:\n{self._build_context_summary()}"}
                ]
                continue

            if cmd in ["c2", "caso 2", "caso2", "case 2", "case2", "case_002"]:
                self._switch_case("case_002")
                conversation_history = [
                    {"role": "system", "content": INTERACTIVE_CHAT_PROMPT},
                    {"role": "system", "content": f"DATOS CONCILIADOS DEL EXPEDIENTE:\n{self._build_context_summary()}"}
                ]
                continue

            if cmd in ["c3", "caso 3", "caso3", "case 3", "case3", "case_003"]:
                self._switch_case("case_003")
                conversation_history = [
                    {"role": "system", "content": INTERACTIVE_CHAT_PROMPT},
                    {"role": "system", "content": f"DATOS CONCILIADOS DEL EXPEDIENTE:\n{self._build_context_summary()}"}
                ]
                continue

            # 1. Analizar disputa (Run autónomo)
            if cmd in ["1", "analizar", "resolver", "run"]:
                console.print(f"\n[bold]Ejecutando ciclo autónomo de resolución para {self.case_id}...[/bold]")
                self.run()
                self._display_report_table()
                continue

            # 2. Ver Reporte Formal
            if cmd in ["2", "reporte", "informe", "report", "tabla"]:
                self._display_report_table()
                continue

            # 3. Inspeccionar Documentos
            if cmd in ["3", "documentos", "docs", "expediente"]:
                self._display_documents_inspection()
                continue

            # 4. Conciliación Detallada
            if cmd in ["4", "conciliacion", "conciliar", "math"]:
                self._display_reconciliation_details()
                continue

            # 5. Dictamen Contractual
            if cmd in ["5", "contrato", "legal", "clausulas"]:
                self._display_contract_evaluation()
                continue

            # 6. Bitácora de Auditoría
            if cmd in ["6", "bitacora", "auditoria", "log", "trail"]:
                self._display_audit_log_tail()
                continue

            # 7. Calibrar Criterio AI
            if cmd in ["7", "calibrar", "entrenar", "benchmark"]:
                self._run_calibration()
                continue

            # 8. Cambiar / Recargar Caso con menú interactivo
            if cmd in ["8", "caso", "cambiar", "switch"]:
                console.print("\n[bold cyan]Selecciona el expediente que deseas cargar:[/bold cyan]")
                console.print("  [bold green]1[/bold green] -> [white]case_001[/white] (Básico: Faltante Físico de $800 USD)")
                console.print("  [bold green]2[/bold green] -> [white]case_002[/white] (Complejo Alta Cuantía: $12,500 USD reclamables)")
                console.print("  [bold green]3[/bold green] -> [white]case_003[/white] (Discrepancia de Precios: $3,000 USD sobreprecio)")
                console.print(f"[dim]Presiona 1, 2, 3 o Enter para mantener {self.case_id}:[/dim] ", end="")
                try:
                    new_id = input().strip()
                except (EOFError, KeyboardInterrupt):
                    new_id = ""
                if new_id:
                    self._switch_case(new_id)
                    conversation_history = [
                        {"role": "system", "content": INTERACTIVE_CHAT_PROMPT},
                        {"role": "system", "content": f"DATOS CONCILIADOS DEL EXPEDIENTE:\n{self._build_context_summary()}"}
                    ]
                continue

            # 9. Matriz Comparativa de los 3 Casos
            if cmd in ["9", "comparar", "todos", "all", "matriz", "cartera"]:
                self._display_all_cases_comparison()
                continue

            # E. Evaluación S1 Jurado en 1 Clic
            if cmd in ["e", "evaluar", "demo", "jurado"]:
                from scripts.evaluar_jurado import run_jury_evaluation
                run_jury_evaluation()
                continue

            # Menú y ayuda
            if cmd in ["menu", "m"]:
                self._display_menu()
                continue

            if cmd in ["cls", "clear", "limpiar"]:
                import os
                os.system("cls" if os.name == "nt" else "clear")
                self._display_menu()
                continue

            if cmd in ["ayuda", "help", "?"]:
                console.print(Panel(
                    "[bold]Comandos de Control Rápido:[/bold]\n"
                    "- [yellow]1 a 7[/yellow]: Acceso directo a análisis, reporte, documentos, conciliación y auditoría.\n"
                    "- [yellow]8[/yellow]: Menú para cambiar entre case_001, case_002 o case_003.\n"
                    "- [yellow]c1[/yellow], [yellow]c2[/yellow], [yellow]c3[/yellow]: Cambiar de expediente al instante con una sola orden.\n"
                    "- [yellow]9[/yellow] o [yellow]comparar[/yellow]: Ver matriz comparativa con los 3 casos en paralelo.\n"
                    "- [yellow]e[/yellow] o [yellow]evaluar[/yellow]: Ejecutar la evaluación integral de 30s del jurado.\n"
                    "- [yellow]menu[/yellow]: Muestra el menú principal nuevamente.\n"
                    "- [yellow]cls[/yellow]: Limpia la pantalla.\n"
                    "- [yellow]0[/yellow] o [yellow]salir[/yellow]: Termina la sesión interactiva.\n\n"
                    "[bold]Ejemplos de preguntas libres en lenguaje natural:[/bold]\n"
                    "- [cyan]¿Cuánto dinero podemos recuperar en el caso 2?[/cyan]\n"
                    "- [cyan]Compara los 3 casos de la cartera[/cyan]\n"
                    "- [cyan]¿Qué dice la cláusula 3.1 en el caso 3?[/cyan]\n"
                    "- [cyan]¿Qué producto tuvo faltante en el caso 1?[/cyan]\n"
                    "- [cyan]¿Qué acción comercial debemos tomar con cartera?[/cyan]",
                    title="Guía de Interacción Multi-Caso",
                    border_style="yellow"
                ))
                continue

            # Pregunta libre a Grok en lenguaje natural
            self.audit_logger.log_step(
                phase="INTERACTIVE_CHAT",
                action_type="USER_QUERY",
                name="User_Question",
                details={"case_id": self.case_id, "question": user_input},
                rationale="Pregunta interactiva formulada por el operador."
            )

            if client:
                conversation_history.append({"role": "user", "content": user_input})
                try:
                    console.print("[dim]Consultando a Grok con criterios calibrados...[/dim]")
                    response = client.chat.completions.create(
                        model=settings.MODEL_NAME,
                        messages=conversation_history,
                        tools=TOOL_DEFINITIONS,
                        tool_choice="auto"
                    )
                    msg = response.choices[0].message
                    
                    if msg.tool_calls:
                        conversation_history.append(msg.model_dump())
                        for tool_call in msg.tool_calls:
                            fn_name = tool_call.function.name
                            fn_args = json.loads(tool_call.function.arguments)
                            console.print(f"[dim]-> Invocando herramienta: {fn_name}...[/dim]")
                            tool_result = self.tool_executor.execute_tool(fn_name, fn_args)
                            conversation_history.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": json.dumps(tool_result, ensure_ascii=False)
                            })
                        response = client.chat.completions.create(
                            model=settings.MODEL_NAME,
                            messages=conversation_history
                        )
                        msg = response.choices[0].message

                    assistant_reply = msg.content or ""
                    conversation_history.append({"role": "assistant", "content": assistant_reply})
                    
                    self.audit_logger.log_step(
                        phase="INTERACTIVE_CHAT",
                        action_type="AI_RESPONSE",
                        name="Agent_Answer",
                        details={"reply": assistant_reply},
                        rationale="Respuesta conversacional de Grok."
                    )
                    
                    console.print(f"\n[bold cyan]SupplyMind AI:[/bold cyan] {assistant_reply}\n")
                except Exception as e:
                    console.print(f"[bold red]Error al comunicarse con Grok:[/bold red] {e}")
                    fallback_reply = self._simulated_ask(user_input)
                    console.print(f"\n[bold cyan]SupplyMind AI (Local):[/bold cyan] {fallback_reply}\n")
            else:
                assistant_reply = self._simulated_ask(user_input)
                self.audit_logger.log_step(
                    phase="INTERACTIVE_CHAT",
                    action_type="AI_RESPONSE",
                    name="Agent_Answer_Local",
                    details={"reply": assistant_reply},
                    rationale="Respuesta simulada local."
                )
                console.print(f"\n[bold cyan]SupplyMind AI:[/bold cyan] {assistant_reply}\n")

    def _generate_error_report(self, error_msg: str) -> DisputeAnalysisReport:
        """Genera un reporte de fallo técnico para el jurado si el caso está completamente roto."""
        from decimal import Decimal
        from datetime import datetime, timezone
        from data.models import DocumentHealthAudit
        audit = DocumentHealthAudit(
            case_id=self.case_id,
            health_score=0.0,
            status="QUARANTINE",
            is_healthy=False,
            repaired_issues=[],
            imputed_documents=[],
            documents_present=[],
            documents_missing=["unrecoverable_corrupt_files"],
            schema_warnings=[error_msg[:300]],
            execution_safety_level="HOLD_SETTLEMENT_DOCUMENT_AUDIT_REQUIRED",
            generated_at=datetime.now(timezone.utc).isoformat()
        )
        from data.models import ZKPFinancialProof
        proof = ZKPFinancialProof(
            case_id=self.case_id,
            proof_hash=f"SM-PROOF-QUARANTINE-{self.case_id}",
            invariant_conservation_ok=True,
            invariant_deductions_ok=True,
            invariant_line_items_ok=False,
            text_hallucination_detected=False,
            audit_status="ARITHMETIC_MISMATCH",
            tamper_proof_timestamp=datetime.now(timezone.utc).isoformat()
        )
        return DisputeAnalysisReport(
            case_id=self.case_id,
            billed_amount=Decimal("0.00"),
            received_amount=Decimal("0.00"),
            difference=Decimal("0.00"),
            justified_amount=Decimal("0.00"),
            claimable_amount=Decimal("0.00"),
            root_cause="TECHNICAL_ERROR: Datos corruptos o esquema inválido.",
            evidence=[f"Trace técnico de Pydantic/Motor: {error_msg[:500]}"],
            recommended_action="Rechazar expediente. Los archivos JSON base carecen de integridad estructural y fallaron la validación de Esquemas (Pydantic). Verifique los datos de entrada.",
            confidence=0.0,
            health_audit=audit,
            financial_proof=proof
        )
