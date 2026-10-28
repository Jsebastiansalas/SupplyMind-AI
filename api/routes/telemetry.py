"""
api/routes/telemetry.py
Métricas de Eficiencia Operativa, Unit Economics y ROI Corporativo para SupplyMind AI.
Provee datos cuantificables de rentabilidad e impacto de negocio para evaluación del VP Operations y CFO.
"""

from typing import Dict, Any
from pathlib import Path
import json
from fastapi import APIRouter, HTTPException

from tools.telemetry.cost_tracker import generate_full_unit_economics_report

router = APIRouter(prefix="/telemetry", tags=["Telemetría & Unit Economics"])


@router.get("/unit-economics")
def get_unit_economics() -> Dict[str, Any]:
    """
    Retorna métricas de ROI y unit economics comparativos entre SupplyMind AI y analistas humanos.
    Lee el artefacto oficial generado por el motor de telemetría.
    """
    json_path = Path("reports/unit_economics_cost_report.json")
    if json_path.exists():
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    # Generación dinámica si no existe el archivo
    report = generate_full_unit_economics_report(total_benchmark_cases=35)
    return report.model_dump(mode="json")


@router.get("/benchmark")
def get_benchmark_report() -> Dict[str, Any]:
    """
    Retorna los resultados periciales del Benchmark Suite de los 35 Casos B2B.
    """
    json_path = Path("reports/benchmark_suite_35_cases_report.json")
    if not json_path.exists():
        raise HTTPException(
            status_code=404,
            detail="El reporte del benchmark de 35 casos no se ha generado aún. Ejecute scripts/benchmark_30_cases.py"
        )
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


@router.post("/benchmark/run")
def trigger_benchmark() -> Dict[str, Any]:
    """
    Dispara la ejecución del benchmark de 35 casos y retorna el resumen pericial actualizado.
    """
    from scripts.benchmark_30_cases import run_35_cases_benchmark
    summary = run_35_cases_benchmark(verbose=False)
    return summary

