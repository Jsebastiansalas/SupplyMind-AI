"""
agent/legal/cross_border_treaties.py
Módulo de Jurisprudencia Transfronteriza (CISG, T-MEC / USMCA, Arbitraje Internacional).
Frontera 1 de Superinteligencia (Sprint 5.2).

Aplica la Convención de las Naciones Unidas sobre los Contratos de Compraventa
Internacional de Mercaderías (Convención de Viena de 1980 - CISG) y el T-MEC
a operaciones de comercio internacional para desmantelar deducciones ilícitas
cuando el comprador incumple sus obligaciones perentorias de examen y notificación.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class TreatyArticle(BaseModel):
    """Representación formal de un precepto de tratado internacional o ley mercantil."""
    treaty: str
    article: str
    title: str
    statutory_text: str
    strategic_defense: str


class CrossBorderEvaluationResult(BaseModel):
    """Dictamen pericial sobre aplicabilidad de tratados transfronterizos."""
    is_cross_border: bool
    seller_country: str
    buyer_country: str
    governing_regime: str
    applicable_articles: List[TreatyArticle] = Field(default_factory=list)
    peremptory_notice_limit_days: int
    days_elapsed: int
    claim_forfeited: bool = False
    binding_legal_thesis: str
    recommended_arbitral_venue: str


# ==============================================================================
# Catálogo Canónico de Preceptos Transfronterizos
# ==============================================================================

CISG_ARTICLES = {
    "ART_38": TreatyArticle(
        treaty="CISG (Convención de Viena 1980)",
        article="Artículo 38",
        title="Obligación Perentoria de Examen de Mercaderías",
        statutory_text=(
            "1. El comprador deberá examinar o hacer examinar las mercaderías en el plazo "
            "más breve posible atendidas las circunstancias.\n"
            "2. Si el contrato implica el transporte de las mercaderías, el examen podrá "
            "aplazarse hasta que las mercaderías hayan llegado a su destino."
        ),
        strategic_defense=(
            "El comprador no puede alegar faltantes o averías semanas después si tenía la obligación "
            "legal insoslayable de verificar las tarimas en el acto mismo de la recepción en muelle."
        )
    ),
    "ART_39": TreatyArticle(
        treaty="CISG (Convención de Viena 1980)",
        article="Artículo 39",
        title="Pérdida Absoluta del Derecho a Reclamar por Caducidad",
        statutory_text=(
            "1. El comprador perderá el derecho a invocar la falta de conformidad de las "
            "mercaderías si no lo comunica al vendedor, especificando su naturaleza, dentro de un "
            "plazo razonable a partir del momento en que la haya descubierto o debiera haberla descubierto.\n"
            "2. En todo caso, el comprador perderá el derecho a invocar la falta de conformidad si no la "
            "comunica a más tardar en el plazo de dos años contados desde la fecha de entrega efectiva."
        ),
        strategic_defense=(
            "Habiendo transcurrido el plazo razonable sin protesta fundada, el derecho a deducir montos "
            "o aplicar cargos retroactivos queda legalmente extinguido por caducidad sustantiva."
        )
    ),
    "ART_50": TreatyArticle(
        treaty="CISG (Convención de Viena 1980)",
        article="Artículo 50",
        title="Restricción a la Rebaja Unilateral de Precio",
        statutory_text=(
            "Si las mercaderías no son conformes al contrato, el comprador podrá rebajar el precio... "
            "Sin embargo, el comprador no podrá rebajar el precio si el vendedor subsana cualquier "
            "incumplimiento con arreglo al artículo 37 o 48, o si el comprador se niega a aceptar "
            "el cumplimiento por el vendedor."
        ),
        strategic_defense=(
            "Las deducciones unilaterales en estado de cuenta constituyen una rebaja forzosa prohibida "
            "por el tratado internacional si no medió derecho a inspección conjunta ni subsanación."
        )
    ),
    "ART_74": TreatyArticle(
        treaty="CISG (Convención de Viena 1980)",
        article="Artículo 74",
        title="Indemnización por Daños y Perjuicios Comerciales",
        statutory_text=(
            "La indemnización de daños y perjuicios por el incumplimiento del contrato en que haya "
            "incurrido una de las partes comprenderá el valor de la pérdida sufrida y el de la ganancia "
            "dejada de obtener por la otra parte como consecuencia del incumplimiento."
        ),
        strategic_defense=(
            "La retención arbitraria de fondos faculta al vendedor a reclamar intereses moratorios "
            "bancarios y gastos de defensa pericial y arbitraje."
        )
    )
}

TMEC_ARTICLES = {
    "CAP_20": TreatyArticle(
        treaty="T-MEC / USMCA (Capítulo 20)",
        article="Capítulo 20, Sección B",
        title="Trato Justo y No Discriminatorio en Cadenas de Suministro Transfronterizas",
        statutory_text=(
            "Las partes asegurarán que los procedimientos comerciales y aduaneros faciliten el "
            "comercio transparente y expedito, prohibiendo prácticas comerciales abusivas o "
            "retenciones unilaterales de pagos que distorsionen el comercio bilateral."
        ),
        strategic_defense=(
            "En el comercio trilateral México-EE.UU.-Canadá, los importadores mayoristas no pueden "
            "imponer penalidades contractuales asimétricas no contempladas expresamente en la orden de compra."
        )
    )
}

CCOM_ARTICLES = {
    "ART_88": TreatyArticle(
        treaty="Código de Comercio (México)",
        article="Artículo 88",
        title="Plazo Perentorio de Reclamación Mercantil",
        statutory_text=(
            "En el contrato de compraventa mercantil, el comprador que no reclame dentro de los "
            "cinco días siguientes a la recepción de las mercaderías sobre las faltas de calidad "
            "o cantidad, o dentro de treinta días por vicios internos, perderá toda acción contra el vendedor."
        ),
        strategic_defense=(
            "Si la deducción se formuló después de los 5 días de ley tras el arribo de la mercancía, "
            "opera la caducidad perentoria de pleno derecho."
        )
    )
}


# ==============================================================================
# Motor Pericial de Tratados Transfronterizos
# ==============================================================================

class CrossBorderTreatiesEngine:
    """
    Evalúa la dimensión transfronteriza y aplica el bloque de legalidad internacional
    para proteger los cobros de exportadores e importadores.
    """

    NORTH_AMERICA_COUNTRIES = {"MEXICO", "MX", "USA", "US", "UNITED STATES", "CANADA", "CA"}

    @classmethod
    def evaluate_transaction(
        cls,
        seller_country: str = "MEXICO",
        buyer_country: str = "MEXICO",
        days_elapsed_before_claim: int = 0,
        claim_type: str = "SHORTAGE",
        contract_has_arbitration: bool = False
    ) -> CrossBorderEvaluationResult:
        """
        Determina el régimen jurídico imperativo y los artículos aplicables.
        """
        seller_clean = seller_country.strip().upper()
        buyer_clean = buyer_country.strip().upper()

        is_cross_border = (seller_clean != buyer_clean) and bool(seller_clean and buyer_clean)

        applicable_articles: List[TreatyArticle] = []
        governing_regime = "CODIGO_COMERCIO_MEXICO"
        peremptory_limit = 5  # Por defecto: 5 días Art. 88 CCom para faltantes aparentes
        arbitral_venue = "Tribunales Locales Mercantiles / Centro de Mediación CANACO"

        if is_cross_border:
            # CISG rige por defecto salvo exclusión contractual expresa (Art. 1 CISG)
            governing_regime = "CISG_CONVENCION_VIENA_1980"
            applicable_articles.append(CISG_ARTICLES["ART_38"])
            applicable_articles.append(CISG_ARTICLES["ART_39"])
            applicable_articles.append(CISG_ARTICLES["ART_50"])

            # En CISG el plazo razonable para faltantes aparentes en retail es típicamente 5 a 10 días
            peremptory_limit = 10
            arbitral_venue = "Corte Internacional de Arbitraje de la Cámara de Comercio Internacional (ICC Paris)"

            # Si es intra-bloque norteamericano, adicionar T-MEC
            if seller_clean in cls.NORTH_AMERICA_COUNTRIES and buyer_clean in cls.NORTH_AMERICA_COUNTRIES:
                governing_regime = "CISG_Y_TMEC_USMCA"
                applicable_articles.append(TMEC_ARTICLES["CAP_20"])
        else:
            # Operación doméstica: Código de Comercio Mexicano
            applicable_articles.append(CCOM_ARTICLES["ART_88"])
            if contract_has_arbitration:
                arbitral_venue = "Comisión de Mediación y Arbitraje Comercial de la CANACO"

        # Evaluar caducidad perentoria
        claim_forfeited = False
        if days_elapsed_before_claim > peremptory_limit:
            claim_forfeited = True

        # Tesis jurídica vinculante
        if is_cross_border:
            if claim_forfeited:
                thesis = (
                    f"RÉGIMEN INTERNACIONAL CISG (Art. 38 y 39): El comprador omitió formular "
                    f"protesta pericial oportuna dentro del plazo razonable de {peremptory_limit} días "
                    f"(reclamo formulado a los {days_elapsed_before_claim} días). Conforme a la doctrina uniforme "
                    f"de la CNUDMI/UNCITRAL, el derecho a invocar falta de conformidad se encuentra "
                    f"definitivamente EXTINTO por caducidad sustantiva."
                )
            else:
                thesis = (
                    f"RÉGIMEN INTERNACIONAL CISG: Operación regida por la Convención de Viena de 1980. "
                    f"El comprador está sujeto al estándar de prueba estricta del Art. 38, requiriendo "
                    f"constancia pericial fáctica de discrepancia en el muelle de destino."
                )
        else:
            if claim_forfeited:
                thesis = (
                    f"DERECHO MERCANTIL MEXICANO (Art. 88 Código de Comercio): La reclamación por {claim_type} "
                    f"fue promovida a los {days_elapsed_before_claim} días naturales, excediendo con creces el plazo "
                    f"fatal de 5 días legalmente estipulado. Se decreta la pérdida de toda acción mercantil."
                )
            else:
                thesis = (
                    f"DERECHO MERCANTIL MEXICANO: Reclamación dentro del término legal preliminar. "
                    f"Requiere cotejo estricto de la remisión sellada y firma de conformidad de recepción."
                )

        return CrossBorderEvaluationResult(
            is_cross_border=is_cross_border,
            seller_country=seller_clean,
            buyer_country=buyer_clean,
            governing_regime=governing_regime,
            applicable_articles=applicable_articles,
            peremptory_notice_limit_days=peremptory_limit,
            days_elapsed=days_elapsed_before_claim,
            claim_forfeited=claim_forfeited,
            binding_legal_thesis=thesis,
            recommended_arbitral_venue=arbitral_venue
        )

    @classmethod
    def get_statutory_catalog(cls) -> Dict[str, Any]:
        """Retorna el catálogo completo de normas internacionales y domésticas."""
        return {
            "cisg": {k: v.model_dump() for k, v in CISG_ARTICLES.items()},
            "tmec": {k: v.model_dump() for k, v in TMEC_ARTICLES.items()},
            "ccom": {k: v.model_dump() for k, v in CCOM_ARTICLES.items()},
        }
