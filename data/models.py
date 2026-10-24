"""
Modelos de datos del expediente de una disputa comercial B2B.

Decisiones de diseño:
- Todos los montos usan Decimal (nunca float) para evitar errores de redondeo financiero.
- Los modelos validan TIPOS y FORMA, pero NO validan que los totales cuadren.
  Una factura con totales inconsistentes es en sí misma una posible causa de
  disputa; detectarlo es trabajo del motor de conciliación (Fase 4), no del parser.
- extra="forbid": un campo desconocido en el JSON es un error inmediato, evitando
  campos espurios o maliciosos.
"""
from decimal import Decimal
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, Field, AliasChoices


class _Base(BaseModel):
    """Clase base con configuración estricta para todos los modelos comerciales."""
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


# ==========================================
# 1. Factura (Invoice) - emitida por el proveedor
# ==========================================
class InvoiceItem(_Base):
    item_id: str
    description: str
    quantity: int = Field(ge=0)
    unit_price: Decimal = Field(ge=0)
    total_price: Decimal = Field(ge=0)


class Invoice(_Base):
    invoice_id: str
    vendor_id: str
    customer_id: str
    po_reference: Optional[str] = None
    issue_date: str
    currency: str = "USD"
    items: List[InvoiceItem] = Field(min_length=1)
    subtotal: Decimal = Field(ge=0)
    tax: Decimal = Field(default=Decimal("0.00"), ge=0)
    total_amount: Decimal = Field(ge=0)


# ==========================================
# 2. Orden de compra (Purchase Order) - emitida por el retailer
# ==========================================
class PurchaseOrderItem(_Base):
    item_id: str
    description: str
    ordered_quantity: int = Field(ge=0)
    agreed_unit_price: Decimal = Field(ge=0)
    total_price: Decimal = Field(ge=0)


class PurchaseOrder(_Base):
    po_id: str
    vendor_id: str
    customer_id: str
    order_date: str
    currency: str = "USD"
    items: List[PurchaseOrderItem] = Field(min_length=1)
    total_amount: Decimal = Field(ge=0)


# ==========================================
# 3. Comprobante de entrega / remisión (Delivery Note)
# ==========================================
class DeliveryItem(_Base):
    item_id: str
    quantity_delivered: int = Field(ge=0)
    quantity_received: int = Field(ge=0)
    missing_quantity: int = Field(default=0, ge=0)
    damaged_quantity: int = Field(default=0, ge=0)
    notes: Optional[str] = None


class DeliveryNote(_Base):
    delivery_id: str
    po_reference: str
    delivery_date: str
    received_by: str
    warehouse_location: str
    signed: bool = True
    discrepancy_reported: bool = False
    items: List[DeliveryItem] = Field(min_length=1)


# ==========================================
# 4. Comprobante de pago (Payment Receipt)
# ==========================================
class PaymentDeduction(_Base):
    code: str
    reason: str
    amount: Decimal = Field(ge=0)
    reference_doc: Optional[str] = None


class PaymentReceipt(_Base):
    payment_id: str
    invoice_reference: str
    payment_date: str
    currency: str = "USD"
    amount_paid: Decimal = Field(ge=0)
    deductions: List[PaymentDeduction] = Field(default_factory=list)


# ==========================================
# 5. Contrato comercial (Contract)
# ==========================================
class ContractClause(_Base):
    clause_id: str
    title: str
    text: str
    # Etiqueta legible por máquina que usará el analizador de contratos (Fase 4).
    policy: str
    tolerance_percentage: Decimal = Field(default=Decimal("0.00"), ge=0)


class CommercialContract(_Base):
    contract_id: str
    vendor_id: str
    customer_id: str
    valid_from: str
    valid_to: str
    clauses: List[ContractClause] = Field(min_length=1)


class CommercialConcession(BaseModel):
    """Registro auditable de una concesión comercial autorizada por Human-in-the-Loop."""
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    concession_id: str
    applied_at: str
    operator: str = "Human-in-the-Loop Operator"
    concession_type: str = "COMMERCIAL_DISCOUNT"  # "PERCENTAGE_PENALTY", "FIXED_AMOUNT", "FULL_WAIVER"
    target: str = "DISPUTED_PENALTY"              # "PENALTY_ASN", "EARLY_PAYMENT", "DAMAGED_GOODS", "GENERAL"
    original_claimable: Decimal = Field(default=Decimal("0.00"), ge=0)
    concession_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    new_claimable: Decimal = Field(default=Decimal("0.00"), ge=0)
    new_justified: Decimal = Field(default=Decimal("0.00"), ge=0)
    reason: str = "Instrucción de operador para salvaguardar la relación comercial"


