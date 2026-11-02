"""
agent/core/relational_health_engine.py
Guardrail de Salud Relacional & Riesgo de Deserción (LTV & Churn Index) (Fase 7 - Sprint 7.3).
Calcula el Relationship Health Index (RHI 0-100 pts) ponderando LTV, Share of Wallet,
Margen Bruto y Reciprocidad Histórica, modulando dinámicamente la agresividad y tono
del motor de negociación bilateral B2B.
"""

from decimal import Decimal
from typing import Dict, Any, Optional
import hashlib

from data.models import RelationalHealthIndexReport
from agent.core.retailer_buyer_simulator import RetailerBuyerSimulator


# Perfiles relacionales corporativos por Retailer / Cuenta B2B
ACCOUNT_RELATIONAL_PROFILES: Dict[str, Dict[str, Any]] = {
    "WALMART": {
        "retailer_name": "Walmart de México y Centroamérica",
        "account_tier": "TIER_1_STRATEGIC",
        "ltv_annual_usd": Decimal("18500000.00"),
        "ltv_pts": 28.5,             # Sobre 30
        "share_of_wallet_pct": 34.0, # 34% de la facturación anual del proveedor
        "wallet_pts": 23.5,          # Sobre 25
        "gross_margin_pct": 29.5,    # 29.5% margen bruto
        "margin_pts": 21.0,          # Sobre 25
        "reciprocity_pts": 15.0,     # Sobre 20 -> Total RHI = 88.0 (DIPLOMATIC_PRESERVATION)
    },
    "AMAZON": {
        "retailer_name": "Amazon Retail LLC (Vendor Central)",
        "account_tier": "TIER_1_STRATEGIC",
        "ltv_annual_usd": Decimal("14200000.00"),
        "ltv_pts": 27.0,
        "share_of_wallet_pct": 28.5,
        "wallet_pts": 21.5,
        "gross_margin_pct": 31.0,
        "margin_pts": 22.0,
        "reciprocity_pts": 14.0,     # Total RHI = 84.5 (DIPLOMATIC_PRESERVATION)
    },
    "CISCO": {
        "retailer_name": "Cisco Systems Enterprise Procurement",
        "account_tier": "TIER_1_STRATEGIC",
        "ltv_annual_usd": Decimal("11800000.00"),
        "ltv_pts": 26.0,
        "share_of_wallet_pct": 22.0,
        "wallet_pts": 20.0,
        "gross_margin_pct": 38.0,
        "margin_pts": 24.0,
        "reciprocity_pts": 16.5,     # Total RHI = 86.5 (DIPLOMATIC_PRESERVATION)
    },
    "HOME_DEPOT": {
        "retailer_name": "The Home Depot México",
        "account_tier": "TIER_2_REGULAR",
        "ltv_annual_usd": Decimal("6400000.00"),
        "ltv_pts": 19.5,
        "share_of_wallet_pct": 14.0,
        "wallet_pts": 15.5,
        "gross_margin_pct": 26.0,
        "margin_pts": 18.0,
        "reciprocity_pts": 13.0,     # Total RHI = 66.0 (FIRM_COMMERCIAL)
    },
    "SORIANA": {
        "retailer_name": "Organización Soriana S.A.B. de C.V.",
        "account_tier": "TIER_2_REGULAR",
        "ltv_annual_usd": Decimal("5100000.00"),
        "ltv_pts": 17.5,
        "share_of_wallet_pct": 11.5,
        "wallet_pts": 14.0,
        "gross_margin_pct": 24.0,
        "margin_pts": 16.5,
        "reciprocity_pts": 11.5,     # Total RHI = 59.5 (FIRM_COMMERCIAL)
    },
    "LOW_MARGIN_DISTRIBUTOR": {
        "retailer_name": "Distribuidora Mayorista Regional S.A.",
        "account_tier": "TIER_3_HIGH_RISK",
        "ltv_annual_usd": Decimal("920000.00"),
        "ltv_pts": 9.0,
        "share_of_wallet_pct": 2.4,
        "wallet_pts": 6.0,
        "gross_margin_pct": 12.5,
        "margin_pts": 8.5,
        "reciprocity_pts": 7.0,      # Total RHI = 30.5 (ASSERTIVE_LITIGIOUS)
    },
}


