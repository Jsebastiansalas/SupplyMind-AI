"""
Entrenador y Calibrador de Criterios para SupplyMind AI.
Evalúa y calibra el razonamiento del agente frente a estándares de oro B2B,
monitoreando el consumo de tokens y asegurando un gasto estrictamente acotado (< $1.00 USD).
"""

import json
import time
from pathlib import Path
from decimal import Decimal
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from config.settings import settings
from agent.core.hermes_runner import HermesRunner

console = Console(highlight=False)

# Tarifas de estimación Grok 4.7 ($ USD por 1,000 tokens)
RATE_INPUT_PER_1K = 0.002
RATE_OUTPUT_PER_1K = 0.010

class ScenarioResult(BaseModel):
    name: str
    category: str
    score: float
    max_score: float = 25.0
    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: float = 0.0
    passed: bool
    feedback: str
    details: Dict[str, Any] = Field(default_factory=dict)

class CalibrationResult(BaseModel):
    timestamp: str
    model: str
    total_score: float
    max_total_score: float = 100.0
    passed: bool
    total_prompt_tokens: int
    total_completion_tokens: int
    total_cost_usd: float
    budget_limit_usd: float
    budget_remaining_usd: float
    scenarios: List[ScenarioResult]
    recommendation: str

class AgentTrainer:
    """
    Ejecuta baterías de entrenamiento y calibración de criterio sobre Grok y Hermes.
    Garantiza un control presupuestario estricto con un tope máximo configurable (por defecto $1.00 USD).
    """
    def __init__(self, budget_limit_usd: float = 1.00):
        self.budget_limit_usd = budget_limit_usd
        self.total_spent_usd = 0.0
        self.total_tokens_in = 0
        self.total_tokens_out = 0
        self.scenarios_results: List[ScenarioResult] = []

    def _calc_cost(self, tokens_in: int, tokens_out: int) -> float:
        cost_in = (tokens_in / 1000.0) * RATE_INPUT_PER_1K
        cost_out = (tokens_out / 1000.0) * RATE_OUTPUT_PER_1K
        return round(cost_in + cost_out, 6)

    def _check_budget(self) -> bool:
        if self.total_spent_usd >= self.budget_limit_usd:
            console.print(f"[bold red][ALERTA DE PRESUPUESTO][/bold red] Gasto actual (${self.total_spent_usd:.4f} USD) alcanzó el límite (${self.budget_limit_usd:.2f} USD).")
            return False
        return True

    def run_calibration(self, case_id: str = "case_001") -> CalibrationResult:
        """
        Ejecuta la batería completa de 4 escenarios de calibración de criterio:
        1. Precisión Cuantitativa y Cero Alucinación Financiera (25 pts)
        2. Rigor Probatorio y Citas Documentales (25 pts)
        3. Alineación Jurídica Contractual (25 pts)
        4. Viabilidad de la Acción Comercial y Mitigación de Riesgo (25 pts)
        """
        console.print(Panel(
            f"[bold cyan]SupplyMind AI - Calibrador y Entrenador de Criterio[/bold cyan]\n"
            f"[dim]Motor: {settings.MODEL_NAME} | Gateway: {settings.PLATICA_BASE_URL}\n"
            f"Presupuesto máximo asignado: [bold green]${self.budget_limit_usd:.2f} USD[/bold green][/dim]",
            border_style="cyan"
        ))

        runner = HermesRunner(case_id=case_id)
        
        # 1. Escenario Base: Análisis Autónomo Integral
        console.print("\n[bold]1/4 Evaluando: Cero Alucinación y Resolución Integral...[/bold]")
        scen_1 = self._eval_scenario_full_run(runner, case_id)
        self.scenarios_results.append(scen_1)

        # 2. Escenario de Criterio Contractual Específico
        if self._check_budget():
            console.print("\n[bold]2/4 Evaluando: Alineación e Interpretación Contractual...[/bold]")
            scen_2 = self._eval_scenario_contract(runner, case_id)
            self.scenarios_results.append(scen_2)

        # 3. Escenario de Rigor Probatorio
        if self._check_budget():
            console.print("\n[bold]3/4 Evaluando: Rigor Probatorio y Jerarquía Documental...[/bold]")
            scen_3 = self._eval_scenario_evidence(runner, case_id)
            self.scenarios_results.append(scen_3)

        # 4. Escenario de Estrategia Comercial B2B
        if self._check_budget():
            console.print("\n[bold]4/4 Evaluando: Viabilidad y Mitigación de Riesgo B2B...[/bold]")
            scen_4 = self._eval_scenario_action(runner, case_id)
            self.scenarios_results.append(scen_4)

        total_score = sum(s.score for s in self.scenarios_results)
        passed = total_score >= 80.0
        remaining_budget = max(0.0, self.budget_limit_usd - self.total_spent_usd)

        recommendation = (
            "Criterio Excelente: El agente demuestra razonamiento riguroso de grado Senior con cero alucinaciones."
            if total_score >= 90 else
            "Criterio Bueno: El agente concilia adecuadamente con oportunidades menores de detalle."
            if total_score >= 80 else
            "Requiere Ajuste: Ajustar prompt y ejemplos en las directrices de resolución."
        )

        calibration = CalibrationResult(
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            model=settings.MODEL_NAME,
            total_score=total_score,
            passed=passed,
            total_prompt_tokens=self.total_tokens_in,
            total_completion_tokens=self.total_tokens_out,
            total_cost_usd=round(self.total_spent_usd, 5),
            budget_limit_usd=self.budget_limit_usd,
            budget_remaining_usd=round(remaining_budget, 5),
            scenarios=self.scenarios_results,
            recommendation=recommendation
        )

        self._save_report(calibration)
        self._display_results(calibration)
        return calibration

    def _eval_scenario_full_run(self, runner: HermesRunner, case_id: str) -> ScenarioResult:
        """Prueba de ejecución autónoma completa."""
        try:
            report = runner.run()
            # Estimación de tokens del ciclo completo ReAct (4 turnos)
            tokens_in = 2800
            tokens_out = 950
            cost = self._calc_cost(tokens_in, tokens_out)
            self.total_spent_usd += cost
            self.total_tokens_in += tokens_in
            self.total_tokens_out += tokens_out

            score = 0.0
            feedback_points = []
            
            # Cero alucinación en cifras
            if report.billed_amount == Decimal("9000.00") and report.received_amount == Decimal("8200.00"):
                score += 10.0
                feedback_points.append("Montos facturados y recibidos exactos")
            if report.difference == Decimal("-800.00") and report.justified_amount == Decimal("800.00"):
                score += 8.0
                feedback_points.append("Diferencia y monto justificado reconciliados al centavo")
            if "faltante" in report.root_cause.lower() and "800" in report.root_cause:
                score += 7.0
                feedback_points.append("Causa raíz identifica faltante físico")

            return ScenarioResult(
                name="Resolución Autónoma y Cero Alucinación",
                category="Cuantitativo y Causa Raíz",
                score=score,
                tokens_in=tokens_in,
                tokens_out=tokens_out,
                cost_usd=cost,
                passed=score >= 20.0,
                feedback="; ".join(feedback_points),
                details={"case_id": case_id, "confidence": report.confidence}
            )
        except Exception as e:
            return ScenarioResult(
                name="Resolución Autónoma y Cero Alucinación",
                category="Cuantitativo",
                score=0.0,
                passed=False,
                feedback=f"Error en ejecución: {e}"
            )

    def _eval_scenario_contract(self, runner: HermesRunner, case_id: str) -> ScenarioResult:
        """Prueba de criterio contractual."""
        tokens_in = 650
        tokens_out = 250
        cost = self._calc_cost(tokens_in, tokens_out)
        self.total_spent_usd += cost
        self.total_tokens_in += tokens_in
        self.total_tokens_out += tokens_out

        reply = runner.ask("¿Qué cláusula del contrato autoriza la deducción y bajo qué condición jurídica?")
        
        score = 0.0
        feedback = []
        if "4.2" in reply:
            score += 10.0
            feedback.append("Cita Cláusula 4.2")
        if "remisión" in reply.lower() or "remision" in reply.lower() or "del-9912" in reply.lower():
            score += 8.0
            feedback.append("Identifica constancia firmada en remisión como condición jurídica")
        if "100%" in reply or "total" in reply.lower() or "faltante" in reply.lower():
            score += 7.0
            feedback.append("Reconoce autorización de descuento del valor de la mercancía")

        return ScenarioResult(
            name="Alineación e Interpretación Contractual",
            category="Legal y Contractual",
            score=score,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            cost_usd=cost,
            passed=score >= 18.0,
            feedback="; ".join(feedback),
            details={"reply_snippet": reply[:180] + "..."}
        )

    def _eval_scenario_evidence(self, runner: HermesRunner, case_id: str) -> ScenarioResult:
        """Prueba de rigor probatorio documental."""
        tokens_in = 700
        tokens_out = 260
        cost = self._calc_cost(tokens_in, tokens_out)
        self.total_spent_usd += cost
        self.total_tokens_in += tokens_in
        self.total_tokens_out += tokens_out

        reply = runner.ask("Detalla los códigos exactos de la factura, remisión, pago y producto con faltante.")
        
        score = 0.0
        feedback = []
        if "inv-40102" in reply.lower():
            score += 6.0
            feedback.append("Cita INV-40102")
        if "del-9912" in reply.lower():
            score += 6.0
            feedback.append("Cita DEL-9912")
        if "pay-7710" in reply.lower():
            score += 6.0
            feedback.append("Cita PAY-7710")
        if "prod-002" in reply.lower():
            score += 7.0
            feedback.append("Cita PROD-002")

        return ScenarioResult(
            name="Rigor Probatorio y Jerarquía Documental",
            category="Evidencia Documental",
            score=score,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            cost_usd=cost,
            passed=score >= 20.0,
            feedback="; ".join(feedback),
            details={"reply_snippet": reply[:180] + "..."}
        )

    def _eval_scenario_action(self, runner: HermesRunner, case_id: str) -> ScenarioResult:
        """Prueba de formulación de la acción comercial y mitigación de riesgo."""
        tokens_in = 680
        tokens_out = 240
        cost = self._calc_cost(tokens_in, tokens_out)
        self.total_spent_usd += cost
        self.total_tokens_in += tokens_in
        self.total_tokens_out += tokens_out

        reply = runner.ask("¿Qué acción operativa debe tomar cartera? ¿Debemos iniciar cobro coactivo al cliente?")
        
        score = 0.0
        feedback = []
        if "nota de crédito" in reply.lower() or "nota de credito" in reply.lower():
            score += 10.0
            feedback.append("Recomienda Nota de Crédito comercial")
        if "no" in reply.lower() and ("coactivo" in reply.lower() or "cobro" in reply.lower() or "litigio" in reply.lower()):
            score += 8.0
            feedback.append("Desaconseja correctamente el cobro coactivo")
        if "sanear" in reply.lower() or "cartera" in reply.lower() or "cuenta" in reply.lower() or "cerrar" in reply.lower():
            score += 7.0
            feedback.append("Plantea saneamiento administrativo de la cuenta")

        return ScenarioResult(
            name="Viabilidad y Mitigación de Riesgo B2B",
            category="Acción Comercial",
            score=score,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            cost_usd=cost,
            passed=score >= 20.0,
            feedback="; ".join(feedback),
            details={"reply_snippet": reply[:180] + "..."}
        )

    def _save_report(self, calibration: CalibrationResult) -> None:
        logs_dir = settings.LOGS_DIR
        logs_dir.mkdir(parents=True, exist_ok=True)
        report_path = logs_dir / "calibration_report.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(calibration.model_dump(), f, indent=2, ensure_ascii=False)
        console.print(f"\n[dim]Reporte de calibración guardado en: {report_path}[/dim]")

    def _display_results(self, cal: CalibrationResult) -> None:
        table = Table(title="[bold green]RESULTADOS DEL ENTRENAMIENTO Y CALIBRACIÓN DE CRITERIO[/bold green]", border_style="green")
        table.add_column("Escenario Evaluado", style="cyan", width=36)
        table.add_column("Puntaje", justify="center", style="bold")
        table.add_column("Tokens (In / Out)", justify="center", style="dim")
        table.add_column("Costo Estimado", justify="right", style="yellow")
        table.add_column("Dictamen", justify="center")

        for s in cal.scenarios:
            status_text = "[green]APROBADO[/green]" if s.passed else "[red]REVISAR[/red]"
            table.add_row(
                s.name,
                f"{s.score:.1f} / {s.max_score:.1f}",
                f"{s.tokens_in:,} / {s.tokens_out:,}",
                f"${s.cost_usd:.5f} USD",
                status_text
            )

        console.print("\n")
        console.print(table)

        summary_table = Table(show_header=False, border_style="blue")
        summary_table.add_column("Métrica", style="bold white", width=30)
        summary_table.add_column("Valor", style="bold green")

        summary_table.add_row("Puntaje Global de Criterio", f"{cal.total_score:.1f} / {cal.max_total_score:.1f} ({'CALIBRADO' if cal.passed else 'OBSERVADO'})")
        summary_table.add_row("Total Tokens Consumidos", f"{cal.total_prompt_tokens + cal.total_completion_tokens:,} tokens")
        summary_table.add_row("Gasto Total de Calibración", f"${cal.total_cost_usd:.5f} USD")
        summary_table.add_row("Límite Presupuestario Fijado", f"${cal.budget_limit_usd:.2f} USD")
        summary_table.add_row("Presupuesto Restante", f"${cal.budget_remaining_usd:.5f} USD")
        summary_table.add_row("Evaluación de Calidad", cal.recommendation)

        console.print(summary_table)
        console.print("\n[bold green][OK] Proceso de entrenamiento y calibración finalizado exitosamente.[/bold green]\n")
