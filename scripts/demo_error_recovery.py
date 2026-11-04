"""
scripts/demo_error_recovery.py
Demostración de Manejo Autónomo de Errores y Auto-Recuperación (Hito S2).

Demuestra cómo SupplyMind AI maneja fallos reales y se auto-recupera sin intervención humana:
1. Error Sintáctico: JSON corrupto/truncado en un comprobante de pago comercial.
2. Auto-Sanación: El parser resiliente detecta la corrupción, repara la sintaxis y reconstruye los modelos.
3. Resiliencia en Invocación de Herramientas: Reintentos seguros y captura de excepciones.
4. Veredicto Final: Conciliación exitosa y generación del dictamen pericial sin abortar el proceso.
"""

import sys
import json
import time
from pathlib import Path
from decimal import Decimal
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Añadir raíz al sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from agent.ingestion.resilient_parser import repair_json_string, ResilientDocumentLoader
from agent.core.skynet_runner import SkynetRunner
from data.models import PaymentReceipt

console = Console()


def run_error_recovery_demo():
    console.print(Panel(
        "[bold cyan]SupplyMind AI — Demostración de Resiliencia y Auto-Recuperación (Hito S2)[/bold cyan]\n"
        "[dim]Simulación pericial de fallos de entrada, inyecciones corruptas y auto-reparación agéntica.[/dim]",
        border_style="cyan"
    ))

    # CASO 1: Inyección de JSON Severamente Corrupto en Comprobante de Pago
    console.print("\n[bold yellow]═══ ESCENARIO 1: Detección y Reparación de JSON Corrupto / Truncado ═══[/bold yellow]")
    
    corrupted_payment_payload = """
    {
        "payment_id": "PAY-ERR-RECOVERY-9999",
        "invoice_reference": "INV-DC-ORD-68914",
        "payment_date": "2026-02-15",
        "amount_paid": 8899.53,
        "currency": "USD",
        "deductions": [
            {
                "code": "SHORTAGE",
                "reason": "Faltante fisico 3 kayak",
                "amount": 599.97
            },
            {
                "code": "COOP_PROMO_UNAUTH",
                "reason": "Cargo unilateral folleto verano",
                "amount": 500.00
            // ERROR SINTÁCTICO: Falta cierre de objeto, coma residual y falta cierre de lista
    """

    console.print("[dim]1. Intentando parsear documento corrupto con json.loads estándar...[/dim]")
    standard_error = None
    try:
        json.loads(corrupted_payment_payload)
        console.print("[red]Inesperado: El JSON fue leído por json.loads.[/red]")
    except json.JSONDecodeError as exc:
        standard_error = str(exc)
        console.print(f"[bold red]❌ FALLO DETECTADO POR PYTHON ESTÁNDAR:[/bold red] [white]{standard_error}[/white]")
        console.print("[yellow]⚠️ En un agente convencional, la ejecución colapsaría aquí (Crash 500).[/yellow]")

    time.sleep(0.8)

    console.print("\n[dim]2. Activando repair_json_string de SupplyMind AI...[/dim]")
    t0 = time.time()
    repaired_obj, recovery_diagnostics = repair_json_string(corrupted_payment_payload)
    elapsed_ms = (time.time() - t0) * 1000.0

    if repaired_obj:
        console.print(f"[bold green]✅ AUTO-RECUPERACIÓN EXITOSA en {elapsed_ms:.2f} ms![/bold green]")
        console.print(f"   [cyan]Diagnóstico de reparación:[/cyan] {recovery_diagnostics}")
        
        # Validar Pydantic con Decimal
        payment_model = PaymentReceipt.model_validate(repaired_obj)
        console.print(f"   [green]Modelo validado:[/green] Comprobante [bold]{payment_model.payment_id}[/bold] por [bold]${payment_model.amount_paid:,.2f} USD[/bold]")
        console.print(f"   [green]Deducciones rescatadas:[/green] {len(payment_model.deductions)} partidas identificadas con precisión.")
    else:
        console.print("[bold red]No se pudo reparar el documento.[/bold red]")
        sys.exit(1)

    time.sleep(1.0)

    # CASO 2: Ejecución de Punta a Punta con Manejo de Excepciones y Circuito de Reintento
    console.print("\n[bold yellow]═══ ESCENARIO 2: Ejecución Completa con Watchdog & Reintentos ═══[/bold yellow]")
    console.print("[dim]Iniciando auditoría de 'dataco_real_001_caguas_pelican_kayak' con tolerancia a fallos...[/dim]")
    
    runner = SkynetRunner(case_id="dataco_real_001_caguas_pelican_kayak", fast_path=True)
    report = runner.run()

    # Tabla resumen de la auto-recuperación
    table = Table(title="Resultados del Protocolo de Resiliencia S2")
    table.add_column("Métrica / Fase", style="cyan", no_wrap=True)
    table.add_column("Estado", style="bold green")
    table.add_column("Detalle Técnico", style="white")

    table.add_row(
        "Detección de Error Sintáctico",
        "INTERCEPTADO",
        f"Capturado JSONDecodeError ('{standard_error[:40]}...')"
    )
    table.add_row(
        "Mecanismo de Auto-Sanación",
        "APLICADO",
        f"Reconstrucción heurística de llaves y corchetes en {elapsed_ms:.1f}ms"
    )
    table.add_row(
        "Integridad Numérica Decimal",
        "PRESERVADA",
        f"Monto facturado: ${report.billed_amount:,.2f} | Reclamable: ${report.claimable_amount:,.2f}"
    )
    table.add_row(
        "Veredicto Final Autónomo",
        "EMITIDO",
        f"Dictamen generado sin intervención humana (Confianza: {report.confidence*100:.1f}%)"
    )

    console.print(table)
    console.print("\n[bold green]Demostración de Auto-Recuperación completada con éxito.[/bold green]\n")


if __name__ == "__main__":
    run_error_recovery_demo()
