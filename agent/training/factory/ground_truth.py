"""
Ground Truth Pydantic Schemas for Adversarial Dispute Factory.

Establece el estándar de oro inmutable para evaluar las decisiones del agente
SupplyMind AI y el veredicto del Tribunal Colegiado (LLM-as-a-Judge).
Todos los montos monetarios utilizan rigurosamente Decimal para garantizar
cero alucinación numérica y precisión contable al centavo.
"""

from decimal import Decimal
from enum import Enum
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, ConfigDict, Field, model_validator


class DiscrepancyCategory(str, Enum):
    """Categorías tipificadas de discrepancia en disputas comerciales B2B."""
    PHYSICAL_SHORTAGE = "PHYSICAL_SHORTAGE"
    DAMAGED_GOODS = "DAMAGED_GOODS"
    PRICE_MISMATCH = "PRICE_MISMATCH"
    UNILATERAL_PENALTY = "UNILATERAL_PENALTY"
    EXTEMPORANEOUS_CLAIM = "EXTEMPORANEOUS_CLAIM"
    TOLERANCE_EXEMPT = "TOLERANCE_EXEMPT"
    MIXED = "MIXED"


class CommercialActionType(str, Enum):
    """Tipos de acción comercial recomendada frente a una disputa."""
    CREDIT_NOTE = "CREDIT_NOTE"
    COLLECTION_LETTER = "COLLECTION_LETTER"
    MIXED_RESOLUTION = "MIXED_RESOLUTION"


