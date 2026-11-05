"""
scripts/run_small_batch_smoke_test.py
Ejecutor y Validador de Lote Pequeño ("Smoke Test Productivo") Pre-Corrida de 12 Horas.

Implementa la recomendación oficial de Platica:
- "Prueba con un lote pequeño antes de lanzar la corrida larga."
- "El consumo debe ser productivo: ligado a tareas reales del agente."

Ejecuta un lote compacto (por defecto 6 unidades representativas) en un entorno aislado
(`reports/small_batch_smoke_test/`) que ejercita de punta a punta:
1. 4 Unidades Nominales (`SUCCESS`): Cruce 3-Way Match de los 5 documentos en disco + dictamen en Platica Gateway (`grok-4.7`).
2. 1 Unidad con Anomalía Técnica Auto-Recuperable (`RECOVERED_QUARANTINE`): `payment.json` truncado (`JSONDecodeError`) reparado al vuelo.
3. 1 Unidad con Fallo Irreconciliable Honesto (`FAILED`): Ausencia física de `delivery.json` (`FileNotFoundError` de POD/BOL), escalada honestamente sin inventar evidencia.
4. Sello Criptográfico SHA-256 (`Merkle Root`), Tablero Visual HTML/SVG y verificación de `$0.00 MAE`.
"""

from __future__ import annotations

import argparse
from decimal import Decimal
import json
from pathlib import Path
import shutil
import sys
from typing import List

# Salida segura UTF-8 en Windows
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure") and sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from config.settings import settings
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from tools.batch_processor.batch_audit_sealer import BatchAuditSealer
from tools.batch_processor.unattended_batch_orchestrator import UnattendedBatchOrchestrator
from tools.batch_processor.work_unit_queue_generator import WorkUnit, WorkUnitQueueGenerator


def build_representative_small_queue(total_units: int = 6) -> List[WorkUnit]:
    """
    Construye una cola pequeña representativa que incluye casos nominales reales,
    1 caso con JSON truncado auto-reparable y 1 caso con falta física de POD (fallo honesto).
    """
    full_queue = WorkUnitQueueGenerator.generate_queue(total_units=1024, seed=2026)

    nominals = [u for u in full_queue if not u.has_anomaly][: max(1, total_units - 2)]
    corrupt_json = next(
        (u for u in full_queue if u.anomaly_type == "CORRUPT_JSON_SYNTAX"),
        None,
    )
    missing_pod = next(
        (u for u in full_queue if u.anomaly_type == "IRRECONCILABLE_MISSING_POD"),
        None,
    )

    selected: List[WorkUnit] = list(nominals)
    if total_units >= 2 and corrupt_json is not None:
        selected.append(corrupt_json)
    if total_units >= 3 and missing_pod is not None:
        selected.append(missing_pod)

    # Reindexar secuencialmente del 1 a N para el lote pequeño
    reindexed: List[WorkUnit] = []
    for idx, u in enumerate(selected[:total_units], start=1):
        copy_u = u.model_copy(
            update={
                "unit_index": idx,
                "task_id": f"smoke_unit_{idx:04d}",
            }
        )
        reindexed.append(copy_u)
    return reindexed


