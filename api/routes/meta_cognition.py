"""
api/routes/meta_cognition.py
Endpoints para Meta-Cognición Dialéctica, Subagente Crítico Adversarial y MCTS.
Frontera 1 de Superinteligencia (Sprint 5.2).
"""

from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from config.settings import settings
from agent.core.skynet_runner import SkynetRunner
from agent.core.adversarial_critic import AdversarialCritic, AdversarialCritiqueResult
from agent.planner.mcts_negotiator import MCTSNegotiator, MCTSPlanResult
from agent.legal.cross_border_treaties import CrossBorderTreatiesEngine, CrossBorderEvaluationResult
from data.models import DisputeAnalysisReport

router = APIRouter(prefix="/meta-cognition", tags=["Meta-Cognición & Negociación MCTS"])
CASES_DIR = settings.DATA_DIR


# ==============================================================================
# Modelos de Petición
# ==============================================================================

class CritiqueCaseRequest(BaseModel):
    case_id: str = Field(..., description="Identificador del expediente a auditar.")
    seller_country: str = Field(default="MEXICO", description="País del vendedor/proveedor.")
    buyer_country: str = Field(default="MEXICO", description="País del comprador/retailer.")
    days_to_claim: int = Field(default=15, description="Días transcurridos entre entrega y reclamo.")
    has_edi_997: bool = Field(default=False, description="¿Existe acuse de recibo funcional EDI 997 con marca UTC?")


class MctsSimulateRequest(BaseModel):
    case_id: str = Field(..., description="Identificador del caso.")
    claimable_amount: Optional[Decimal] = Field(default=None, description="Monto en disputa (si es None, se toma del caso).")
    retailer_account_weight_pct: float = Field(default=20.0, ge=0.0, le=100.0, description="% de concentración de ventas.")
    supplier_cashflow_priority: str = Field(default="BALANCED", description="AGGRESSIVE, BALANCED o CASH_URGENT.")
    num_simulations: int = Field(default=500, ge=10, le=5000, description="Número de iteraciones Monte Carlo.")


class CrossBorderEvaluateRequest(BaseModel):
    seller_country: str = Field(..., description="País de origen del vendedor.")
    buyer_country: str = Field(..., description="País de destino del comprador.")
    days_elapsed: int = Field(default=12, description="Días entre arribo y reclamo de deducción.")
    claim_type: str = Field(default="SHORTAGE", description="Tipo de deducción (SHORTAGE, PRICING, DAMAGED, LOGISTICS).")
    contract_has_arbitration: bool = Field(default=False, description="¿Contrato prevé arbitraje comercial?")


# ==============================================================================
# Helpers
# ==============================================================================

def _get_case_report_and_docs(case_id: str):
    """Ejecuta o recupera el análisis del caso y sus documentos asociados."""
    case_path = CASES_DIR / case_id
    if not case_path.exists() or not case_path.is_dir():
        raise HTTPException(status_code=404, detail=f"Caso '{case_id}' no encontrado.")

    runner = SkynetRunner(case_id=case_id, fast_path=True, use_cache=True)
    report: Optional[DisputeAnalysisReport] = runner.run()
    if not report:
        raise HTTPException(status_code=422, detail=f"No se pudo conciliar el expediente '{case_id}'.")

    docs = getattr(runner.tool_executor, "loaded_documents", {}) or {}
    return report, docs


# ==============================================================================
# Endpoints
# ==============================================================================

@router.post("/critique", response_model=AdversarialCritiqueResult)
def critique_case(request: CritiqueCaseRequest):
    """
    Somete el dictamen del caso al Subagente Crítico Adversarial ('Abogado del Diablo').
    Audita vacíos probatorios, firmas en remisión, acuses EDI 997 y caducidad de plazos.
    """
    report, docs = _get_case_report_and_docs(request.case_id)

    critique = AdversarialCritic.critique_report(
        report=report,
        docs=docs,
        seller_country=request.seller_country,
        buyer_country=request.buyer_country,
        days_to_claim=request.days_to_claim,
        has_edi_997=request.has_edi_997
    )
    return critique


@router.post("/auto-harden")
def auto_harden_case(request: CritiqueCaseRequest):
    """
    Ejecuta el ciclo de meta-cognición dialéctica completo:
    1. Audita el dictamen con el subagente crítico hostil.
    2. Si detecta vulnerabilidades, inyecta automáticamente el escudo jurídico preventivo.
    """
    report, docs = _get_case_report_and_docs(request.case_id)

    critique = AdversarialCritic.critique_report(
        report=report,
        docs=docs,
        seller_country=request.seller_country,
        buyer_country=request.buyer_country,
        days_to_claim=request.days_to_claim,
        has_edi_997=request.has_edi_997
    )

    hardened_report = AdversarialCritic.auto_harden_report(report, critique)

    return {
        "status": "success",
        "case_id": request.case_id,
        "original_robustness_score": critique.robustness_score,
        "is_hardened": True,
        "critique": critique.model_dump(mode="json"),
        "hardened_resolution_notes": hardened_report.resolution_notes,
        "hardened_report": hardened_report.model_dump(mode="json")
    }


@router.post("/mcts-simulate", response_model=MCTSPlanResult)
def simulate_mcts_negotiation(request: MctsSimulateRequest):
    """
    Ejecuta la simulación de Árbol de Búsqueda Monte Carlo (MCTS) para determinar
    la trayectoria de negociación óptima (Litigio Agresivo, Preservación de Relación o Liquidación Express).
    """
    report, _ = _get_case_report_and_docs(request.case_id)

    claimable = request.claimable_amount
    if claimable is None:
        claimable = report.claimable_amount

    result = MCTSNegotiator.simulate_negotiation(
        case_id=request.case_id,
        claimable_amount=claimable,
        retailer_account_weight_pct=request.retailer_account_weight_pct,
        supplier_cashflow_priority=request.supplier_cashflow_priority,
        num_simulations=request.num_simulations
    )
    return result


@router.get("/treaties")
def get_international_treaties():
    """
    Retorna el compendio de artículos jurídicos y jurisprudencia transfronteriza
    (CISG Convención de Viena 1980, T-MEC Capítulo 20 y Código de Comercio Mexicano).
    """
    return CrossBorderTreatiesEngine.get_statutory_catalog()


@router.post("/evaluate-cross-border", response_model=CrossBorderEvaluationResult)
def evaluate_cross_border_trade(request: CrossBorderEvaluateRequest):
    """
    Audita una transacción comercial internacional y determina el régimen legal imperativo
    (CISG, T-MEC o Código de Comercio) y si operó la caducidad perentoria de la reclamación.
    """
    return CrossBorderTreatiesEngine.evaluate_transaction(
        seller_country=request.seller_country,
        buyer_country=request.buyer_country,
        days_elapsed_before_claim=request.days_elapsed,
        claim_type=request.claim_type,
        contract_has_arbitration=request.contract_has_arbitration
    )
