"""
scripts/verify_batch_resilience.py
CLI para ejecutar el Validador de Resiliencia y Simulador de Caos Autónomo (Eje 3).
"""

from __future__ import annotations

from pathlib import Path
import sys

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from tools.batch_processor.batch_resilience_verifier import BatchResilienceVerifier


def main() -> int:
    console = Console()
    verifier = BatchResilienceVerifier()
    report = verifier.run_full_resilience_audit()

    table = Table(
        title="Pruebas de Caos Controlado y Recuperación Autónoma (Eje 3)",
        show_lines=True,
    )
    table.add_column("ID", style="bold cyan", width=8)
    table.add_column("Escenario de Fallo", style="white")
    table.add_column("Mecanismo de Auto-Recuperación", style="magenta")
    table.add_column("Unidades", justify="center")
    table.add_column("$0.00 MAE", justify="center")
    table.add_column("Estado", justify="center")

    for s in report["scenarios"]:
        status_str = "[bold green]PASS[/bold green]" if s["passed"] else "[bold red]FAIL[/bold red]"
        mae_str = "[green]OK[/green]" if s["mae_zero_preserved"] else "[red]ERROR[/red]"
        table.add_row(
            s["scenario_id"],
            s["scenario_name"],
            s["expected_recovery_mechanism"],
            f"{s['units_recovered']}/{s['units_tested']}",
            mae_str,
            status_str,
        )

    console.print(table)

    q_prof = report["queue_fault_profile"]
    anom_lines = "\n".join(
        f"  • [bold]{k}[/bold]: {v} casos → Auto-Cuarentena NIF C-3 (`RECOVERED_QUARANTINE`)"
        for k, v in sorted(q_prof["breakdown_by_anomaly_type"].items(), key=lambda x: x[1], reverse=True)
    )
    console.print(
        Panel(
            f"[bold]Total en Cola Oficial:[/bold] {q_prof['total_queue_units']:,} unidades\n"
            f"[bold]Unidades Nominales:[/bold] {q_prof['nominal_units']:,} | "
            f"[bold]Anomalías Inyectadas:[/bold] {q_prof['injected_anomaly_units']:,} ({q_prof['anomaly_rate_pct']}%)\n\n"
            f"[bold cyan]Desglose de Fallos Documentales y Trampas en el Lote:[/bold cyan]\n{anom_lines}\n\n"
            f"[dim]Reporte exportado en: {verifier.audit_md_path}[/dim]",
            title="Perfil de Errores y Recuperación del Lote de 1,024 Unidades",
            border_style="green" if report["all_resilience_scenarios_passed"] else "red",
        )
    )

    return 0 if report["all_resilience_scenarios_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
