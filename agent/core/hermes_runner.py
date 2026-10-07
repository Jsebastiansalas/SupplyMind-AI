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

    def _display_menu(self) -> None:
        """Despliega el menú interactivo con todas las opciones disponibles."""
        menu_text = (
            "[bold cyan]1[/bold cyan]  [bold white]🧠 Analizar Disputa[/bold white]       [dim]-> Ejecutar ciclo autónomo ReAct con Grok[/dim]\n"
            "[bold cyan]2[/bold cyan]  [bold white]📊 Ver Reporte Formal[/bold white]       [dim]-> Cuadro ejecutivo con causa raíz y acción[/dim]\n"
            "[bold cyan]3[/bold cyan]  [bold white]📂 Inspeccionar Documentos[/bold white]  [dim]-> Ver Factura, OC, Remisión, Pago y Contrato[/dim]\n"
            "[bold cyan]4[/bold cyan]  [bold white]🔢 Conciliación Detallada[/bold white]   [dim]-> Auditoría línea a línea en Decimal[/dim]\n"
            "[bold cyan]5[/bold cyan]  [bold white]⚖️  Dictamen Contractual[/bold white]     [dim]-> Cláusulas aplicables y amparo jurídico[/dim]\n"
            "[bold cyan]6[/bold cyan]  [bold white]📜 Bitácora de Auditoría[/bold white]    [dim]-> Historial de trazabilidad JSONL[/dim]\n"
            "[bold cyan]7[/bold cyan]  [bold white]🎯 Calibrar Criterio AI[/bold white]     [dim]-> Benchmark de entrenamiento (< $1.00 USD)[/dim]\n"
            "[bold cyan]8[/bold cyan]  [bold white]🔄 Cambiar / Recargar Caso[/bold white]  [dim]-> Cambiar expediente activo actual[/dim]\n"
            "[bold cyan]?[/bold cyan]  [bold white]💡 Ayuda[/bold white]                    [dim]-> Preguntas sugeridas y atajos[/dim]\n"
            "[bold cyan]0[/bold cyan]  [bold white]🚪 Salir[/bold white]                    [dim]-> Finalizar sesión interactiva[/dim]\n\n"
            "[italic dim]O escribe cualquier pregunta en lenguaje natural directamente a Grok.[/italic dim]"
        )
        console.print(Panel(
            menu_text,
            title=f"[bold green]SupplyMind AI - Menú de Control Interactivo ({self.case_id})[/bold green]",
            border_style="cyan"
        ))

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
        """Cambia el caso activo del expediente."""
        new_case_id = new_case_id.strip()
        if not new_case_id:
            return
        self.case_id = new_case_id
        self.objective = f"Analiza la disputa {new_case_id}"
        self.state = DisputeState(case_id=new_case_id, objective=self.objective)
        self.audit_logger = AuditLogger(case_id=new_case_id)
        self.tool_executor = ToolExecutor(state=self.state, audit_logger=self.audit_logger)
        self._ensure_case_loaded()
        console.print(f"[bold green][OK] Caso activo cambiado a:[/bold green] [cyan]{new_case_id}[/cyan]\n")

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
                console.print(f"[bold green]SupplyMind [{self.case_id}] >[/bold green] ", end="")
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

            # 8. Cambiar / Recargar Caso
            if cmd in ["8", "caso", "cambiar"]:
                console.print(f"[bold cyan]Ingresa el ID del caso a cargar (actual: {self.case_id}):[/bold cyan] ", end="")
                new_id = input().strip()
                if new_id:
                    self._switch_case(new_id)
                    # Actualizar historial
                    conversation_history = [
                        {"role": "system", "content": INTERACTIVE_CHAT_PROMPT},
                        {"role": "system", "content": f"DATOS CONCILIADOS DEL EXPEDIENTE:\n{self._build_context_summary()}"}
                    ]
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
                    "[bold]Comandos Rápidos:[/bold]\n"
                    "- [yellow]1[/yellow] a [yellow]8[/yellow]: Acceso directo a las funciones del menú.\n"
                    "- [yellow]menu[/yellow]: Muestra el menú principal nuevamente.\n"
                    "- [yellow]cls[/yellow]: Limpia la pantalla.\n"
                    "- [yellow]0[/yellow] o [yellow]salir[/yellow]: Termina la sesión.\n\n"
                    "[bold]Ejemplos de preguntas libres en lenguaje natural:[/bold]\n"
                    "- [cyan]¿Por qué el cliente retuvo $800 dólares?[/cyan]\n"
                    "- [cyan]¿Qué dice la cláusula 4.2 del contrato comercial?[/cyan]\n"
                    "- [cyan]¿Qué producto tuvo faltante y cuántas cajas no llegaron?[/cyan]\n"
                    "- [cyan]¿Cuánto dinero podemos recuperar o reclamar legalmente?[/cyan]\n"
                    "- [cyan]¿Qué acción comercial debemos tomar con cartera?[/cyan]",
                    title="Guía de Interacción y Comandos",
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


