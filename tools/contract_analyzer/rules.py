import re
import unicodedata
from typing import List, Union, Dict, Any, Optional, Tuple
from decimal import Decimal
from pydantic import BaseModel, ConfigDict
from data.models import CommercialContract, ContractClause
from tools.reconciliation_engine.engine import ReconciliationSummary
from config.settings import settings

try:
    from tools.contract_analyzer.rag import VectorContract, ContractRAG
except ImportError:
    VectorContract = None
    ContractRAG = None

class ClauseMatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    clause_id: str
    title: str
    is_applicable: bool
    is_deduction_authorized: bool
    explanation: str

class ContractEvaluationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    contract_id: str
    matches: List[ClauseMatch]
    contractual_justification_valid: bool
    summary_legal_assessment: str
    recommended_contract_action: str

# =========================================================================
# PERFILES DE INTENCIÓN SEMÁNTICA COMERCIAL (RAG & TAXONOMÍA DE DISPUTAS)
# =========================================================================

INTENT_PROFILES = {
    "SHORTAGE": {
        "keywords": [
            "faltant", "shortage", "merma", "incomplet", "no entregad", "no recibid",
            "dock shortage", "conteo fisico", "cantidades no recibidas", "unidades faltantes",
            "recepcion en muelle", "bienes no entregados", "recepcion incompleta"
        ],
        "policies": [
            "deduction_allowed_on_signed_discrepancy", "allow_shortage", "shortage",
            "shortage_deduction", "signed_discrepancy", "allow_shortage_deduction_if_signed"
        ],
        "rag_query": "faltante físico en muelle unidades no entregadas merma conteo remisión deducción"
    },
    "PRICE_VARIANCE": {
        "keywords": [
            "precio", "precios", "sobreprecio", "orden de compra", "tarifa", "unit price",
            "rate", "costo unitario", "variacion de precio", "strict match", "oc", "acordado en po",
            "prevalecera", "ajuste de precio", "alineacion a precios"
        ],
        "policies": [
            "strict_match", "price", "pricing", "po_price", "price_variance", "po_prevalence"
        ],
        "rag_query": "precio unitario orden de compra tarifa pactada sobreprecio ajuste unitario PO"
    },
    "DAMAGED_GOODS": {
        "keywords": [
            "danad", "danio", "averia", "averiad", "empaque roto", "humedad", "abollad",
            "destruid", "calidad defectuosa", "damaged", "constancia de averia", "reproceso",
            "mercancia danada", "mercancia averiada"
        ],
        "policies": [
            "photo_evidence_required", "damaged_goods_policy", "damage", "averia"
        ],
        "rag_query": "avería física humedad empaque roto abollado deducción penalidad mercancía dañada"
    },
    "UNILATERAL_PENALTY": {
        "keywords": [
            "penaliz", "penalidad", "cargo administrativo", "multa", "extemporane",
            "asn", "otif", "sancion", "unilateral", "fee", "mora", "descarga extemporanea",
            "retenciones unilaterales", "sin adenda", "improcedencia"
        ],
        "policies": [
            "limit_penalty_or_forbidden", "general_compliance", "penalty", "compliance"
        ],
        "rag_query": "penalización unilateral cargo administrativo multa descarga extemporánea EDI ASN mora"
    }
}

def _normalize_text(text: str) -> str:
    """Normaliza texto eliminando acentos, caracteres de control y convirtiendo a minúsculas."""
    if not text:
        return ""
    nfkd = unicodedata.normalize('NFKD', text.lower())
    return "".join(c for c in nfkd if not unicodedata.combining(c))

def _score_clause_for_intent(
    clause_id: str,
    title: str,
    text: str,
    policy: str,
    intent_key: str
) -> float:
    """
    Calcula la afinidad semántica de una cláusula con una intención de disputa comercial.
    Asigna pesos diferenciales a título (x4.0), política (x3.0) y cuerpo normativo (x1.5).
    """
    profile = INTENT_PROFILES.get(intent_key)
    if not profile:
        return 0.0

    norm_id = _normalize_text(clause_id)
    norm_title = _normalize_text(title)
    norm_text = _normalize_text(text)
    norm_policy = _normalize_text(policy)

    score = 0.0

    # Coincidencias en política explícita
    for pol_target in profile["policies"]:
        if pol_target in norm_policy:
            score += 4.0
            break

    # Coincidencias de palabras clave en el título
    for kw in profile["keywords"]:
        if kw in norm_title:
            score += 3.5
        elif kw in norm_text:
            score += 1.2

    # Bonus por numeraciones clásicas si están presentes como fallback secundario
    if intent_key == "SHORTAGE" and ("4.2" in norm_id or "4.1" in norm_id):
        score += 1.5
    elif intent_key == "PRICE_VARIANCE" and ("3.1" in norm_id or "3.2" in norm_id):
        score += 1.5
    elif intent_key == "DAMAGED_GOODS" and ("5.1" in norm_id or "37" in norm_id):
        score += 1.5
    elif intent_key == "UNILATERAL_PENALTY" and ("7.2" in norm_id or "7.3" in norm_id or "5.3" in norm_id):
        score += 1.5

    return score