class GroundTruthLineItem(BaseModel):
    """Desglose a nivel SKU de la discrepancia física o de precios."""
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    item_id: str
    description: str = ""
    invoiced_qty: int = Field(default=0, ge=0)
    received_qty: int = Field(default=0, ge=0)
    missing_qty: int = Field(default=0, ge=0)
    damaged_qty: int = Field(default=0, ge=0)
    invoiced_price: Decimal = Field(default=Decimal("0.00"), ge=0)
    agreed_price: Decimal = Field(default=Decimal("0.00"), ge=0)
    price_diff: Decimal = Field(default=Decimal("0.00"))
    missing_financial_impact: Decimal = Field(default=Decimal("0.00"), ge=0)
    damaged_financial_impact: Decimal = Field(default=Decimal("0.00"), ge=0)
    price_variance_impact: Decimal = Field(default=Decimal("0.00"))
    total_line_impact: Decimal = Field(default=Decimal("0.00"))

    @model_validator(mode="before")
    @classmethod
    def align_and_calculate(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        # Mapeo de compatibilidad para esquemas con nombres alternativos
        if "sku" in data and "item_id" not in data:
            data["item_id"] = str(data["sku"])
        if "billed_qty" in data and "invoiced_qty" not in data:
            data["invoiced_qty"] = int(data["billed_qty"])
        if "unit_price" in data and "invoiced_price" not in data:
            data["invoiced_price"] = Decimal(str(data["unit_price"]))
        if "agreed_price" not in data:
            data["agreed_price"] = data.get("invoiced_price", Decimal("0.00"))
        if not data.get("description"):
            data["description"] = f"Product {data.get('item_id', 'SKU')}"

        invoiced_qty = int(data.get("invoiced_qty", 0))
        received_qty = int(data.get("received_qty", 0))
        missing_qty = int(data.get("missing_qty", max(0, invoiced_qty - received_qty)))
        damaged_qty = int(data.get("damaged_qty", 0))

        data["missing_qty"] = missing_qty
        data["damaged_qty"] = damaged_qty

        inv_p = Decimal(str(data.get("invoiced_price", "0.00")))
        agr_p = Decimal(str(data.get("agreed_price", inv_p)))
        p_diff = inv_p - agr_p

        data["price_diff"] = p_diff
        data["missing_financial_impact"] = Decimal(missing_qty) * inv_p
        data["damaged_financial_impact"] = Decimal(damaged_qty) * inv_p
        data["price_variance_impact"] = Decimal(invoiced_qty) * p_diff
        data["total_line_impact"] = (
            data["missing_financial_impact"] +
            data["damaged_financial_impact"] +
            data["price_variance_impact"]
        )
        return data

    @property
    def sku(self) -> str:
        return self.item_id

    @property
    def billed_qty(self) -> int:
        return self.invoiced_qty

    @property
    def unit_price(self) -> Decimal:
        return self.invoiced_price

    @property
    def line_total(self) -> Decimal:
        return self.invoiced_price * Decimal(self.invoiced_qty)


class GroundTruthDeductionAssessment(BaseModel):
    """Evaluación objetiva e individual de una deducción aplicada en pago."""
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    code: str
    amount: Decimal = Field(ge=0)
    reason: str
    is_justified: bool
    governing_clause_id: Optional[str] = None
    factual_basis: str = ""
    remedy_action: str = ""  # "ACCEPT_AND_CREDIT" o "REJECT_AND_CLAIM"

    @model_validator(mode="before")
    @classmethod
    def set_defaults_and_aliases(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        if "legal_basis" in data and "governing_clause_id" not in data:
            data["governing_clause_id"] = data["legal_basis"]
        if not data.get("factual_basis"):
            data["factual_basis"] = data.get("reason", "")
        if not data.get("remedy_action"):
            is_just = bool(data.get("is_justified", False))
            data["remedy_action"] = "ACCEPT_AND_CREDIT" if is_just else "REJECT_AND_CLAIM"
        return data

    @property
    def legal_basis(self) -> Optional[str]:
        return self.governing_clause_id


# Alias de compatibilidad
GroundTruthDeduction = GroundTruthDeductionAssessment


class GroundTruth(BaseModel):
    """
    Estándar de Oro Inmutable de un Caso de Disputa Adversarial.
    
    Invariante matemática fundamental:
    billed_amount - received_amount = sum(deductions.amount) = expected_justified_amount + expected_claimable_amount
    """
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    case_id: str
    difficulty_level: int = Field(default=1, ge=1, le=5)
    category: DiscrepancyCategory = DiscrepancyCategory.PHYSICAL_SHORTAGE
    expected_action_type: CommercialActionType = CommercialActionType.CREDIT_NOTE

    # Conciliación financiera exacta en Decimal
    billed_amount: Decimal = Field(ge=0)
    received_amount: Decimal = Field(ge=0)
    difference: Decimal = Field(default=Decimal("0.00"))  # received_amount - billed_amount
    expected_justified_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    expected_claimable_amount: Decimal = Field(default=Decimal("0.00"), ge=0)

    # Detalle analítico
    line_items: List[GroundTruthLineItem] = Field(default_factory=list)
    deductions: List[GroundTruthDeductionAssessment] = Field(default_factory=list)

    # Evidencia y marco jurídico
    required_evidence_citations: List[str] = Field(default_factory=list)
    required_clause_citations: List[str] = Field(default_factory=list)
    evidence_hierarchy_rule_applied: str = ""
    scenario_tags: List[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def populate_defaults_before(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        billed = Decimal(str(data.get("billed_amount", "0.00")))
        received = Decimal(str(data.get("received_amount", "0.00")))
        
        # Si no se pasó difference, establecer como received - billed (convención contable)
        if "difference" not in data:
            data["difference"] = received - billed

        # Compatibilidad con campos de PROJECT.md
        if "justified_deductions_amount" in data and "expected_justified_amount" not in data:
            data["expected_justified_amount"] = Decimal(str(data["justified_deductions_amount"]))
        if "claimable_deductions_amount" in data and "expected_claimable_amount" not in data:
            data["expected_claimable_amount"] = Decimal(str(data["claimable_deductions_amount"]))
            
        return data

    @model_validator(mode="after")
    def validate_coherence_invariants(self) -> "GroundTruth":
        # 1. Suma de deducciones
        sum_deductions = sum((d.amount for d in self.deductions), Decimal("0.00"))

        # 2. Diferencia facturado vs recibido
        underpaid = self.billed_amount - self.received_amount

        if underpaid != sum_deductions:
            raise ValueError(
                f"Violación de Invariante Contable: billed_amount ({self.billed_amount}) - "
                f"received_amount ({self.received_amount}) = {underpaid} no coincide con "
                f"sum(deductions.amount) = {sum_deductions}"
            )

        # 3. Suma de montos justificados y reclamables
        sum_justified_claimable = self.expected_justified_amount + self.expected_claimable_amount
        if sum_deductions != sum_justified_claimable:
            raise ValueError(
                f"Violación de Invariante de Resolución: sum(deductions.amount) = {sum_deductions} "
                f"no coincide con expected_justified_amount ({self.expected_justified_amount}) + "
                f"expected_claimable_amount ({self.expected_claimable_amount}) = {sum_justified_claimable}"
            )

        # 4. Validar suma individual de deducciones según bandera is_justified si hay deducciones
        if self.deductions:
            sum_justified_deductions = sum((d.amount for d in self.deductions if d.is_justified), Decimal("0.00"))
            sum_claimable_deductions = sum((d.amount for d in self.deductions if not d.is_justified), Decimal("0.00"))
            if sum_justified_deductions != self.expected_justified_amount:
                raise ValueError(
                    f"Inconsistencia en deducciones justificadas: sum(justified)={sum_justified_deductions} "
                    f"!= expected_justified_amount={self.expected_justified_amount}"
                )
            if sum_claimable_deductions != self.expected_claimable_amount:
                raise ValueError(
                    f"Inconsistencia en deducciones reclamables: sum(claimable)={sum_claimable_deductions} "
                    f"!= expected_claimable_amount={self.expected_claimable_amount}"
                )

        return self

    @property
    def net_difference(self) -> Decimal:
        """Diferencia neta (monto facturado - monto recibido). Positivo si hay saldo insoluto."""
        return self.billed_amount - self.received_amount

    @property
    def justified_deductions_amount(self) -> Decimal:
        return self.expected_justified_amount

    @property
    def claimable_deductions_amount(self) -> Decimal:
        return self.expected_claimable_amount

    @property
    def expected_root_cause(self) -> str:
        return self.evidence_hierarchy_rule_applied or self.category.value

    @property
    def expected_commercial_action(self) -> str:
        return self.expected_action_type.value
