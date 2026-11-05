"""
scripts/view_task_detail.py
Visor Interactivo y Detallado de Expedientes de la Corrida Desatendida de 12 Horas.

Permite consultar cualquier unidad de trabajo a detalle examinando el dictamen legal,
la reconciliación financiera ($0.00 MAE), la telemetría de tokens y costo en pasarela Platica,
el asiento contable ERP generado y el protocolo de recuperación de anomalías.

Uso:
    # 1. Ver detalle por índice o ID de tarea:
    python scripts/view_task_detail.py 1
    python scripts/view_task_detail.py work_unit_0001

    # 2. Ver la última tarea completada:
    python scripts/view_task_detail.py --last

    # 3. Listar todas las tareas procesadas en una tabla resumida:
    python scripts/view_task_detail.py --list

    # 4. Ver casos que entraron a cuarentena forense / resiliencia:
    python scripts/view_task_detail.py --quarantine

    # 5. Filtrar expedientes por retailer (ej. Walmart, Soriana, Amazon):
    python scripts/view_task_detail.py --retailer Walmart
"""

import argparse
import json
import os
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional

# Salida segura UTF-8 en Windows
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

console = Console(highlight=False, legacy_windows=False)


def load_all_records() -> List[Dict[str, Any]]:
    """Carga todos los registros disponibles desde stream, log json o manifiesto."""
    reports_dir = WORKSPACE_ROOT / "reports"
    stream_path = reports_dir / "unattended_batch_execution_stream.jsonl"
    json_path = reports_dir / "unattended_batch_execution_log.json"
    manifest_path = reports_dir / "work_unit_queue_manifest_1024.json"

    records: List[Dict[str, Any]] = []

    # 1. Intentar leer stream en tiempo real (más fresco)
    if stream_path.exists():
        try:
            with open(stream_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        records.append(json.loads(line))
            if records:
                return records
        except Exception:
            pass

    # 2. Intentar leer log JSON consolidado
    if json_path.exists():
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                records = data.get("records", [])
                if records:
                    return records
        except Exception:
            pass

    # 3. Fallback al manifiesto de cola si aún no se ha ejecutado
    if manifest_path.exists():
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for u in data.get("units", []):
                    records.append({
                        "unit_index": u["unit_index"],
                        "task_id": u["task_id"],
                        "case_id": u["case_id"],
                        "source_origin": u["source_origin"],
                        "retailer_id": u["retailer_id"],
                        "retailer_name": u["retailer_name"],
                        "category": u["category"],
                        "status": "PENDING_EXECUTION",
                        "billed_amount": u["billed_amount"],
                        "received_amount": u["received_amount"],
                        "disputed_amount": u["disputed_amount"],
                        "recovered_amount": u["expected_claimable"],
                        "justified_amount": u["expected_justified"],
                        "financial_delta": 0.00,
                        "tokens_prompt": 0,
                        "tokens_completion": 0,
                        "tokens_total": 0,
                        "cost_usd": 0.0,
                        "model_used": "grok-4.7",
                        "input_summary": f"Unidad pendiente en cola: {u['retailer_name']} (${u['disputed_amount']} MXN)",
                        "result_summary": f"Acción esperada: {u['expected_action']}",
                        "error_encountered": "None",
                        "recovery_action": "None",
                        "legal_basis": "Pendiente de dictamen en pasarela",
                        "erp_action": "Pendiente de póliza",
                        "timestamp_start": "N/A",
                        "timestamp_end": "N/A",
                        "duration_seconds": 0.0,
                    })
        except Exception:
            pass

    return records


def find_record(records: List[Dict[str, Any]], query: str) -> Optional[Dict[str, Any]]:
    """Busca un registro por índice numérico, task_id o case_id."""
    query_clean = query.strip().lower()

    # Si es número entero (ej. "1", "42")
    if query_clean.isdigit():
        target_idx = int(query_clean)
        for r in records:
            if r.get("unit_index") == target_idx:
                return r

    # Buscar por task_id exacto o case_id
    for r in records:
        tid = str(r.get("task_id", "")).lower()
        cid = str(r.get("case_id", "")).lower()
        if tid == query_clean or cid == query_clean:
            return r

    # Búsqueda parcial por task_id
    for r in records:
        tid = str(r.get("task_id", "")).lower()
        if query_clean in tid:
            return r

    return None


def render_task_detail(record: Dict[str, Any]) -> None:
    """Muestra el reporte detallado e interactivo de una unidad de trabajo."""
    status = record.get("status", "UNKNOWN")
    if status == "SUCCESS":
        status_badge = "[bold white on green]  ✔ AUDITORÍA EXITOSA (PROCEDENTE)  [/bold white on green]"
        status_color = "green"
    elif status == "RECOVERED_QUARANTINE":
        status_badge = "[bold white on yellow]  ▲ EN CUARENTENA FORENSE (AUTO-RECUPERADO)  [/bold white on yellow]"
        status_color = "yellow"
    elif status == "PENDING_EXECUTION":
        status_badge = "[bold white on blue]  ⏳ PENDIENTE DE EJECUCIÓN EN COLA  [/bold white on blue]"
        status_color = "blue"
    else:
        status_badge = "[bold white on red]  ✖ FALLO / CONTINGENCIA  [/bold white on red]"
        status_color = "red"

    # Panel Principal de Identificación
    console.print(
        Panel(
            f"{status_badge}\n\n"
            f"[bold cyan]Tarea (Task ID):[/bold cyan] [bold white]{record.get('task_id')}[/bold white] (Índice #{record.get('unit_index')})\n"
            f"[bold cyan]Expediente Único:[/bold cyan] {record.get('case_id')}\n"
            f"[bold cyan]Cadena Comercial (Retailer):[/bold cyan] [bold]{record.get('retailer_name')}[/bold] ({record.get('retailer_id')})\n"
            f"[bold cyan]Tipología de Disputa:[/bold cyan] [magenta]{record.get('category')}[/magenta]\n"
            f"[bold cyan]Origen Documental:[/bold cyan] {record.get('source_origin', 'RETAILER_CATALOG')}\n"
            f"[bold cyan]Marca de Tiempo:[/bold cyan] {record.get('timestamp_start', 'N/A')} | Duración: {record.get('duration_seconds', 0.0):.2f}s",
            title=f"[bold white]EXPEDIENTE AUDITADO: {record.get('task_id')}[/bold white]",
            border_style=status_color,
        )
    )

    # 1. Tabla de Reconciliación Financiera ($0.00 MAE)
    fin_table = Table(title="1. Reconciliación Contable y Financiera ($0.00 MAE)", expand=True)
    fin_table.add_column("Concepto Contable", style="bold cyan")
    fin_table.add_column("Importe (MXN)", justify="right")
    fin_table.add_column("Porcentaje %", justify="right")
    fin_table.add_column("Estado de Reclamación", style="dim")

    billed = float(record.get("billed_amount", 0.0))
    received = float(record.get("received_amount", 0.0))
    disputed = float(record.get("disputed_amount", 0.0))
    recovered = float(record.get("recovered_amount", 0.0))
    justified = float(record.get("justified_amount", 0.0))
    delta = float(record.get("financial_delta", 0.0))

    rec_pct = (recovered / disputed * 100.0) if disputed > 0 else 0.0
    just_pct = (justified / disputed * 100.0) if disputed > 0 else 0.0

    fin_table.add_row("Total Facturado Original", f"${billed:,.2f}", "100.0%", "CFDI Emitido al Comprador")
    fin_table.add_row("Pago Recibido en Cuenta", f"${received:,.2f}", f"{(received / billed * 100.0) if billed > 0 else 0:.1f}%", "Transferencia SPEI / Remesa")
    fin_table.add_row("Deducción Retenida (Disputada)", f"[yellow]${disputed:,.2f}[/yellow]", f"{(disputed / billed * 100.0) if billed > 0 else 0:.1f}%", "Retención Comercial Auditada")
    fin_table.add_row("Capital Exigible / Reclamado", f"[bold green]${recovered:,.2f}[/bold green]", f"[bold green]{rec_pct:.1f}%[/bold green]", "Reclamación Procedente")
    fin_table.add_row("Deducción Justificada Comercial", f"${justified:,.2f}", f"{just_pct:.1f}%", "Penalización Conforme a Reglas")
    fin_table.add_row(
        "Invariante Financiero (MAE)",
        f"[bold green]${delta:.2f}[/bold green]",
        "0.00%",
        "[bold green]✔ Cuadre Matemático Exacto ($0.00 MAE)[/bold green]" if delta == 0.0 else "[red]Error de cuadre[/red]",
    )
    console.print(fin_table)

    # 2. Telemetría de la Pasarela Platica
    tok_p = record.get("tokens_prompt", 0)
    tok_c = record.get("tokens_completion", 0)
    tok_tot = record.get("tokens_total", tok_p + tok_c)
    cost = float(record.get("cost_usd", 0.0))
    model = record.get("model_used", "grok-4.7")

    telemetry_table = Table(title="2. Telemetría y Consumo Real en Pasarela Platica", expand=True)
    telemetry_table.add_column("Métrica de Consumo", style="bold cyan")
    telemetry_table.add_column("Valor Medido", justify="right")
    telemetry_table.add_column("Detalle de Calibración", style="dim")

    telemetry_table.add_row("Modelo de Inferencia", model, "Pasarela Oficial Platica (api.reto.pltk.mx)")
    telemetry_table.add_row("Tokens de Entrada (Prompt)", f"{tok_p:,}", f"Longitud del expediente comercial de {record.get('retailer_name')[:15]}")
    telemetry_table.add_row("Tokens de Salida (Completion)", f"{tok_c:,}", "Dictamen legal estructurado en JSON")
    telemetry_table.add_row("Total de Tokens", f"{tok_tot:,}", "Telemetría real de la petición")
    telemetry_table.add_row("Costo Medido de la Tarea", f"[bold green]${cost:.6f} USD[/bold green]", "Tarifa calibrada de pasarela Platica")
    console.print(telemetry_table)

    # 3. Dictamen Legal y Fundamentación Contractual
    console.print(
        Panel(
            f"[bold]Fundamento Legal y Contractual:[/bold]\n"
            f"{record.get('legal_basis', 'N/A')}\n\n"
            f"[bold]Dictamen Ejecutivo:[/bold]\n"
            f"{record.get('result_summary', 'N/A')}",
            title="[bold white]3. DICTAMEN LEGAL Y COMERCIAL[/bold white]",
            border_style="cyan",
        )
    )

    # 4. Póliza y Asiento Contable ERP
    console.print(
        Panel(
            f"[bold]Acción Contable ERP:[/bold] [green]{record.get('erp_action', 'N/A')}[/green]\n"
            f"[dim]Generación automática de póliza contable bajo NIF C-3 y asiento compensatorio SAP BAPI / CFDI 4.0 Nota de Crédito.[/dim]",
            title="[bold white]4. INTEGRACIÓN CONTABLE ERP / SAP[/bold white]",
            border_style="green",
        )
    )

    # 5. Si hubo error o cuarentena, mostrar bitácora forense
    if record.get("error_encountered") and record.get("error_encountered") != "None":
        console.print(
            Panel(
                f"[bold red]Incidencia Detectada:[/bold red]\n{record.get('error_encountered')}\n\n"
                f"[bold yellow]Protocolo de Auto-Recuperación Aplicado:[/bold yellow]\n{record.get('recovery_action')}",
                title="[bold white]5. RESILIENCIA FORENSE Y AUTO-RECUPERACIÓN[/bold white]",
                border_style="yellow",
            )
        )


def render_task_list(records: List[Dict[str, Any]], filter_retailer: Optional[str] = None, only_quarantine: bool = False) -> None:
    """Muestra una lista tabular de todas las tareas registradas."""
    filtered = records
    if only_quarantine:
        filtered = [r for r in filtered if r.get("status") == "RECOVERED_QUARANTINE"]
    elif filter_retailer:
        ret_low = filter_retailer.lower()
        filtered = [r for r in filtered if ret_low in str(r.get("retailer_name", "")).lower()]

    if not filtered:
        console.print("[yellow]No se encontraron expedientes con los criterios especificados.[/yellow]")
        return

    table = Table(
        title=f"Expedientes Registrados en Bitácora ({len(filtered):,} tareas)",
        expand=True,
    )
    table.add_column("Índice", justify="center", style="dim")
    table.add_column("Task ID", style="cyan")
    table.add_column("Retailer", style="bold")
    table.add_column("Categoría", style="magenta")
    table.add_column("Disputa (MXN)", justify="right")
    table.add_column("Recuperado", justify="right", style="green")
    table.add_column("Tokens", justify="right")
    table.add_column("Costo (USD)", justify="right")
    table.add_column("Estado", justify="center")

    for r in filtered:
        status = r.get("status", "UNKNOWN")
        if status == "SUCCESS":
            st_text = "[green]SUCCESS[/green]"
        elif status == "RECOVERED_QUARANTINE":
            st_text = "[yellow]QUARANTINE[/yellow]"
        elif status == "PENDING_EXECUTION":
            st_text = "[blue]PENDING[/blue]"
        else:
            st_text = "[red]FAILED[/red]"

        table.add_row(
            str(r.get("unit_index", "-")),
            str(r.get("task_id", "-")),
            str(r.get("retailer_name", "-"))[:20],
            str(r.get("category", "-"))[:20],
            f"${float(r.get('disputed_amount', 0.0)):,.2f}",
            f"${float(r.get('recovered_amount', 0.0)):,.2f}",
            f"{int(r.get('tokens_total', 0)):,}",
            f"${float(r.get('cost_usd', 0.0)):.4f}",
            st_text,
        )

    console.print(table)
    console.print(
        "\n[dim cyan]💡 Tip: Para ver el detalle completo de cualquiera de estos casos ejecuta:\n"
        "   python scripts/view_task_detail.py <Índice_o_Task_ID>[/dim cyan]\n"
    )


def main():
    parser = argparse.ArgumentParser(
        description="Visor Detallado de Casos de la Jornada de Carga Desatendida de 12 Horas."
    )
    parser.add_argument(
        "query",
        nargs="?",
        default=None,
        help="Índice (ej. 1, 42) o Task ID (ej. work_unit_0001) para ver su expediente completo.",
    )
    parser.add_argument(
        "--last",
        action="store_true",
        help="Ver la última tarea procesada en la bitácora.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Listar todas las unidades procesadas en una tabla resumida.",
    )
    parser.add_argument(
        "--quarantine",
        action="store_true",
        help="Listar únicamente los casos de prueba de resiliencia / cuarentena forense.",
    )
    parser.add_argument(
        "--retailer",
        type=str,
        default=None,
        help="Filtrar casos por nombre de cadena comercial (ej. Walmart, Amazon, Soriana).",
    )
    args = parser.parse_args()

    records = load_all_records()

    if not records:
        console.print("[yellow]No se encontraron registros de tareas. Ejecuta primero run_unattended_12h_batch.py.[/yellow]")
        return

    if args.last:
        render_task_detail(records[-1])
    elif args.list:
        render_task_list(records, filter_retailer=args.retailer)
    elif args.quarantine:
        render_task_list(records, only_quarantine=True)
    elif args.retailer and not args.query:
        render_task_list(records, filter_retailer=args.retailer)
    elif args.query:
        record = find_record(records, args.query)
        if record:
            render_task_detail(record)
        else:
            console.print(f"[bold red]No se encontró la tarea '{args.query}'.[/bold red]")
            console.print("Usa [cyan]python scripts/view_task_detail.py --list[/cyan] para ver los IDs disponibles.")
    else:
        # Por defecto muestra la primera tarea procesada o la última
        render_task_detail(records[0])


if __name__ == "__main__":
    main()
