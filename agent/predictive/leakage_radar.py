"""
agent/predictive/leakage_radar.py
Radar Preventivo Pre-Despacho y Machine Learning de Vulnerabilidad de Deducciones (DVI).
Frontera 4 de Superinteligencia (Sprint 5.4).

Evalúa Órdenes de Compra (PO / EDI 850) antes de que la mercancía salga de almacén,
calculando el Índice de Vulnerabilidad de Deducción (Deduction Vulnerability Index - DVI)
y prescribiendo salvaguardas operativas blindadas (fotos 4 ángulos, precinto C-TPAT,
notificación anticipada EDI 856) para prevenir deducciones ilícitas en muelle.
"""

from decimal import Decimal
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


# ==============================================================================
# Modelos de Datos del Radar Preventivo
# ==============================================================================

class DviRiskFactor(BaseModel):
    """Factor de riesgo individual detectado en la orden de compra o ruta logística."""
    factor_id: str
    category: str  # LOGISTICS_WINDOW, DESTINATION_MERMA_HISTORY, PRICE_MISMATCH, UNILATERAL_PENALTY, EDI_TIMING
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    score_impact: float
    description: str
    mandatory_safeguard: str


class DviPredictionResult(BaseModel):
    """Resultado del Índice de Vulnerabilidad de Deducción (DVI)."""
    po_reference: str
    retailer_id: str
    destination_dc: str
    total_po_amount: Decimal
    dvi_score: float = Field(..., ge=0.0, le=100.0)
    risk_level: str  # CRITICAL (>=75), HIGH (>=50), MODERATE (>=25), LOW (<25)
    predicted_leakage_amount: Decimal
    estimated_leakage_pct: float
    risk_factors: List[DviRiskFactor] = Field(default_factory=list)
    pre_dispatch_safeguards: List[str] = Field(default_factory=list)
    binding_executive_directive: str


# ==============================================================================
# Catálogo Topológico de Centros de Distribución de Alto Riesgo
# ==============================================================================

HIGH_RISK_DC_PROFILES = {
    "WALMART_DC_6014": {
        "retailer": "Walmart México",
        "location": "San Martín Obispo / Cuautitlán",
        "risk_rating": "CRITICAL",
        "historical_merma_rate": 0.048,
        "otif_penalty_strictness": 0.95,
        "primary_deduction_types": ["OTIF_LATE_DELIVERY", "ASN_EXTEMPORANEO", "FALTANTE_TARIMA"],
        "min_lead_hours_asn": 4.0,
        "notes": "Ventana de muelle estricta de 2 horas. Si el transportista llega 15 minutos tarde, cancelan cita y aplican multa del 3%."
    },
    "AMAZON_FC_DFW": {
        "retailer": "Amazon Fulfillment Services",
        "location": "Dallas-Fort Worth FC (DFW)",
        "risk_rating": "HIGH",
        "historical_merma_rate": 0.038,
        "otif_penalty_strictness": 0.90,
        "primary_deduction_types": ["RECEIVING_SHORTAGE", "BARCODE_UNREADABLE", "CARTON_OVERSIZED"],
        "min_lead_hours_asn": 6.0,
        "notes": "Escaneo automatizado por bandas transportadoras. Alta tasa de falsos faltantes en tarimas multi-SKU."
    },
    "SORIANA_DC_TULTITLAN": {
        "retailer": "Tiendas Soriana",
        "location": "Tultitlán, Edo. Mex.",
        "risk_rating": "HIGH",
        "historical_merma_rate": 0.042,
        "otif_penalty_strictness": 0.85,
        "primary_deduction_types": ["REBATE_UNILATERAL", "MERMA_OPERATIVA_NO_PACTADA", "PALLET_DEFECTUOSO"],
        "min_lead_hours_asn": 4.0,
        "notes": "Rechazo de tarimas por astillamiento leve o falta de precinto térmico."
    },
    "LIVERPOOL_CUAUTITLAN": {
        "retailer": "El Puerto de Liverpool",
        "location": "Cuautitlán Izcalli",
        "risk_rating": "MODERATE",
        "historical_merma_rate": 0.025,
        "otif_penalty_strictness": 0.80,
        "primary_deduction_types": ["ETIQUETA_COLGADO_ERRONEA", "DESCUENTO_FINANCIERO_ABUSIVO"],
        "min_lead_hours_asn": 3.0,
        "notes": "Penalización por código de barras GS1 no centrado o fuera de altura reglamentaria."
    }
}


