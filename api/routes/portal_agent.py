"""
api/routes/portal_agent.py
Endpoints para el Motor RPA de Portales Retailer B2B (Sprint 6.1).
Frontera 1 de Superinteligencia 4.0.
"""

from decimal import Decimal
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from agent.portal.retailer_portal_agent import (
    RetailerPortalAgent,
    PortalSyncResult,
    PortalDisputeSubmissionResult,
    PortalDeductionItem
)

router = APIRouter(prefix="/portal", tags=["RPA Portales Retailer B2B"])


# ==============================================================================
# Modelos de Petición
# ==============================================================================

class PortalSyncRequest(BaseModel):
    portal_type: str = Field(default="WALMART_RETAIL_LINK", description="Identificador del portal (ej. WALMART_RETAIL_LINK, AMAZON_VENDOR_CENTRAL, SORIANA_B2B, LIVERPOOL_B2B)")
    date_from: Optional[str] = Field(default=None, description="Fecha inicial en formato YYYY-MM-DD")
    date_to: Optional[str] = Field(default=None, description="Fecha final en formato YYYY-MM-DD")
    max_items: int = Field(default=5, ge=1, le=50, description="Número máximo de deducciones a cosechar")


class PortalUploadDisputeRequest(BaseModel):
    portal_type: str = Field(..., description="Tipo de portal B2B destino")
    deduction_id: str = Field(..., description="ID de la deducción en el portal")
    case_id: str = Field(..., description="ID del caso local en SupplyMind")
    claimable_amount: Decimal = Field(..., description="Monto reclamado a restituir")
    evidence_manifest_hash: Optional[str] = Field(default=None, description="Hash SHA-256 del manifiesto probatorio")


# ==============================================================================
# Endpoints
# ==============================================================================

@router.get("/catalog")
def get_supported_portals():
    """
    Retorna el catálogo oficial de portales B2B configurados, sus métodos de autenticación,
    códigos de deducción típicos y estado de disponibilidad del bot.
    """
    return {
        "status": "success",
        "supported_portals": RetailerPortalAgent.get_supported_portals()
    }


@router.post("/sync-retailer", response_model=PortalSyncResult)
def sync_retailer_portal(request: PortalSyncRequest):
    """
    Ejecuta el bot de navegación desatendida sobre el portal del Retailer seleccionado,
    extrayendo las notas de débito y deducciones activas para su conciliación determinística.
    """
    try:
        return RetailerPortalAgent.sync_retailer_portal(
            portal_type=request.portal_type,
            date_from=request.date_from,
            date_to=request.date_to,
            max_items=request.max_items
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en bot de portal: {str(e)}")


@router.post("/upload-dispute", response_model=PortalDisputeSubmissionResult)
def upload_dispute_package(request: PortalUploadDisputeRequest):
    """
    Carga desatendida del expediente de disputa, carta de reclamación formal
    y evidencia pericial sellada directamente en el portal del Retailer.
    """
    try:
        return RetailerPortalAgent.submit_dispute_to_portal(
            portal_type=request.portal_type,
            deduction_id=request.deduction_id,
            case_id=request.case_id,
            claimable_amount=request.claimable_amount,
            evidence_manifest_hash=request.evidence_manifest_hash
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al cargar disputa en portal: {str(e)}")
