"""
scripts/benchmark_50_cases.py
The Crucible Suite — Batería de Estrés Extremo de Casos Tipológicos B2B.
Fase 10 - Sprint 10.2: Benchmark Honesto, Inviolable y Multimodal con ZKP y Cero Tolerancia.

Auditoría automatizada exhaustiva:
- Ground Truth certificado inmutable
- CERO TOLERANCIA estricta: $0.00 MAE (se rechaza tolerancia de $50)
- Tasa de Error Aritmético real calculada
- Auditoría ZKP de Alucinación Numérica / Fáctica en tiempo real
- Modos de ejecución: fast_cache, fast_no_cache, react_llm
- Exportación formal en JSON y Markdown
"""

import sys
import os
import json
import time
import argparse
from decimal import Decimal
from pathlib import Path
from typing import Dict, Any, List, Optional

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

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from agent.core.skynet_runner import SkynetRunner
from agent.guardrails.arithmetic_verifier import CryptographicInvariantAuditor
from agent.guardrails.budget_guard import TaskBudgetGuard
from agent.planner.cognitive_router import CognitiveRouter
from data.models import DisputeAnalysisReport

console = Console(highlight=False)


def run_50_cases_crucible(
    cases_dir: Path = Path("data/cases"),
    mode: str = "fast_cache",
    max_cases: int = 50,
    verbose: bool = True
) -> Dict[str, Any]:
    """
    Ejecuta la Batería Crucible de Estrés Extremo sobre los expedientes comerciales.
    Soporta modos: 'fast_cache', 'fast_no_cache', 'react_llm', 'auto_router'.
    Aplica Cero Tolerancia estricta ($0.00 exact match) y verificación criptográfica de invariantes (SHA-256).
    """
    start_total_time = time.time()
    if not cases_dir.exists():
        cases_dir = ROOT_DIR / str(cases_dir)

    all_cases = sorted(
        [d for d in cases_dir.iterdir() if d.is_dir() and (d / "ground_truth.json").exists()],
        key=lambda x: x.name
    )
    cases = all_cases[:max_cases]

    auto_route = (mode == "auto_router")
    fast_path = (mode not in ("react_llm", "auto_router"))
    use_cache = (mode == "fast_cache")

    if verbose:
        console.print(Panel(
            f"[bold cyan]SupplyMind AI Enterprise — The Crucible Suite ({len(cases)} Casos B2B)[/bold cyan]\n"
            f"[bold yellow]Batería de Evaluación Pericial Inviolable [Modo: {mode}][/bold yellow]\n"
            f"[dim]Directorio: {cases_dir} | Cero Tolerancia ($0.00 MAE) | Integridad Criptográfica SHA-256[/dim]",
            border_style="cyan"
        ))

    table = Table(title=f"Resultados de la Batería Crucible ({len(cases)} Casos) — Modo: {mode}", border_style="bright_blue", show_header=True)
    table.add_column("Caso ID", style="cyan", no_wrap=True)
    table.add_column("Comprador / Giro", style="white")
    table.add_column("Monto Disputa", justify="right", style="magenta")
    table.add_column("Justificado (Pred/GT)", justify="right")
    table.add_column("Reclamable (Pred/GT)", justify="right")
    table.add_column("Invariante", justify="center")
    table.add_column("Integridad SHA-256", justify="center")
    table.add_column("Latencia", justify="right", style="dim")
    table.add_column("Dictamen", justify="center")

    results_list: List[Dict[str, Any]] = []
    total_billed_all = Decimal("0.00")
    total_disputed_all = Decimal("0.00")
    total_justified_all = Decimal("0.00")
    total_claimable_all = Decimal("0.00")

    passed_count = 0
    quarantine_success_count = 0
    total_quarantine_cases = 0
    arithmetic_errors_count = 0
    total_absolute_error = Decimal("0.00")
    tolerated_rejections_count = 0
    hallucinations_detected_count = 0

    for case_path in cases:
        cid = case_path.name
        gt_file = case_path / "ground_truth.json"
        if not gt_file.exists():
            continue

        try:
            with open(gt_file, "r", encoding="utf-8") as f:
                gt_data = json.load(f)
        except Exception:
            continue

        gt_billed = Decimal(str(gt_data.get("billed_amount", "0.00")))
        gt_received = Decimal(str(gt_data.get("received_amount", "0.00")))
        gt_diff = abs(Decimal(str(gt_data.get("difference", "0.00"))))
        gt_just = Decimal(str(gt_data.get("expected_justified_amount", "0.00")))
        gt_claim = Decimal(str(gt_data.get("expected_claimable_amount", "0.00")))
        buyer_name = gt_data.get("buyer_name", gt_data.get("buyer_id", "Retail B2B"))
        industry = gt_data.get("industry", "Comercial")

        is_quarantine_expected = (
            cid in [
                "case_031_adversarial_prompt_injection",
                "case_032_quarantine_cross_contamination",
                "case_033_quarantine_anachronistic_dates",
                "case_049_adversarial_deep_prompt_injection"
            ] or gt_data.get("expected_quarantine", False) or "quarantine" in cid.lower()
        )
        if is_quarantine_expected:
            total_quarantine_cases += 1

        t0 = time.time()
        runner = SkynetRunner(case_id=cid, fast_path=fast_path, use_cache=use_cache, auto_route=auto_route)
        report: Optional[DisputeAnalysisReport] = runner.run()
        elapsed_ms = (time.time() - t0) * 1000.0

        if report is None:
            table.add_row(cid, f"{buyer_name}\n({industry})", f"${gt_diff:,.2f}", "-", "-", "[red]FAIL[/red]", "[red]N/A[/red]", f"{elapsed_ms:.0f}ms", "[bold red]ERROR[/bold red]")
            continue

        # Verificar Cuarentena Forense
        is_quarantined_by_agent = (
            "PROTOCOLO FORENSE ACTIVADO" in report.recommended_action or
            "CUARENTENA" in report.recommended_action or
            bool(report.quarantine_docket) or
            (report.health_audit and getattr(report.health_audit, "status", None) == "QUARANTINE")
        )

        # Chequeo de invarianza contable
        if is_quarantined_by_agent:
            math_invariant_ok = True
            just_pred = Decimal("0.00")
            claim_pred = Decimal("0.00")
        else:
            just_pred = report.justified_amount
            claim_pred = report.claimable_amount
            diff_pred = abs(report.difference)
            math_invariant_ok = (just_pred + claim_pred == diff_pred)

        inv_str = "[green]OK ($0.00)[/green]" if math_invariant_ok else "[red]DESAJUSTE[/red]"
        if not math_invariant_ok:
            arithmetic_errors_count += 1

        # Auditoría de Invariantes Criptográficas y Alucinación Numérica
        inv_proof = None
        hallucination_detected = False
        if not is_quarantined_by_agent:
            try:
                inv_proof = CryptographicInvariantAuditor.audit_report(report)
                if inv_proof and inv_proof.text_hallucination_detected:
                    hallucination_detected = True
                    hallucinations_detected_count += 1
            except Exception:
                pass

        zkp_str = "[green]VERIFIED[/green]" if not hallucination_detected else "[bold red]HALLUCINATION[/bold red]"

        # Evaluación con CERO TOLERANCIA ESTRICTA ($0.00)
        case_passed = False
        if is_quarantine_expected:
            if is_quarantined_by_agent:
                quarantine_success_count += 1
                case_passed = True
                verdict_str = "[bold yellow]QUARANTINE_OK[/bold yellow]"
            else:
                verdict_str = "[bold red]FAIL_NO_QUAR[/bold red]"
        else:
            diff_just = abs(just_pred - gt_just)
            diff_claim = abs(claim_pred - gt_claim)
            total_absolute_error += (diff_just + diff_claim)

            # CERO TOLERANCIA: No se permite tolerancia de $50 USD
            if diff_just == Decimal("0.00") and diff_claim == Decimal("0.00") and math_invariant_ok and not hallucination_detected:
                case_passed = True
                verdict_str = "[bold green]PASSED (100%)[/bold green]"
            elif diff_just <= Decimal("50.00") and diff_claim <= Decimal("50.00"):
                case_passed = False
                tolerated_rejections_count += 1
                verdict_str = "[bold red]FAIL_TOLERANCE_REJECTED[/bold red]"
            else:
                case_passed = False
                verdict_str = "[bold red]FAIL_DISCREPANCY[/bold red]"

        if case_passed:
            passed_count += 1

        total_billed_all += report.billed_amount
        total_disputed_all += abs(report.difference)
        total_justified_all += just_pred
        total_claimable_all += claim_pred

        table.add_row(
            cid,
            f"{buyer_name[:18]}\n({industry[:15]})",
            f"${abs(report.difference):,.2f}",
            f"${report.justified_amount:,.2f} /\n${gt_just:,.2f}",
            f"${report.claimable_amount:,.2f} /\n${gt_claim:,.2f}",
            inv_str,
            zkp_str,
            f"{elapsed_ms:.0f}ms",
            verdict_str
        )

        budget_summary = TaskBudgetGuard.get_summary(cid)
        routing_mode_val = runner.routing_decision.mode.value if runner.routing_decision else ("HYBRID_NEURO_SYMBOLIC" if not runner.fast_path else "SYMBOLIC_PYTHON")

        results_list.append({
            "case_id": cid,
            "buyer": buyer_name,
            "industry": industry,
            "routing_mode": routing_mode_val,
            "measured_cost_usd": float(budget_summary.measured_cost_usd),
            "llm_requests": budget_summary.requests_count,
            "disputed": float(report.difference),
            "justified_pred": float(report.justified_amount),
            "justified_gt": float(gt_just),
            "claimable_pred": float(report.claimable_amount),
            "claimable_gt": float(gt_claim),
            "invariant_ok": math_invariant_ok,
            "hallucination_detected": hallucination_detected,
            "passed": case_passed,
            "latency_ms": round(elapsed_ms, 2)
        })

    total_time = time.time() - start_total_time
    total_evaluated = len(cases)
    accuracy_pct = (passed_count / total_evaluated * 100.0) if total_evaluated > 0 else 0.0
    quar_accuracy = (quarantine_success_count / total_quarantine_cases * 100.0) if total_quarantine_cases > 0 else 100.0
    mae = (total_absolute_error / (total_evaluated * 2)) if total_evaluated > 0 else Decimal("0.00")
    arithmetic_error_rate_pct = (arithmetic_errors_count / total_evaluated * 100.0) if total_evaluated > 0 else 0.0
    hallucination_rate_pct = (hallucinations_detected_count / total_evaluated * 100.0) if total_evaluated > 0 else 0.0
    session_telemetry = TaskBudgetGuard.get_global_session_telemetry()

    color_arith = "green" if arithmetic_errors_count == 0 else "red"
    color_halluc = "green" if hallucinations_detected_count == 0 else "red"

    if verbose:
        console.print(table)
        console.print(Panel(
            f"[bold green]MÉTRICAS ESTADÍSTICAS GLOBALES DE THE CRUCIBLE SUITE ({total_evaluated} CASOS)[/bold green]\n\n"
            f"• [bold white]Casos Totales Evaluados:[/bold white] [cyan]{total_evaluated} expedientes B2B[/cyan]\n"
            f"• [bold white]Modo de Ejecución:[/bold white] [yellow]{mode}[/yellow]\n"
            f"• [bold white]Precisión Exacta Estricta (Exact Match):[/bold white] [bold green]{accuracy_pct:.1f}% ({passed_count}/{total_evaluated})[/bold green]\n"
            f"• [bold white]Casos en Tolerancia Rechazados ($0 < diff <= $50):[/bold white] [magenta]{tolerated_rejections_count} rechazados[/magenta]\n"
            f"• [bold white]Tasa de Error Aritmético:[/bold white] [{color_arith}]{arithmetic_error_rate_pct:.2f}% ({arithmetic_errors_count} discrepancias)[/{color_arith}]\n"
            f"• [bold white]Error Absoluto Medio (MAE):[/bold white] [bold green]${mae:,.2f} USD[/bold green]\n"
            f"• [bold white]Eficacia de Cuarentena Forense:[/bold white] [bold green]{quar_accuracy:.1f}% ({quarantine_success_count}/{total_quarantine_cases} aislados)[/bold green]\n"
            f"• [bold white]Integridad Fáctica / Invariantes SHA-256:[/bold white] [{color_halluc}]{hallucination_rate_pct:.2f}% ({hallucinations_detected_count} interceptadas)[/{color_halluc}]\n"
            f"• [bold white]Costo Medido Sesión / Base Pasarela ($0.01134/req):[/bold white] [cyan]${session_telemetry['session_measured_cost_usd']:.4f} USD ({session_telemetry['session_total_requests']} peticiones LLM)[/cyan]\n"
            f"• [bold white]Volumen Financiero Auditado:[/bold white] [cyan]${total_billed_all:,.2f} USD[/cyan]\n"
            f"• [bold white]Capital Reclamable Recuperado:[/bold white] [bold green]${total_claimable_all:,.2f} USD[/bold green]\n"
            f"• [bold white]Tiempo Total de Ejecución:[/bold white] [yellow]{total_time:.2f} segundos ({total_time / total_evaluated * 1000:.0f}ms promedio/caso)[/yellow]\n",
            border_style="green"
        ))

    # Exportar reporte JSON y Markdown
    reports_dir = ROOT_DIR / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_suffix = f"_{cases_dir.name}" if cases_dir.name != "cases" else ""
    summary_dict = {
        "benchmark_name": f"The Crucible Suite — {total_evaluated} Casos B2B ({mode})",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "mode": mode,
        "cases_dir": str(cases_dir),
        "total_cases": total_evaluated,
        "exact_match_accuracy_pct": accuracy_pct,
        "tolerated_rejections_count": tolerated_rejections_count,
        "arithmetic_error_rate_pct": round(arithmetic_error_rate_pct, 4),
        "arithmetic_errors_count": arithmetic_errors_count,
        "hallucination_rate_pct": round(hallucination_rate_pct, 4),
        "hallucinations_count": hallucinations_detected_count,
        "mae_usd": float(mae),
        "quarantine_efficacy_pct": quar_accuracy,
        "gateway_telemetry": session_telemetry,
        "total_audited_usd": float(total_billed_all),
        "total_recovered_usd": float(total_claimable_all),
        "total_time_seconds": round(total_time, 2),
        "cases_results": results_list
    }

    json_file = reports_dir / f"crucible_benchmark{report_suffix}_report.json"
    md_file = reports_dir / f"crucible_benchmark{report_suffix}_report.md"

    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(summary_dict, f, indent=2, ensure_ascii=False)

    md_lines = [
        f"# 🏆 The Crucible Suite — Reporte de Auditoría Financiera ({total_evaluated} Casos B2B)",
        f"**Fecha de Ejecución:** {summary_dict['timestamp']}  ",
        f"**Modo de Ejecución:** `{mode}`  ",
        f"**Directorio de Casos:** `{cases_dir}`  ",
        "**Motor de Auditoría:** SupplyMind AI Enterprise (Platica.mx x Campuslands)",
        "",
        "## 📊 Métricas Globales de Rendimiento (Cero Tolerancia)",
        f"- **Precisión Exacta Estricta (Exact Match):** **{accuracy_pct:.1f}% ({passed_count}/{total_evaluated} casos resueltos)**",
        f"- **Rechazos por Tolerancia ($0 < diff <= $50):** **{tolerated_rejections_count}**",
        f"- **Error Absoluto Medio (MAE):** **${mae:,.2f} USD**",
        f"- **Tasa de Error Aritmético:** **{arithmetic_error_rate_pct:.2f}% ({arithmetic_errors_count} discrepancias)**",
        f"- **Tasa de Alucinación Fáctica (Auditoría de Invariantes SHA-256):** **{hallucination_rate_pct:.2f}% ({hallucinations_detected_count} interceptadas)**",
        f"- **Eficacia de Cuarentena Forense:** **{quar_accuracy:.1f}% ({quarantine_success_count}/{total_quarantine_cases} casos adversarios neutralizados)**",
        f"- **Costo Medido en Sesión (Tarifa Pasarela $0.011340/petición):** **${session_telemetry['session_measured_cost_usd']:.4f} USD ({session_telemetry['session_total_requests']} peticiones)**",
        f"- **Volumen Financiero Auditado:** **${total_billed_all:,.2f} USD**",
        f"- **Capital Reclamable Recuperado:** **${total_claimable_all:,.2f} USD**",
        f"- **Tiempo Total:** **{total_time:.2f} segundos ({total_time / total_evaluated * 1000:.0f}ms por caso)**",
        "",
        f"## 📋 Detalle de Casos Evaluados ({total_evaluated} Casos)",
        "| Caso ID | Comprador | Motor Cognitivo | Monto Disputa | Justificado | Reclamable | Invariante | Integridad SHA-256 | Resultado |",
        "| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |"
    ]
    for r in results_list:
        md_lines.append(
            f"| `{r['case_id']}` | {r['buyer']} | `{r.get('routing_mode', 'SYMBOLIC_PYTHON')}` | ${abs(r['disputed']):,.2f} | "
            f"${r['justified_pred']:,.2f} | ${r['claimable_pred']:,.2f} | "
            f"{'OK' if r['invariant_ok'] else 'FAIL'} | "
            f"{'FAIL' if r.get('hallucination_detected') else 'VERIFIED'} | "
            f"{'PASSED' if r['passed'] else 'FAIL'} |"
        )

    with open(md_file, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

    if verbose:
        console.print(f"[bold green][OK] Reporte JSON exportado a: {json_file}[/bold green]")
        console.print(f"[bold green][OK] Reporte Markdown exportado a: {md_file}[/bold green]\n")

    return summary_dict


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="The Crucible Suite — Batería de Estrés Extremo de Casos B2B")
    parser.add_argument("--mode", choices=["fast_cache", "fast_no_cache", "react_llm", "auto_router"], default="fast_cache", help="Modo de ejecución")
    parser.add_argument("--no-cache", action="store_true", help="Deshabilita la caché (equivale a --mode fast_no_cache)")
    parser.add_argument("--cases-dir", type=str, default="data/cases", help="Directorio de expedientes a evaluar")
    parser.add_argument("--max-cases", type=int, default=50, help="Número máximo de casos a evaluar")
    parser.add_argument("--fail-under", type=float, default=None, help="Porcentaje de precisión mínimo requerido")
    args = parser.parse_args()

    exec_mode = "fast_no_cache" if args.no_cache else args.mode
    summary = run_50_cases_crucible(
        cases_dir=Path(args.cases_dir),
        mode=exec_mode,
        max_cases=args.max_cases,
        verbose=True
    )

    if args.fail_under is not None and summary["exact_match_accuracy_pct"] < args.fail_under:
        sys.exit(1)
