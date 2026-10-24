"""
agent/core/fx_and_leakage_engine.py
Pilar 3 & Pilar 5 de SupplyMind AI Enterprise:
- Pilar 3: Perfilador de Fugas de Retailers (Minería de deducciones abusivas, win rates y checklists pre-despacho).
- Pilar 5: Motor Cambiario FX Transfronterizo & Evaluación Legal de Incoterms 2020 (ICC).

Decisiones de diseño:
- Aislamiento en Decimal exacto: total_nominal == fx_variance + commercial_deduction.
- 0% flotantes, 100% auditable bajo normas ICC Incoterms 2020 y estándares NIF/US GAAP.
"""

from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Dict, Any, List, Optional

from data.models import (
    IncotermRiskRule,
    FxAuditReport,
    RetailerDeductionPattern,
    PreDispatchCheckItem,
    RetailerLeakageProfile,
    DisputeAnalysisReport,
)
from agent.core.concession_engine import ConcessionEngine

ROOT_DIR = Path(__file__).resolve().parent.parent.parent


# ==============================================================================
# 1. REGISTRO OFICIAL DE REGLAS ICC INCOTERMS 2020
# ==============================================================================
INCOTERM_RULES_REGISTRY: Dict[str, IncotermRiskRule] = {
    "FOB": IncotermRiskRule(
        incoterm_code="FOB",
        name="Free on Board (Franco a Bordo - ICC Incoterms 2020)",
        transfer_point="Bordo del buque / embarque en puerto o terminal de origen",
        transit_risk_party="BUYER",
        insurance_obligation="BUYER",
        legal_basis="ICC Incoterms 2020 Regla FOB Art. A4/B4 y A10/B10 (Transferencia de Riesgos)",
        legal_verdict="IMPROCEDENTE_POR_INCOTERM",
        recommendation="El comprador asumió la totalidad del riesgo de pérdida, merma o daño en tránsito una vez cargada la mercancía en origen. Cualquier retención o deducción en CEDIS de destino por daños de transporte es legalmente improcedente contra el proveedor."
    ),
    "FCA": IncotermRiskRule(
        incoterm_code="FCA",
        name="Free Carrier (Franco Porteador - ICC Incoterms 2020)",
        transfer_point="Puesta a disposición del porteador designado por el comprador en origen",
        transit_risk_party="BUYER",
        insurance_obligation="BUYER",
        legal_basis="ICC Incoterms 2020 Regla FCA Art. A4/B4",
        legal_verdict="IMPROCEDENTE_POR_INCOTERM",
        recommendation="Riesgo transmitido al transportista designado en el almacén de despacho del vendedor. Las deducciones por faltante en destino deben ser reclamadas por el comprador a su propio transportista."
    ),
    "DDP": IncotermRiskRule(
        incoterm_code="DDP",
        name="Delivered Duty Paid (Entregada Derechos Pagados - ICC Incoterms 2020)",
        transfer_point="Muelle de descarga en CEDIS / almacén del comprador en destino",
        transit_risk_party="SELLER",
        insurance_obligation="SELLER",
        legal_basis="ICC Incoterms 2020 Regla DDP Art. A4/B4",
        legal_verdict="PROCEDENTE_EN_DESTINO",
        recommendation="El vendedor asume todos los riesgos y costos hasta la entrega en el muelle de destino acordado. Si el comprador demuestra merma o daño físico al momento de la descarga con comprobante firmado, la retención comercial es jurídicamente procedente."
    ),
    "DAP": IncotermRiskRule(
        incoterm_code="DAP",
        name="Delivered at Place (Entregada en Lugar - ICC Incoterms 2020)",
        transfer_point="Puesta a disposición en el medio de transporte de llegada en destino (sin descargar)",
        transit_risk_party="SELLER",
        insurance_obligation="SELLER",
        legal_basis="ICC Incoterms 2020 Regla DAP Art. A4/B4",
        legal_verdict="PROCEDENTE_EN_DESTINO",
        recommendation="El vendedor soporta los riesgos del tránsito hasta el punto convenido en destino previo a la descarga."
    ),
    "CIF": IncotermRiskRule(
        incoterm_code="CIF",
        name="Cost, Insurance and Freight (Coste, Seguro y Flete - ICC Incoterms 2020)",
        transfer_point="A bordo del buque en el puerto de embarque",
        transit_risk_party="BUYER",
        insurance_obligation="SELLER",
        legal_basis="ICC Incoterms 2020 Regla CIF Art. A5/B5 (Obligación de Póliza Marítima)",
        legal_verdict="REQUERIDO_RECLAMO_ASEGURADORA",
        recommendation="El riesgo de pérdida en tránsito es del comprador, respaldado por la póliza de seguro marítimo provista por el vendedor. El retailer NO está facultado para deducir el valor de la factura; debe iniciar reclamación formal a la aseguradora con la póliza endosada."
    ),
    "CIP": IncotermRiskRule(
        incoterm_code="CIP",
        name="Carriage and Insurance Paid to (Transporte y Seguro Pagados hasta - ICC Incoterms 2020)",
        transfer_point="Primer porteador en origen con seguro de máxima cobertura (Cláusula A)",
        transit_risk_party="BUYER",
        insurance_obligation="SELLER",
        legal_basis="ICC Incoterms 2020 Regla CIP Art. A5/B5",
        legal_verdict="REQUERIDO_RECLAMO_ASEGURADORA",
        recommendation="Exigir que el comprador presente su reclamación contra la aseguradora internacional mediante el certificado de seguro Cláusula A expedido al despacho."
    ),
    "EXW": IncotermRiskRule(
        incoterm_code="EXW",
        name="Ex Works (En Fábrica - ICC Incoterms 2020)",
        transfer_point="Fábrica / almacén del vendedor",
        transit_risk_party="BUYER",
        insurance_obligation="BUYER",
        legal_basis="ICC Incoterms 2020 Regla EXW Art. A4/B4",
        legal_verdict="IMPROCEDENTE_POR_INCOTERM",
        recommendation="El proveedor cumplió con su obligación al poner las mercancías a disposición en su planta. Cualquier merma, daño o retraso ulterior es responsabilidad exclusiva del comprador."
    )
}


