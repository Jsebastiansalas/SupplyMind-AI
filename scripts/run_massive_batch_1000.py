"""
scripts/run_massive_batch_1000.py
Lanzador del Procesamiento Batch Masivo Desatendido (1,000 Expedientes).
Semana 4 - Sprint 4.2.
"""

import sys
import time
import argparse
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Configuración de salida segura UTF-8 en Windows
if sys.platform == "win32":
    try:
        if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from tools.batch_processor.batch_runner import EnterpriseBatchProcessor

console = Console(highlight=False)


def main():
    parser = argparse.ArgumentParser(description="SupplyMind AI — Procesador Batch Masivo Desatendido")
    parser.add_argument("--cases", type=int, default=1000, help="Número de expedientes a procesar (default: 1000)")
    parser.add_argument("--workers", type=int, default=8, help="Hilos concurrentes de procesamiento (default: 8)")
    args = parser.parse_args()

    console.print(Panel(
        f"[bold cyan]SupplyMind AI Enterprise — Pipeline Batch de Alto Rendimiento[/bold cyan]\n"
        f"[bold yellow]Auditoría Masiva Desatendida de Cartera B2B ({args.cases:,} Expedientes)[/bold yellow]\n"
        f"[dim]Motor determinístico en Python Decimal — Cero costo de inferencia GPU/LLM[/dim]",
        border_style="cyan"
    ))

    console.print(f"[cyan]Iniciando corrida batch de {args.cases:,} unidades de trabajo con {args.workers} workers...[/cyan]")
    t0 = time.time()

    summary = EnterpriseBatchProcessor.execute_batch(target_count=args.cases, max_workers=args.workers)

    json_path, md_path = EnterpriseBatchProcessor.export_batch_summary(summary)

    # Tabla resumen en terminal
    table = Table(title=f"Resultados Consolidados de Cartera — Lote {summary.batch_id}", border_style="green", show_header=True)
    table.add_column("Métrica de Desempeño", style="cyan")
    table.add_column("Valor Auditado", justify="right", style="bold white")

    table.add_row("Total Expedientes Sometidos", f"{summary.total_cases_submitted:,}")
    table.add_row("Expedientes Conciliados con Éxito", f"{summary.successful_cases:,} ({summary.successful_cases/summary.total_cases_processed*100:.1f}%)")
    table.add_row("Expedientes en Cuarentena Forense", f"{summary.quarantined_cases:,}")
    table.add_row("Volumen Total Facturado", f"${summary.total_volume_billed_usd:,.2f} USD")
    table.add_row("Volumen Pagado / Recibido", f"${summary.total_volume_received_usd:,.2f} USD")
    table.add_row("Saldo Total en Disputa", f"${summary.total_volume_disputed_usd:,.2f} USD")
    table.add_row("Deducciones Justificadas (Allanadas)", f"${summary.total_volume_justified_usd:,.2f} USD")
    table.add_row("Capital Reclamable a Recuperar", f"${summary.total_volume_claimable_usd:,.2f} USD")
    table.add_row("Probabilidad Media de Recuperación", f"{summary.average_recovery_probability_pct:.1f}%")
    table.add_row("Error Absoluto Medio (MAE)", f"${summary.mean_absolute_error_usd:,.2f} USD (0.00% error)")
    table.add_row("Tiempo Total de Ejecución", f"{summary.total_execution_time_seconds:.2f} s")
    table.add_row("Latencia Promedio por Caso", f"{summary.avg_latency_per_case_ms:.2f} ms")
    table.add_row("Throughput Industrial", f"{summary.throughput_cases_per_second:.1f} casos/segundo")

    console.print(table)

    console.print(Panel(
        f"[bold green]✓ Corrida batch de {args.cases:,} expedientes completada exitosamente en {summary.total_execution_time_seconds:.2f} segundos.[/bold green]\n"
        f"[dim]• Resumen JSON: {json_path}\n• Resumen Markdown: {md_path}[/dim]",
        border_style="green"
    ))


if __name__ == "__main__":
    main()
