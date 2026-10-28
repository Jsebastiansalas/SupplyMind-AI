"""
api/routes/batch.py
Endpoints para Procesamiento Batch Masivo Desatendido (Semana 4 - Sprint 4.2).
"""

from pathlib import Path
import json
from typing import Optional, List
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from tools.batch_processor.batch_runner import EnterpriseBatchProcessor
from tools.batch_processor.models import BatchExecutionSummary

router = APIRouter(prefix="/batch", tags=["Procesamiento Batch Masivo"])


class BatchRunRequest(BaseModel):
    cases_count: int = Field(default=100, ge=1, le=1000, description="Cantidad de expedientes a auditar en lote")
    workers: int = Field(default=8, ge=1, le=16, description="Hilos concurrentes de ejecución")


@router.post("/run")
def trigger_batch_execution(request: BatchRunRequest = BatchRunRequest()):
    """
    Ejecuta una corrida batch desatendida de alta concurrencia (hasta 1,000 unidades)
    y genera métricas macroeconómicas consolidadas de la cartera.
    """
    try:
        summary: BatchExecutionSummary = EnterpriseBatchProcessor.execute_batch(
            target_count=request.cases_count,
            max_workers=request.workers
        )
        json_path, md_path = EnterpriseBatchProcessor.export_batch_summary(summary)

        # Retornar dict serializado
        raw_dict = summary.model_dump()
        clean_dict = EnterpriseBatchProcessor._decimal_to_float(raw_dict)
        clean_dict["report_json_path"] = str(json_path)
        clean_dict["report_md_path"] = str(md_path)
        return clean_dict
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en ejecución batch: {str(e)}")


@router.get("/latest")
def get_latest_batch_summary():
    """Recupera el resumen consolidado del último lote batch ejecutado."""
    reports_dir = Path("reports")
    batch_files = sorted(reports_dir.glob("batch_summary_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not batch_files:
        raise HTTPException(status_code=404, detail="No se han registrado ejecuciones batch previas.")

    try:
        with open(batch_files[0], "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al leer resumen batch: {str(e)}")