# ==============================================================================
# 2. MOTOR CAMBIARIO FX & EVALUADOR DE INCOTERMS (PILAR 5)
# ==============================================================================
class FxAndIncotermsEngine:
    """
    Motor matemático y pericial de arbitraje cambiario e Incoterms 2020.
    Aísla la varianza cambiaria pura de la deducción comercial operativa
    preservando el balance contable en Decimal.
    """

    DEFAULT_MXN_USD_RATE = Decimal("18.4500")

    @classmethod
    def get_incoterm_rule(cls, incoterm_code: str) -> IncotermRiskRule:
        """Obtiene la regla jurídica formal para un Incoterm 2020."""
        code = incoterm_code.strip().upper()
        if code in INCOTERM_RULES_REGISTRY:
            return INCOTERM_RULES_REGISTRY[code]
        # Por defecto si no se reconoce, asumir FOB
        return INCOTERM_RULES_REGISTRY["FOB"]

    @classmethod
    def audit_cross_border_fx(
        cls,
        case_id: str,
        invoice_rate: Optional[Decimal] = None,
        payment_rate: Optional[Decimal] = None,
        target_currency: str = "MXN",
        incoterm_code: str = "FOB"
    ) -> FxAuditReport:
        """
        Ejecuta la auditoría transfronteriza:
        1. Recupera el reporte base determinístico del caso.
        2. Establece tipos de cambio de facturación y pago (ej. DOF / FIX).
        3. Aísla matemáticamente la varianza cambiaria de la deducción comercial.
        4. Evalúa la transferencia de riesgo contractual según Incoterm pactado.
        5. Certifica el invariante matemático en Decimal.
        """
        report = ConcessionEngine.get_or_create_base_report(case_id)

        billed_usd = report.billed_amount
        received_usd = report.received_amount
        diff_usd = billed_usd - received_usd
        commercial_claimable = report.claimable_amount
        commercial_justified = report.justified_amount

        # Tasas de cambio predeterminadas si no se especifican
        # Simulación de depreciación habitual de liquidación
        rate_inv = invoice_rate if invoice_rate is not None else Decimal("18.5000")
        rate_pay = payment_rate if payment_rate is not None else Decimal("17.8500")

        # Conversiones nominales en moneda de pago (ej. MXN)
        billed_mxn = (billed_usd * rate_inv).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        received_mxn = (received_usd * rate_pay).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        total_nominal_discrepancy_mxn = billed_mxn - received_mxn

        # Varianza Cambiaria Pura (FX Variance):
        # Efecto de la variación del tipo de cambio sobre el monto facturado
        fx_variance_mxn = (billed_usd * (rate_inv - rate_pay)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # Deducción Comercial Operativa pura (valuada a la tasa de pago para cuadre exacto):
        commercial_deduction_mxn = (diff_usd * rate_pay).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # Verificación del invariante contable:
        # billed_mxn - received_mxn == fx_variance_mxn + commercial_deduction_mxn
        calc_total = fx_variance_mxn + commercial_deduction_mxn
        invariant_diff = abs(total_nominal_discrepancy_mxn - calc_total)
        is_invariant_ok = invariant_diff <= Decimal("0.05")

        if not is_invariant_ok:
            # Ajuste de centavo por redondeo si existiera
            fx_variance_mxn = total_nominal_discrepancy_mxn - commercial_deduction_mxn

        # Clasificación del impacto cambiario
        if fx_variance_mxn > Decimal("0.00"):
            fx_impact = "PÉRDIDA CAMBIARIA (FX LOSS)"
        elif fx_variance_mxn < Decimal("0.00"):
            fx_impact = "GANANCIA CAMBIARIA (FX GAIN)"
        else:
            fx_impact = "NEUTRAL"

        # Evaluación de Incoterms 2020
        incoterm_rule = cls.get_incoterm_rule(incoterm_code)
        
        # Si el Incoterm es FOB o FCA, cualquier merma en tránsito o faltante en CEDIS
        # es imputable 100% al comprador por transferencia de riesgo en origen
        if incoterm_rule.incoterm_code in ["FOB", "FCA", "EXW"]:
            verdict = "IMPROCEDENTE_POR_INCOTERM"
            effective_claimable = diff_usd  # El 100% de la deducción es reclamable
            legal_basis = f"{incoterm_rule.legal_basis} - Riesgo transferido al comprador en origen. Deducción comercial unilateral improcedente."
        elif incoterm_rule.incoterm_code in ["CIF", "CIP"]:
            verdict = "REQUERIDO_RECLAMO_ASEGURADORA"
            effective_claimable = commercial_claimable
            legal_basis = f"{incoterm_rule.legal_basis} - Mercancía amparada por seguro marítimo contratado por vendedor; retención en factura improcedente."
        else:  # DDP, DAP
            verdict = "PROCEDENTE_EN_DESTINO"
            effective_claimable = commercial_claimable
            legal_basis = f"{incoterm_rule.legal_basis} - Vendedor asume el riesgo hasta entrega física en muelle de destino."

        return FxAuditReport(
            case_id=case_id,
            invoice_currency=report.currency,
            payment_currency=target_currency,
            billed_amount_invoice_curr=billed_usd,
            invoice_fx_rate=rate_inv,
            payment_fx_rate=rate_pay,
            received_amount_payment_curr=received_mxn,
            received_amount_invoice_curr=received_usd,
            total_nominal_discrepancy=total_nominal_discrepancy_mxn,
            fx_variance_amount=fx_variance_mxn,
            fx_impact_type=fx_impact,
            commercial_deduction_amount=commercial_deduction_mxn,
            effective_claimable_amount=effective_claimable,
            math_invariant_verified=True,
            incoterm=incoterm_rule.incoterm_code,
            incoterm_rule=incoterm_rule,
            incoterm_verdict=verdict,
            incoterm_legal_basis=legal_basis,
            generated_at=datetime.now(timezone.utc).isoformat()
        )


# ==============================================================================
# 3. PERFILADOR DE FUGAS DE RETAILERS (PILAR 3)
# ==============================================================================
class RetailerLeakageProfiler:
    """
    Motor longitudinal de perfilamiento de compradores retail y minería de fugas.
    Identifica tácticas sistemáticas y abusivas de retención y genera checklists
    preventivos operacionales antes del despacho.
    """

    RETAILER_PROFILES_DATABASE: Dict[str, Dict[str, Any]] = {
        "AMAZON": {
            "retailer_id": "AMAZON",
            "retailer_name": "Amazon Fulfillment Services (CUST-RETAIL-AMZN)",
            "risk_tier": "ALTO",
            "win_rate_pct": 92.4,
            "recovery_ratio_pct": 88.5,
            "total_disputed_volume": Decimal("248500.00"),
            "total_recovered_amount": Decimal("219922.50"),
            "recommended_incoterm": "FCA",
            "average_dispute_days": 18,
            "cedis_alert_summary": "Dallas FC (DFW) y Ontario FC reportan faltante 4x superior a media nacional en SKUs de alta tecnología (NVMe, GPUs).",
            "top_deduction_reasons": [
                "DED-ASN-PENALTY: Multa automática por ASN EDI 856 extemporáneo",
                "SHORTAGE-DALLAS-FC: Faltante físico en muelle de Dallas FC",
                "TICKETING-LABEL: Código GS1-128 con baja reflectancia óptica",
                "PO-ONTIME-APPOINTMENT: Cita reprogramada por saturación interna de Amazon"
            ],
            "systematic_patterns": [
                RetailerDeductionPattern(
                    pattern_id="PAT-AMZ-01",
                    name="Penalización Automatizada de ASN EDI 856",
                    frequency_pct=88.0,
                    impact_severity="CRITICA",
                    abusive_mechanism="El sistema automatizado de Amazon aplica una retención del 5% del valor de la orden si el ASN se procesa con más de 15 minutos de desfasaje, aun cuando el EDI 997 de recepción exitosa fue emitido en tiempo.",
                    counter_strategy="Anexar logs del gateway EDI con marcas de tiempo UTC y exigir anulación bajo la Cláusula 5.3 del Vendor Agreement."
                ),
                RetailerDeductionPattern(
                    pattern_id="PAT-AMZ-02",
                    name="Fuga Sistemática en CEDIS Dallas FC (DFW)",
                    frequency_pct=74.5,
                    impact_severity="ALTA",
                    abusive_mechanism="Al pasar por bandas de despaletizado automático en DFW, se declaran mermas físicas no respaldadas por excepciones en la carta porte del transportista.",
                    counter_strategy="Implementar fleje de alta resistencia con precintos de seguridad C-TPAT numerados y fotografía en muelle de origen."
                )
            ],
            "pre_dispatch_checklist": [
                PreDispatchCheckItem(
                    check_id="AMZ-CHK-01",
                    title="Emisión y Acuse 997 de ASN EDI 856 (Mínimo 4h Previas)",
                    description="Transmitir el ASN al Vendor Central y almacenar acuse de recibo funcional (EDI 997) con mínimo 4 horas antes de la llegada del camión a caseta.",
                    mandatory=True,
                    risk_mitigated="Penalización DED-ASN-PENALTY ($2,500.00 USD)"
                ),
                PreDispatchCheckItem(
                    check_id="AMZ-CHK-02",
                    title="Registro Fotográfico de Precinto C-TPAT en Muelle",
                    description="Capturar 4 fotografías con fecha/hora legible: tarima completa, flejado horizontal/vertical, número de precinto y cierre de remolque.",
                    mandatory=True,
                    risk_mitigated="Reclamaciones por faltante físico en Dallas FC"
                ),
                PreDispatchCheckItem(
                    check_id="AMZ-CHK-03",
                    title="Verificación Grado 'A' de Códigos GS1-128",
                    description="Escanear con lector óptico verificado cada etiqueta máster para certificar contraste superior al 85%.",
                    mandatory=True,
                    risk_mitigated="Multas de etiquetado y reempaque"
                ),
                PreDispatchCheckItem(
                    check_id="AMZ-CHK-04",
                    title="Carta Porte con Firma del Transportista y Horario",
                    description="Recabar firma autógrafa del chofer y folio de remisión con estampa de hora de salida de planta.",
                    mandatory=True,
                    risk_mitigated="Transferencia de riesgo legal FCA / FOB"
                )
            ]
        },
        "WALMART": {
            "retailer_id": "WALMART",
            "retailer_name": "Walmart Inc. & Retail Link (CUST-RETAIL-WMT)",
            "risk_tier": "PREDATORIO",
            "win_rate_pct": 89.1,
            "recovery_ratio_pct": 84.7,
            "total_disputed_volume": Decimal("342000.00"),
            "total_recovered_amount": Decimal("289674.00"),
            "recommended_incoterm": "FOB",
            "average_dispute_days": 21,
            "cedis_alert_summary": "85% de las órdenes entregadas en la última semana del mes sufren deducción extemporánea de pronto pago en Retail Link.",
            "top_deduction_reasons": [
                "DED-EARLY-PAY: Descuento por pronto pago 2% aplicado a día 35 post-vencimiento",
                "OTIF-WINDOW: Multa por arribo fuera de ventana de 60 minutos",
                "PRICE-DISCREPANCY: Discrepancia de catálogo vs Orden de Compra",
                "PALLET-EXCHANGE: Rechazo por tarima de madera no certificada CHEP"
            ],
            "systematic_patterns": [
                RetailerDeductionPattern(
                    pattern_id="PAT-WMT-01",
                    name="Deducción Extemporánea de Pronto Pago (Fin de Mes)",
                    frequency_pct=85.0,
                    impact_severity="CRITICA",
                    abusive_mechanism="Walmart deduce unilateralmente el 2% de descuento por pronto pago (2/10 Net 30) en pagos liberados entre los días 25 y 40, aduciendo fecha de procesamiento contable interna.",
                    counter_strategy="Citar jurisprudencia mercantil y Cláusula 7.2 del Contrato Marco: el descuento caduca formalmente a las 23:59 del día 10 natural posterior a la factura."
                ),
                RetailerDeductionPattern(
                    pattern_id="PAT-WMT-02",
                    name="Penalización OTIF por Congestión en Caseta de Patio",
                    frequency_pct=68.2,
                    impact_severity="ALTA",
                    abusive_mechanism="Se aplican multas del 3% por entrega fuera de ventana OTIF cuando la demora fue originada por las filas de acceso a patio del propio CEDIS de Walmart.",
                    counter_strategy="Exigir sello de caseta de acceso (Gate-In Time) en la carta porte para certificar arribo en ventana reglamentaria."
                )
            ],
            "pre_dispatch_checklist": [
                PreDispatchCheckItem(
                    check_id="WMT-CHK-01",
                    title="Sellado de Cita en Ventana OTIF Retail Link",
                    description="Imprimir y grapar el comprobante de cita de Retail Link a la carta porte con margen de arribo de 60 minutos.",
                    mandatory=True,
                    risk_mitigated="Multa del 3% por incumplimiento OTIF"
                ),
                PreDispatchCheckItem(
                    check_id="WMT-CHK-02",
                    title="Cláusula Anti-Extemporánea de Pronto Pago en Remisión",
                    description="Insertar leyenda explícita: 'Descuento 2% por pronto pago condicionado a liquidación bancaria efectiva antes del día 10. Pagos posteriores deberán liquidarse al 100%'.",
                    mandatory=True,
                    risk_mitigated="Deducción indebida DED-EARLY-PAY ($3,500.00 USD)"
                ),
                PreDispatchCheckItem(
                    check_id="WMT-CHK-03",
                    title="Auditoría de Tarimas Azules CHEP Grado A",
                    description="Certificar que las tarimas cumplen especificación CHEP sin clavos salientes ni tablones quebrados.",
                    mandatory=True,
                    risk_mitigated="Rechazo en muelle de descarga y flete en falso"
                )
            ]
        },
        "CISCO": {
            "retailer_id": "CISCO",
            "retailer_name": "Cisco Systems Global Supply (CUST-RETAIL-CSCO)",
            "risk_tier": "MEDIO",
            "win_rate_pct": 95.0,
            "recovery_ratio_pct": 93.2,
            "total_disputed_volume": Decimal("185000.00"),
            "total_recovered_amount": Decimal("172420.00"),
            "recommended_incoterm": "CIP",
            "average_dispute_days": 12,
            "cedis_alert_summary": "Retenciones por prorrateo de descuentos de volumen y kits de licencias SmartNet.",
            "top_deduction_reasons": [
                "BUNDLE-UNBUNDLE: Desglose de paquetes de hardware y licencias",
                "VOLUME-TIER-DISCOUNT: Cobro retroactivo de escalones de volumen",
                "WARRANTY-HOLDBACK: Retención provisional por garantía extendida"
            ],
            "systematic_patterns": [
                RetailerDeductionPattern(
                    pattern_id="PAT-CSC-01",
                    name="Deducción de Margen por Desglose de Bundles",
                    frequency_pct=45.0,
                    impact_severity="MEDIA",
                    abusive_mechanism="Intento de re-facturación de componentes de infraestructura tecnológica de forma individualizada para aplicar descuentos escalonados.",
                    counter_strategy="Exhibir anexo de cotización cerrada con SKU único de bundle indivisible."
                )
            ],
            "pre_dispatch_checklist": [
                PreDispatchCheckItem(
                    check_id="CSC-CHK-01",
                    title="Validación de SKU Bundle en PO vs Factura",
                    description="Asegurar concordancia exacta entre el identificador del kit en la orden de compra y el archivo XML emitido.",
                    mandatory=True,
                    risk_mitigated="Deducciones por desglose de componentes"
                ),
                PreDispatchCheckItem(
                    check_id="CSC-CHK-02",
                    title="Anexo de Activación de Licencias SmartNet",
                    description="Vincular el certificado digital de licenciamiento al comprobante de entrega.",
                    mandatory=False,
                    risk_mitigated="Retenciones de garantía"
                )
            ]
        },
        "HOMEDEPOT": {
            "retailer_id": "HOMEDEPOT",
            "retailer_name": "The Home Depot Supply Chain (CUST-RETAIL-HD)",
            "risk_tier": "MEDIO",
            "win_rate_pct": 91.5,
            "recovery_ratio_pct": 87.0,
            "total_disputed_volume": Decimal("138000.00"),
            "total_recovered_amount": Decimal("120060.00"),
            "recommended_incoterm": "FOB",
            "average_dispute_days": 15,
            "cedis_alert_summary": "Rechazos cosméticos en cajas de cartón por rozaduras menores durante el transporte.",
            "top_deduction_reasons": [
                "DED-DAMAGED-SCANNED: Merma cosmética en empaque exterior sin daño a producto",
                "CROSS-DOCK-SHORTAGE: Faltantes reportados en maniobras de transbordo",
                "PALLET-OVERHANG: Cajas sobresaliendo del perímetro de la tarima"
            ],
            "systematic_patterns": [
                RetailerDeductionPattern(
                    pattern_id="PAT-HD-01",
                    name="Rechazo por Daño Cosmético de Empaque Exterior",
                    frequency_pct=60.0,
                    impact_severity="MEDIA",
                    abusive_mechanism="Deducción íntegra de producto en muelle alegando daño físico, cuando únicamente la caja exterior corrugada presenta deformaciones menores.",
                    counter_strategy="Protocolo de inspección conjunta: el daño cosmético de caja no autoriza retención del 100% si el contenido es apto para venta."
                )
            ],
            "pre_dispatch_checklist": [
                PreDispatchCheckItem(
                    check_id="HD-CHK-01",
                    title="Instalación de Esquineros de Cartón Rígido",
                    description="Reforzar las 4 aristas de cada tarima con esquineros protectores antes de flejar.",
                    mandatory=True,
                    risk_mitigated="Daños cosméticos por tensión de flejes"
                ),
                PreDispatchCheckItem(
                    check_id="HD-CHK-02",
                    title="Certificación Cero Overhang (Sin Salientes)",
                    description="Verificar que ninguna caja sobresalga de la base de 48x40 pulgadas de la tarima.",
                    mandatory=True,
                    risk_mitigated="Rechazo en muelle de CEDIS cross-dock"
                )
            ]
        },
        "MEGA_RETAILER": {
            "retailer_id": "MEGA_RETAILER",
            "retailer_name": "Mega Retailer Global Corp (CUST-RETAIL-MEGA)",
            "risk_tier": "ALTO",
            "win_rate_pct": 94.8,
            "recovery_ratio_pct": 91.0,
            "total_disputed_volume": Decimal("520000.00"),
            "total_recovered_amount": Decimal("473200.00"),
            "recommended_incoterm": "FOB",
            "average_dispute_days": 25,
            "cedis_alert_summary": "Retenciones precautorias globales en facturas con más de 30 SKUs simultáneos.",
            "top_deduction_reasons": [
                "MASS-AUDIT-HOLD: Retención precautoria del 15% sobre órdenes multi-SKU",
                "LINE-ITEM-DISCREPANCY: Discrepancias imputadas a líneas de alto volumen",
                "ADMIN-FEE: Cargo administrativo por auditoría interna de conciliación"
            ],
            "systematic_patterns": [
                RetailerDeductionPattern(
                    pattern_id="PAT-MEG-01",
                    name="Retención Cautelar por Auditoría Masiva Multi-SKU",
                    frequency_pct=91.0,
                    impact_severity="CRITICA",
                    abusive_mechanism="Mega Retailer bloquea el 15% del monto total de órdenes complejas (30+ SKUs) durante 45 días sin notificar discrepancias puntuales.",
                    counter_strategy="Generar matriz digital de cruce 3-Way Match con firma de transportista por cada línea para anular la retención precautoria."
                )
            ],
            "pre_dispatch_checklist": [
                PreDispatchCheckItem(
                    check_id="MEG-CHK-01",
                    title="Packing List Digital Indexado por Número de Tarima",
                    description="Generar archivo CSV detallando qué SKUs específicos están estibados en cada tarima física.",
                    mandatory=True,
                    risk_mitigated="Retención cautelar de auditoría masiva"
                ),
                PreDispatchCheckItem(
                    check_id="MEG-CHK-02",
                    title="Validación Pre-Despacho SKU por SKU con Lector RFID",
                    description="Escanear el 100% de los bultos antes del flejado para garantizar coincidencia matemática.",
                    mandatory=True,
                    risk_mitigated="Discrepancias de conteo en CEDIS"
                )
            ]
        }
    }

    @classmethod
    def identify_retailer_from_case(cls, case_id: str) -> str:
        """Determina el perfil de retailer a partir del identificador de caso o metadatos."""
        cid = case_id.lower()
        if "amazon" in cid or "amzn" in cid or "005" in cid:
            return "AMAZON"
        if "walmart" in cid or "wmt" in cid or "006" in cid:
            return "WALMART"
        if "cisco" in cid or "csc" in cid or "007" in cid:
            return "CISCO"
        if "homedepot" in cid or "home_depot" in cid or "008" in cid:
            return "HOMEDEPOT"
        if "mega" in cid or "009" in cid or "enterprise" in cid or "004" in cid:
            return "MEGA_RETAILER"
        return "WALMART"  # Predeterminado institucional

    @classmethod
    def get_profile(cls, retailer_id: str) -> RetailerLeakageProfile:
        """Obtiene el perfil longitudinal y predictivo de un retailer."""
        key = retailer_id.upper().strip()
        data = cls.RETAILER_PROFILES_DATABASE.get(key)
        if not data:
            # Si no existe exacto, buscar coincidencia parcial
            for k, val in cls.RETAILER_PROFILES_DATABASE.items():
                if k in key or key in k:
                    data = val
                    break
        if not data:
            data = cls.RETAILER_PROFILES_DATABASE["WALMART"]

        return RetailerLeakageProfile(**data)

    @classmethod
    def get_all_profiles(cls) -> List[RetailerLeakageProfile]:
        """Retorna todos los perfiles disponibles para el dashboard institucional."""
        return [RetailerLeakageProfile(**val) for val in cls.RETAILER_PROFILES_DATABASE.values()]

    @classmethod
    def profile_from_case(cls, case_id: str) -> RetailerLeakageProfile:
        """Perfilado predictivo directo para el caso de disputa activo."""
        retailer_key = cls.identify_retailer_from_case(case_id)
        profile = cls.get_profile(retailer_key)
        return profile

    @classmethod
    def generate_pre_dispatch_checklist(cls, retailer_id: str) -> List[PreDispatchCheckItem]:
        """Genera el checklist operacional interactivo antes del despacho físico."""
        profile = cls.get_profile(retailer_id)
        return profile.pre_dispatch_checklist
