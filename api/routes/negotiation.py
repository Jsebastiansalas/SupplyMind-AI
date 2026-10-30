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


class SetGovernanceModeRequest(BaseModel):
    governance_mode: str = Field(..., description="FULL_AUTONOMY | HUMAN_GATEKEEPER")


@router.post("/{case_id}/negotiation/duel/governance")
def set_duel_governance_endpoint(case_id: str, request: SetGovernanceModeRequest):
    """
    Conmuta el modo de gobernanza del careo (FULL_AUTONOMY vs HUMAN_GATEKEEPER)
    con auditoría estricta de salvaguardas financieras de la Matriz CFO.
    """
    case_path = Path("data/cases") / case_id
    if not case_path.exists():
        raise HTTPException(status_code=404, detail=f"Caso '{case_id}' no encontrado.")

    try:
        session = BilateralNegotiationEngine.set_governance_mode(case_id, request.governance_mode.upper())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "status": "success",
        "case_id": case_id,
        "governance_mode": session.governance_mode,
        "session": _decimal_to_float(session.model_dump(mode="python"))
    }


@router.get("/{case_id}/negotiation/duel/minutes")
def get_duel_settlement_minutes_endpoint(case_id: str):
    """
    Retorna el convenio formal de transacción mercantil, sello ZKP SHA-256
    y el texto íntegro en Markdown con autoridad de cosa juzgada.
    """
    case_path = Path("data/cases") / case_id
    if not case_path.exists():
        raise HTTPException(status_code=404, detail=f"Caso '{case_id}' no encontrado.")

    session = BilateralNegotiationEngine.get_duel_session(case_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"No hay careo registrado para el caso '{case_id}'.")

    minutes_file = Path("reports") / f"convenio_finiquito_{case_id}.md"
    if not minutes_file.exists():
        minutes_file = Path("reports") / f"minuta_conciliacion_duel_{case_id}.md"

    minutes_content = ""
    if minutes_file.exists():
        with open(minutes_file, "r", encoding="utf-8") as f:
            minutes_content = f.read()

    details = BilateralNegotiationEngine.get_settlement_agreement_details(case_id)
    details_dict = _decimal_to_float(details.model_dump(mode="python")) if details else None

    return {
        "status": "success",
        "case_id": case_id,
        "session_id": session.session_id,
        "settlement_minutes_hash": session.settlement_minutes_hash,
        "agreement_details": details_dict,
        "markdown_content": minutes_content
    }


# ==============================================================================
# Matriz de Delegación Financiera & Gobernanza B2B (Sprint 6.2)
# ==============================================================================
from agent.core.delegation_matrix_engine import DelegationMatrixEngine
from data.models import FinancialDelegationMatrix, SettlementAgreementDetails

governance_router = APIRouter(prefix="/negotiation", tags=["Gobernanza Financiera B2B"])


class UpdateDelegationMatrixRequest(BaseModel):
    matrix_id: Optional[str] = None
    cfo_approver: Optional[str] = None
    strict_approval_threshold: Optional[Decimal] = None
    allow_autonomous_execution: Optional[bool] = None
    tier_policies: Optional[Dict[str, Any]] = None


@governance_router.get("/delegation-matrix")
@router.get("/delegation-matrix")
def get_delegation_matrix_endpoint():
    """Retorna la matriz corporativa activa de delegación financiera y salvaguardas."""
    matrix = DelegationMatrixEngine.get_active_matrix()
    return {
        "status": "success",
        "matrix": _decimal_to_float(matrix.model_dump(mode="python"))
    }


@governance_router.post("/delegation-matrix")
@router.post("/delegation-matrix")
def update_delegation_matrix_endpoint(request: UpdateDelegationMatrixRequest):
    """Actualiza los parámetros o políticas de la matriz de delegación financiera del CFO."""
    matrix = DelegationMatrixEngine.get_active_matrix()
    if request.matrix_id is not None:
        matrix.matrix_id = request.matrix_id
    if request.cfo_approver is not None:
        matrix.cfo_approver = request.cfo_approver
    if request.strict_approval_threshold is not None:
        matrix.strict_approval_threshold = request.strict_approval_threshold
    if request.allow_autonomous_execution is not None:
        matrix.allow_autonomous_execution = request.allow_autonomous_execution
    if request.tier_policies is not None:
        for tier_k, tier_v in request.tier_policies.items():
            if tier_k in matrix.tier_policies and isinstance(tier_v, dict):
                curr = matrix.tier_policies[tier_k]
                updated = curr.model_copy(update=tier_v)
                matrix.tier_policies[tier_k] = updated

    DelegationMatrixEngine.save_matrix(matrix)
    return {
        "status": "success",
        "message": "Matriz de Delegación Financiera actualizada y persistida correctamente.",
        "matrix": _decimal_to_float(matrix.model_dump(mode="python"))
    }


