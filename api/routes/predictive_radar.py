"""
api/routes/predictive_radar.py
Endpoints para el Radar Preventivo Pre-Despacho (DVI) y Generador de Dossier Arbitral ICC/CANACO.
Frontera 4 de Superinteligencia (Sprint 5.4).
"""

from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from config.settings import settings
from agent.core.skynet_runner import SkynetRunner
from agent.predictive.leakage_radar import (
    DviPredictionResult,
    PreDispatchLeakageRadar,
)
from agent.legal.arbitration_dossier import (
    ArbitrationDossier,
    ArbitrationDossierGenerator,
)
from data.models import DisputeAnalysisReport

router = APIRouter(prefix="/radar", tags=["Radar Preventivo Pre-Despacho & Arbitraje ICC"])
CASES_DIR = settings.DATA_DIR


# ==============================================================================
# Modelos de Petición
# ==============================================================================

class DviEvaluateRequest(BaseModel):
    po_reference: str = Field(..., description="Número de referencia de la Orden de Compra (PO).")
    retailer_id: str = Field(default="WALMART_MEXICO", description="Identificador del Retailer.")
    destination_dc: str = Field(default="WALMART_DC_6014", description="Centro de distribución de destino.")
    total_amount: Decimal = Field(..., description="Monto total de la orden de compra.")
    estimated_transit_hours: float = Field(default=3.5, description="Tiempo proyectado de tránsito en horas.")
    appointment_window_hours: float = Field(default=2.0, description="Ventana de cita de descarga otorgada por el muelle.")
    sku_list: List[str] = Field(default_factory=list, description="Lista de SKUs incluidos en el pedido.")
    agreed_catalog_price_match: bool = Field(default=True, description="¿Los precios coinciden con el contrato?")
    contract_has_unilateral_penalty: bool = Field(default=False, description="¿Existe cláusula de penalidad unilateral?")


class GenerateArbitrationDossierRequest(BaseModel):
    case_id: str = Field(..., description="Identificador del caso en disputa para compilar el dossier.")
    claimant_name: str = Field(default="PROVEEDOR INDUSTRIAL ALIMENTICIO S.A. DE C.V.")
    claimant_tax_id: str = Field(default="PRO920101XYZ")
    respondent_name: str = Field(default="NUEVA WAL MART DE MEXICO S. DE R.L. DE C.V.")
    respondent_tax_id: str = Field(default="NWM9709244W4")
    institution: str = Field(default="ICC", description="ICC (Cámara de Comercio Internacional) o CANACO.")
    days_in_arrears: int = Field(default=90, description="Días naturales de mora para liquidación de intereses.")


# ==============================================================================
# Endpoints
# ==============================================================================

@router.post("/dvi-evaluate", response_model=DviPredictionResult)
def evaluate_pre_dispatch_dvi(request: DviEvaluateRequest):
    """
    Evalúa preventivamente una Orden de Compra antes de expedir la mercancía.
    Calcula el Deduction Vulnerability Index (DVI) e identifica salvaguardas obligatorias.
    """
    if request.total_amount <= Decimal("0.00"):
        raise HTTPException(status_code=400, detail="El monto de la orden debe ser mayor a cero.")

    result = PreDispatchLeakageRadar.evaluate_purchase_order(
        po_reference=request.po_reference,
        retailer_id=request.retailer_id,
        destination_dc=request.destination_dc,
        total_amount=request.total_amount,
        estimated_transit_hours=request.estimated_transit_hours,
        appointment_window_hours=request.appointment_window_hours,
        sku_list=request.sku_list,
        agreed_catalog_price_match=request.agreed_catalog_price_match,
        contract_has_unilateral_penalty=request.contract_has_unilateral_penalty
    )
    return result


@router.post("/generate-arbitration-dossier", response_model=ArbitrationDossier)
def generate_arbitration_dossier(request: GenerateArbitrationDossierRequest):
    """
    Genera un Dossier Pericial Foliado oficial para arbitraje comercial vinculante
    ante la Corte de Arbitraje de la ICC (París) o la Comisión de Arbitraje de la CANACO.
    """
    case_path = CASES_DIR / request.case_id
    if not case_path.exists() or not case_path.is_dir():
        raise HTTPException(status_code=404, detail=f"Caso '{request.case_id}' no encontrado.")

    runner = SkynetRunner(case_id=request.case_id, fast_path=True, use_cache=True)
    report: Optional[DisputeAnalysisReport] = runner.run()
    if not report:
        raise HTTPException(status_code=422, detail=f"No se pudo conciliar el expediente '{request.case_id}'.")

    docs = getattr(runner.tool_executor, "loaded_documents", {}) or {}

    dossier = ArbitrationDossierGenerator.generate_dossier(
        report=report,
        docs=docs,
        claimant_name=request.claimant_name,
        claimant_tax_id=request.claimant_tax_id,
        respondent_name=request.respondent_name,
        respondent_tax_id=request.respondent_tax_id,
        institution=request.institution,
        days_in_arrears=request.days_in_arrears
    )
    return dossier


@router.get("/high-risk-destinations")
def get_high_risk_destinations():
    """
    Retorna el catálogo topológico de centros de distribución con historial
    recurrente de mermas, cancelaciones de citas y penalidades OTIF.
    """
    return PreDispatchLeakageRadar.get_high_risk_destinations_catalog()
