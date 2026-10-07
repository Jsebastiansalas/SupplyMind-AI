import json
import time
from typing import Dict, Any, List, Optional
from rich.console import Console
from rich.panel import Panel

from config.settings import settings
from agent.core.state import DisputeState, ProcessStatus
from agent.memory.audit_logger import AuditLogger
from agent.planner.prompts import SYSTEM_PROMPT
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
