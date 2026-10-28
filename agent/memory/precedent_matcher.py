"""
agent/memory/precedent_matcher.py
Motor de Emparejamiento Semántico y Relevancia de Precedentes B2B (Pilar 2).

Compara las características de una disputa en curso contra la Red de Memoria
para identificar precedentes jurídicos y comerciales vinculantes aplicables,
generando argumentaciones sólidas para forzar el pago inmediato del retailer.
"""

import re
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, ConfigDict, Field

from agent.memory.precedent_graph import (
    DisputeMemoryNetwork,
    DisputePrecedentRecord
)


class MatchedPrecedent(BaseModel):
    """Precedente recuperado con puntaje de pertinencia y argumentación vinculante formulada."""
    model_config = ConfigDict(extra="allow")

    precedent: DisputePrecedentRecord
    similarity_score: float
    match_reasons: List[str]
    citation_clause_ref: str
    formal_citation_text: str


class PrecedentMatcher:
    """Motor de similitud multidimensional y generación de citas vinculantes."""

    def __init__(self, memory_network: Optional[DisputeMemoryNetwork] = None):
        self.memory = memory_network or DisputeMemoryNetwork()

    @staticmethod
    def _tokenize(text: str) -> set:
        """Extrae términos significativos de un texto."""
        words = re.findall(r'[a-zA-ZÁÉÍÓÚáéíóú0-9]+', text.lower())
        return {w for w in words if len(w) > 3}

    @classmethod
    def _jaccard_similarity(cls, text_a: str, text_b: str) -> float:
        """Calcula similitud de Jaccard entre dos cadenas de texto."""
        set_a = cls._tokenize(text_a)
        set_b = cls._tokenize(text_b)
        if not set_a or not set_b:
            return 0.0
        intersection = len(set_a.intersection(set_b))
        union = len(set_a.union(set_b))
        return intersection / union if union > 0 else 0.0

    def find_relevant_precedents(
        self,
        retailer_id: str,
        dispute_type: str,
        deduction_code: Optional[str] = None,
        contract_clause: Optional[str] = None,
        top_k: int = 3,
        min_threshold: float = 0.35
    ) -> List[MatchedPrecedent]:
        """
        Encuentra y clasifica los precedentes históricos más pertinentes a la disputa.
        """
        all_precedents = self.memory.get_all_precedents()
        if not all_precedents:
            return []

        target_ret = retailer_id.upper()
        target_code = (deduction_code or "").upper()
        target_clause = (contract_clause or "").upper()

        scored_matches: List[tuple[float, List[str], DisputePrecedentRecord]] = []

        for p in all_precedents:
            score = 0.0
            reasons = []

            # 1. Coincidencia de Retailer (Peso: 40%)
            p_ret = p.retailer_id.upper()
            if target_ret in p_ret or p_ret in target_ret:
                score += 0.40
                reasons.append(f"Mismo cliente corporativo ({p.retailer_name})")
            elif any(chain in target_ret and chain in p_ret for chain in ["WALMART", "AMAZON", "SORIANA", "CHEDRAUI", "COSTCO"]):
                score += 0.35
                reasons.append(f"Cadena comercial afín ({p.retailer_name})")

            # 2. Coincidencia de Tipo de Disputa / Causa Raíz (Peso: 35%)
            lex_sim = self._jaccard_similarity(dispute_type, p.dispute_type)
            if lex_sim > 0.15:
                sim_component = min(0.35, lex_sim * 0.7)
                score += sim_component
                reasons.append(f"Tipología de disputa similar ({p.dispute_type[:40]}...)")
            elif any(w in p.dispute_type.upper() for w in self._tokenize(dispute_type)):
                score += 0.20
                reasons.append("Palabras clave de controversia coincidentes")

            # 3. Coincidencia de Código de Deducción (Peso: 15%)
            if target_code and p.deduction_code:
                if target_code == p.deduction_code.upper():
                    score += 0.15
                    reasons.append(f"Mismo código de deducción '{p.deduction_code}'")
                elif target_code[:6] == p.deduction_code[:6].upper():
                    score += 0.08
                    reasons.append(f"Familia de deducción afín '{p.deduction_code}'")

            # 4. Bonificación por Precedente Favorable Ganado (Peso: 10%)
            if p.outcome == "WON":
                score += 0.10
                reasons.append("Precedente formalmente ganado al 100%")
            elif p.outcome == "PARTIAL_CONCESSION":
                score += 0.05
                reasons.append("Precedente con resolución favorable parcial")

            # 5. Coincidencia de Cláusula Contractual (Bonus adicional: 5%)
            if target_clause and p.governing_clause:
                if target_clause == p.governing_clause.upper():
                    score += 0.05
                    reasons.append(f"Idéntica cláusula contractual amparada ({p.governing_clause})")

            if score >= min_threshold:
                scored_matches.append((score, reasons, p))

        # Ordenar por puntaje descendente
        scored_matches.sort(key=lambda x: x[0], reverse=True)

        results: List[MatchedPrecedent] = []
        for s, reasons, prec in scored_matches[:top_k]:
            citation_text = (
                f"Conforme al precedente formalizado en el expediente {prec.case_id} "
                f"(fecha {prec.date_resolved}), donde {prec.retailer_name} acordó el reintegro de "
                f"${prec.recovered_amount:,.2f} USD ante una deducción análoga por '{prec.deduction_code}', "
                f"amparada en la cláusula contractual {prec.governing_clause}."
            )
            results.append(MatchedPrecedent(
                precedent=prec,
                similarity_score=round(s, 3),
                match_reasons=reasons,
                citation_clause_ref=prec.governing_clause,
                formal_citation_text=citation_text
            ))

        return results

    @classmethod
    def format_precedents_block_for_letter(cls, matches: List[MatchedPrecedent]) -> str:
        """Genera el bloque Markdown formal para insertar en la Carta de Reclamación."""
        if not matches:
            return ""

        lines = [
            "#### 4. Antecedentes y Precedentes Comerciales Vinculantes",
            "Hacemos notar que esta discrepancia no constituye un hecho aislado, existiendo antecedentes "
            "previos resueltos favorablemente con su representada bajo idénticos fundamentos técnico-contractuales:\n"
        ]

        for idx, m in enumerate(matches, 1):
            p = m.precedent
            lines.append(
                f"**Precedente {idx} (Expediente {p.case_id} — {p.date_resolved}):**\n"
                f"- **Criterio Acreditado:** {p.binding_argument}\n"
                f"- **Resultado Previo:** Restitución de **${p.recovered_amount:,.2f} USD** a favor del proveedor.\n"
                f"- **Fundamento Vinculante:** {p.governing_clause}."
            )
            lines.append("")

        lines.append(
            "Por tanto, en observancia del principio de coherencia comercial y buena fe contractual, "
            "solicitamos la aplicación del mismo criterio para el reintegro de la presente retención.\n"
        )
        return "\n".join(lines)
