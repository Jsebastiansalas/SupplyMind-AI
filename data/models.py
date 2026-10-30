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
    raw_content: Optional[str] = None


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
    financial_proof: Optional[Any] = Field(default=None)  # Prueba Criptográfica de Invarianza Aritmética / ZKP (ZKPFinancialProof o dict)
    evidence_manifest: Optional[Any] = Field(default=None)  # Manifiesto de Anclaje Fáctico y Cero Reclamaciones sin Cita (Pilar 3)
    quarantine_docket: Optional[Any] = Field(default=None)  # Expediente pericial de Cuarentena Forense y Bloqueo de Liquidación (Pilar 4)
    session_anchor: Optional[Any] = Field(default=None)  # Ancla de Estado Inmutable contra manipulación conversacional (Pilar 5)
    watchdog_metrics: Optional[Any] = Field(default=None)  # Métricas operativas del vigilante ReAct contra bucles infinitos (Pilar 5)
    adversarial_verdict: Optional[Any] = Field(default=None)  # Debate Dialéctico Multi-Agente (Pilar 3)
    recovery_prediction: Optional[Any] = Field(default=None)  # Motor Predictivo de Cobro & Simulación (Pilar 4)
    sanity_gate_audit: Optional[Any] = Field(default=None)  # Filtro de Sanidad Cuádruple & Anti-Puntos Ciegos (Semana 4)
    resolution_notes: Optional[List[str]] = Field(default_factory=list)  # Notas de resolución y blindaje jurídico (Sprint 5.2)
    deduction_type: Optional[str] = Field(default=None)  # Tipo específico de deducción (ej. SHORTAGE, OTIF, PRICING)
    adversarial_critique: Optional[Any] = Field(default=None)  # Dictamen del Subagente Crítico Reflexivo (Sprint 5.2)
    mcts_negotiation_plan: Optional[Any] = Field(default=None)  # Plan MCTS de Negociación Estratégica (Sprint 5.2)
    cross_border_assessment: Optional[Any] = Field(default=None)  # Dictamen de Tratados CISG/T-MEC (Sprint 5.2)


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
    quarantine_docket: Optional[Any] = Field(default=None)  # Expediente de Aislamiento Forense si status == 'QUARANTINE'
    generated_at: str = ""


# ==========================================
# 12. Prueba Criptográfica de Invarianza Aritmética y Cero Alucinación (Pilar 2)
# ==========================================
class ZKPFinancialProof(BaseModel):
    """Prueba criptográfica de invariantes aritméticas y verificación de cero alucinaciones financieras."""
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    case_id: str
    proof_hash: str                                     # SHA-256 HMAC del balance matemático
    invariant_conservation_ok: bool = True              # billed - received == abs(difference)
    invariant_deductions_ok: bool = True                # justified + claimable == abs(difference)
    invariant_line_items_ok: bool = True                # sum(items) == billed
    text_hallucination_detected: bool = False           # ¿El texto del LLM inventó cifras?
    detected_hallucinated_figures: List[str] = Field(default_factory=list)
    verified_figures: List[str] = Field(default_factory=list)
    confidence_penalty: float = 0.0                     # Penalización aplicada al score si hubo alucinación
    audit_status: str = "MATHEMATICALLY_PROVEN"         # "MATHEMATICALLY_PROVEN" | "HALLUCINATION_INTERCEPTED" | "ARITHMETIC_MISMATCH"
    tamper_proof_timestamp: str = ""


# ==========================================
# 13. Anclaje Fáctico Estricto y Certificación Probatoria (Pilar 3)
# ==========================================
class EvidencePointer(BaseModel):
    """Puntero auditable a una evidencia fáctica concreta (Factura, POD, Remisión, PO o Contrato)."""
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    pointer_id: str                                     # ej: "PTR-INV-001-TOTAL", "PTR-DEL-001-SKU-01"
    doc_type: str                                       # "INVOICE", "DELIVERY", "PURCHASE_ORDER", "PAYMENT", "CONTRACT"
    doc_id: str                                         # ej: "INV-2024-001"
    field_ref: str                                      # ej: "total_amount", "missing_quantity", "asn_penalty_clause"
    item_sku: Optional[str] = None                      # ej: "SKU-PROD-01"
    amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    citation_tag: str                                   # ej: "[Factura INV-001 §Total $12,500.00 USD]"
    is_backed_by_physical_proof: bool = True            # ¿Tiene soporte físico verificable (firma, sello, POD)?
    status: str = "ACREDITADO"                          # "ACREDITADO" | "CAUTELAR_NO_ACREDITADA"
    detail: Optional[str] = None                        # Explicación del soporte documental


