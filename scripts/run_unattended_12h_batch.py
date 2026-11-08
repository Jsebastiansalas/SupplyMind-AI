"""
scripts/run_unattended_12h_batch.py
Lanzador Interactivo y Desatendido de la Jornada de Carga de 12 Horas / 1,000+ Unidades.

Uso:
    # 1. Ejecución Desatendida Oficial Completa (12 horas, 1,024 unidades, llamadas en vivo a Grok):
    python scripts/run_unattended_12h_batch.py

    # 2. Prueba Rápida de Verificación (Dry-run de 5 unidades en 5 segundos):
    python scripts/run_unattended_12h_batch.py --dry-run --units 5

    # 3. Corrida en Vivo Acelerada (sin pausas de ritmo de 12 horas, procesa a máxima velocidad de API):
    python scripts/run_unattended_12h_batch.py --units 20 --no-pacing

    # 4. Reanudar una corrida interrumpida desde la última tarea completada:
    python scripts/run_unattended_12h_batch.py --resume
"""

import argparse
from datetime import datetime, timezone
import os
import signal
import sys
import time
from pathlib import Path

# Salida segura UTF-8 en Windows para caracteres especiales
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure") and sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Añadir raíz del proyecto al sys.path
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn, TimeRemainingColumn

from config.settings import settings
from tools.batch_processor.unattended_batch_orchestrator import (
    UnattendedBatchOrchestrator,
    TaskExecutionRecord,
)

console = Console(highlight=False, legacy_windows=False)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="SupplyMind AI - Orquestador Desatendido de 12 Horas / 1,000+ Unidades."
    )
    parser.add_argument(
        "--units",
        type=int,
        default=1024,
        help="Número total de unidades de trabajo a procesar (default: 1024).",
    )
    parser.add_argument(
        "--hours",
        type=float,
        default=12.0,
        help="Duración objetivo en horas de la corrida desatendida (default: 12.0).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Ejecutar en modo de prueba local ultrarrápido sin consumo de pasarela.",
    )
    parser.add_argument(
        "--no-pacing",
        action="store_true",
        help="Desactivar las pausas de ritmo adaptativo (procesar a velocidad máxima).",
    )
    parser.add_argument(
        "--no-resume",
        action="store_true",
        help="No reanudar desde stream previo; comenzar desde cero.",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Reanudar desde stream previo (modo predeterminado tolerante a interrupciones).",
    )
    return parser.parse_args()


