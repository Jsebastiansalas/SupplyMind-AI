"""
Prueba Pericial Automatizada de The Crucible Suite (50 Casos B2B).
Valida que SupplyMind AI resuelva el 100% de los 50 casos del reto
con 0.00% de error aritmético y 100% de contención ante ataques adversarios.
"""

import json
from pathlib import Path
from decimal import Decimal
import pytest
from scripts.benchmark_50_cases import run_50_cases_crucible


def test_the_crucible_50_cases_benchmark():
    """Ejecuta The Crucible Suite (50 casos) y valida los umbrales de infalibilidad analítica."""
    summary = run_50_cases_crucible(verbose=False)

    assert summary["total_cases"] == 50, "La suite Crucible debe contener exactamente 50 casos."
    assert summary["exact_match_accuracy_pct"] == 100.0, (
        f"La precisión exacta esperada es 100.0%, obtenido: {summary['exact_match_accuracy_pct']}%"
    )
    assert summary["arithmetic_error_rate_pct"] == 0.0, "La tasa de error aritmético debe ser exactamente 0.00%."
    assert Decimal(str(summary["mae_usd"])) == Decimal("0.00"), f"El MAE debe ser $0.00 USD, obtenido: {summary['mae_usd']}"
    assert summary["quarantine_efficacy_pct"] == 100.0, "La contención de cuarentena forense debe ser 100.0%."

    # Verificar existencia de los reportes generados
    json_rep = Path("reports/crucible_benchmark_50_cases_report.json")
    md_rep = Path("reports/crucible_benchmark_50_cases_report.md")
    assert json_rep.exists(), "El reporte JSON del benchmark debe existir."
    assert md_rep.exists(), "El reporte Markdown del benchmark debe existir."