class EvidenceBindingManifest(BaseModel):
    """Manifiesto de gobernanza que certifica el anclaje fáctico estricto del 100% de cifras reclamadas."""
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    case_id: str
    total_claims_audited: int = 0
    backed_claims_count: int = 0
    unbacked_claims_count: int = 0
    total_backed_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    total_unbacked_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    backing_ratio_pct: float = Field(default=100.0, ge=0.0, le=100.0)
    evidence_pointers: List[EvidencePointer] = Field(default_factory=list)
    cautelar_items: List[str] = Field(default_factory=list)
    binding_verdict: str = "FULL_EVIDENCE_BINDING_VERIFIED"  # "FULL_EVIDENCE_BINDING_VERIFIED" | "CAUTIONARY_ITEMS_DETECTED" | "CRITICAL_UNBACKED_DEFICIT"
    confidence_penalty: float = 0.0
    generated_at: str = ""


# ==========================================
# 14. Protocolo Forense de Cuarentena Documental (Pilar 4)
# ==========================================
class ForensicQuarantineDocket(BaseModel):
    """Expediente de aislamiento forense para casos con inconsistencias críticas o datos irreparables."""
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    quarantine_id: str                                  # ej: "FRQ-CASE-001-ISOLATION"
    case_id: str
    severity: str = "CRITICAL_CONTAMINATION"             # "CRITICAL_CONTAMINATION" | "UNRECOVERABLE_SYNTAX" | "ANACHRONISM_RISK" | "SEVERE_DOCUMENT_DEFICIT"
    is_settlement_blocked: bool = True                  # Bloqueo estricto de notas de crédito y acuerdos vinculantes
    blocking_reasons: List[str] = Field(default_factory=list)
    violated_invariants: List[str] = Field(default_factory=list)
    remediation_steps: List[str] = Field(default_factory=list)
    quarantine_timestamp: str = ""
    release_conditions: List[str] = Field(default_factory=list)
    operator_override_permitted: bool = False


# ==========================================
# 15. Ancla de Estado Inmutable y Watchdog ReAct (Pilar 5)
# ==========================================
class SessionStateAnchor(BaseModel):
    """Ancla de estado inmutable para sesiones de chat y resolución multi-turno contra pérdida de contexto."""
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    case_id: str
    currency: str = "USD"
    billed_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    received_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    difference: Decimal = Decimal("0.00")
    justified_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    claimable_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    health_status: str = "PRISTINE"
    health_score: float = 100.0
    zkp_proof_hash: str = ""
    zkp_status: str = "MATHEMATICALLY_PROVEN"
    is_quarantined: bool = False
    evidence_backing_ratio: float = 100.0
    anchored_at: str = ""

    def formatted_anchor_header(self) -> str:
        """Genera el bloque inmutable de anclaje para inyección en el prompt."""
        quarantine_tag = "🚨 EN CUARENTENA" if self.is_quarantined else "NORMAL"
        return (
            f"[INMUTABLE_CASE_ANCHOR | Caso: {self.case_id} | Facturado: ${self.billed_amount:,.2f} {self.currency} | "
            f"Recibido: ${self.received_amount:,.2f} {self.currency} | Diferencia: ${self.difference:,.2f} {self.currency} | "
            f"Justificado: ${self.justified_amount:,.2f} {self.currency} | Reclamable: ${self.claimable_amount:,.2f} {self.currency} | "
            f"ZKP: {self.zkp_status} ({self.zkp_proof_hash[:16] if self.zkp_proof_hash else 'OK'}) | "
            f"Salud: {self.health_status} ({self.health_score}%) | Estado: {quarantine_tag}]"
        )


class WatchdogMetrics(BaseModel):
    """Métricas operativas del vigilante ReAct contra bucles infinitos y llamadas duplicadas."""
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    total_tool_calls: int = 0
    unique_tool_calls: int = 0
    deduplicated_calls_count: int = 0
    circuit_breaker_triggered: bool = False
    warnings: List[str] = Field(default_factory=list)