def main():
    args = parse_arguments()

    console.print(
        Panel(
            f"[bold green]SupplyMind AI - Orquestador de Carga Masiva Desatendida[/bold green]\n"
            f"[cyan]Unidades Objetivo:[/cyan] {args.units:,} tareas completas B2B de punta a punta\n"
            f"[cyan]Ventana Desatendida:[/cyan] {args.hours:.1f} horas continuas (~42s / tarea)\n"
            f"[cyan]Pasarela Oficial:[/cyan] {settings.PLATICA_BASE_URL} (Modelo: [yellow]{settings.MODEL_NAME}[/yellow])\n"
            f"[cyan]Modo:[/cyan] {'[yellow]DRY-RUN (Simulación Rápida)[/yellow]' if args.dry_run else '[bold green]EN VIVO (Platica Gateway Oficial)[/bold green]'}\n"
            f"[cyan]Ritmo Adaptativo:[/cyan] {'Desactivado (--no-pacing)' if args.no_pacing or args.dry_run else 'Activado (12 Horas Continuas)'}\n"
            f"[cyan]Reanudación (--resume):[/cyan] {'Desactivada' if args.no_resume else 'Activada (Tolerante a desconexiones)'}",
            title="[bold white]PLATICA - JORNADA DE CARGA DESATENDIDA[/bold white]",
            border_style="green",
        )
    )

    orchestrator = UnattendedBatchOrchestrator(
        total_units=args.units,
        target_duration_hours=args.hours,
        dry_run=args.dry_run,
        pacing=not args.no_pacing,
        resume=not args.no_resume,
    )

    if args.no_resume:
        import shutil
        backup_dir = orchestrator.output_dir / "backup_prior_run"
        backup_dir.mkdir(parents=True, exist_ok=True)
        ts = int(time.time())
        for path in [
            orchestrator.stream_path,
            orchestrator.checkpoint_path,
            orchestrator.heartbeat_path,
            orchestrator.csv_log_path,
            orchestrator.json_log_path,
            orchestrator.summary_md_path,
        ]:
            if path.exists():
                shutil.copy2(path, backup_dir / f"{path.stem}_backup_{ts}{path.suffix}")
                try:
                    path.unlink()
                except Exception:
                    pass

    # Captura elegante de SIGINT (Ctrl+C) para exportar bitácora antes de salir
    def handle_sigint(sig, frame):
        console.print("\n[bold red][INTERRUPCIÓN RECIBIDA][/bold red] Guardando bitácora y resumen de estado...")
        paths = orchestrator.export_logs()
        console.print(f"[bold green]✔ Bitácora guardada con éxito en:[/bold green] {paths['csv_log']}")
        console.print(f"[bold green]✔ Resumen ejecutivo guardado en:[/bold green] {paths['summary_md']}")
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_sigint)

    # Tabla de métricas en vivo
    accumulated_cost = 0.0
    success_count = 0
    quarantine_count = 0
    failed_count = 0

    progress_bar = Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TextColumn("({task.completed}/{task.total})"),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        console=console,
    )

    with progress_bar:
        task_tracker = progress_bar.add_task(
            description="[green]Procesando cola desatendida...",
            total=args.units,
        )

        def on_unit_completed(index: int, total: int, record: TaskExecutionRecord):
            nonlocal accumulated_cost, success_count, quarantine_count, failed_count
            accumulated_cost += record.cost_usd

            if record.status == "SUCCESS":
                success_count += 1
                status_color = "[green]SUCCESS[/green]"
            elif record.status == "RECOVERED_QUARANTINE":
                quarantine_count += 1
                status_color = "[yellow]QUARANTINE_RECOVERED[/yellow]"
            else:
                failed_count += 1
                status_color = "[red]FAILED[/red]"

            progress_bar.update(task_tracker, completed=index)

            # Notificación de línea en consola en tiempo real para cada unidad procesada
            console.print(
                f"[{datetime.now().strftime('%H:%M:%S')}] "
                f"#{index:04d}/{total} | {record.task_id} | {record.retailer_name[:20]:20s} | "
                f"Disputado: ${record.disputed_amount:8.2f} MXN | "
                f"Recuperado: ${record.recovered_amount:8.2f} MXN | "
                f"Status: {status_color} | Costo: ${accumulated_cost:.4f} USD | "
                f"Δ: ${record.financial_delta:.2f}"
            )

        result = orchestrator.run_unattended_batch(progress_callback=on_unit_completed)

    console.print("\n")
    console.print(
        Panel(
            f"[bold green]✔ JORNADA DE CARGA DESATENDIDA FINALIZADA CON ÉXITO[/bold green]\n\n"
            f"[bold]Total Unidades Procesadas:[/bold] {result['total_processed']:,} / {args.units:,}\n"
            f"[bold]Exitosas / Recuperadas:[/bold] {success_count:,} nominales + {quarantine_count:,} en cuarentena\n"
            f"[bold]Costo Total Acumulado:[/bold] ${accumulated_cost:.4f} USD\n"
            f"[bold]Costo Promedio por Tarea:[/bold] ${(accumulated_cost / max(1, result['total_processed'])):.6f} USD\n\n"
            f"[cyan]Bitácora CSV:[/cyan] {result['export_paths']['csv_log']}\n"
            f"[cyan]Bitácora JSON:[/cyan] {result['export_paths']['json_log']}\n"
            f"[cyan]Resumen Ejecutivo Markdown:[/cyan] {result['export_paths']['summary_md']}",
            title="[bold white]INFORME FINAL DE ENTREGA[/bold white]",
            border_style="green",
        )
    )


if __name__ == "__main__":
    main()
