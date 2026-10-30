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


# ==============================================================================
# Despachador Robótico B2B Multi-Portal (Sprint 6.3)
# ==============================================================================
from pathlib import Path
from agent.portal.portal_dispatcher_engine import PortalDispatcherEngine
from data.models import PortalDispatchDossier, PortalDispatchReceipt


def _decimal_to_float(obj: Any) -> Any:
    """Convierte recursivamente Decimals a floats para serialización JSON segura."""
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, dict):
        return {k: _decimal_to_float(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_decimal_to_float(item) for item in obj]
    return obj


class DispatchCaseRequest(BaseModel):
    portal_type: Optional[str] = Field(default=None, description="WALMART_RETAIL_LINK | AMAZON_VENDOR_CENTRAL | SORIANA_B2B | LIVERPOOL_B2B")
    operator_name: Optional[str] = Field(default="SupplyMind Robotic Dispatcher", description="Nombre del operador firmante")


@router.get("/cases/{case_id}/dossier")
def get_case_dossier_endpoint(case_id: str, portal_type: Optional[str] = None):
    """
    Construye y retorna el expediente pericial consolidado con índice foliado,
    hashes SHA-256 y payload del adaptador adaptado al portal destino.
    """
    case_path = Path("data/cases") / case_id
    if not case_path.exists():
        raise HTTPException(status_code=404, detail=f"Caso '{case_id}' no encontrado.")

    dossier = PortalDispatcherEngine.build_dispatch_dossier(case_id, portal_type)
    return {
        "status": "success",
        "case_id": case_id,
        "dossier": _decimal_to_float(dossier.model_dump(mode="python"))
    }


@router.post("/cases/{case_id}/dispatch")
def dispatch_case_endpoint(case_id: str, request: Optional[DispatchCaseRequest] = None):
    """
    Ejecuta el despacho robótico del expediente hacia el portal B2B del retailer.
    Genera el ticket oficial y la bitácora de auditoría con marcas de tiempo.
    """
    case_path = Path("data/cases") / case_id
    if not case_path.exists():
        raise HTTPException(status_code=404, detail=f"Caso '{case_id}' no encontrado.")

    req = request or DispatchCaseRequest()
    try:
        receipt = PortalDispatcherEngine.dispatch_case_to_portal(
            case_id=case_id,
            portal_type=req.portal_type,
            operator_name=req.operator_name or "SupplyMind Robotic Dispatcher"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "status": "success",
        "case_id": case_id,
        "receipt": _decimal_to_float(receipt.model_dump(mode="python"))
    }


@router.get("/cases/{case_id}/receipt")
def get_case_dispatch_receipt_endpoint(case_id: str):
    """
    Retorna el recibo oficial y ticket de radicación emitido por el portal.
    """
    receipt = PortalDispatcherEngine.get_dispatch_receipt(case_id)
    if not receipt:
        raise HTTPException(status_code=404, detail=f"El caso '{case_id}' aún no ha sido radicado en ningún portal.")

    return {
        "status": "success",
        "case_id": case_id,
        "receipt": _decimal_to_float(receipt.model_dump(mode="python"))
    }


@router.get("/dispatches")
def list_dispatches_endpoint():
    """Retorna la lista de todos los casos radicados en portales B2B."""
    items = PortalDispatcherEngine.list_dispatched_cases()
    return {
        "status": "success",
        "total_dispatches": len(items),
        "dispatches": _decimal_to_float(items)
    }

