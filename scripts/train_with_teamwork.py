"""
scripts/train_with_teamwork.py
Script CLI de Producción para Entrenamiento Adversarial y Calibración Colegiada de SupplyMind AI.

Argumentos soportados:
  --budget <float>      Tope presupuestario máximo en USD (por defecto: 1.00 USD)
  --cases <int>         Número de casos adversariales a evaluar por nivel / sesión (por defecto: 2)
  --curriculum          Ejecuta la progresión completa a través de los 5 niveles curriculares
  --simulate            Modo offline determinístico a costo cero ($0.00 USD de tokens)
  --report <path>       Ruta de guardado del informe Markdown ejecutivo (por defecto: reports/adversarial_training_report.md)
  --mastery <float>     Umbral de puntuación para alcanzar la maestría (por defecto: 90.0)

Muestra panel en vivo con Rich (Scoreboard de CFO, Legal y COO, Unit Economics y Directivas),
y persiste los resultados en logs/multiagent_training_report.json y reports/.
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional

# Configuración de salida segura UTF-8 para consola en Windows
if sys.platform == "win32":
    try:
        if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Asegurar path raíz del proyecto
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from config.settings import settings
from agent.planner.precedents import PrecedentRegistry
from agent.training.budget import BudgetTracker
from agent.training.curriculum import CurriculumManager, CurriculumTrainer
from agent.training.factory.case_synthesizer import AdversarialCaseSynthesizer
from agent.training.runner_bridge import TrainingRunnerBridge
from agent.training.tribunal.tribunal import CollegiateTribunal

console = Console(highlight=False)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="SupplyMind AI - Entrenamiento Adversarial y Calibración Colegiada CLI",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--budget",
        type=float,
        default=getattr(settings, "BUDGET_LIMIT_USD", 5.00),
        help="Presupuesto máximo asignado en USD para la sesión",
    )
    parser.add_argument(
        "--elite",
        action="store_true",
        default=True,
        help="Entrenar y evaluar exclusivamente la cartera de élite (2 casos más exigentes + 2 casos reales)",
    )
    parser.add_argument(
        "--cases",
        type=int,
        default=4,
        help="Número de casos adversariales a generar y entrenar",
    )
    parser.add_argument(
        "--curriculum",
        action="store_true",
        default=False,
        help="Ejecutar el curriculum progresivo completo de 5 niveles",
    )
    parser.add_argument(
        "--simulate",
        action="store_true",
        default=False,
        help="Ejecutar en modo simulación determinística con costo cero ($0.00 USD)",
    )
    parser.add_argument(
        "--report",
        type=str,
        default="reports/adversarial_training_report.md",
        help="Ruta de salida del reporte ejecutivo en Markdown",
    )
    parser.add_argument(
        "--mastery",
        type=float,
        default=90.0,
        help="Puntuación mínima requerida sobre 100 para aprobar la maestría",
    )
    return parser.parse_args()


def render_header(args: argparse.Namespace) -> None:
    mode_str = "[bold yellow]SIMULACIÓN DETERMINÍSTICA ($0.00 USD)[/bold yellow]" if args.simulate else "[bold green]LIVE API GROK 4.7 GATEWAY[/bold green]"
    if args.curriculum:
        curr_str = "[bold magenta]CURRICULUM 6 NIVELES (ENTERPRISE DOCKET)[/bold magenta]"
    elif args.elite:
        curr_str = "[bold cyan]CARTERA ÉLITE (2 MÁS EXIGENTES + 2 REALES)[/bold cyan]"
    else:
        curr_str = f"[bold cyan]BATERÍA ADVERSARIAL ({args.cases} casos)[/bold cyan]"

    console.print(Panel(
        f"[bold white]SupplyMind AI — Multi-Agent Adversarial Training & Collegiate Calibration[/bold white]\n\n"
        f"  • [dim]Modalidad:[/dim] {mode_str}\n"
        f"  • [dim]Estrategia:[/dim] {curr_str}\n"
        f"  • [dim]Presupuesto Máximo:[/dim] [bold green]${args.budget:.2f} USD[/bold green]\n"
        f"  • [dim]Umbral de Maestría:[/dim] [bold cyan]>={args.mastery:.1f} / 100 pts[/bold cyan]\n"
        f"  • [dim]Modelo:[/dim] {settings.MODEL_NAME} | Gateway: {settings.PLATICA_BASE_URL}",
        title="[bold cyan]SISTEMA DE ENTRENAMIENTO MULTIAGENTE[/bold cyan]",
        border_style="cyan",
    ))


def run_training_session(args: argparse.Namespace) -> int:
    render_header(args)

    budget_tracker = BudgetTracker(budget_limit_usd=args.budget)
    precedent_registry = PrecedentRegistry()
    trainer = CurriculumTrainer(
        budget_tracker=budget_tracker,
        precedent_registry=precedent_registry,
        mastery_threshold=args.mastery,
    )
    synthesizer = AdversarialCaseSynthesizer()

    evaluated_records: List[Dict[str, Any]] = []
    start_time = time.time()

    scoreboard = Table(
        title="[bold cyan]Scoreboard del Tribunal Colegiado (LLM-as-a-Judge)[/bold cyan]",
        header_style="bold white on navy_blue",
        border_style="bright_blue",
    )
    scoreboard.add_column("Caso ID", style="cyan", no_wrap=True)
    scoreboard.add_column("Tipología", style="yellow")
    scoreboard.add_column("CFO (/40)", justify="right", style="green")
    scoreboard.add_column("Legal (/30)", justify="right", style="magenta")
    scoreboard.add_column("COO (/30)", justify="right", style="blue")
    scoreboard.add_column("Total (/100)", justify="right", style="bold white")
    scoreboard.add_column("Estado Maestría", justify="center")
    scoreboard.add_column("Costo USD", justify="right", style="dim")

    # Selección de casos a evaluar
    if args.curriculum:
        console.print("\n[bold]Ejecutando recorrido curricular en 6 niveles progresivos (incluye Tier 6 Enterprise Mega Docket)...[/bold]\n")
        curriculum_res = trainer.train_full_curriculum(
            cases_per_tier=max(1, args.cases // 5 or 1),
            simulate=args.simulate,
        )
        evaluated_records = curriculum_res["results"]
    elif args.elite:
        console.print("\n[bold cyan]Evaluando y Calibrando los 4 Casos de Élite (2 Más Exigentes + 2 Reales)...[/bold cyan]\n")
        from tools.document_reader.reader import load_case_documents
        from agent.training.factory.ground_truth import GroundTruth, DiscrepancyCategory, CommercialActionType
        from tools.reconciliation_engine.engine import reconcile_dispute_data

        elite_targets = [
            ("case_009_mega_retailer_dispute", "Exigente: 40 SKUs Mega Retailer ($385k)", DiscrepancyCategory.MIXED),
            ("case_007_cisco_large_bundle", "Exigente: Cisco Large Infrastructure ($125k)", DiscrepancyCategory.MIXED),
            ("case_005_amazon_shortage", "Real: Amazon Fulfillment Center ($48k)", DiscrepancyCategory.PHYSICAL_SHORTAGE),
            ("case_006_walmart_otif_pricing", "Real: Walmart OTIF & Unit Price ($64.5k)", DiscrepancyCategory.PRICE_MISMATCH),
        ]

        for cid, typ_name, disc_cat in elite_targets:
            case_docs = load_case_documents(cid)
            gt_file = ROOT_DIR / "data" / "cases" / cid / "ground_truth.json"
            if gt_file.exists():
                with open(gt_file, "r", encoding="utf-8") as f:
                    gt_json = json.load(f)
                gt = GroundTruth(
                    case_id=cid,
                    category=disc_cat,
                    difficulty_level=5,
                    billed_amount=Decimal(str(gt_json["billed_amount"])),
                    received_amount=Decimal(str(gt_json["received_amount"])),
                    difference=Decimal(str(gt_json["difference"])),
                    expected_justified_amount=Decimal(str(gt_json["expected_justified_amount"])),
                    expected_claimable_amount=Decimal(str(gt_json["expected_claimable_amount"])),
                    expected_primary_category=disc_cat,
                    expected_commercial_action=(
                        CommercialActionType.MIXED_RESOLUTION
                        if "MIXED" in str(gt_json.get("category", "")).upper() or "RECOVERY" in str(gt_json.get("recommended_commercial_action", "")).upper()
                        else CommercialActionType.CREDIT_NOTE
                    ),
                    expected_contract_validity=True,
                )
            else:
                rec = reconcile_dispute_data(
                    invoice=case_docs["invoice"],
                    purchase_order=case_docs["purchase_order"],
                    delivery=case_docs["delivery"],
                    payment=case_docs["payment"],
                )
                gt = GroundTruth(
                    case_id=cid,
                    category=disc_cat,
                    difficulty_level=5,
                    billed_amount=rec.billed_amount,
                    received_amount=rec.received_amount,
                    difference=rec.difference,
                    expected_justified_amount=rec.justified_deductions_amount,
                    expected_claimable_amount=rec.unjustified_deductions_amount,
                    expected_primary_category=disc_cat,
                    expected_commercial_action=CommercialActionType.MIXED_RESOLUTION,
                )

            res = trainer.train_case(
                case_id=cid,
                case_docs=case_docs,
                ground_truth=gt,
                simulate=args.simulate,
            )
            res["typology"] = typ_name
            evaluated_records.append(res)
    else:
        console.print(f"\n[bold]Generando y evaluando batería de {args.cases} casos de frontera...[/bold]\n")
        typologies = [
            "unsigned_pod",
            "price_precedence",
            "extemporaneous_damage",
            "administrative_penalties",
            "compound_mixed",
            "tolerance_window",
        ]
        for i in range(1, args.cases + 1):
            typology = typologies[(i - 1) % len(typologies)]
            case_id = f"ADVER-{typology.upper()[:6]}-{i:03d}"
            case_docs, gt = synthesizer.generate_case(
                case_id=case_id,
                typology=typology,
                difficulty_level=((i - 1) % 5) + 1,
            )
            res = trainer.train_case(
                case_id=case_id,
                case_docs=case_docs,
                ground_truth=gt,
                simulate=args.simulate,
            )
            res["typology"] = typology
            evaluated_records.append(res)

    # Llenar scoreboard
    for rec in evaluated_records:
        cid = rec["case_id"]
        typ = rec.get("typology", "EXPEDIENTE_B2B")
        cfo = f"{rec.get('cfo_score', 0.0):.1f}"
        leg = f"{rec.get('legal_score', 0.0):.1f}"
        coo = f"{rec.get('operations_score', 0.0):.1f}"
        tot = f"{rec.get('total_score', 0.0):.1f}"
        passed = rec.get("passed_mastery", False)
        status = "[bold green]MAESTRÍA APROBADA[/bold green]" if passed else "[bold red]CALIBRANDO[/bold red]"
        cost = "$0.0000" if args.simulate else f"${rec.get('cost', 0.002):.4f}"

        scoreboard.add_row(cid, typ, cfo, leg, coo, tot, status, cost)

    console.print(scoreboard)

    # Tabla de Economía y Consumo de Tokens
    econ_table = Table(
        title="[bold green]Unit Economics & Presupuesto de Inferencia[/bold green]",
        header_style="bold white on dark_green",
        border_style="green",
    )
    econ_table.add_column("Métrica", style="bold")
    econ_table.add_column("Valor", justify="right", style="cyan")

    econ_table.add_row("Presupuesto Asignado", f"${budget_tracker.budget_limit_usd:.4f} USD")
    econ_table.add_row("Gasto Acumulado en Sesión", f"${budget_tracker.total_spent_usd:.4f} USD")
    econ_table.add_row("Presupuesto Restante", f"${budget_tracker.budget_remaining_usd:.4f} USD")
    econ_table.add_row("Tokens Entrada (Prompt)", f"{budget_tracker.total_tokens_in:,}")
    econ_table.add_row("Tokens Salida (Completion)", f"{budget_tracker.total_tokens_out:,}")
    avg_score = (
        sum(r["total_score"] for r in evaluated_records) / len(evaluated_records)
        if evaluated_records
        else 0.0
    )
    econ_table.add_row("Puntaje Promedio del Agente", f"{avg_score:.2f} / 100.0 pts")
    all_mastered = all(r["passed_mastery"] for r in evaluated_records)
    econ_table.add_row("Aprobación Global de Maestría", "[bold green]100% APROBADO[/bold green]" if all_mastered else "[bold yellow]PARCIAL[/bold yellow]")

    console.print("\n", econ_table)

    # Panel de Precedentes y Directivas Registradas
    all_precedents = precedent_registry.get_all_precedents()
    if all_precedents:
        prec_lines = [f"[bold white]Precedentes Registrados en la Base de Conocimiento ({len(all_precedents)}):[/bold white]"]
        for p in all_precedents[-5:]:  # Mostrar los últimos 5
            prec_lines.append(f"  • [[cyan]{p.get('case_id')}[/cyan]] [yellow]{p.get('dispute_type')}[/yellow]: {p.get('directive')}")
        console.print("\n", Panel("\n".join(prec_lines), title="[bold magenta]Jurisprudencia y Calibración de Directivas[/bold magenta]", border_style="magenta"))

    # =========================================================================
    # PERSISTENCIA DE REPORTES (JSON & Markdown)
    # =========================================================================
    logs_dir = ROOT_DIR / "logs"
    reports_dir = ROOT_DIR / "reports"
    logs_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    session_ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    duration_sec = round(time.time() - start_time, 2)

    session_payload: Dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "duration_seconds": duration_sec,
        "configuration": {
            "budget_limit_usd": args.budget,
            "simulate": args.simulate,
            "curriculum": args.curriculum,
            "cases_count": args.cases,
            "mastery_threshold": args.mastery,
        },
        "budget_summary": budget_tracker.summary(),
        "evaluation_summary": {
            "total_cases": len(evaluated_records),
            "passed_cases": sum(1 for r in evaluated_records if r["passed_mastery"]),
            "average_score": round(avg_score, 2),
            "all_passed_mastery": all_mastered,
        },
        "cases": [
            {
                "case_id": r["case_id"],
                "typology": r.get("typology", "GENERAL"),
                "cfo_score": r.get("cfo_score", 0.0),
                "legal_score": r.get("legal_score", 0.0),
                "operations_score": r.get("operations_score", 0.0),
                "total_score": r.get("total_score", 0.0),
                "passed_mastery": r.get("passed_mastery", False),
                "iterations": r.get("iterations", 1),
                "precedents_registered_count": len(r.get("precedents_registered", [])),
            }
            for r in evaluated_records
        ],
        "precedents_total_count": len(all_precedents),
    }

    # 1. Guardar log JSON principal y de sesión
    main_json_path = logs_dir / "multiagent_training_report.json"
    session_json_path = logs_dir / f"training_session_{session_ts}.json"

    with open(main_json_path, "w", encoding="utf-8") as f:
        json.dump(session_payload, f, ensure_ascii=False, indent=2)

    with open(session_json_path, "w", encoding="utf-8") as f:
        json.dump(session_payload, f, ensure_ascii=False, indent=2)

    # 2. Guardar reporte Markdown ejecutivo
    md_path = Path(args.report)
    if not md_path.is_absolute():
        md_path = ROOT_DIR / md_path
    md_path.parent.mkdir(parents=True, exist_ok=True)

    md_lines = [
        "# Reporte Ejecutivo: Entrenamiento Adversarial y Calibración Colegiada de SupplyMind AI",
        "",
        f"- **Fecha y Hora UTC:** {session_payload['timestamp']}",
        f"- **Duración:** {duration_sec} s",
        f"- **Modalidad:** {'Simulación Offline ($0.00 USD)' if args.simulate else 'Inferencia Live Grok 4.7'}",
        f"- **Estrategia:** {'Curriculum de 5 Niveles' if args.curriculum else f'Batería Adversarial ({args.cases} casos)'}",
        f"- **Presupuesto Asignado:** ${args.budget:.2f} USD",
        f"- **Gasto Consumido:** ${budget_tracker.total_spent_usd:.4f} USD",
        f"- **Puntaje Promedio:** {avg_score:.2f} / 100.0 pts",
        f"- **Aprobación de Maestría:** {'100% APROBADO' if all_mastered else 'REQUIERE CALIBRACIÓN ADICIONAL'}",
        "",
        "## 1. Tabla de Calificaciones del Tribunal Colegiado (LLM-as-a-Judge)",
        "",
        "| Caso ID | Tipología | CFO (/40) | Legal (/30) | COO (/30) | Total (/100) | Estado Maestría |",
        "|---|---|---|---|---|---|---|",
    ]

    for r in evaluated_records:
        cid = r["case_id"]
        typ = r.get("typology", "GENERAL")
        cfo = f"{r.get('cfo_score', 0.0):.1f}"
        leg = f"{r.get('legal_score', 0.0):.1f}"
        coo = f"{r.get('operations_score', 0.0):.1f}"
        tot = f"{r.get('total_score', 0.0):.1f}"
        st = "MAESTRÍA APROBADA" if r.get("passed_mastery") else "CALIBRANDO"
        md_lines.append(f"| {cid} | {typ} | {cfo} | {leg} | {coo} | {tot} | {st} |")

    md_lines.extend([
        "",
        "## 2. Auditoría Económica de Inferencia",
        "",
        f"- **Tokens de Entrada:** {budget_tracker.total_tokens_in:,}",
        f"- **Tokens de Salida:** {budget_tracker.total_tokens_out:,}",
        f"- **Costo Total USD:** ${budget_tracker.total_spent_usd:.4f} USD",
        f"- **Presupuesto Restante:** ${budget_tracker.budget_remaining_usd:.4f} USD",
        "",
        "## 3. Precedentes Jurisprudenciales Registrados",
        "",
    ])

    if all_precedents:
        for p in all_precedents:
            md_lines.append(f"- **[{p.get('case_id')}] {p.get('dispute_type')}:** {p.get('ruling')}")
            md_lines.append(f"  * *Directriz:* {p.get('directive')}")
    else:
        md_lines.append("No se registraron nuevos precedentes en esta sesión (los casos resolvieron con puntaje superior al umbral de maestría en primera instancia).")

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

    console.print(f"\n[bold green]Reportes generados exitosamente:[/bold green]")
    console.print(f"  • JSON Log: [cyan]{main_json_path}[/cyan]")
    console.print(f"  • Markdown Report: [cyan]{md_path}[/cyan]\n")

    return 0


def main() -> None:
    args = parse_args()
    sys.exit(run_training_session(args))


if __name__ == "__main__":
    main()
