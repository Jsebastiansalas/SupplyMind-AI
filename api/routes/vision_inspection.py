"""
api/routes/vision_inspection.py
Endpoints para el Motor de Visión Multimodal en Muelle & Certificación C-TPAT (Sprint 6.2).
Frontera 2 de Superinteligencia 4.0.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from agent.vision.pallet_vision_auditor import (
    PalletVisionAuditor,
    CargoIntegrityCertificate,
    BoundingBox
)

router = APIRouter(prefix="/vision", tags=["Visión Multimodal & Peritaje C-TPAT"])


# ==============================================================================
# Modelos de Petición
# ==============================================================================

class PalletInspectRequest(BaseModel):
    image_name: str = Field(default="tarima_descarga_01.jpg", description="Nombre del archivo o identificador de imagen")
    expected_seal: Optional[str] = Field(default="CTPAT-MX-982144", description="Número de precinto C-TPAT manifestado en remisión")
    po_reference: str = Field(default="PO-994820", description="Orden de compra asociada")
    case_id: str = Field(default="case_001", description="Expediente local de la disputa")
    dock_location: str = Field(default="Walmart Supercenter DC 6014 Muelle 12", description="Ubicación física del muelle")
    simulate_damage: bool = Field(default=False, description="Simular detección de daños y precinto violado")


# ==============================================================================
# Endpoints
# ==============================================================================

@router.post("/inspect-pallet", response_model=CargoIntegrityCertificate)
def inspect_pallet_and_seal(request: PalletInspectRequest):
    """
    Ejecuta el peritaje de visión artificial sobre la fotografía de la carga en muelle.
    Analiza el precinto C-TPAT, estiba, emplaye y emite el Certificado Criptográfico de Carga Intacta.
    """
    try:
        return PalletVisionAuditor.inspect_pallet(
            image_name=request.image_name,
            expected_seal=request.expected_seal,
            po_reference=request.po_reference,
            case_id=request.case_id,
            dock_location=request.dock_location,
            simulate_damage=request.simulate_damage
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en peritaje de visión: {str(e)}")


@router.get("/samples")
def get_sample_vision_inspections():
    """
    Retorna catálogo de muestras periciales de visión (Carga Prístina vs Merma y Precinto Violado)
    para visualización inmediata en la interfaz Obsidian Glass.
    """
    return {
        "status": "success",
        "samples": PalletVisionAuditor.get_sample_inspections()
    }
