"""
api/routes/negotiation.py
Endpoints REST para el Motor de Negociación B2B Multitáctico (Fase 2).
"""

from decimal import Decimal
from pathlib import Path
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from agent.core.negotiation_engine import NegotiationEngine, parse_negotiation_query, format_negotiation_plan_reply
from data.models import NegotiationPlan, NegotiationScenario

router = APIRouter(prefix="/cases", tags=["Negociación B2B Multitáctica"])


def _decimal_to_float(obj: Any) -> Any:
    """Convierte recursivamente Decimals a floats para serialización JSON segura."""
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, dict):
        return {k: _decimal_to_float(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_decimal_to_float(item) for item in obj]
    return obj


class SelectScenarioRequest(BaseModel):
    scenario_id: str = Field(..., description="Escenario a seleccionar: AGGRESSIVE, BALANCED, CONSERVATIVE")
    operator_name: Optional[str] = Field(default="Director Comercial B2B", description="Nombre del operador")


@router.get("/{case_id}/negotiation")
def get_negotiation_plan_endpoint(case_id: str):
    """
    Genera y retorna los 3 escenarios determinísticos de negociación para el expediente.
    """
    case_path = Path("data/cases") / case_id
    if not case_path.exists():
        raise HTTPException(status_code=404, detail=f"Caso '{case_id}' no encontrado.")

    plan = NegotiationEngine.build_negotiation_plan(case_id)
    return {
        "status": "success",
        "case_id": case_id,
        "plan": _decimal_to_float(plan.model_dump(mode="python")),
        "summary_markdown": format_negotiation_plan_reply(plan)
    }


@router.post("/{case_id}/negotiation/select")
def select_negotiation_scenario_endpoint(case_id: str, request: SelectScenarioRequest):
    """
    Selecciona y aplica un escenario de negociación B2B, recalculando balances
    y emitiendo la Minuta Formal de Conciliación.
    """
    case_path = Path("data/cases") / case_id
    if not case_path.exists():
        raise HTTPException(status_code=404, detail=f"Caso '{case_id}' no encontrado.")

    valid_scenarios = ["AGGRESSIVE", "BALANCED", "CONSERVATIVE"]
    if request.scenario_id.upper() not in valid_scenarios:
        raise HTTPException(
            status_code=400,
            detail=f"Escenario '{request.scenario_id}' no válido. Opciones permitidas: {', '.join(valid_scenarios)}"
        )

    updated_report = NegotiationEngine.apply_scenario(
        case_id=case_id,
        scenario_id=request.scenario_id.upper(),
        operator_name=request.operator_name or "Director Comercial B2B"
    )

    # Cargar minuta generada
    minutes_file = Path("reports") / f"minuta_acuerdo_{case_id}.md"
    minutes_content = ""
    if minutes_file.exists():
        with open(minutes_file, "r", encoding="utf-8") as f:
            minutes_content = f.read()

    return {
        "status": "success",
        "case_id": case_id,
        "selected_scenario": request.scenario_id.upper(),
        "report": _decimal_to_float(updated_report.model_dump(mode="python")),
        "settlement_minutes": minutes_content
    }


# ==============================================================================
# Confrontación Dialéctica Multi-Agente en Tiempo Real (Sprint 6.1)
# ==============================================================================
from agent.core.bilateral_negotiation_engine import BilateralNegotiationEngine
from data.models import NegotiationDuelSession


class StartDuelRequest(BaseModel):
    governance_mode: Optional[str] = Field(default="HUMAN_GATEKEEPER", description="FULL_AUTONOMY | HUMAN_GATEKEEPER")
    delegation_limit_pct: Optional[float] = Field(default=50.0, ge=0.0, le=100.0, description="Porcentaje máximo de concesión autorizada")


class ApproveDuelRequest(BaseModel):
    operator_name: Optional[str] = Field(default="Director Comercial B2B", description="Nombre del operador firmante")


@router.get("/{case_id}/negotiation/duel")
def get_duel_session_endpoint(case_id: str):
    """
    Retorna el estado de la sesión de careo bilateral activa para el expediente.
    """
    case_path = Path("data/cases") / case_id
    if not case_path.exists():
        raise HTTPException(status_code=404, detail=f"Caso '{case_id}' no encontrado.")

    session = BilateralNegotiationEngine.get_duel_session(case_id)
    if not session:
        return {"status": "not_started", "case_id": case_id, "session": None}

    return {
        "status": "success",
        "case_id": case_id,
        "session": _decimal_to_float(session.model_dump(mode="python"))
    }


@router.post("/{case_id}/negotiation/duel/start")
def start_duel_endpoint(case_id: str, request: Optional[StartDuelRequest] = None):
    """
    Inicia una nueva sesión de careo bilateral multi-agente y ejecuta la Ronda 1.
    """
    case_path = Path("data/cases") / case_id
    if not case_path.exists():
        raise HTTPException(status_code=404, detail=f"Caso '{case_id}' no encontrado.")

    req = request or StartDuelRequest()
    session = BilateralNegotiationEngine.start_duel(
        case_id=case_id,
        governance_mode=req.governance_mode or "HUMAN_GATEKEEPER",
        delegation_limit_pct=req.delegation_limit_pct if req.delegation_limit_pct is not None else 50.0
    )

    return {
        "status": "success",
        "case_id": case_id,
        "session": _decimal_to_float(session.model_dump(mode="python"))
    }


@router.post("/{case_id}/negotiation/duel/step")
def step_duel_endpoint(case_id: str):
    """
    Avanza una ronda en el careo bilateral entre SupplyMind y el Comprador Retailer.
    """
    case_path = Path("data/cases") / case_id
    if not case_path.exists():
        raise HTTPException(status_code=404, detail=f"Caso '{case_id}' no encontrado.")

    session = BilateralNegotiationEngine.advance_duel_step(case_id)
    return {
        "status": "success",
        "case_id": case_id,
        "session": _decimal_to_float(session.model_dump(mode="python"))
    }


@router.post("/{case_id}/negotiation/duel/approve")
def approve_duel_settlement_endpoint(case_id: str, request: Optional[ApproveDuelRequest] = None):
    """
    Aprueba formalmente el acuerdo preliminar en modo Human Gatekeeper,
    rubricando la Minuta de Conciliación con sello criptográfico ZKP.
    """
    case_path = Path("data/cases") / case_id
    if not case_path.exists():
        raise HTTPException(status_code=404, detail=f"Caso '{case_id}' no encontrado.")

    req = request or ApproveDuelRequest()
    try:
        session = BilateralNegotiationEngine.approve_settlement(
            case_id=case_id,
            operator_name=req.operator_name or "Director Comercial B2B"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "status": "success",
        "case_id": case_id,
        "session": _decimal_to_float(session.model_dump(mode="python")),
        "minutes_hash": session.settlement_minutes_hash
    }