def _evaluate_clause_decision(
    clause_id: str,
    title: str,
    text: str,
    policy: str,
    intent_key: str
) -> Tuple[bool, str]:
    """
    Determina si la cláusula seleccionada autoriza legalmente la retención aplicada
    y redacta la fundamentación jurídica.
    """
    norm_text = _normalize_text(text)
    norm_policy = _normalize_text(policy)

    if intent_key == "SHORTAGE":
        # Autorizado si contempla deducción por faltante en remisión
        auth_cues = [
            "facultado para deducir", "podra deducir", "deducible", "compensacion automatica",
            "descontar", "retener", "deduccion permitida", "deduccion del 100%", "deduccion autorizada",
            "autoriza la deduccion"
        ]
        if any(cue in norm_text for cue in auth_cues) or "deduction_allowed" in norm_policy or "allow_shortage" in norm_policy or "4.2" in clause_id:
            return True, f"La {clause_id} autoriza la deducción por faltantes físicos acreditados en remisión de entrega."
        else:
            return False, f"La {clause_id} ('{title}') no contempla deducción directa sin acta previa."

    elif intent_key == "PRICE_VARIANCE":
        # Autorizado si prevalece la Orden de Compra sobre precios facturados
        price_cues = [
            "coincidir estrictamente", "regiran con caracter vinculante", "deducir de pleno derecho el sobreprecio",
            "ajustarse a la orden de compra", "ajustarse a la oc", "prevalecera la orden de compra",
            "facultado para deducir", "sobreprecio", "strict_match"
        ]
        if any(cue in norm_text for cue in price_cues) or "strict_match" in norm_policy or "3.1" in clause_id:
            return True, f"Precios facturados deben ajustarse a la OC según {clause_id} ('{title}')."
        else:
            return False, f"La {clause_id} ('{title}') no ampara ajuste unilateral de tarifa."

    elif intent_key == "DAMAGED_GOODS":
        # Casos con deducción autorizada (ej. penalidad 150% o deducción pactada con sello de muelle)
        if "photo_evidence_required" in norm_policy or ("fotografic" in norm_text and "48 horas" in norm_text and "150%" not in norm_text and "retener o deducir" not in norm_text):
            return False, f"Requiere notificación fotográfica según {clause_id}."
        elif "150%" in norm_text or "retener o deducir" in norm_text or "descontados inmediatamente" in norm_text or "damaged_goods_policy" in norm_policy:
            return True, f"La {clause_id} ('{title}') autoriza deducir mercancía dañada constatada al momento de la descarga."
        else:
            return False, f"Requiere acreditación de avería conforme a {clause_id}."

    elif intent_key == "UNILATERAL_PENALTY":
        # Retenciones unilaterales, multas operativas o EDI ASN sin adenda escrita
        return False, f"La {clause_id} ('{title}') estipula la improcedencia de penalizaciones unilaterales sin acuerdo formal previo."

    return False, f"Cláusula {clause_id} evaluada para {intent_key}."

