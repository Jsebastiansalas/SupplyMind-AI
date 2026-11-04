"""
scripts/demo_real_cases_cognitive_separation.py
Demostración de Ejecución de Casos Reales (DataCo) y Separación Cognitiva:
Muestra cómo el agente decide qué delega a las herramientas deterministas de Python
y qué delega al modelo neuronal Grok-4.7.
"""

import sys
from decimal import Decimal
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from agent.planner.cognitive_router import CognitiveRouter
from agent.core.skynet_runner import SkynetRunner
from tools.document_reader.reader import load_case_documents

console = Console(highlight=False)

REAL_CASES_TO_TEST = [
    ("dataco_real_001_caguas_pelican_kayak", "Pacific NW Outdoor", "Outdoors / Kayak", "$9,999.50", "$500.00", "$599.97"),
    ("dataco_real_002_cleveland_diamondback_cycling", "Midwest Cycling Corp", "Cycling / Bikes", "$11,999.20", "$800.00", "$599.96"),
    ("dataco_real_004_chicago_nike_footwear_overcharge", "Great Lakes Footwear", "Footwear / Nike", "$9,999.00", "$450.00", "$1,000.00"),
]

def run_real_cases_separation_demo():
    console.print(Panel(
        "[bold cyan]SupplyMind AI — Demostración de Casos Reales (DataCo) y Separación Cognitiva[/bold cyan]\n"
        "[dim]Evaluación de dominio real abierto (DOI: 10.17632/8gx2fvg2k6.5) y separación de responsabilidades[/dim]",
        border_style="cyan"
    ))

    summary_table = Table(title="[bold green]RESULTADOS DE AUDITORÍA SOBRE CASOS REALES[/bold green]", border_style="green")
    summary_table.add_column("Caso ID", style="bold white", width=22)
    summary_table.add_column("Comprador Real", style="cyan", width=20)
    summary_table.add_column("Decisión Router", style="bold yellow", width=16)
    summary_table.add_column("Herramientas Python", style="green", width=26)
    summary_table.add_column("Cerebro Grok", style="magenta", width=24)
    summary_table.add_column("Monto Fact.", justify="right", style="white")
    summary_table.add_column("Reclamable", justify="right", style="bold green")
    summary_table.add_column("Justificado", justify="right", style="yellow")
    summary_table.add_column("MAE", justify="right", style="bold green")

    for case_id, buyer, category, exp_billed, exp_claim, exp_just in REAL_CASES_TO_TEST:
        console.print(f"\n[bold yellow]Auditoría del Caso Real:[/bold yellow] [bold white]{case_id}[/bold white]")
        
        # 1. Enrutamiento Cognitivo
        decision = CognitiveRouter.evaluate_routing(case_id)
        console.print(f"  • [cyan]Modo de Operación:[/cyan] {decision.mode.value} (Complejidad: {decision.complexity_score})")
        console.print(f"  • [yellow]Disparadores detectados:[/yellow] {', '.join(decision.triggers)}")
        console.print(f"  • [green]Operaciones delegadas a Python:[/green] {', '.join(decision.python_delegated_operations[:3])}")
        console.print(f"  • [magenta]Operaciones delegadas a Grok:[/magenta] {', '.join(decision.grok_delegated_operations) if decision.grok_delegated_operations else 'Ninguna (Cálculo directo)'}")

        # 2. Ejecución con el Runner (Fast-Path determinista para validación matemática exacta)
        runner = SkynetRunner(case_id=case_id, fast_path=True)
        report = runner.run()

        # 3. Comprobar exactitud contra el Ground Truth del dataset
        gt_billed = Decimal(exp_billed.replace("$", "").replace(",", ""))
        gt_claim = Decimal(exp_claim.replace("$", "").replace(",", ""))
        gt_just = Decimal(exp_just.replace("$", "").replace(",", ""))

        mae = abs(report.billed_amount - gt_billed) + abs(report.claimable_amount - gt_claim) + abs(report.justified_amount - gt_just)
        mae_str = f"${mae:.2f}"

        summary_table.add_row(
            case_id.replace("dataco_real_", "real_"),
            buyer,
            decision.mode.value.replace("HYBRID_NEURO_SYMBOLIC", "NEURO-SIMBÓLICO"),
            "Decimal + OpenXML + Ledger",
            "Semántica de Cláusulas" if decision.grok_delegated_operations else "Directo",
            f"${report.billed_amount:,.2f}",
            f"${report.claimable_amount:,.2f}",
            f"${report.justified_amount:,.2f}",
            mae_str
        )

    console.print("\n")
    console.print(summary_table)

    # 4. Explicación de la Separación
    console.print(Panel(
        "[bold green]PRINCIPIO DE SEPARACIÓN NEURO-SIMBÓLICA (CERO ALUCINACIÓN):[/bold green]\n"
        "1. [bold white]¿Qué resuelve Python?[/bold white]\n"
        "   - Lectura multiformato (.xlsx OpenXML, .csv manifiestos, .txt comprobantes).\n"
        "   - Matemática financiera exacta con precisión Decimal (sumas, restas, diferencias y porcentajes de descuento).\n"
        "   - Pólizas de partida doble para ERP (SAP / NetSuite) e invariantes criptográficos SHA-256.\n\n"
        "2. [bold white]¿Qué resuelve Grok-4.7?[/bold white]\n"
        "   - Interpretación contextual de cláusulas comerciales y ventanas de reclamación (SLA).\n"
        "   - Resolución de ambigüedades en notas de entrega no estructuradas y alegatos de los compradores.\n"
        "   - Redacción de la Carta Formal de Reclamación con fundamentación contractual sólida.",
        title="[bold yellow]Arquitectura de Separación de Responsabilidades[/bold yellow]",
        border_style="green"
    ))

if __name__ == "__main__":
    run_real_cases_separation_demo()