# ==========================================
# 6. Salida: Dispute Analysis Report
# ==========================================
class DisputeAnalysisReport(_Base):
    case_id: str
    currency: str = "USD"
    billed_amount: Decimal          # Monto facturado
    received_amount: Decimal        # Monto recibido
    difference: Decimal             # Diferencia (facturado - recibido, puede ser negativa)
    root_cause: str                 # Causa encontrada
    evidence: List[str] = Field(validation_alias=AliasChoices("evidence", "evidence_used"))
    justified_amount: Decimal = Field(ge=0)       # Monto justificado
    claimable_amount: Decimal = Field(ge=0)       # Monto reclamable
    confidence: float = Field(ge=0.0, le=1.0, validation_alias=AliasChoices("confidence", "confidence_score"))
    recommended_action: str         # Acción recomendada
    concessions: List[CommercialConcession] = Field(default_factory=list)  # Auditoría Human-in-the-Loop
    active_scenario: Optional[str] = Field(default=None)  # Escenario activo: "AGGRESSIVE", "BALANCED", "CONSERVATIVE"
    health_audit: Optional[Any] = Field(default=None)  # Auditoría de Integridad y Resiliencia Documental (DocumentHealthAudit o dict)

    def formatted_display(self) -> str:
        """Formatea el reporte con la estructura solicitada para el reto."""
        evidence_str = "\n  - " + "\n  - ".join(self.evidence) if self.evidence else " Ninguna"
        return (
            "====================================================\n"
            "              DISPUTE ANALYSIS REPORT               \n"
            "====================================================\n"
            f"Caso analizado:     {self.case_id}\n"
            f"Monto facturado:    ${self.billed_amount:,.2f} {self.currency}\n"
            f"Monto recibido:     ${self.received_amount:,.2f} {self.currency}\n"
            f"Diferencia:         ${self.difference:,.2f} {self.currency}\n"
            f"Causa encontrada:   {self.root_cause}\n"
            f"Evidencia utilizada:{evidence_str}\n"
            f"Monto justificado:  ${self.justified_amount:,.2f} {self.currency}\n"
            f"Monto reclamable:   ${self.claimable_amount:,.2f} {self.currency}\n"
            f"Nivel de confianza: {self.confidence * 100:.1f}%\n"
            f"Acción recomendada: {self.recommended_action}\n"
            "===================================================="
        )


# ==========================================
# 7. Modelos de Negociación B2B Multi-Ruta (Fase 2)
# ==========================================
class NegotiationScenario(BaseModel):
    """Escenario individual de contrapropuesta y negociación comercial."""
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    scenario_id: str                          # "AGGRESSIVE", "BALANCED", "CONSERVATIVE"
    title: str                                # Título descriptivo
    strategy_summary: str                     # Resumen ejecutivo de la táctica
    justified_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    claimable_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    concession_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    recovery_rate_pct: float = Field(default=100.0, ge=0.0, le=100.0)
    friction_risk: str = "MEDIO"              # "ALTO", "MEDIO", "BAJO"
    expected_timeline_days: int = 15          # Plazo proyectado de resolución
    counterparty_concession_requested: str    # Contraprestación comercial exigida al cliente
    tactical_action: str                      # Acción operativa a seguir
    formal_memo: str                          # Minuta/comunicado formal para el cliente


class NegotiationPlan(BaseModel):
    """Plan integral de negociación bilateral con 3 escenarios comparativos."""
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    case_id: str
    account_name: str = "Cliente B2B"
    account_tier: str = "TIER_1_STRATEGIC"    # "TIER_1_STRATEGIC", "TIER_2_REGULAR"
    recommended_scenario: str = "BALANCED"
    total_dispute_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    scenarios: List[NegotiationScenario] = Field(default_factory=list)
    generated_at: str = ""


# ==========================================
# 8. Modelos de Integración ERP y Fiscal CFDI 4.0 (Fase 3)
# ==========================================
class ErpPostingLine(BaseModel):
    """Línea individual de asiento contable de partida doble."""
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    line_number: int
    account_code: str
    account_name: str
    debit: Decimal = Field(default=Decimal("0.00"), ge=0)
    credit: Decimal = Field(default=Decimal("0.00"), ge=0)
    cost_center: Optional[str] = None
    tax_code: Optional[str] = None
    memo: str = ""


class ErpExportPackage(BaseModel):
    """Paquete integral de exportación para sistemas ERP (SAP / NetSuite) y fiscal (CFDI 4.0)."""
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    case_id: str
    total_discrepancy: Decimal = Field(default=Decimal("0.00"), ge=0)
    credit_memo_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    claimable_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    accounting_standard: str = "NIF C-3 / US GAAP"
    sap_bapi: Dict[str, Any] = Field(default_factory=dict)
    netsuite_journal_lines: List[Dict[str, Any]] = Field(default_factory=list)
    cfdi_uuid: str = ""
    cfdi_xml: str = ""
    generated_at: str = ""


