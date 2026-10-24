"""
api/routes/fx_leakage.py
Endpoints REST para el Motor Cambiario FX Transfronterizo con Incoterms 2020 (Pilar 5)
y el Perfilador de Fugas de Retailers con Checklists Pre-Despacho (Pilar 3).
"""

from decimal import Decimal
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from agent.core.fx_and_leakage_engine import FxAndIncotermsEngine, RetailerLeakageProfiler
from data.models import FxAuditReport, RetailerLeakageProfile, PreDispatchCheckItem

router = APIRouter(tags=["Arbitraje Cambiario FX & Perfilador de Retailers"])


def _decimal_to_float(obj: Any) -> Any:
    """Convierte recursivamente Decimals a floats para serialización JSON segura."""
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, dict):
        return {k: _decimal_to_float(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_decimal_to_float(item) for item in obj]
    return obj


class FxSimulationRequest(BaseModel):
    """Parámetros de simulación cambiaria y contractual."""
    invoice_fx_rate: Optional[float] = Field(default=None, description="Tipo de cambio de emisión de factura (ej. DOF)")
    payment_fx_rate: Optional[float] = Field(default=None, description="Tipo de cambio efectivo de liquidación")
    target_currency: str = Field(default="MXN", description="Divisa de liquidación cruzada")
    incoterm: str = Field(default="FOB", description="Cláusula ICC Incoterms 2020 pactada (FOB, FCA, DDP, CIF, etc.)")


@router.get("/cases/{case_id}/fx-audit")
def get_case_fx_audit(
    case_id: str,
    invoice_rate: Optional[float] = Query(default=None, description="Tasa de cambio de facturación"),
    payment_rate: Optional[float] = Query(default=None, description="Tasa de cambio de liquidación"),
    target_currency: str = Query(default="MXN", description="Divisa de liquidación transfronteriza"),
    incoterm: str = Query(default="FOB", description="Incoterm pactado (FOB, DDP, CIF, etc.)")
):
    """
    Calcula la auditoría de varianza cambiaria transfronteriza y dictamen Incoterms 2020
    aislando la pérdida/ganancia cambiaria de la deducción comercial operativa.
    """
    case_path = Path("data/cases") / case_id
    if not case_path.exists():
        raise HTTPException(status_code=404, detail=f"Caso '{case_id}' no encontrado.")

    inv_dec = Decimal(str(invoice_rate)) if invoice_rate is not None else None
    pay_dec = Decimal(str(payment_rate)) if payment_rate is not None else None

    report = FxAndIncotermsEngine.audit_cross_border_fx(
        case_id=case_id,
        invoice_rate=inv_dec,
        payment_rate=pay_dec,
        target_currency=target_currency,
        incoterm_code=incoterm
    )

    return {
        "status": "success",
        "case_id": case_id,
        "fx_audit": _decimal_to_float(report.model_dump(mode="python"))
    }


@router.post("/cases/{case_id}/fx-audit/simulate")
def simulate_case_fx_audit(case_id: str, payload: FxSimulationRequest):
    """
    Simulación interactiva de escenarios cambiarios e Incoterms para arbitraje comercial.
    """
    case_path = Path("data/cases") / case_id
    if not case_path.exists():
        raise HTTPException(status_code=404, detail=f"Caso '{case_id}' no encontrado.")

    inv_dec = Decimal(str(payload.invoice_fx_rate)) if payload.invoice_fx_rate is not None else None
    pay_dec = Decimal(str(payload.payment_fx_rate)) if payload.payment_fx_rate is not None else None

    report = FxAndIncotermsEngine.audit_cross_border_fx(
        case_id=case_id,
        invoice_rate=inv_dec,
        payment_rate=pay_dec,
        target_currency=payload.target_currency,
        incoterm_code=payload.incoterm
    )

    return {
        "status": "success",
        "case_id": case_id,
        "simulated_fx_audit": _decimal_to_float(report.model_dump(mode="python"))
    }


@router.get("/cases/{case_id}/retailer-profile")
def get_case_retailer_profile(case_id: str):
    """
    Obtiene el perfil longitudinal de fugas del comprador asociado al caso activo.
    """
    case_path = Path("data/cases") / case_id
    if not case_path.exists():
        raise HTTPException(status_code=404, detail=f"Caso '{case_id}' no encontrado.")

    profile = RetailerLeakageProfiler.profile_from_case(case_id)
    return {
        "status": "success",
        "case_id": case_id,
        "retailer_profile": _decimal_to_float(profile.model_dump(mode="python"))
    }


@router.get("/retailers/leakage-profiles")
def list_retailer_profiles():
    """
    Retorna el catálogo completo de perfiles de compradores comerciales (Amazon, Walmart, Cisco, etc.).
    """
    profiles = RetailerLeakageProfiler.get_all_profiles()
    return {
        "status": "success",
        "count": len(profiles),
        "profiles": [_decimal_to_float(p.model_dump(mode="python")) for p in profiles]
    }


@router.get("/retailers/{retailer_id}/profile")
def get_single_retailer_profile(retailer_id: str):
    """
    Obtiene el perfil predictivo y patrones de un comprador específico.
    """
    profile = RetailerLeakageProfiler.get_profile(retailer_id)
    return {
        "status": "success",
        "retailer_id": retailer_id,
        "profile": _decimal_to_float(profile.model_dump(mode="python"))
    }


@router.get("/retailers/{retailer_id}/pre-dispatch-checklist")
def get_retailer_pre_dispatch_checklist(retailer_id: str):
    """
    Retorna el checklist operacional interactivo antes del despacho físico para un retailer.
    """
    checklist = RetailerLeakageProfiler.generate_pre_dispatch_checklist(retailer_id)
    return {
        "status": "success",
        "retailer_id": retailer_id,
        "checklist": [_decimal_to_float(item.model_dump(mode="python")) for item in checklist]
    }
