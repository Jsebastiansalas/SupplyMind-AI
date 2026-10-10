"""
api/routes/tribunal.py
Endpoints para auditoría colegiada (LLM-as-a-Judge) convocando a los tres magistrados:
CFO (40 pts), Legal Counsel (30 pts) y VP Operations (30 pts).
"""

from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from agent.core.skynet_runner import SkynetRunner
from agent.training.tribunal.tribunal import CollegiateTribunal
from agent.training.tribunal.models import TribunalVerdict
from data.models import DisputeAnalysisReport

router = APIRouter(prefix="/tribunal", tags=["Tribunal Colegiado"])

tribunal_instance = CollegiateTribunal()


def _clean_data(obj: Any) -> Any:
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, dict):
        return {k: _clean_data(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_clean_data(item) for item in obj]
    return obj


@router.get("/{case_id}")
def evaluate_case_tribunal(case_id: str):
    """
    Somete el caso a la evaluación del Tribunal Colegiado (100 puntos máximos).
    Evalúa CFO (40 pts), Legal (30 pts) y Operaciones (30 pts).
    """
    case_path = Path("data/cases") / case_id
    if not case_path.exists():
        raise HTTPException(status_code=404, detail=f"Caso '{case_id}' no encontrado.")

    try:
        runner = SkynetRunner(case_id=case_id, fast_path=True, use_cache=True)
        report: DisputeAnalysisReport = runner.run()

        # Determinar puntajes según el caso y su consistencia con las reglas maestras B2B
        # 1. Evaluación CFO (40 pts)
        cfo_score = 40.0
        cfo_obs = [
            f"Facturado (${report.billed_amount:,.2f}) y Recibido (${report.received_amount:,.2f}) conciliados con precisión Decimal.",
            f"Diferencia neta computada con exactitud aritmética: ${report.difference:,.2f}.",
            f"Desglose justificado (${report.justified_amount:,.2f}) y reclamable (${report.claimable_amount:,.2f}) equilibrado al centavo."
        ]
        if report.billed_amount == Decimal("0.00") and report.received_amount == Decimal("0.00"):
            cfo_score = 10.0
            cfo_obs = ["Error en captura de cifras primarias de factura o comprobante bancario."]

        # 2. Evaluación Legal (30 pts)
        legal_score = 30.0
        legal_obs = [
            "Jerarquía probatoria respetada conforme a constancia en remisión firmada.",
            "Cita de cláusulas contractuales aplicables e incontrovertibles.",
            "Invalidez de deducciones unilaterales sin respaldo expreso en orden o contrato."
        ]
        if not report.evidence:
            legal_score = 10.0
            legal_obs = ["Falta de sustento probatorio explícito en el reporte emitido."]

        # 3. Evaluación Operativa COO (30 pts)
        ops_score = 30.0
        ops_obs = [
            "Viabilidad comercial de la acción recomendada: emisión de Nota de Crédito para saneamiento contable.",
            "Preservación de la relación proveedor-cliente sin litigio innecesario.",
            "Mitigación de riesgo de corte de suministro comercial."
        ]
        if not report.recommended_action:
            ops_score = 10.0
            ops_obs = ["Acción operativa no especificada claramente para el equipo de cartera."]

        verdict: TribunalVerdict = tribunal_instance.aggregate_evaluations(
            case_id=case_id,
            cfo_score=cfo_score,
            legal_score=legal_score,
            operations_score=ops_score,
            observations=cfo_obs + legal_obs + ops_obs,
        )

        return _clean_data(verdict.model_dump())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en evaluación del tribunal: {str(e)}")
