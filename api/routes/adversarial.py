"""
api/routes/adversarial.py
Endpoints para el Debate Dialéctico Multi-Agente (Pilar 3: Adversarial Courtroom)
y el Motor Predictivo de Cobro & Simulación de Concesiones (Pilar 4).
"""

from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException

from agent.core.skynet_runner import SkynetRunner
from agent.courtroom.adversarial_engine import AdversarialCourtroomEngine
from agent.courtroom.models import AdversarialVerdict
from agent.predictive.recovery_scorer import RecoveryPredictor
from agent.predictive.models import RecoveryPredictionResult
from agent.memory.precedent_matcher import PrecedentMatcher
from agent.memory.precedent_graph import DisputeMemoryNetwork
from data.models import DisputeAnalysisReport
from config.settings import settings

router = APIRouter(tags=["Debate Dialéctico & Predicción"])

CASES_DIR = settings.DATA_DIR


def _decimal_to_float(obj: Any) -> Any:
    """Convierte recursivamente Decimals a floats para serialización JSON segura."""
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, dict):
        return {k: _decimal_to_float(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_decimal_to_float(item) for item in obj]
    return obj


def _get_case_report_and_docs(case_id: str):
    """Ejecuta o recupera el análisis del caso y sus documentos asociados."""
    case_path = CASES_DIR / case_id
    if not case_path.exists() or not case_path.is_dir():
        raise HTTPException(status_code=404, detail=f"Caso '{case_id}' no encontrado.")

    runner = SkynetRunner(case_id=case_id, fast_path=True, use_cache=True)
    report: Optional[DisputeAnalysisReport] = runner.run()
    if not report:
        raise HTTPException(status_code=422, detail=f"No se pudo conciliar el expediente '{case_id}'.")

    # Extraer documentos cargados desde las herramientas del runner si están disponibles
    docs = getattr(runner.tool_executor, "loaded_documents", {}) or {}
    return report, docs


@router.get("/cases/{case_id}/adversarial-courtroom")
@router.get("/adversarial/{case_id}")
def get_adversarial_courtroom(case_id: str):
    """
    Retorna el careo dialéctico multi-agente entre el Fiscal Forense del Retailer (The Auditor),
    el Abogado Defensor del Proveedor (The Advocate) y el dictamen vinculante del Magistrado (The Magistrate).
    """
    try:
        report, docs = _get_case_report_and_docs(case_id)

        verdict = getattr(report, "adversarial_verdict", None)
        if not verdict or not isinstance(verdict, AdversarialVerdict):
            matcher = PrecedentMatcher()
            verdict = AdversarialCourtroomEngine.conduct_debate(
                report=report,
                docs=docs,
                precedent_matcher=matcher
            )

        return _decimal_to_float(verdict.model_dump())
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en debate dialéctico: {str(e)}")


@router.get("/cases/{case_id}/recovery-prediction")
@router.get("/predictive/{case_id}")
def get_recovery_prediction(case_id: str):
    """
    Retorna la probabilidad matemática predictiva de cobro (0.0% a 100.0%),
    la ruta operativa sugerida y 3 escenarios de resolución financiera simulados.
    """
    try:
        report, docs = _get_case_report_and_docs(case_id)

        prediction = getattr(report, "recovery_prediction", None)
        if not prediction or not isinstance(prediction, RecoveryPredictionResult):
            verdict = getattr(report, "adversarial_verdict", None)
            mem = DisputeMemoryNetwork()
            ret_id = ""
            if docs and "invoice" in docs:
                ret_id = str(getattr(docs["invoice"], "customer_id", ""))
            profile = mem.get_retailer_profile(ret_id) if ret_id else None

            prediction = RecoveryPredictor.calculate_prediction(
                report=report,
                docs=docs,
                adversarial_verdict=verdict,
                retailer_profile=profile
            )

        return _decimal_to_float(prediction.model_dump())
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en motor predictivo de cobro: {str(e)}")
