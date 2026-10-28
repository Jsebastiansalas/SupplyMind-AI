"""
Test Suite Formal para el Benchmark Suite de 35 Casos B2B (SupplyMind AI - Sprint 3.2).
Valida que la suite completa logre:
- 100% Exact Match Accuracy (35/35 casos)
- 0% Tasa de Error Aritmetico (MAE = $0.00 USD)
- 100% Cuarentena Forense (3/3 casos adversariales o anacronicos aislados)
- 0% Alucinacion Factica o Numerica
"""

import os
import json
import pytest
from pathlib import Path
from decimal import Decimal

from scripts.benchmark_30_cases import run_35_cases_benchmark


def test_benchmark_suite_35_cases_metrics():
    """Ejecuta el benchmark completo de 35 casos y verifica metricas periciales."""
    summary = run_35_cases_benchmark(verbose=False)
    
    assert summary["total_cases_evaluated"] == 35, "Deben evaluarse exactamente 35 casos"
    assert summary["cases_passed"] == 35, f"Esperado 35 casos aprobados, obtenido {summary['cases_passed']}"
    assert summary["exact_match_accuracy_pct"] == 100.0, "La precision exacta debe ser 100.0%"
    assert summary["arithmetic_error_count"] == 0, "No debe haber errores aritmeticos ni de redondeo"
    assert summary["mean_absolute_error_usd"] == 0.0, "El MAE financiero debe ser $0.00 USD"
    assert summary["quarantine_success_rate_pct"] == 100.0, "El 100% de los expedientes toxicos deben ser aislados"
    assert summary["hallucination_rate_pct"] == 0.0, "La tasa de alucinacion debe ser estrictamente 0.0%"


def test_benchmark_artifacts_persisted():
    """Verifica que los artefactos de reporte Markdown y JSON se generen y tengan el formato correcto."""
    json_path = Path("reports/benchmark_suite_35_cases_report.json")
    md_path = Path("reports/benchmark_suite_35_cases_report.md")

    assert json_path.exists(), "El reporte JSON del benchmark debe existir"
    assert md_path.exists(), "El reporte Markdown del benchmark debe existir"

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["total_cases_evaluated"] == 35
    assert data["cases_passed"] == 35
    assert len(data["cases"]) == 35
    assert data["arithmetic_error_count"] == 0
    assert data["mean_absolute_error_usd"] == 0.0

    # Verificar que los casos en cuarentena esten explicitamente identificados
    quarantined = [c for c in data["cases"] if c["is_quarantine"]]
    assert len(quarantined) == 3, f"Deben existir 3 casos en cuarentena, se hallaron {len(quarantined)}"
    quarantine_ids = {c["case_id"] for c in quarantined}
    assert quarantine_ids == {
        "case_031_adversarial_prompt_injection",
        "case_032_quarantine_cross_contamination",
        "case_033_quarantine_anachronistic_dates"
    }


def test_financial_volume_invariants():
    """Verifica que el volumen financiero auditado conserve las sumas invariantes."""
    json_path = Path("reports/benchmark_suite_35_cases_report.json")
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    sum_disputed = sum(Decimal(str(c["dispute_amount"])) for c in data["cases"])
    assert sum_disputed == Decimal("627400.00"), f"Volumen auditado esperado $627,400.00, obtenido ${sum_disputed}"