def evaluate_contract_compliance(
    contract: Union[CommercialContract, "VectorContract"],
    summary: ReconciliationSummary
) -> ContractEvaluationResult:
    """
    Analiza semánticamente las cláusulas del contrato contra los hallazgos de conciliación física.
    Soporta contratos masivos en ChromaDB (RAG) y modelos CommercialContract con numeración arbitraria.
    """
    matches: List[ClauseMatch] = []
    is_valid = False

    # 1. Determinar intenciones de disputa relevantes a partir del ReconciliationSummary
    needed_intents = []
    if summary.total_missing_amount > Decimal("0.00") or summary.primary_discrepancy_type == "FALTANTE_DE_MERCANCIA":
        needed_intents.append("SHORTAGE")
    if summary.total_price_discrepancy_amount != Decimal("0.00") or summary.primary_discrepancy_type == "DIFERENCIA_DE_PRECIO":
        needed_intents.append("PRICE_VARIANCE")
    if summary.total_damaged_amount > Decimal("0.00") or summary.primary_discrepancy_type == "MERCANCIA_AVERIADA":
        needed_intents.append("DAMAGED_GOODS")
    if summary.unjustified_deductions_amount > Decimal("0.00"):
        needed_intents.append("UNILATERAL_PENALTY")

    # Si no se detectaron intenciones primarias pero hay deducciones en el pago, evaluar penalidad general
    if not needed_intents and summary.difference != Decimal("0.00"):
        needed_intents.append("SHORTAGE")

    # =========================================================================
    # CAMINO A: CONTRATO VECTORIAL RAG (ChromaDB para contratos masivos o Markdown)
    # =========================================================================
    if VectorContract and isinstance(contract, VectorContract):
        rag = ContractRAG()
        for intent_key in needed_intents:
            query = INTENT_PROFILES[intent_key]["rag_query"]
            rich_results = rag.search_clauses_rich(contract.collection_name, query, n_results=1)

            if rich_results:
                top_clause = rich_results[0]
                doc_text = top_clause["text"]
                c_id = top_clause.get("clause_id", "RAG-MATCH")
                c_title = top_clause.get("title", "Cláusula Contractual")

                # Si el título o id vienen como RAG-MATCH genérico, extraer del encabezado del texto
                if c_id == "RAG-MATCH" and "##" in doc_text:
                    first_line = doc_text.splitlines()[0].replace("#", "").strip()
                    parts = first_line.split(":", 1)
                    c_id = parts[0].strip() if parts[0].strip() else "RAG-MATCH"
                    if len(parts) > 1 and parts[1].strip():
                        c_title = parts[1].strip()

                auth, expl = _evaluate_clause_decision(
                    clause_id=c_id,
                    title=c_title,
                    text=doc_text,
                    policy=top_clause.get("policy", ""),
                    intent_key=intent_key
                )

                matches.append(
                    ClauseMatch(
                        clause_id=c_id,
                        title=c_title,
                        is_applicable=True,
                        is_deduction_authorized=auth,
                        explanation=expl
                    )
                )
                if auth:
                    is_valid = True

    # =========================================================================
    # CAMINO B: CONTRATO COMERCIAL PYDANTIC (Clasificación Semántica Híbrida)
    # =========================================================================
    elif isinstance(contract, CommercialContract):
        for intent_key in needed_intents:
            best_clause: Optional[ContractClause] = None
            best_score = -1.0

            for clause in contract.clauses:
                score = _score_clause_for_intent(
                    clause_id=clause.clause_id,
                    title=clause.title,
                    text=clause.text,
                    policy=clause.policy,
                    intent_key=intent_key
                )
                if score > best_score:
                    best_score = score
                    best_clause = clause

            # Si encontramos una cláusula con afinidad semántica suficiente (>= 1.5)
            if best_clause and best_score >= 1.5:
                auth, expl = _evaluate_clause_decision(
                    clause_id=best_clause.clause_id,
                    title=best_clause.title,
                    text=best_clause.text,
                    policy=best_clause.policy,
                    intent_key=intent_key
                )

                # Evitar duplicar la misma cláusula si ya fue agregada por otra intención
                if not any(m.clause_id == best_clause.clause_id for m in matches):
                    matches.append(
                        ClauseMatch(
                            clause_id=best_clause.clause_id,
                            title=best_clause.title,
                            is_applicable=True,
                            is_deduction_authorized=auth,
                            explanation=expl
                        )
                    )
                    if auth:
                        is_valid = True

    # =========================================================================
    # DICTAMEN LEGAL FINAL CONSERVANDO COMPATIBILIDAD CON REPORTES Y AUDITORÍAS
    # =========================================================================
    if is_valid and summary.unjustified_deductions_amount == Decimal("0.00"):
        assessment = (
            f"La deducción de ${summary.justified_deductions_amount:,.2f} aplicada por el cliente "
            f"se encuentra plenamente justificada conforme a las cláusulas comerciales extraídas."
        )
        action = "Aceptar la deducción en cartera y emitir Nota de Crédito comercial."
    elif summary.unjustified_deductions_amount > Decimal("0.00"):
        assessment = (
            f"Evaluación algorítmica y semántica completada. Posible deducción de ${summary.unjustified_deductions_amount:,.2f} requiere análisis final por el Agente."
        )
        action = "Revisar evidencia y cláusulas RAG para determinar validez total."
    elif is_valid:
        assessment = "Se detectaron cláusulas contractuales aplicables para la conciliación."
        action = "Proceder con la formalización del ajuste comercial."
    else:
        assessment = "No se detectaron causales contractuales válidas."
        action = "Solicitar aclaración al cliente."

    contract_id = getattr(contract, "contract_id", "Desconocido")
    return ContractEvaluationResult(
        contract_id=contract_id,
        matches=matches,
        contractual_justification_valid=is_valid,
        summary_legal_assessment=assessment,
        recommended_contract_action=action
    )