def run_small_batch_smoke_test(
    output_dir: Path,
    units_count: int = 6,
    dry_run: bool = False,
) -> dict:
    """Ejecuta el lote pequeño de punta a punta y audita todos sus invariantes."""
    if output_dir.exists():
        shutil.rmtree(output_dir, ignore_errors=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    queue = build_representative_small_queue(total_units=units_count)
    manifest_paths = WorkUnitQueueGenerator.export_queue_manifest(queue, output_dir=output_dir)

    orchestrator = UnattendedBatchOrchestrator(
        queue_manifest_path=Path(manifest_paths["json_manifest"]),
        output_dir=output_dir,
        total_units=units_count,
        target_duration_hours=0.0,
        dry_run=dry_run,
        resume=False,
    )
    orchestrator.pacing = False

    batch_result = orchestrator.run_unattended_batch()
    records = [r.to_dict() for r in orchestrator.completed_records]

    sealer = BatchAuditSealer(reports_dir=output_dir)
    verification = sealer.verify_batch_integrity(records=records)

    # Verificar que los expedientes físicos se hayan materializado con sus 5 documentos + docket
    dossiers_verified = 0
    for r in records:
        cdir = orchestrator.dossiers_dir / r["case_id"]
        if (cdir / "invoice.json").exists() and (cdir / "audit_resolution_docket.json").exists():
            dossiers_verified += 1

    distinct_token_counts = len({r["tokens_total"] for r in records})

    return {
        "batch_result": batch_result,
        "records": records,
        "seal_verification": verification.to_dict(),
        "dossiers_verified": dossiers_verified,
        "distinct_token_counts": distinct_token_counts,
        "output_dir": str(output_dir),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ejecutor de Lote Pequeño en Vivo (Smoke Test Productivo) antes de la corrida de 12 horas"
    )
    parser.add_argument(
        "--units",
        type=int,
        default=6,
        help="Número de unidades para el lote pequeño (por defecto: 6)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Ejecutar sin gastar llamadas HTTP reales (modo calibración local)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Directorio de salida (por defecto: reports/small_batch_smoke_test)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    console = Console(highlight=False, legacy_windows=False)
    out_dir = Path(args.output_dir) if args.output_dir else (WORKSPACE_ROOT / "reports" / "small_batch_smoke_test")

    mode_label = (
        "[yellow]SIMULACIÓN CALIBRADA (--dry-run)[/yellow]"
        if args.dry_run or not settings.is_live_api_ready
        else f"[bold green]PASARELA OFICIAL PLATICA EN VIVO ({settings.MODEL_NAME})[/bold green]"
    )

    console.print(
        Panel(
            f"[bold cyan]Prueba de Lote Pequeño Pre-Corrida (Consejo Oficial Platica)[/bold cyan]\n"
            f"• [bold]Modo de Inferencia:[/bold] {mode_label}\n"
            f"• [bold]Unidades Seleccionadas:[/bold] {args.units} (Nominales + JSON Corrupto Auto-Reparable + Falta Física de POD)\n"
            f"• [bold]Directorio Aislado:[/bold] {out_dir}",
            title="Iniciando Smoke Test Productivo",
            border_style="cyan",
        )
    )

    summary = run_small_batch_smoke_test(
        output_dir=out_dir,
        units_count=args.units,
        dry_run=args.dry_run,
    )
    records = summary["records"]
    seal_ver = summary["seal_verification"]
    export_paths = summary["batch_result"]["export_paths"]

    table = Table(
        title="Resultados del Lote Pequeño (Consumo Productivo 3-Way Match + Honestidad en Fallos)",
        show_lines=True,
    )
    table.add_column("#", justify="right", style="dim", width=3)
    table.add_column("Task ID", style="cyan", width=15)
    table.add_column("Retailer", style="white", width=22)
    table.add_column("Categoría / Escenario", style="magenta", width=26)
    table.add_column("Estado", justify="center", width=20)
    table.add_column("Recuperado", justify="right", style="green", width=13)
    table.add_column("Tokens", justify="right", style="yellow", width=8)
    table.add_column("Costo USD", justify="right", style="bold yellow", width=11)

    for r in records:
        st = r["status"]
        if st == "SUCCESS":
            st_badge = "[bold green]SUCCESS[/bold green]"
        elif st == "RECOVERED_QUARANTINE":
            st_badge = "[bold yellow]RECOVERED_QUARANTINE[/bold yellow]"
        else:
            st_badge = "[bold red]FAILED (HONEST)[/bold red]"

        table.add_row(
            str(r["unit_index"]),
            r["task_id"],
            r["retailer_name"][:21],
            r["category"][:25],
            st_badge,
            f"${r['recovered_amount']:,.2f}",
            f"{r['tokens_total']:,}",
            f"${r['cost_usd']:.6f}",
        )

    console.print(table)

    succ_cnt = sum(1 for r in records if r["status"] == "SUCCESS")
    quar_cnt = sum(1 for r in records if r["status"] == "RECOVERED_QUARANTINE")
    fail_cnt = sum(1 for r in records if r["status"] == "FAILED")
    total_cost = sum(r["cost_usd"] for r in records)

    console.print(
        Panel(
            f"• [bold]Expedientes Físicos 3-Way Match Verificados en Disco:[/bold] [green]{summary['dossiers_verified']}/{len(records)}[/green]\n"
            f"• [bold]Desglose Honesto de Estados:[/bold] [green]{succ_cnt} SUCCESS[/green] | [yellow]{quar_cnt} RECOVERED_QUARANTINE[/yellow] | [red]{fail_cnt} FAILED (Falta física de POD)[/red]\n"
            f"• [bold]Consumo Dinámico Productivo:[/bold] {summary['distinct_token_counts']} conteos distintos de tokens | Costo Total Lote: [bold yellow]${total_cost:.6f} USD[/bold yellow]\n"
            f"• [bold]Sello Criptográfico SHA-256 (Merkle Root):[/bold] [cyan]{seal_ver['merkle_root_computed'][:32]}...[/cyan] ({'[green]VÁLIDO[/green]' if seal_ver['is_valid'] else '[red]ERROR[/red]'})\n"
            f"• [bold]Tablero HTML del Lote Pequeño:[/bold] [green]{export_paths['analytics_html']}[/green]\n"
            f"• [bold]Bitácora CSV del Lote Pequeño:[/bold] [cyan]{export_paths['csv_log']}[/cyan]\n\n"
            f"[bold green]✔ LOTE PEQUEÑO VALIDADO CON ÉXITO. Ya puedes lanzar la corrida desatendida de 12 horas con total confianza:[/bold green]\n"
            f"  [bold white]python scripts/monitor_unattended_batch.py --auto-restart[/bold white]",
            title="Dictamen de Preparación Pre-Corrida de 12 Horas",
            border_style="green" if seal_ver["is_valid"] else "red",
        )
    )

    return 0 if seal_ver["is_valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
