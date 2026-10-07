import json
import time
from typing import Dict, Any, List, Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from config.settings import settings
from agent.core.state import DisputeState, ProcessStatus
from agent.memory.audit_logger import AuditLogger
from agent.planner.prompts import SYSTEM_PROMPT, INTERACTIVE_CHAT_PROMPT
from agent.tools.registry import TOOL_DEFINITIONS, ToolExecutor
from data.models import DisputeAnalysisReport

console = Console(highlight=False)

class HermesRunner:
    """
    Orquestador del agente SupplyMind AI sobre la arquitectura Hermes Agent.
    Soporta:
    - Modo Live: Conexión directa a Grok a través del gateway de Platica (https://api.reto.pltk.mx/v1).
    - Modo Simulado / Harness Local: Motor ReAct autónomo local para desarrollo y pruebas.
    """
    def __init__(self, case_id: str, objective: Optional[str] = None):
        self.case_id = case_id
        self.objective = objective or f"Analiza la disputa {case_id}"
        self.state = DisputeState(case_id=case_id, objective=self.objective)
        self.audit_logger = AuditLogger(case_id=case_id)
        self.tool_executor = ToolExecutor(state=self.state, audit_logger=self.audit_logger)
        
    def run(self) -> DisputeAnalysisReport:
        """Ejecuta el ciclo de resolución autónomo de la disputa."""
        console.print(Panel(
            f"[bold green]SupplyMind AI - Hermes Agent Runner[/bold green]\n"
            f"[cyan]Caso:[/cyan] {self.case_id} | [cyan]Objetivo:[/cyan] {self.objective}\n"
            f"[yellow]Modo:[/yellow] {'En Vivo (Grok / Platica Gateway)' if settings.is_live_api_ready else 'Harness Local / Simulador ReAct'}",
            border_style="green"
        ))
        
        self.audit_logger.log_step(
            phase="INITIALIZATION",
            action_type="THOUGHT",
            name="Objective_Received",
            details={"case_id": self.case_id, "objective": self.objective},
            rationale="Iniciando ciclo autónomo de análisis de disputa comercial."
        )
        
        if settings.is_live_api_ready:
            return self._run_live_hermes()
        else:
            return self._run_simulated_hermes()

    def _run_live_hermes(self) -> DisputeAnalysisReport:
        """Bucle ReAct contra el gateway oficial de Platica Grok."""
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
            
            response = client.chat.completions.create(
                model=settings.MODEL_NAME,
                messages=messages,
                tools=TOOL_DEFINITIONS,
                tool_choice="auto"
            )
            
            msg = response.choices[0].message
            messages.append(msg.model_dump())
            
            if msg.content:
                console.print(f"[bold blue]SupplyMind AI:[/bold blue] {msg.content}")
                
            if not msg.tool_calls:
                break
                
            for tool_call in msg.tool_calls:
                fn_name = tool_call.function.name
                fn_args = json.loads(tool_call.function.arguments)
                
                console.print(f"[bold yellow]-> Invocando herramienta:[/bold yellow] [magenta]{fn_name}[/magenta] con [dim]{fn_args}[/dim]")
                tool_result = self.tool_executor.execute_tool(fn_name, fn_args)
                
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(tool_result, ensure_ascii=False)
                })
                
            if self.state.final_report:
                break
                
        if not self.state.final_report:
            raise RuntimeError("El agente no completó la generación del informe final.")
            
        return self.state.final_report

    def _run_simulated_hermes(self) -> DisputeAnalysisReport:
        """
        Bucle ReAct determinístico para desarrollo, CI y pruebas locales.
        Emula la secuencia de razonamiento y llamadas a herramientas de Hermes.
        """
        # Turno 1: Inspeccionar expediente
        console.print("[cyan][Pensamiento Hermes][/cyan]: Para analizar la disputa, primero debo inspeccionar los documentos comerciales disponibles en el expediente.")
        console.print(f"[bold yellow]-> Hermes Tool Call:[/bold yellow] [magenta]read_dispute_documents[/magenta](case_id='{self.case_id}')")
        self.tool_executor.execute_tool("read_dispute_documents", {"case_id": self.case_id})
        time.sleep(0.1)
        
        # Turno 2: Conciliación física y matemática
        console.print("[cyan][Pensamiento Hermes][/cyan]: Documentos cargados correctamente. Procedo a ejecutar la conciliación matemática determinística.")
        console.print(f"[bold yellow]-> Hermes Tool Call:[/bold yellow] [magenta]execute_reconciliation[/magenta](case_id='{self.case_id}')")
        self.tool_executor.execute_tool("execute_reconciliation", {"case_id": self.case_id})
        time.sleep(0.1)
        
        # Turno 3: Análisis contractual
        console.print("[cyan][Pensamiento Hermes][/cyan]: La conciliación detectó faltante físico de 10 unidades de Producto B por $800 USD. Verifico respaldo contractual.")
        console.print(f"[bold yellow]-> Hermes Tool Call:[/bold yellow] [magenta]evaluate_contract_terms[/magenta](case_id='{self.case_id}')")
        self.tool_executor.execute_tool("evaluate_contract_terms", {"case_id": self.case_id})
        time.sleep(0.1)
        
        # Turno 4: Síntesis y reporte formal
        console.print("[cyan][Pensamiento Hermes][/cyan]: La deducción está amparada por la Cláusula 4.2 debido a la remisión firmada con discrepancia. Genero informe final.")
        console.print("[bold yellow]-> Hermes Tool Call:[/bold yellow] [magenta]generate_final_report[/magenta](...)")
        
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
                    "por dicho valor a favor del cliente Supermercados Éxito / RetailCorp para conciliar y cerrar la factura INV-40102."
                )
            }
        )
        
        if not self.state.final_report:
            raise RuntimeError("Error al generar el reporte en la simulación.")
            
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
                summary_lines.append(f"- Remisión de Entrega: {deliv.delivery_id} (Faltantes: {', '.join(short_items) or 'Ninguno'})")
            if pay:
                deductions_desc = [f"{d.code}: ${d.amount:,.2f} ({d.reason})" for d in pay.deductions]
                summary_lines.append(f"- Pago Recibido: {pay.payment_id} por ${pay.amount_paid:,.2f} (Deducciones: {', '.join(deductions_desc)})")
            if ctr:
                clauses_desc = [f"{c.clause_id} ({c.title})" for c in ctr.clauses]
                summary_lines.append(f"- Contrato Comercial: {ctr.contract_id} (Cláusulas: {', '.join(clauses_desc)})")
                
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
            
        return "\n".join(summary_lines)

    def _display_report_table(self) -> None:
        """Muestra una tabla con el informe de conciliación."""
        if not self.state.final_report:
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

    def _simulated_ask(self, question: str) -> str:
        """Generador determinístico de respuestas locales para pruebas y modo offline."""
        q = question.lower()
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
        elif any(k in q for k in ["reten", "deduc", "800", "pago", "cuanto", "monto", "diferen"]):
            return (
                "El cliente pagó $8,200.00 USD de una factura de $9,000.00 USD, aplicando una deducción de $800.00 USD "
                "(código DED-MISSING-ITEM) por las 10 cajas no entregadas de PROD-002. La conciliación matemática confirma "
                "que los $800.00 USD corresponden exactamente al faltante físico verificado."
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
        else:
            return (
                f"Expediente {self.case_id}: Facturado $9,000.00 USD, Pagado $8,200.00 USD. "
                "Existe una deducción de $800.00 USD por 10 cajas faltantes de PROD-002 amparada por la cláusula 4.2 "
                "del contrato CTR-RETAIL-2026. Monto reclamable: $0.00 USD. Acción sugerida: Emitir Nota de Crédito."
            )

    def ask(self, question: str) -> str:
        """Responde una pregunta puntual sobre el expediente del caso."""
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
            f"[bold cyan]SupplyMind AI - Modo Conversacional Interactivo[/bold cyan]\n"
            f"[white]Caso activo:[/white] [green]{self.case_id}[/green] | [yellow]Modo:[/yellow] {'Grok en Vivo (Platica Gateway)' if settings.is_live_api_ready else 'Harness Local'}\n\n"
            f"[dim]Escribe tus preguntas sobre la factura, remisión, pagos, contrato o recomendaciones.\n"
            f"Comandos útiles: '[bold yellow]reporte[/bold yellow]' (ver cuadro formal), '[bold yellow]ayuda[/bold yellow]' (preguntas sugeridas), '[bold yellow]salir[/bold yellow]' (terminar).[/dim]",
            border_style="cyan"
        ))
        
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
                console.print("[bold green]Tú >[/bold green] ", end="")
                user_input = input().strip()
            except (EOFError, KeyboardInterrupt):
                console.print("\n[dim]Sesión finalizada.[/dim]")
                break

            if not user_input:
                continue

            cmd = user_input.lower()
            if cmd in ["salir", "exit", "quit", "q", "adios", "bye"]:
                console.print(f"\n[bold cyan]SupplyMind AI:[/bold cyan] [yellow]Hasta luego. Bitácora guardada en {self.audit_logger.log_file}[/yellow]\n")
                break

            if cmd in ["reporte", "informe", "report", "tabla"]:
                self._display_report_table()
                continue

            if cmd in ["ayuda", "help", "?"]:
                console.print(Panel(
                    "[bold]Preguntas sugeridas que puedes hacerme:[/bold]\n"
                    "- [cyan]¿Por qué el cliente retuvo $800 dólares?[/cyan]\n"
                    "- [cyan]¿Qué dice la cláusula contractual sobre faltantes?[/cyan]\n"
                    "- [cyan]¿Qué producto tuvo faltante y cuántas cajas?[/cyan]\n"
                    "- [cyan]¿Cuánto dinero podemos recuperar o reclamar legalmente?[/cyan]\n"
                    "- [cyan]¿Qué acción comercial debemos tomar ahora?[/cyan]\n"
                    "- [yellow]reporte[/yellow] (Muestra el cuadro formal de conciliación)",
                    title="Guía de Interacción",
                    border_style="yellow"
                ))
                continue

            # Procesar pregunta
            self.audit_logger.log_step(
                phase="INTERACTIVE_CHAT",
                action_type="USER_QUERY",
                name="User_Question",
                details={"case_id": self.case_id, "question": user_input},
                rationale="Pregunta formulada por el usuario en modo interactivo."
            )

            if client:
                conversation_history.append({"role": "user", "content": user_input})
                try:
                    console.print("[dim]Consultando a Grok...[/dim]")
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