# ==============================================================================
# Motor Radar Preventivo Pre-Despacho (DVI Engine)
# ==============================================================================

class PreDispatchLeakageRadar:
    """
    Radar predictivo para blindar la carga antes de la expedición y despacho.
    """

    @classmethod
    def evaluate_purchase_order(
        cls,
        po_reference: str,
        retailer_id: str,
        destination_dc: str,
        total_amount: Decimal,
        estimated_transit_hours: float = 3.0,
        appointment_window_hours: float = 2.0,
        sku_list: Optional[List[str]] = None,
        agreed_catalog_price_match: bool = True,
        contract_has_unilateral_penalty: bool = False
    ) -> DviPredictionResult:
        """
        Calcula el Deduction Vulnerability Index (DVI) e identifica salvaguardas obligatorias.
        """
        sku_list = sku_list or []
        retailer_clean = retailer_id.strip().upper()
        dc_clean = destination_dc.strip().upper().replace(" ", "_")

        risk_factors: List[DviRiskFactor] = []
        safeguards: List[str] = []
        raw_dvi = 10.0  # Riesgo base residual de la cadena de suministro

        # 1. EVALUACIÓN DE VENTANA LOGÍSTICA (OTIF / Ventana de Cita)
        # Si el tiempo de tránsito estimado excede o consume >80% de la holgura previa a la cita
        safety_margin = appointment_window_hours - (estimated_transit_hours * 0.4)
        if safety_margin < 1.0 or estimated_transit_hours > appointment_window_hours:
            impact = 35.0
            raw_dvi += impact
            rf = DviRiskFactor(
                factor_id="RF-LOG-01",
                category="LOGISTICS_WINDOW",
                severity="CRITICAL",
                score_impact=impact,
                description=(
                    f"Tiempo de tránsito estimado ({estimated_transit_hours:.1f}h) excede el margen seguro "
                    f"respecto a la ventana de cita de descarga ({appointment_window_hours:.1f}h en {destination_dc})."
                ),
                mandatory_safeguard=(
                    "Reprogramar cita de muelle a una ventana posterior o despachar la unidad con 4 horas de "
                    "anticipación adicional; monitoreo GPS activo en caseta."
                )
            )
            risk_factors.append(rf)
            safeguards.append(rf.mandatory_safeguard)

        # 2. HISTORIAL DE MERMAS DEL CENTRO DE DISTRIBUCIÓN
        dc_profile = None
        for key, prof in HIGH_RISK_DC_PROFILES.items():
            if key in dc_clean or prof["retailer"].upper() in retailer_clean:
                dc_profile = prof
                break

        if dc_profile:
            impact = 25.0
            raw_dvi += impact
            rf = DviRiskFactor(
                factor_id="RF-DC-HIST",
                category="DESTINATION_MERMA_HISTORY",
                severity=dc_profile["risk_rating"],
                score_impact=impact,
                description=(
                    f"El destino '{destination_dc}' presenta tasa histórica de deducciones del "
                    f"{dc_profile['historical_merma_rate']*100:.1f}%. Tipologías frecuentes: "
                    f"{', '.join(dc_profile['primary_deduction_types'])}."
                ),
                mandatory_safeguard=(
                    "Registro fotográfico obligatorio de 4 ángulos de las tarimas antes del flejado, "
                    "incluyendo código de precinto de seguridad C-TPAT y estiba certificada."
                )
            )
            risk_factors.append(rf)
            safeguards.append(rf.mandatory_safeguard)

        # 3. DISCREPANCIA DE PRECIOS EN LA ORDEN DE COMPRA
        if not agreed_catalog_price_match:
            impact = 20.0
            raw_dvi += impact
            rf = DviRiskFactor(
                factor_id="RF-PRICING-01",
                category="PRICE_MISMATCH",
                severity="HIGH",
                score_impact=impact,
                description="Los precios unitarios de la PO no coinciden con la lista de precios oficial pactada.",
                mandatory_safeguard=(
                    "Suspender facturación automática; enviar EDI 855 (PO Acknowledgment) con código de rechazo "
                    "de precio o confirmar addendum de precios antes del embarque."
                )
            )
            risk_factors.append(rf)
            safeguards.append(rf.mandatory_safeguard)

        # 4. CONDICIONES CONTRACTUALES ASIMÉTRICAS
        if contract_has_unilateral_penalty:
            impact = 15.0
            raw_dvi += impact
            rf = DviRiskFactor(
                factor_id="RF-CTR-PENALTY",
                category="UNILATERAL_PENALTY",
                severity="MEDIUM",
                score_impact=impact,
                description="El acuerdo comercial prevé deducción automática sin derecho a conciliación previa.",
                mandatory_safeguard=(
                    "Exigir que la remisión incluya leyenda de 'Recepción sujeta a conteo ciego conjunto' "
                    "conforme al Art. 88 del Código de Comercio."
                )
            )
            risk_factors.append(rf)
            safeguards.append(rf.mandatory_safeguard)

        # 5. SALVAGUARDA ELECTRÓNICA EDI 856
        safeguards.append(
            "Transmitir el Advance Ship Notice (EDI 856) con al menos 6 horas de antelación y resguardar "
            "el acuse técnico Functional Acknowledgment (EDI 997) con marca UTC como prueba pericial."
        )

        # Normalización del DVI
        dvi_score = max(0.0, min(100.0, round(raw_dvi, 1)))

        if dvi_score >= 75.0:
            risk_level = "CRITICAL"
            leakage_rate = 0.08  # ~8% del valor de la orden en riesgo
            directive = (
                f"🚨 ALERTA CRÍTICA PRE-DESPACHO (DVI: {dvi_score:.1f}%): "
                f"La orden {po_reference} con destino a {destination_dc} presenta riesgo severo de deducción. "
                f"Se prohíbe la salida del transporte hasta ejecutar el protocolo de precinto C-TPAT y acuse EDI 997."
            )
        elif dvi_score >= 50.0:
            risk_level = "HIGH"
            leakage_rate = 0.05
            directive = (
                f"⚠️ RIESGO ALTO DETECTADO (DVI: {dvi_score:.1f}%): "
                f"Activar protocolo de fotos de estiba y verificación de precios en orden {po_reference}."
            )
        elif dvi_score >= 25.0:
            risk_level = "MODERATE"
            leakage_rate = 0.02
            directive = f"ℹ️ RIESGO MODERADO (DVI: {dvi_score:.1f}%): Despacho autorizado bajo salvaguardas estándar."
        else:
            risk_level = "LOW"
            leakage_rate = 0.005
            directive = f"✅ RIESGO BAJO (DVI: {dvi_score:.1f}%): Embarque rutinario sin anomalías detectadas."

        predicted_leakage = (total_amount * Decimal(str(leakage_rate))).quantize(Decimal("0.01"))

        return DviPredictionResult(
            po_reference=po_reference,
            retailer_id=retailer_id,
            destination_dc=destination_dc,
            total_po_amount=total_amount,
            dvi_score=dvi_score,
            risk_level=risk_level,
            predicted_leakage_amount=predicted_leakage,
            estimated_leakage_pct=round(leakage_rate * 100.0, 2),
            risk_factors=risk_factors,
            pre_dispatch_safeguards=safeguards,
            binding_executive_directive=directive
        )

    @classmethod
    def get_high_risk_destinations_catalog(cls) -> Dict[str, Any]:
        """Retorna el catálogo de centros de distribución de alto riesgo."""
        return HIGH_RISK_DC_PROFILES
