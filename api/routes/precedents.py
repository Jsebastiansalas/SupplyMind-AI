"""
api/routes/precedents.py
Rutas de API para consulta de la Red de Memoria de Precedentes B2B y Perfiles de Retailer (Pilar 2).
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from agent.memory.precedent_graph import DisputeMemoryNetwork
from agent.memory.precedent_matcher import PrecedentMatcher

router = APIRouter(prefix="/precedents", tags=["Red de Memoria de Precedentes"])

memory_network = DisputeMemoryNetwork()
precedent_matcher = PrecedentMatcher(memory_network)


@router.get("/profiles")
def get_retailer_profiles():
    """Retorna todos los perfiles analíticos de retailers indexados en la red."""
    profiles = memory_network.get_all_retailer_profiles()
    return {
        "status": "success",
        "total_retailers": len(profiles),
        "profiles": [p.model_dump(mode="json") for p in profiles]
    }


@router.get("/retailer/{retailer_id}")
def get_retailer_precedents(retailer_id: str):
    """Retorna el perfil y el historial detallado de precedentes de un retailer."""
    profile = memory_network.get_retailer_profile(retailer_id)
    if not profile:
        raise HTTPException(status_code=404, detail=f"No se halló historial para el retailer '{retailer_id}'")

    precedents = memory_network.get_precedents_by_retailer(retailer_id)
    return {
        "status": "success",
        "profile": profile.model_dump(mode="json"),
        "total_precedents": len(precedents),
        "precedents": [p.model_dump(mode="json") for p in precedents]
    }


@router.get("/match")
def match_precedents(
    retailer_id: str = Query(..., description="ID o nombre del retailer / comprador"),
    dispute_type: str = Query(..., description="Causa raíz o tipo de discrepancia"),
    deduction_code: Optional[str] = Query(None, description="Código de deducción aplicada"),
    top_k: int = Query(3, ge=1, le=10)
):
    """Busca y pondera los precedentes históricos más pertinentes a una disputa en curso."""
    matches = precedent_matcher.find_relevant_precedents(
        retailer_id=retailer_id,
        dispute_type=dispute_type,
        deduction_code=deduction_code,
        top_k=top_k
    )
    formatted_letter_block = PrecedentMatcher.format_precedents_block_for_letter(matches)
    return {
        "status": "success",
        "matches_count": len(matches),
        "matches": [m.model_dump(mode="json") for m in matches],
        "formatted_letter_block": formatted_letter_block
    }


@router.get("/all")
def get_all_precedents():
    """Retorna la lista completa de precedentes almacenados en la red."""
    all_precedents = memory_network.get_all_precedents()
    return {
        "status": "success",
        "total_precedents": len(all_precedents),
        "precedents": [p.model_dump(mode="json") for p in all_precedents]
    }
