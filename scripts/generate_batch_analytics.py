"""
scripts/generate_batch_analytics.py
CLI de Generación de Tablero Visual HTML/SVG y Verificación Criptográfica SHA-256.

Permite:
1. Sellar criptográficamente la bitácora actual (`--seal`) generando la cadena de hashes SHA-256
   y la raíz de Merkle (`unattended_batch_audit_manifest.json` y `.sha256`).
2. Auditar y verificar la integridad inmutable de la bitácora (`--verify-seal`) detectando
   cualquier alteración en montos, estados o archivos físicos.
3. Generar el Tablero Ejecutivo Interactivo HTML/SVG (`reports/unattended_batch_analytics_dashboard.html`)
   y el resumen estadístico (`reports/unattended_batch_analytics_summary.json`).
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from tools.batch_processor.batch_analytics_visualizer import BatchAnalyticsVisualizer
from tools.batch_processor.batch_audit_sealer import BatchAuditSealer


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generador de Analítica Visual HTML/SVG y Verificador Criptográfico SHA-256"
    )
    parser.add_argument(
        "--reports-dir",
        type=str,
        default=None,
        help="Directorio de reportes (por defecto: reports/)",
    )
    parser.add_argument(
        "--seal",
        action="store_true",
        help="Recalcular y sellar criptográficamente la bitácora antes de generar el tablero",
    )
    parser.add_argument(
        "--verify-seal",
        action="store_true",
        help="Auditar y verificar la integridad criptográfica SHA-256 de la bitácora sellada",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    console = Console()
    reports_dir = Path(args.reports_dir) if args.reports_dir else (WORKSPACE_ROOT / "reports")

    sealer = BatchAuditSealer(reports_dir=reports_dir)
    visualizer = BatchAnalyticsVisualizer(reports_dir=reports_dir)

    records = visualizer._load_records_from_disk()
    if not records:
        console.print(
            Panel(
                "[yellow]No se encontraron registros ejecutados aún en 'reports/'.[/yellow]\n"
                "Ejecuta primero el orquestador:\n"
                "[bold cyan]python scripts/run_unattended_12h_batch.py --units 10 --duration-hours 0.01 --dry-run[/bold cyan]",
                title="Analítica de Carga Desatendida",
                border_style="yellow",
            )
        )
        return 1

    seal_info = None
    if args.seal or not sealer.manifest_json_path.exists():
        seal_info = sealer.seal_records(records)

    paths = visualizer.export_visual_dashboard(records=records, seal_info=seal_info)
    summary = visualizer.compute_analytics_summary(records=records, seal_info=seal_info)
    verification = sealer.verify_batch_integrity(records=records)

    # Panel de Certificación Criptográfica
    status_color = "green" if verification.is_valid else "red"
    console.print(
        Panel(
            f"[bold {status_color}]{verification.summary_message}[/bold {status_color}]\n\n"
            f"• [bold]Unidades Auditadas:[/bold] {verification.total_records_verified:,}\n"
            f"• [bold]Merkle Root SHA-256:[/bold] [cyan]{verification.merkle_root_computed}[/cyan]\n"
            f"• [bold]Tip Chain Hash:[/bold] [cyan]{verification.tip_chain_hash_computed}[/cyan]\n"
            f"• [bold]Invariante Contable ($0.00 MAE):[/bold] {'[green]VERIFICADO[/green]' if verification.mae_zero_invariant_passed else '[red]FALLO[/red]'}\n"
            f"• [bold]Digests de Archivos en Disco:[/bold] {'[green]INTACTOS[/green]' if verification.files_digest_passed else '[red]MODIFICADOS[/red]'}",
            title="Sello de Inmutabilidad Criptográfica (Eje 2)",
            border_style=status_color,
        )
    )

    # Tabla de Resumen de Telemetría y Finanzas
    tel = summary["telemetry"]
    fin = summary["financials"]
    kpi_table = Table(title="Resumen de Telemetría y Recuperación Comercial (Eje 1)", show_lines=True)
    kpi_table.add_column("Métrica", style="bold white")
    kpi_table.add_column("Valor Auditado", style="cyan", justify="right")

    kpi_table.add_row("Total de Unidades Procesadas", f"{summary['total_units']:,}")
    kpi_table.add_row("Tasa de Éxito Operativo", f"{summary['success_rate_pct']:.2f}%")
    kpi_table.add_row("Costo Total Pasarela Platica", f"${tel['total_cost_usd']:,.6f} USD")
    kpi_table.add_row("Costo Promedio por Unidad", f"${tel['avg_cost_usd']:,.6f} USD")
    kpi_table.add_row("Rango Dinámico de Costo/Caso", f"${tel['min_cost_usd']:.6f} — ${tel['max_cost_usd']:.6f} USD")
    kpi_table.add_row("Total de Tokens Procesados", f"{tel['total_tokens']:,} tokens")
    kpi_table.add_row("Latencia (p50 / p95)", f"{tel['p50_latency_seconds']:.2f}s / {tel['p95_latency_seconds']:.2f}s")
    kpi_table.add_row("Capital Retenido en Disputa", f"${fin['total_disputed_mxn']:,.2f} MXN")
    kpi_table.add_row("Capital Recuperado con Éxito", f"[bold green]${fin['total_recovered_mxn']:,.2f} MXN[/bold green]")

    console.print(kpi_table)

    console.print(
        Panel(
            f"• [bold]Tablero Interactivo HTML/SVG:[/bold] [green]{paths['analytics_html']}[/green]\n"
            f"• [bold]Resumen Analítico JSON:[/bold] [cyan]{paths['analytics_json']}[/cyan]\n"
            f"• [bold]Manifiesto Criptográfico JSON:[/bold] [cyan]{sealer.manifest_json_path}[/cyan]\n"
            f"• [bold]Sumas SHA-256 Estándar:[/bold] [cyan]{sealer.manifest_sha256_path}[/cyan]",
            title="Artefactos Generados",
            border_style="cyan",
        )
    )

    if args.verify_seal and not verification.is_valid:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
