import sys
import os
from pathlib import Path

# Configuración de salida segura UTF-8 para consola en Windows
if sys.platform == "win32":
    try:
        if sys.stdout.encoding.lower() != "utf-8":
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from agent.core.hermes_runner import HermesRunner
from config.settings import settings

console = Console(highlight=False)

def main():
    args = sys.argv[1:]
    
    # Detectar banderas de modo
    is_interactive = any(a.lower() in ["-i", "--interactive", "chat", "--chat"] for a in args)
    is_ask = any(a.lower() in ["ask", "--ask", "-q", "pregunta"] for a in args)
    is_calibrate = any(a.lower() in ["calibrar", "--calibrar", "benchmark", "--benchmark", "train"] for a in args)
    is_evaluate = any(a.lower() in ["evaluar", "--evaluar", "demo", "--demo", "verify"] for a in args)

    # 0. Modo Evaluación Integral para Jurados
    if is_evaluate:
        from scripts.evaluar_jurado import run_jury_evaluation
        run_jury_evaluation()
        return
    
    # Extraer case_id de argumentos si existe (default: case_001)
    case_id = "case_001"
    for a in args:
        if a.startswith("case_"):
            case_id = a
            break
        elif "case_" in a:
            for part in a.split():
                if part.startswith("case_"):
                    case_id = part
                    break

    runner = HermesRunner(case_id=case_id)

    # 1. Modo Interactivo Conversacional continuo
    if is_interactive:
        runner.interactive_chat()
        return

    # 2. Modo Calibración y Benchmark de Criterio
    if is_calibrate:
        from agent.training.trainer import AgentTrainer
        trainer = AgentTrainer(budget_limit_usd=1.00)
        trainer.run_calibration(case_id=case_id)
        return

    # 3. Modo Consulta Puntual (CLI)
    if is_ask:
        question_parts = [a for a in args if a.lower() not in ["ask", "--ask", "-q", "pregunta"] and not a.startswith("case_")]
        question = " ".join(question_parts) or "¿Por qué existe una diferencia en el pago?"
        console.print(Panel.fit(
            f"[bold cyan]SupplyMind AI - Consulta Puntual[/bold cyan]\n"
            f"[dim]Caso: [green]{case_id}[/green] | Pregunta: [white]{question}[/white][/dim]",
            border_style="cyan"
        ))
        answer = runner.ask(question)
        console.print(f"\n[bold cyan]SupplyMind AI:[/bold cyan] {answer}\n")
        return

    # 4. Modo Análisis Autónomo Formal (Default)
    console.print(Panel.fit(
        "[bold cyan]SupplyMind AI[/bold cyan] - [yellow]Analista Autonomo de Disputas B2B[/yellow]\n"
        "[dim]Reto Agente Platica.mx x Campuslands - Powered by Hermes Agent & Grok[/dim]",
        border_style="cyan"
    ))
    
    objective = None
    if args:
        joined_args = " ".join(args)
        if "analiza" in joined_args.lower() or len(joined_args) > 15:
            objective = joined_args
        else:
            objective = f"Analiza la disputa {case_id}"
    else:
        objective = f"Analiza la disputa {case_id}"
        
    console.print(f"[bold]Iniciando analisis para:[/bold] [green]{case_id}[/green]\n")
    
    runner.objective = objective
    report = runner.run()
    
    # Desplegar reporte formal estructurado
    console.print("\n")
    report_table = Table(title="[bold green]DISPUTE ANALYSIS REPORT[/bold green]", show_header=False, border_style="green")
    report_table.add_column("Campo", style="bold cyan", width=24)
    report_table.add_column("Detalle", style="white")
    
    report_table.add_row("Caso analizado", report.case_id)
    report_table.add_row("Monto facturado", f"${report.billed_amount:,.2f} {report.currency}")
    report_table.add_row("Monto recibido", f"${report.received_amount:,.2f} {report.currency}")
    report_table.add_row("Diferencia", f"[bold red]${report.difference:,.2f} {report.currency}[/bold red]")
    report_table.add_row("Causa encontrada", report.root_cause)
    
    evidence_text = "\n".join([f"- {e}" for e in report.evidence])
    report_table.add_row("Evidencia utilizada", evidence_text)
    
    report_table.add_row("Monto justificado", f"[green]${report.justified_amount:,.2f} {report.currency}[/green]")
    report_table.add_row("Monto reclamable", f"${report.claimable_amount:,.2f} {report.currency}")
    report_table.add_row("Nivel de confianza", f"[bold yellow]{report.confidence * 100:.1f}%[/bold yellow]")
    report_table.add_row("Accion recomendada", f"[bold yellow]{report.recommended_action}[/bold yellow]")
    
    console.print(report_table)
    
    # Confirmación de trazabilidad y bitácora
    log_file = runner.audit_logger.log_file
    console.print(f"\n[dim][OK] Trazabilidad y bitacora de decisiones guardada en: {log_file}[/dim]")
    if runner.state.tokens_in > 0 or runner.state.execution_time_seconds > 0:
        console.print(
            f"[dim]⚡ Inferencia: {runner.state.tokens_in + runner.state.tokens_out:,} tokens "
            f"({runner.state.tokens_in:,} in / {runner.state.tokens_out:,} out) | "
            f"Costo: ${runner.state.estimated_cost_usd:.5f} USD | "
            f"Tiempo: {runner.state.execution_time_seconds:.2f}s[/dim]"
        )
    console.print("[dim]💡 Tip: Para modo interactivo ejecuta:[/dim] [bold cyan]python main.py -i[/bold cyan] [dim]| Para evaluación integral:[/dim] [bold cyan]python main.py evaluar[/bold cyan]\n")

if __name__ == "__main__":
    main()
