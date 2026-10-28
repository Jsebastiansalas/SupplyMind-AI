"""
Test Suite para Unit Economics y Telemetria de Costo por Tarea (SupplyMind AI - Sprint 3.3).
Valida:
- Cumplimiento estricto del SLA (< $0.0050 USD por caso).
- Costo $0.000000 USD para tareas de computo local deterministico.
- Consumo exacto de tokens segun la matriz del Plan Maestro.
- Generacion y validez de los reportes en JSON y Markdown.
- Precision de la proyeccion de ROI anual.
"""

import json
from decimal import Decimal
from pathlib import Path
import pytest

from tools.telemetry.cost_tracker import (
    CostTracker,
    generate_full_unit_economics_report,
    UnitEconomicsGlobalReport
)


def test_average_cost_under_sla():
    """El costo promedio ponderado de inferencia debe ser estrictamente menor a $0.0050 USD."""
    report = generate_full_unit_economics_report(total_benchmark_cases=35)
    
    assert report.average_cost_per_case_usd < Decimal("0.005000"), (
        f"El costo promedio ${report.average_cost_per_case_usd} debe ser menor al SLA de $0.0050 USD"
    )
    assert report.sla_compliance is True, "El indicador de cumplimiento de SLA debe ser True"


def test_deterministic_local_tasks_zero_cost():
    """Las tareas contables y de emision ERP deterministica no deben generar costo de inferencia LLM."""
    std = CostTracker.audit_case_cost("case_005_amazon_shortage", sku_count=3, complexity_tier="STANDARD")

    # Identificar tarea 2 (Conciliacion Matematica) y tarea 5 (Poliza ERP)
    t2 = next(t for t in std.tasks if t.task_id == "TASK-2")
    t5 = next(t for t in std.tasks if t.task_id == "TASK-5")

    assert t2.cost_usd == Decimal("0.000000"), "La conciliacion matematica local debe tener costo $0.000000"
    assert t2.input_tokens == 0, "No debe consumir tokens de entrada al LLM"
    assert t2.output_tokens == 0, "No debe consumir tokens de salida del LLM"
    assert t2.execution_mode == "LOCAL_DETERMINISTIC"

    assert t5.cost_usd == Decimal("0.000000"), "La generacion de poliza ERP local debe tener costo $0.000000"
    assert t5.input_tokens == 0
    assert t5.output_tokens == 0
    assert t5.execution_mode == "LOCAL_DETERMINISTIC"


def test_standard_case_profile_tokens_and_cost():
    """Verifica que el caso estandar tenga 1,950 tokens de entrada y 480 de salida segun US-304."""
    std = CostTracker.audit_case_cost("case_001", sku_count=3, complexity_tier="STANDARD")

    assert std.total_input_tokens == 1950, f"Esperado 1,950 tokens in, obtenido {std.total_input_tokens}"
    assert std.total_output_tokens == 480, f"Esperado 480 tokens out, obtenido {std.total_output_tokens}"
    assert std.total_tokens == 2430, f"Esperado 2,430 tokens totales, obtenido {std.total_tokens}"
    assert std.total_cost_usd < Decimal("0.004000"), "El costo del caso estandar debe rondar los $0.00350 USD"


def test_unit_economics_artifacts_persistence():
    """Valida la integridad de los archivos exportados en reports/."""
    json_path = Path("reports/unit_economics_cost_report.json")
    md_path = Path("reports/unit_economics_cost_report.md")

    assert json_path.exists(), "El archivo reports/unit_economics_cost_report.json debe existir"
    assert md_path.exists(), "El archivo reports/unit_economics_cost_report.md debe existir"

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "gateway_model" in data
    assert "average_cost_per_case_usd" in data
    assert "comparative_unit_economics" in data
    assert len(data["comparative_unit_economics"]) >= 5
    assert data["sla_compliance"] is True

    with open(md_path, "r", encoding="utf-8") as f:
        md_text = f.read()

    assert "Arquitectura de Costos por Fase Operativa" in md_text
    assert "Matriz Comparativa de Unit Economics" in md_text
    assert "Retorno de Inversión Empresarial" in md_text


def test_annual_roi_savings_projection():
    """Verifica la proyeccion de ahorros millonarios para 100,000 disputas anuales."""
    report = generate_full_unit_economics_report(total_benchmark_cases=35)
    
    # 100k casos * $35.00 USD humano = $3,500,000 USD
    # Agente < $1,000 USD
    # Ahorro > $3,490,000 USD
    assert report.annual_savings_projection_100k_cases_usd > Decimal("3400000.00"), (
        f"Ahorro anual esperado > $3,400,000 USD, obtenido ${report.annual_savings_projection_100k_cases_usd}"
    )
