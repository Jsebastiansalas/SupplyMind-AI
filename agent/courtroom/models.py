"""
agent/courtroom/models.py
Modelos de Datos para el Debate Dialéctico Multi-Agente (Adversarial Courtroom - Pilar 3).
Define los roles del Fiscal Forense, Abogado Defensor y Magistrado Sentenciador.
"""

from decimal import Decimal
from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, ConfigDict, Field


class AdversarialRole(str, Enum):
    PROSECUTOR = "PROSECUTOR"      # Fiscal Forense del Retailer (The Auditor)
    DEFENDER = "DEFENDER"          # Abogado Defensor del Proveedor (The Advocate)
    MAGISTRATE = "MAGISTRATE"      # Magistrado Sentenciador (The Magistrate)


class AdversarialArgument(BaseModel):
    """Alegato individual emitido durante el debate dialéctico."""
    model_config = ConfigDict(extra="allow")

    role: AdversarialRole
    speaker_name: str
    topic: str
    argument_text: str
    legal_or_contractual_ground: str
    strength_score: float = Field(ge=0.0, le=1.0)
    evidence_referenced: List[str] = Field(default_factory=list)


class AdversarialVerdict(BaseModel):
    """Sentencia judicial y dictamen dialéctico inapelable."""
    model_config = ConfigDict(extra="allow")

    case_id: str
    courtroom_session_id: str
    disputed_amount: Decimal
    justified_amount: Decimal
    claimable_amount: Decimal
    prosecutor_arguments: List[AdversarialArgument] = Field(default_factory=list)
    advocate_counterarguments: List[AdversarialArgument] = Field(default_factory=list)
    sustained_objections: List[str] = Field(default_factory=list)   # Procedentes (a favor del retailer)
    dismissed_objections: List[str] = Field(default_factory=list)   # Desestimadas (a favor del proveedor)
    magistrate_summary_ruling: str
    probative_force_supplier_pct: float = Field(ge=0.0, le=100.0)
    final_legal_doctrine: str