# ==========================================
# 16. Confrontación Dialéctica Multi-Agente (Fase 6 - Sprint 6.1)
# ==========================================
class RetailerArchetypeConfig(BaseModel):
    """Configuración psicológica y táctica del comprador hostil retail."""
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    archetype_id: str                      # "WALMART_OTIF", "AMAZON_FC", "SORIANA_REBATE", "COSTCO_DEPOT", "GENERIC_B2B"
    retailer_name: str                     # "Walmart Supercenter", "Amazon Fulfillment Services", etc.
    buyer_title: str                       # "Director de Compras & Compliance OTIF", etc.
    initial_demand_pct: float = 100.0      # Demanda inicial de retención (% del saldo disputado)
    concession_resistance_score: float = 8.5 # 1.0 (flexible) a 10.0 (intransigente)
    key_pressure_points: List[str] = Field(default_factory=list) # "Scorecard OTIF", "Corte de pedidos", etc.
    evidence_vulnerability: str = "DELIVERY_SLIP_AND_SEAL" # Qué prueba lo desarma ("DELIVERY_SLIP_AND_SEAL", "EDI_997", "CCOM_ART88")
    tone: str = "Hostil y burocrático"


class NegotiationDuelRound(BaseModel):
    """Ronda individual del careo bilateral entre Agente SupplyMind y Comprador."""
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    round_number: int                      # 1 a 5
    buyer_message: str                     # Argumento del comprador retail
    buyer_stance: str                      # "INTRANSIGENT", "DEFENSIVE", "PARTIAL_CONCESSION", "FINAL_SETTLEMENT"
    buyer_demand_credit_memo: Decimal = Field(default=Decimal("0.00"), ge=0) # Cuánto exige en Nota de Crédito
    buyer_cash_payout_offer: Decimal = Field(default=Decimal("0.00"), ge=0)  # Cuánto ofrece pagar en banco
    
    supplier_message: str                  # Réplica de SupplyMind AI
    supplier_stance: str                   # "EVIDENCE_FIRMNESS", "COUNTER_OFFER", "PROPORTIONAL_CONCESSION", "CLOSING_AGREEMENT"
    supplier_offer_credit_memo: Decimal = Field(default=Decimal("0.00"), ge=0) # Cuánto concede el proveedor
    supplier_claim_cash: Decimal = Field(default=Decimal("0.00"), ge=0)       # Cuánto exige cobrar en efectivo
    
    evidence_exhibited: List[str] = Field(default_factory=list) # Pruebas mostradas en la ronda
    spread: Decimal = Field(default=Decimal("0.00"), ge=0)      # Brecha entre pretensiones
    convergence_pct: float = Field(default=0.0, ge=0.0, le=100.0)
    round_status: str = "IN_PROGRESS"      # "IN_PROGRESS", "CONVERGING", "AGREED", "IMPASSE"


class NegotiationDuelSession(BaseModel):
    """Sesión completa de careo dialéctico multi-agente."""
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    session_id: str                        # "DUEL-CASE-001-XXXX"
    case_id: str
    retailer_name: str
    archetype: RetailerArchetypeConfig
    governance_mode: str = "HUMAN_GATEKEEPER" # "FULL_AUTONOMY" | "HUMAN_GATEKEEPER"
    status: str = "IN_PROGRESS"            # "IN_PROGRESS", "AGREEMENT_REACHED", "IMPASSE_REACHED", "AWAITING_HUMAN_APPROVAL"
    current_round: int = 1
    max_rounds: int = 5
    delegation_limit_pct: float = Field(default=50.0, ge=0.0, le=100.0) # Máxima concesión de reclamable autorizada
    delegation_limit_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    total_disputed_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    rounds: List[NegotiationDuelRound] = Field(default_factory=list)
    final_agreed_credit_memo: Optional[Decimal] = None
    final_agreed_cash_recovery: Optional[Decimal] = None
    settlement_minutes_hash: Optional[str] = None
    minutes_markdown_path: Optional[str] = None
    started_at: str = ""
    completed_at: Optional[str] = None
    summary_verdict: str = ""


# ==========================================
# 17. Matriz de Delegación Financiera & Gobernanza B2B (Fase 6 - Sprint 6.2)
# ==========================================
class DelegationTierPolicy(BaseModel):
    """Política de concesión y plazos por nivel de cuenta comercial."""
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    tier_id: str                           # "TIER_1_STRATEGIC", "TIER_2_REGULAR", "TIER_3_HIGH_RISK"
    tier_name: str                         # "Cuentas Estratégicas Tier-1", etc.
    max_concession_pct: float = Field(default=50.0, ge=0.0, le=100.0)
    max_concession_fixed_cap: Decimal = Field(default=Decimal("15000.00"), ge=0)
    max_payment_days: int = 5
    require_reciprocal_concession: bool = True
    reciprocal_clauses_required: List[str] = Field(default_factory=list)