# ==========================================
# 9. Modelos de Motor Cambiario FX & Incoterms 2020 (Fase 4 - Pilar 5)
# ==========================================
class IncotermRiskRule(BaseModel):
    """Regla formal de transferencia de riesgo legal según ICC Incoterms 2020."""
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    incoterm_code: str                          # "FOB", "FCA", "DDP", "DAP", "CIF", "CIP", "EXW"
    name: str                                   # Ej: "Free on Board (Franco a Bordo)"
    transfer_point: str                         # "ORIGEN_PUERTO", "DESTINO_CEDIS", "ORIGEN_CARRIER", etc.
    transit_risk_party: str                     # "BUYER" / "SELLER"
    insurance_obligation: str                   # "BUYER" / "SELLER" / "NONE"
    legal_basis: str                            # Cita normativa ICC Incoterms 2020 (ej. "ICC Incoterms 2020 Regla FOB Art. A4/B4")
    legal_verdict: str                          # "IMPROCEDENTE_POR_INCOTERM", "PROCEDENTE_EN_DESTINO", "REQUERIDO_RECLAMO_ASEGURADORA"
    recommendation: str                         # Directriz de arbitraje para el proveedor


class FxAuditReport(BaseModel):
    """Auditoría matemática determinística que aísla la varianza cambiaria del conflicto comercial."""
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    case_id: str
    invoice_currency: str = "USD"
    payment_currency: str = "MXN"
    billed_amount_invoice_curr: Decimal = Field(default=Decimal("0.00"))
    invoice_fx_rate: Decimal = Field(default=Decimal("1.0000"), gt=0)
    payment_fx_rate: Decimal = Field(default=Decimal("1.0000"), gt=0)
    received_amount_payment_curr: Decimal = Field(default=Decimal("0.00"))
    received_amount_invoice_curr: Decimal = Field(default=Decimal("0.00"))
    total_nominal_discrepancy: Decimal = Field(default=Decimal("0.00"))
    fx_variance_amount: Decimal = Field(default=Decimal("0.00"))
    fx_impact_type: str = "NEUTRAL"             # "PÉRDIDA CAMBIARIA (FX LOSS)", "GANANCIA CAMBIARIA (FX GAIN)", "NEUTRAL"
    commercial_deduction_amount: Decimal = Field(default=Decimal("0.00"))
    effective_claimable_amount: Decimal = Field(default=Decimal("0.00"))
    math_invariant_verified: bool = True        # total_nominal == fx_variance + commercial_deduction
    incoterm: str = "FOB"
    incoterm_rule: Optional[IncotermRiskRule] = None
    incoterm_verdict: str = "IMPROCEDENTE_POR_INCOTERM"
    incoterm_legal_basis: str = ""
    generated_at: str = ""


# ==========================================
# 10. Modelos de Perfilador de Fugas de Retailers (Fase 4 - Pilar 3)
# ==========================================
class RetailerDeductionPattern(BaseModel):
    """Patrón sistemático o abusivo de deducciones identificado en un retailer."""
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    pattern_id: str
    name: str
    frequency_pct: float = Field(ge=0.0, le=100.0)
    impact_severity: str = "ALTA"               # "CRITICA", "ALTA", "MEDIA", "BAJA"
    abusive_mechanism: str
    counter_strategy: str


class PreDispatchCheckItem(BaseModel):
    """Ítem interactivo del checklist preventivo pre-despacho para mitigar retenciones."""
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    check_id: str
    title: str
    description: str
    mandatory: bool = True
    risk_mitigated: str
    verified: bool = False


class RetailerLeakageProfile(BaseModel):
    """Perfil longitudinal de comportamiento, fugas y mitigación de un gran comprador comercial."""
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    retailer_id: str
    retailer_name: str
    risk_tier: str = "MEDIO"                    # "PREDATORIO", "ALTO", "MEDIO", "BAJO"
    win_rate_pct: float = Field(default=0.0, ge=0.0, le=100.0)
    recovery_ratio_pct: float = Field(default=0.0, ge=0.0, le=100.0)
    total_disputed_volume: Decimal = Field(default=Decimal("0.00"), ge=0)
    total_recovered_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    top_deduction_reasons: List[str] = Field(default_factory=list)
    systematic_patterns: List[RetailerDeductionPattern] = Field(default_factory=list)
    pre_dispatch_checklist: List[PreDispatchCheckItem] = Field(default_factory=list)
    recommended_incoterm: str = "FOB"
    average_dispute_days: int = 15
    cedis_alert_summary: Optional[str] = None


# ==========================================
# 11. Auditoría de Integridad y Resiliencia Documental (Pilar 1)
# ==========================================
class DocumentHealthAudit(BaseModel):
    """Auditoría de integridad estructural, autocuración y salud de los documentos del caso."""
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    case_id: str
    health_score: float = Field(default=100.0, ge=0.0, le=100.0)
    status: str = "PRISTINE"                    # "PRISTINE" (100%), "AUTO_REPAIRED" (80-99%), "DEGRADED" (50-79%), "QUARANTINE" (<50%)
    is_healthy: bool = True
    repaired_issues: List[str] = Field(default_factory=list)
    imputed_documents: List[str] = Field(default_factory=list)
    documents_present: List[str] = Field(default_factory=list)
    documents_missing: List[str] = Field(default_factory=list)
    schema_warnings: List[str] = Field(default_factory=list)
    execution_safety_level: str = "SAFE_FOR_AUTONOMOUS_SETTLEMENT"
    generated_at: str = ""