class RelationalHealthEngine:
    """
    Motor de cálculo del Índice de Salud Relacional (RHI 0-100) y modulador
    dinámico de agresividad para el careo bilateral multi-agente.
    """

    @classmethod
    def _select_profile(cls, case_id: str) -> Dict[str, Any]:
        cid = case_id.lower()
        if "walmart" in cid or "case_006" in cid:
            return ACCOUNT_RELATIONAL_PROFILES["WALMART"]
        if "amazon" in cid or "case_005" in cid:
            return ACCOUNT_RELATIONAL_PROFILES["AMAZON"]
        if "cisco" in cid or "case_007" in cid:
            return ACCOUNT_RELATIONAL_PROFILES["CISCO"]
        if "homedepot" in cid or "case_008" in cid:
            return ACCOUNT_RELATIONAL_PROFILES["HOME_DEPOT"]
        if "soriana" in cid or "mega" in cid or "case_009" in cid:
            return ACCOUNT_RELATIONAL_PROFILES["SORIANA"]
        if "case_004" in cid or "case_002" in cid:
            return ACCOUNT_RELATIONAL_PROFILES["LOW_MARGIN_DISTRIBUTOR"]
        if "case_003" in cid:
            return ACCOUNT_RELATIONAL_PROFILES["HOME_DEPOT"]
        if "case_001" in cid:
            return ACCOUNT_RELATIONAL_PROFILES["WALMART"]

        # Distribución determinística para casos sintéticos de benchmark
        h = int(hashlib.md5(case_id.encode("utf-8")).hexdigest()[:4], 16) % 3
        if h == 0:
            return ACCOUNT_RELATIONAL_PROFILES["WALMART"]
        if h == 1:
            return ACCOUNT_RELATIONAL_PROFILES["SORIANA"]
        return ACCOUNT_RELATIONAL_PROFILES["LOW_MARGIN_DISTRIBUTOR"]

    @classmethod
    def resolve_modulation_mode(cls, rhi_score: float) -> Dict[str, Any]:
        """
        US-706: Determina el modo de modulación táctica según el puntaje RHI:
        - DIPLOMATIC_PRESERVATION (RHI > 80 pts)
        - FIRM_COMMERCIAL (RHI 50 - 80 pts)
        - ASSERTIVE_LITIGIOUS (RHI < 50 pts)
        """
        if rhi_score > 80.0:
            return {
                "modulation_mode": "DIPLOMATIC_PRESERVATION",
                "churn_risk_level": "LOW_STRATEGIC",
                "recommended_max_concession_pct": 35.0,
                "concession_multiplier": Decimal("1.00"),
                "tone_directive": (
                    "Tono colaborativo, institucional y estratégico. Priorizar la preservación de la cuenta "
                    "Tier-1 condicionando cualquier concesión comercial al compromiso recíproco de volumen en "
                    "futuras órdenes de compra (POs) y ajuste de ventana EDI."
                ),
                "commercial_tradeoff_proposal": (
                    "Bonificación escalonada vía Nota de Crédito CFDI 4.0 a cambio de incremento del +12% en "
                    "asignación de órdenes de compra del próximo trimestre y exención en Scorecard OTIF."
                ),
            }
        if rhi_score >= 50.0:
            return {
                "modulation_mode": "FIRM_COMMERCIAL",
                "churn_risk_level": "MODERATE_MANAGED",
                "recommended_max_concession_pct": 20.0,
                "concession_multiplier": Decimal("0.65"),
                "tone_directive": (
                    "Tono ejecutivo firme y balanceado 50/50. Sustentar cada postura en precedentes de muelle "
                    "(POD sellado y telemetría ASN 856), otorgando concesiones moderadas únicamente ante pago "
                    "inmediato en 5 días hábiles."
                ),
                "commercial_tradeoff_proposal": (
                    "Conciliación bipartita respaldada por evidencia física de andén y liberación de pago SPEI "
                    "en 5 días hábiles sin penalización comercial."
                ),
            }
        return {
            "modulation_mode": "ASSERTIVE_LITIGIOUS",
            "churn_risk_level": "HIGH_EXPENDABLE",
            "recommended_max_concession_pct": 0.0,
            "concession_multiplier": Decimal("0.00"),
            "tone_directive": (
                "Tono pericial estricto, asertivo y pre-litigioso. Cero concesiones sobre faltantes o "
                "retenciones injustificadas; exigir restitución íntegra del 100% reclamable con apercibimiento "
                "de arbitraje CANACO / ICC, causación de intereses moratorios (Art. 362 CCom) y suspensión de línea de crédito."
            ),
            "commercial_tradeoff_proposal": (
                "Cero concesiones sobre deducciones improcedentes. Liquidación íntegra exigible en 72 horas "
                "para evitar bloqueo de suministro y demanda arbitral."
            ),
        }

    @classmethod
    def evaluate_relational_health(
        cls,
        case_id: str,
        override_rhi_score: Optional[float] = None
    ) -> RelationalHealthIndexReport:
        """
        US-705: Calcula el Relationship Health Index (RHI) de 0 a 100 puntos ponderando:
        1. Customer Lifetime Value (LTV) [0-30 pts]
        2. Share of Wallet (% Concentración) [0-25 pts]
        3. Margen Bruto Comercial [0-25 pts]
        4. Historial de Reciprocidad [0-20 pts]
        """
        prof = cls._select_profile(case_id)
        archetype = RetailerBuyerSimulator.resolve_archetype(case_id)
        retailer_name = archetype.retailer_name or prof["retailer_name"]

        ltv_pts = float(prof["ltv_pts"])
        wallet_pts = float(prof["wallet_pts"])
        margin_pts = float(prof["margin_pts"])
        reciprocity_pts = float(prof["reciprocity_pts"])

        computed_rhi = round(min(100.0, max(0.0, ltv_pts + wallet_pts + margin_pts + reciprocity_pts)), 1)
        if override_rhi_score is not None:
            computed_rhi = round(min(100.0, max(0.0, float(override_rhi_score))), 1)

        mod = cls.resolve_modulation_mode(computed_rhi)

        rationale = (
            f"RHI {computed_rhi}/100 calculado para {retailer_name} ({prof['account_tier']}): "
            f"LTV Anual ${prof['ltv_annual_usd']:,.0f} USD ({ltv_pts} pts), "
            f"Share of Wallet {prof['share_of_wallet_pct']}% ({wallet_pts} pts), "
            f"Margen Bruto {prof['gross_margin_pct']}% ({margin_pts} pts), "
            f"Reciprocidad ({reciprocity_pts} pts) -> Modo activo: {mod['modulation_mode']}."
        )

        return RelationalHealthIndexReport(
            case_id=case_id,
            retailer_name=retailer_name,
            account_tier=prof["account_tier"],
            rhi_score=computed_rhi,
            ltv_annual_usd=prof["ltv_annual_usd"],
            ltv_score_component=ltv_pts,
            share_of_wallet_pct=float(prof["share_of_wallet_pct"]),
            wallet_score_component=wallet_pts,
            gross_margin_pct=float(prof["gross_margin_pct"]),
            margin_score_component=margin_pts,
            reciprocity_score_component=reciprocity_pts,
            churn_risk_level=mod["churn_risk_level"],
            modulation_mode=mod["modulation_mode"],
            recommended_max_concession_pct=mod["recommended_max_concession_pct"],
            tone_directive=mod["tone_directive"],
            commercial_tradeoff_proposal=mod["commercial_tradeoff_proposal"],
            rationale=rationale,
        )

    @classmethod
    def evaluate_case_relationship(
        cls,
        case_id: str,
        override_rhi_score: Optional[float] = None
    ) -> RelationalHealthIndexReport:
        """Alias para interoperabilidad con el copiloto omnisciente del chat."""
        return cls.evaluate_relational_health(case_id, override_rhi_score)

