"""
api/routes/remittance.py
Endpoints REST para la Fase 7:
- Sprint 7.1: Watchdog de Prescripción Legal y Caducidad SLA (Art. 1041 CCom)
- Sprint 7.2: Conciliación de Remesas Bancarias EDI 820 & Cierre Order-to-Cash 3-Way
- Sprint 7.3: Guardrail de Salud Relacional & Riesgo de Deserción (LTV & RHI Index)
- Sprint 7.4: Inteligencia Preventiva de Causa Raíz (RCA) & Tickets CAPA
"""

from decimal import Decimal
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from agent.core.dispute_sla_watchdog import DisputeSlaWatchdog
from agent.core.bank_remittance_reconciler import BankRemittanceReconciler
from agent.core.relational_health_engine import RelationalHealthEngine
from agent.core.root_cause_analyzer import RootCauseAnalyzer
from agent.core.capa_ticket_generator import CapaTicketGenerator

router = APIRouter(prefix="/remittance", tags=["Cierre Financiero EDI 820, SLA Watchdog & Prevención CAPA (Fase 7)"])


def _decimal_to_float(obj: Any) -> Any:
    """Convierte recursivamente Decimals a floats para serialización JSON segura."""
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, dict):
        return {k: _decimal_to_float(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_decimal_to_float(item) for item in obj]
    return obj


class InterruptSlaRequest(BaseModel):
    operator_name: Optional[str] = Field(
        default="Dirección Jurídica & Tesorería B2B",
        description="Nombre o cargo del responsable que suscribe la interpelación Art. 1041 CCom"
    )
    simulated_elapsed_days: Optional[int] = Field(
        default=None,
        description="Días transcurridos simulados opcionales"
    )


class ParseRemittanceRequest(BaseModel):
    case_id: Optional[str] = Field(default="case_005_amazon_shortage")
    raw_remittance_content: str = Field(..., description="Trama cruda EDI 820 o CSV bancario")


class ReconcileRemittanceRequest(BaseModel):
    raw_remittance_content: Optional[str] = Field(
        default=None,
        description="Trama opcional EDI 820 o CSV; si se omite, genera la remesa oficial del caso"
    )
    override_bank_deposit: Optional[Decimal] = Field(
        default=None,
        description="Importe opcional de depósito bancario para simular cuadre o varianza"
    )


class GenerateCapaRequest(BaseModel):
    override_department: Optional[str] = Field(
        default=None,
        description="Departamento opcional: WAREHOUSE_CEDIS | TRANSPORT_LOGISTICS | SYSTEMS_EDI | SALES_COMMERCIAL"
    )


# ==============================================================================
# Sprint 7.1: Watchdog de Prescripción Legal y Caducidad SLA
# ==============================================================================
@router.get("/sla-fleet")
def get_sla_fleet_monitor(limit: int = Query(default=15, ge=1, le=60)):
    """Retorna el semáforo de caducidad SLA y riesgo de prescripción de toda la flota."""
    fleet_data = DisputeSlaWatchdog.scan_fleet_sla(limit=limit)
    return {
        "status": "success",
        "fleet": {
            "total_cases_monitored": fleet_data["total_cases_monitored"],
            "total_claimable_monitored_usd": float(fleet_data["total_claimable_monitored_usd"]),
            "imminent_or_expired_unprotected_usd": float(fleet_data["imminent_or_expired_unprotected_usd"]),
            "urgency_breakdown": fleet_data["urgency_breakdown"],
            "cases": [_decimal_to_float(c.model_dump(mode="python")) for c in fleet_data["cases"]],
        }
    }


@router.get("/sla/{case_id}")
def get_case_sla_status(
    case_id: str,
    simulated_elapsed_days: Optional[int] = Query(default=None)
):
    """Evalúa los Days-to-Prescription (DTP) y ventana SLA del expediente."""
    sla_status = DisputeSlaWatchdog.evaluate_case_sla(
        case_id=case_id,
        simulated_elapsed_days=simulated_elapsed_days
    )
    existing_notice = DisputeSlaWatchdog.get_existing_notice(case_id)
    return {
        "status": "success",
        "case_id": case_id,
        "sla_status": _decimal_to_float(sla_status.model_dump(mode="python")),
        "interruption_notice": _decimal_to_float(existing_notice.model_dump(mode="python")) if existing_notice else None,
    }


@router.post("/sla/{case_id}/interrupt")
def interrupt_case_prescription(
    case_id: str,
    request: Optional[InterruptSlaRequest] = None
):
    """
    US-702: Emite y sella la Notificación Formal de Interrupción de Prescripción Mercantil
    bajo el Art. 1041 del Código de Comercio, congelando el reloj SLA.
    """
    req = request or InterruptSlaRequest()
    notice = DisputeSlaWatchdog.issue_prescription_interruption_notice(
        case_id=case_id,
        operator_name=req.operator_name or "Dirección Jurídica & Tesorería B2B",
        simulated_elapsed_days=req.simulated_elapsed_days,
    )
    updated_sla = DisputeSlaWatchdog.evaluate_case_sla(
        case_id=case_id,
        simulated_elapsed_days=req.simulated_elapsed_days,
    )
    return {
        "status": "success",
        "case_id": case_id,
        "notice": _decimal_to_float(notice.model_dump(mode="python")),
        "sla_status": _decimal_to_float(updated_sla.model_dump(mode="python")),
    }


# ==============================================================================
# Sprint 7.2: Conciliación Bancaria EDI 820 & Cierre Order-to-Cash 3-Way
# ==============================================================================
@router.get("/edi820/{case_id}")
def get_case_edi820_remittance(case_id: str):
    """Genera y decodifica el estado de remesa bancaria EDI 820 del expediente."""
    raw_edi820 = BankRemittanceReconciler.generate_case_edi820_payload(case_id)
    parsed = BankRemittanceReconciler.parse_remittance_payload(raw_edi820, case_id=case_id)
    return {
        "status": "success",
        "case_id": case_id,
        "raw_edi820": raw_edi820,
        "remittance": _decimal_to_float(parsed.model_dump(mode="python")),
    }


@router.post("/parse")
def parse_remittance_endpoint(request: ParseRemittanceRequest):
    """Decodifica una trama cruda EDI 820 o CSV bancario."""
    parsed = BankRemittanceReconciler.parse_remittance_payload(
        raw_content=request.raw_remittance_content,
        case_id=request.case_id or "case_005_amazon_shortage"
    )
    return {
        "status": "success",
        "remittance": _decimal_to_float(parsed.model_dump(mode="python")),
    }


@router.post("/reconcile/{case_id}")
def reconcile_three_way_settlement(
    case_id: str,
    request: Optional[ReconcileRemittanceRequest] = None
):
    """
    US-704: Ejecuta el 3-Way Settlement Matcher con precisión Decimal ($0.00 MAE)
    y emite el Certificado de Cierre y Liquidación de Cartera.
    """
    req = request or ReconcileRemittanceRequest()
    remittance, match_res, certificate = BankRemittanceReconciler.execute_three_way_settlement_match(
        case_id=case_id,
        raw_remittance_content=req.raw_remittance_content,
        override_bank_deposit=req.override_bank_deposit,
    )
    return {
        "status": "success",
        "case_id": case_id,
        "remittance": _decimal_to_float(remittance.model_dump(mode="python")),
        "three_way_match": _decimal_to_float(match_res.model_dump(mode="python")),
        "clearance_certificate": _decimal_to_float(certificate.model_dump(mode="python")),
    }


# ==============================================================================
# Sprint 7.3: Guardrail de Salud Relacional & Riesgo de Deserción (LTV & RHI)
# ==============================================================================
@router.get("/relational-health/{case_id}")
def get_relational_health_index(
    case_id: str,
    override_rhi_score: Optional[float] = Query(default=None, ge=0.0, le=100.0)
):
    """
    US-705 / US-706: Retorna el Relationship Health Index (RHI 0-100) y el modo de
    modulación táctica de negociación para el expediente.
    """
    rhi_report = RelationalHealthEngine.evaluate_relational_health(
        case_id=case_id,
        override_rhi_score=override_rhi_score,
    )
    return {
        "status": "success",
        "case_id": case_id,
        "relational_health": _decimal_to_float(rhi_report.model_dump(mode="python")),
    }


# ==============================================================================
# Sprint 7.4: Inteligencia Preventiva de Causa Raíz (RCA) & Tickets CAPA
# ==============================================================================
@router.get("/rca-fleet")
def get_longitudinal_rca_report(target_benchmark_size: int = Query(default=50, ge=1, le=200)):
    """
    US-707: Retorna el análisis longitudinal de Causa Raíz (RCA) atribuyendo fugas
    a los 4 frentes operativos internos (Almacén, Transporte, Sistemas EDI, Comercial).
    """
    rca_report = RootCauseAnalyzer.analyze_fleet_root_causes(target_benchmark_size=target_benchmark_size)
    return {
        "status": "success",
        "rca_report": _decimal_to_float(rca_report.model_dump(mode="python")),
    }


@router.get("/capa/{case_id}")
def get_capa_ticket_endpoint(case_id: str):
    """Obtiene o genera el Ticket de Acción Correctiva y Preventiva (CAPA) del caso."""
    ticket = CapaTicketGenerator.generate_capa_ticket(case_id=case_id)
    return {
        "status": "success",
        "case_id": case_id,
        "capa_ticket": _decimal_to_float(ticket.model_dump(mode="python")),
    }


@router.post("/capa/{case_id}")
def create_capa_ticket_endpoint(
    case_id: str,
    request: Optional[GenerateCapaRequest] = None
):
    """
    US-708: Genera y persiste un Ticket CAPA dirigido al líder operativo interno
    con checklist de verificación pre-despacho.
    """
    req = request or GenerateCapaRequest()
    ticket = CapaTicketGenerator.generate_capa_ticket(
        case_id=case_id,
        override_department=req.override_department,
    )
    return {
        "status": "success",
        "case_id": case_id,
        "capa_ticket": _decimal_to_float(ticket.model_dump(mode="python")),
    }