class FinancialDelegationMatrix(BaseModel):
    """Matriz corporativa de delegación financiera y salvaguardas de gobernanza."""
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    matrix_id: str = "FDM-GLOBAL-DEFAULT"
    cfo_approver: str = "Dirección de Finanzas & Tesorería B2B"
    strict_approval_threshold: Decimal = Field(default=Decimal("10000.00"), ge=0) # Casos > este importe fuerzan Gatekeeper
    tier_policies: Dict[str, DelegationTierPolicy] = Field(default_factory=dict)
    allow_autonomous_execution: bool = True
    last_updated: str = ""


class SettlementAgreementDetails(BaseModel):
    """Detalle legal y financiero del convenio formal de finiquito y transacción comercial."""
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    agreement_id: str                      # "AGR-CASE-001-XXXX"
    case_id: str
    retailer_name: str
    dispute_original_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    justified_credit_memo: Decimal = Field(default=Decimal("0.00"), ge=0)
    commercial_concession_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    total_credit_memo: Decimal = Field(default=Decimal("0.00"), ge=0)
    cash_recovery_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    payment_deadline_days: int = 5
    legal_doctrines: List[str] = Field(default_factory=list)
    reciprocal_commitments: List[str] = Field(default_factory=list)
    zkp_seal_hash: str = ""
    signed_by_operator: str = ""
    signed_at: str = ""


# ==========================================
# 18. Despachador Robótico a Portales B2B (Fase 6 - Sprint 6.3)
# ==========================================
class PortalEvidenceManifestItem(BaseModel):
    """Ítem individual del manifiesto de evidencias con hash criptográfico SHA-256."""
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    doc_id: str
    doc_type: str                          # "CFDI_40_XML", "REMISSION_STAMPED_POD", "ASN_EDI_856", "EDI_997_ACK", "CTPAT_SEAL_CERTIFICATE", "SETTLEMENT_AGREEMENT"
    file_name: str
    file_size_bytes: int = 0
    sha256_hash: str
    description: str
    status: str = "VERIFIED_VALID"


class PortalAdapterPayload(BaseModel):
    """Payload normalizado adaptado a la API o formulario del portal B2B del retailer."""
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    portal_type: str                       # "WALMART_RETAIL_LINK", "AMAZON_VENDOR_CENTRAL", "SORIANA_B2B", "LIVERPOOL_B2B"
    retailer_name: str
    claim_code: str                        # "21 (Shortage)", "SHORTAGE_FC", "DED-MERMA", "DED-04"
    invoice_uuid_or_folio: str
    po_reference: str
    dc_or_fc_code: str                     # "CEDIS 6014 San Martín", "DAL3 Dallas FC", etc.
    receipt_folio: str
    dispute_reason: str
    claimable_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    currency: str = "USD"
    attached_evidence_files: List[str] = Field(default_factory=list)
    portal_specific_fields: Dict[str, Any] = Field(default_factory=dict)


class PortalDispatchDossier(BaseModel):
    """Expediente forense consolidado foliado y listo para radicación desatendida."""
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    dossier_id: str                        # "DOSSIER-CASE_001-XXXX"
    case_id: str
    portal_type: str
    retailer_name: str
    total_disputed_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    claimable_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    currency: str = "USD"
    manifest_items: List[PortalEvidenceManifestItem] = Field(default_factory=list)
    adapter_payload: Optional[PortalAdapterPayload] = None
    zkp_dossier_digest: str = ""
    generated_at: str = ""


class PortalDispatchReceipt(BaseModel):
    """Recibo oficial emitido por el portal comercial y bitácora de auditoría de radicación."""
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    receipt_id: str                        # "RCPT-WLMT-XXXX"
    case_id: str
    portal_type: str
    retailer_name: str
    tracking_ticket: str                   # "WLMT-TK-2026-XXXX", "AMZN-CASE-2026-XXXX", etc.
    status: str = "CONFIRMED_ACCEPTED"     # "CONFIRMED_ACCEPTED", "UNDER_REVIEW", "FAILED"
    http_status_code: int = 201
    claimable_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    currency: str = "USD"
    confirmation_seal_sha256: str = ""
    estimated_sla_days: int = 7
    log_trace: List[str] = Field(default_factory=list)
    submitted_at: str = ""








