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


def _canonical_retailer(name: str) -> tuple[str, str, str]:
    """Retorna (canonical_id, display_name, color_hex) para agrupación."""
    n = name.lower()
    if "walmart" in n:
        return ("RET_WALMART", "Walmart México", "#0071dc")
    elif "amazon" in n:
        return ("RET_AMAZON", "Amazon México", "#ff9900")
    elif "liverpool" in n:
        return ("RET_LIVERPOOL", "Liverpool", "#e6007e")
    elif "soriana" in n:
        return ("RET_SORIANA", "Soriana Hiper", "#e31837")
    elif "costco" in n:
        return ("RET_COSTCO", "Costco Wholesale", "#005baa")
    elif "chedraui" in n:
        return ("RET_CHEDRAUI", "Chedraui", "#f58220")
    elif "home" in n and "depot" in n:
        return ("RET_HOMEDEPOT", "The Home Depot", "#f96302")
    elif "mercadolibre" in n:
        return ("RET_MELI", "Mercado Libre", "#ffe600")
    elif "oxxo" in n:
        return ("RET_OXXO", "OXXO FEMSA", "#e11b22")
    elif "cisco" in n:
        return ("RET_CISCO", "Cisco Systems", "#049fd9")
    elif "samsung" in n:
        return ("RET_SAMSUNG", "Samsung Electronics", "#1428a0")
    elif "nestle" in n:
        return ("RET_NESTLE", "Nestlé México", "#4a90e2")
    elif "inditex" in n:
        return ("RET_INDITEX", "Inditex Zara", "#c084fc")
    elif "apple" in n:
        return ("RET_APPLE", "Apple Enterprise", "#a855f7")
    elif "pepsico" in n:
        return ("RET_PEPSICO", "PepsiCo", "#2563eb")
    elif "modelo" in n:
        return ("RET_MODELO", "Grupo Modelo", "#d97706")
    elif "farma" in n:
        return ("RET_FARMA", "Farmacias del Ahorro", "#10b981")
    elif "truper" in n:
        return ("RET_TRUPER", "Truper Herramientas", "#ea580c")
    elif "adversarial" in n:
        return ("RET_ADVERSARIAL", "Pruebas Adversariales", "#ef4444")
    else:
        clean = name.replace("Cust-", "").replace(" Mx", "").replace(" Mexico", "").title()
        return (f"RET_{clean[:8].upper()}", clean, "#8b5cf6")


def _classify_norm(clause: str, dispute_type: str) -> tuple[str, str, str, str]:
    """Retorna (norm_id, norm_name, desc, color_hex)."""
    c = (clause + " " + dispute_type).lower()
    if "faltante" in c or "remisi" in c or "88" in c or "pod" in c or "sell" in c:
        return ("NORM_ART88", "Art. 88 CCom (Recepción Tácita)", "Prevalencia de POD firmado en muelle frente a reclamos tardíos", "#10b981")
    elif "averia" in c or "avería" in c or "48h" in c or "notific" in c or "5.1" in c:
        return ("NORM_NOTICE_48H", "Cláusula 5.1 (Ventana 48h)", "Plazo perentorio improrrogable para dictamen de daños ocultos", "#f59e0b")
    elif "precio" in c or "price" in c or "3.1" in c or "oc" in c or "po" in c:
        return ("NORM_PRICE_PO", "Cláusula 3.1 (Inalterabilidad PO)", "Precios unitarios pactados en orden de compra prevalecen sobre factura", "#38bdf8")
    elif "doble" in c or "otif" in c or "7.3" in c or "multa" in c or "penaliz" in c:
        return ("NORM_DOUBLE_PENALTY", "Cláusula 7.3 (Non Bis In Idem)", "Prohibición contractual de doble penalización sobre un mismo evento", "#f43f5e")
    elif "fob" in c or "cif" in c or "incoterm" in c or "flete" in c:
        return ("NORM_INCOTERM", "Incoterms 2020 (Riesgo en Muelle)", "Transferencia formal del riesgo operativo al transportista en origen", "#a855f7")
    elif "rebate" in c or "volumen" in c or "descuento" in c:
        return ("NORM_REBATE", "Acuerdo Marco (Rebates Pactados)", "Exigibilidad de adendas formalmente firmadas para aplicar descuentos anuales", "#06b6d4")
    elif "fx" in c or "cambi" in c or "dolar" in c or "divisa" in c:
        return ("NORM_FX", "BANXICO / DOF (Tipo de Cambio)", "Tipo de cambio oficial del día de pago bancario sin sobrecargos", "#ec4899")
    else:
        return ("NORM_GENERAL", "Código de Comercio (Buena Fe)", "Principio general de cumplimiento estricto y pacta sunt servanda", "#d4af37")


