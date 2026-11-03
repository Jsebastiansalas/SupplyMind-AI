"""
api/routes/batch.py
Endpoints para Procesamiento Batch Masivo Desatendido (Semana 4 - Sprint 4.2).
"""

from pathlib import Path
import json
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from tools.batch_processor.batch_runner import EnterpriseBatchProcessor
from tools.batch_processor.models import BatchExecutionSummary
from agent.core.portfolio_optimizer import WorkingCapitalPortfolioOptimizer, PortfolioOptimizationSummary

router = APIRouter(prefix="/batch", tags=["Procesamiento Batch Masivo"])


class BatchRunRequest(BaseModel):
    cases_count: int = Field(default=100, ge=1, le=1000, description="Cantidad de expedientes a auditar en lote")
    workers: int = Field(default=8, ge=1, le=16, description="Hilos concurrentes de ejecución")


class PortfolioOptimizationRequest(BaseModel):
    case_ids: Optional[List[str]] = Field(default=None, description="Expedientes específicos a incluir en la auditoría")
    wacc_annual: float = Field(default=0.12, ge=0.0, le=1.0, description="Tasa de costo ponderado de capital WACC anual (ejemplo: 0.12 para 12%)")
    target_count: int = Field(default=50, ge=1, le=100, description="Cantidad máxima de expedientes a evaluar")


class BatchActionRequest(BaseModel):
    case_ids: List[str] = Field(..., description="Expedientes sobre los cuales ejecutar la acción masiva")
    action_type: str = Field(default="INTERRUPT_PRESCRIPTION", description="INTERRUPT_PRESCRIPTION, POST_ERP, GENERATE_CAPA")
    operator_name: str = Field(default="Dirección Jurídica & Tesorería B2B", description="Nombre del operador o apoderado legal firmante")


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


@router.post("/optimize-portfolio")
def optimize_working_capital_portfolio(request: PortfolioOptimizationRequest = PortfolioOptimizationRequest()):
    """
    US-961: Optimiza la cartera de controversias B2B de capital de trabajo, priorizando casos
    por Valor Presente Neto (NPV con WACC anual), riesgo de caducidad SLA (DTP) y salud relacional (RHI).
    """
    try:
        summary = WorkingCapitalPortfolioOptimizer.optimize_portfolio(
            case_ids=request.case_ids,
            wacc_annual=request.wacc_annual,
            target_count=request.target_count
        )
        return summary.model_dump(mode="json")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al optimizar cartera de capital de trabajo: {str(e)}")


@router.get("/portfolio-summary")
def get_portfolio_optimization_summary(target_count: int = 50, wacc: float = 0.12):
    """
    Recupera el resumen consolidado de prelación y War-Room C-Level para los expedientes del portafolio.
    """
    try:
        summary = WorkingCapitalPortfolioOptimizer.optimize_portfolio(
            wacc_annual=wacc,
            target_count=target_count
        )
        return summary.model_dump(mode="json")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar resumen de cartera: {str(e)}")


@router.post("/execute-action")
def execute_batch_action(request: BatchActionRequest):
    """
    Ejecuta acciones masivas en lote (Batch Action Execution):
    - INTERRUPT_PRESCRIPTION: Emisión en lote de avisos Art. 1041 CCom.
    - POST_ERP: Generación masiva de pólizas ERP y paquetes CFDI 4.0.
    - GENERATE_CAPA: Generación masiva de tickets de acción preventiva.
    """
    try:
        result = WorkingCapitalPortfolioOptimizer.execute_batch_action(
            case_ids=request.case_ids,
            action_type=request.action_type,
            operator_name=request.operator_name
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al ejecutar acción masiva: {str(e)}")