@router.get("/graph")
def get_precedent_graph():
    """
    Retorna la topología interactiva de la red de precedentes jurídicos y comerciales:
    Nodos de Retailers, Nodos de Precedentes ganados y Nodos de Normas Legales / Cláusulas rectoras.
    """
    all_precedents = memory_network.get_all_precedents()

    # 1. Normas Legales predefinidas
    legal_norms: Dict[str, Dict[str, Any]] = {}
    
    # 2. Agrupación por Retailer
    retailers_map: Dict[str, Dict[str, Any]] = {}

    precedent_nodes = []
    links = []

    total_disputed = 0.0
    total_recovered = 0.0
    won_count = 0

    # Procesar cada precedente
    for p in all_precedents:
        rec_f = float(p.recovered_amount)
        disp_f = float(p.disputed_amount)
        total_recovered += rec_f
        total_disputed += disp_f
        if p.outcome == "WON":
            won_count += 1

        # Retailer
        ret_id, ret_name, ret_color = _canonical_retailer(p.retailer_name)
        if ret_id not in retailers_map:
            retailers_map[ret_id] = {
                "id": ret_id,
                "label": ret_name,
                "type": "retailer",
                "color": ret_color,
                "cases_count": 0,
                "total_disputed": 0.0,
                "total_recovered": 0.0,
                "precedent_ids": []
            }
        retailers_map[ret_id]["cases_count"] += 1
        retailers_map[ret_id]["total_disputed"] += disp_f
        retailers_map[ret_id]["total_recovered"] += rec_f
        retailers_map[ret_id]["precedent_ids"].append(p.precedent_id)

        # Norma Legal
        norm_id, norm_title, norm_desc, norm_color = _classify_norm(p.governing_clause, p.dispute_type)
        if norm_id not in legal_norms:
            legal_norms[norm_id] = {
                "id": norm_id,
                "label": norm_title,
                "description": norm_desc,
                "type": "legal_norm",
                "color": norm_color,
                "precedents_count": 0,
                "recovered_usd": 0.0
            }
        legal_norms[norm_id]["precedents_count"] += 1
        legal_norms[norm_id]["recovered_usd"] += rec_f

        # Nodo de Precedente
        prec_color = "#10b981" if p.outcome == "WON" else ("#f59e0b" if p.outcome == "PARTIAL_CONCESSION" else "#f43f5e")
        prec_node = {
            "id": p.precedent_id,
            "label": p.case_id.upper().replace("CASE_", "CASO "),
            "subtitle": p.dispute_type[:45],
            "type": "precedent",
            "case_id": p.case_id,
            "outcome": p.outcome,
            "disputed_amount": disp_f,
            "recovered_amount": rec_f,
            "success_rate_pct": round(p.success_rate_ratio * 100, 1),
            "governing_clause": p.governing_clause,
            "binding_argument": p.binding_argument,
            "color": prec_color,
            "radius": 12 if rec_f > 10000 else 9
        }
        precedent_nodes.append(prec_node)

        # Enlace Retailer -> Precedente
        links.append({
            "source": ret_id,
            "target": p.precedent_id,
            "relation": "DISPUTA_RESUELTA",
            "color": f"{ret_color}66",
            "value": 1
        })

        # Enlace Precedente -> Norma Legal
        links.append({
            "source": p.precedent_id,
            "target": norm_id,
            "relation": "FUNDADO_EN",
            "color": f"{norm_color}66",
            "value": 1
        })

    # Nodo Central Hub
    hub_node = {
        "id": "HUB_SUPPLYMIND",
        "label": "SupplyMind AI Legal Core",
        "subtitle": f"{len(all_precedents)} Fallos Vinculantes",
        "type": "hub",
        "color": "#d4af37",
        "radius": 26,
        "total_recovered_usd": round(total_recovered, 2),
        "total_precedents": len(all_precedents)
    }

    # Formatear nodos de Retailers y agregar enlaces Hub -> Retailers
    retailer_nodes = []
    for r_id, r_data in retailers_map.items():
        success_rate = round((r_data["total_recovered"] / r_data["total_disputed"] * 100), 1) if r_data["total_disputed"] > 0 else 0.0
        r_node = {
            "id": r_id,
            "label": r_data["label"],
            "type": "retailer",
            "cases_count": r_data["cases_count"],
            "total_disputed_usd": round(r_data["total_disputed"], 2),
            "total_recovered_usd": round(r_data["total_recovered"], 2),
            "recovery_rate_pct": success_rate,
            "color": r_data["color"],
            "radius": min(24, 14 + r_data["cases_count"] * 2)
        }
        retailer_nodes.append(r_node)

        links.append({
            "source": "HUB_SUPPLYMIND",
            "target": r_id,
            "relation": "AUDITA_CARTERA",
            "color": "rgba(212, 175, 55, 0.4)",
            "value": max(1, r_data["cases_count"])
        })

    # Formatear nodos de Normas
    norm_nodes = []
    for n_id, n_data in legal_norms.items():
        n_node = {
            "id": n_id,
            "label": n_data["label"],
            "subtitle": n_data["description"][:50],
            "type": "legal_norm",
            "precedents_count": n_data["precedents_count"],
            "recovered_usd": round(n_data["recovered_usd"], 2),
            "color": n_data["color"],
            "radius": min(22, 13 + n_data["precedents_count"])
        }
        norm_nodes.append(n_node)

    all_nodes = [hub_node] + retailer_nodes + norm_nodes + precedent_nodes

    return {
        "status": "success",
        "summary": {
            "total_nodes": len(all_nodes),
            "total_links": len(links),
            "total_retailers": len(retailer_nodes),
            "total_precedents": len(precedent_nodes),
            "total_legal_norms": len(norm_nodes),
            "total_disputed_usd": round(total_disputed, 2),
            "total_recovered_usd": round(total_recovered, 2),
            "global_recovery_rate_pct": round((total_recovered / total_disputed * 100), 2) if total_disputed > 0 else 0.0,
            "won_ratio_pct": round((won_count / len(all_precedents) * 100), 2) if all_precedents else 0.0
        },
        "nodes": all_nodes,
        "links": links
    }

