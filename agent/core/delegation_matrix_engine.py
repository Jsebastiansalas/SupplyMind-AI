"""
agent/core/delegation_matrix_engine.py
Motor de Matriz de Delegación Financiera y Salvaguardas de Gobernanza B2B (Sprint 6.2).
Establece límites infranqueables de concesión por nivel de cuenta (Tier 1, Tier 2, Tier 3),
aplica salvaguarda de forzado a Human Gatekeeper para controversias mayores a $10,000 USD
y exige reciprocidad comercial vinculante en toda transacción económica.
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from datetime import datetime, timezone
import json

from data.models import (
    DelegationTierPolicy,
    FinancialDelegationMatrix,
    DisputeAnalysisReport
)
from agent.core.concession_engine import ConcessionEngine
from agent.core.negotiation_engine import NegotiationEngine

ROOT_DIR = Path(__file__).resolve().parent.parent.parent


DEFAULT_TIER_POLICIES: Dict[str, DelegationTierPolicy] = {
    "TIER_1_STRATEGIC": DelegationTierPolicy(
        tier_id="TIER_1_STRATEGIC",
        tier_name="Cuentas Estratégicas Tier-1 (Walmart, Amazon, Soriana)",
        max_concession_pct=50.0,
        max_concession_fixed_cap=Decimal("15000.00"),
        max_payment_days=5,
        require_reciprocal_concession=True,
        reciprocal_clauses_required=[
            "Exención de penalizaciones logísticas análogas en las siguientes 2 Órdenes de Compra",
            "Asignación de citas prioritarias en muelle de CEDIS sin recargos de reprogramación",
            "Compromiso vinculante de mantenimiento o incremento de volumen de compra trimestral"
        ]
    ),
    "TIER_2_REGULAR": DelegationTierPolicy(
        tier_id="TIER_2_REGULAR",
        tier_name="Cuentas Comerciales Regulares Tier-2",
        max_concession_pct=25.0,
        max_concession_fixed_cap=Decimal("5000.00"),
        max_payment_days=5,
        require_reciprocal_concession=True,
        reciprocal_clauses_required=[
            "Liquidación bancaria expedita en menos de 5 días hábiles del saldo no deducido",
            "Eliminación de cargos administrativos de patio en entregas subsecuentes"
        ]
    ),
    "TIER_3_HIGH_RISK": DelegationTierPolicy(
        tier_id="TIER_3_HIGH_RISK",
        tier_name="Cuentas de Alto Riesgo o Reincidentes Tier-3",
        max_concession_pct=0.0,
        max_concession_fixed_cap=Decimal("0.00"),
        max_payment_days=3,
        require_reciprocal_concession=False,
        reciprocal_clauses_required=[
            "Cobro íntegro del 100% de lo reclamable bajo apercibimiento formal de suspensión de suministros"
        ]
    )
}


class DelegationMatrixEngine:
    """Motor central de gobernanza y control de límites de delegación financiera."""

    _cached_matrix: Optional[FinancialDelegationMatrix] = None

    @classmethod
    def get_matrix_file_path(cls) -> Path:
        reports_dir = ROOT_DIR / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        return reports_dir / "financial_delegation_matrix.json"

    @classmethod
    def get_active_matrix(cls) -> FinancialDelegationMatrix:
        """Obtiene la matriz activa de memoria, de archivo JSON o inicializa los valores por defecto."""
        if cls._cached_matrix:
            return cls._cached_matrix

        file_path = cls.get_matrix_file_path()
        if file_path.exists():
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                matrix = FinancialDelegationMatrix.model_validate(data)
                cls._cached_matrix = matrix
                return matrix
            except Exception:
                pass

        # Inicialización por defecto
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        default_matrix = FinancialDelegationMatrix(
            matrix_id="FDM-POLICY-CORP-V1",
            cfo_approver="Dirección Corporativa de Finanzas & Tesorería B2B",
            strict_approval_threshold=Decimal("10000.00"),
            tier_policies=DEFAULT_TIER_POLICIES,
            allow_autonomous_execution=True,
            last_updated=now_str
        )
        cls._cached_matrix = default_matrix
        cls.save_matrix(default_matrix)
        return default_matrix

    @classmethod
    def save_matrix(cls, matrix: FinancialDelegationMatrix) -> None:
        """Persiste la matriz en el repositorio."""
        matrix.last_updated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        cls._cached_matrix = matrix
        file_path = cls.get_matrix_file_path()
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(matrix.model_dump_json(indent=2))

    @classmethod
    def evaluate_case_delegation(
        cls,
        case_id: str,
        requested_mode: str = "FULL_AUTONOMY"
    ) -> Dict[str, Any]:
        """
        Evalúa el expediente contra la matriz de delegación y determina:
        1. Si se permite el modo Piloto Automático o se fuerza Human Gatekeeper.
        2. El monto máximo exacto de concesión en USD autorizado en Python Decimal.
        3. Las cláusulas obligatorias de reciprocidad comercial.
        """
        matrix = cls.get_active_matrix()
        report = ConcessionEngine.get_or_create_base_report(case_id)
        acct_meta = NegotiationEngine.get_account_metadata(case_id)

        tier_id = acct_meta.get("tier", "TIER_2_REGULAR")
        if tier_id not in matrix.tier_policies:
            tier_id = "TIER_2_REGULAR"

        policy = matrix.tier_policies[tier_id]
        total_dispute = abs(report.difference).quantize(Decimal("0.01"))
        claimable = report.claimable_amount.quantize(Decimal("0.01"))

        # Cálculo de tope de concesión
        limit_pct = Decimal(str(policy.max_concession_pct)) / Decimal("100.0")
        calculated_cap = (claimable * limit_pct).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        allowed_concession = min(calculated_cap, policy.max_concession_fixed_cap)

        # Regla de Salvaguarda: Casos mayores al umbral fuerzan Gatekeeper
        is_high_value = total_dispute >= matrix.strict_approval_threshold
        enforced_mode = requested_mode
        safeguard_triggered = False
        safeguard_reason = ""

        if is_high_value and requested_mode == "FULL_AUTONOMY":
            enforced_mode = "HUMAN_GATEKEEPER"
            safeguard_triggered = True
            safeguard_reason = (
                f"Salvaguarda Financiera Activa: El monto disputado (${total_dispute:,.2f} USD) "
                f"alcanza o supera el umbral estricto de ${matrix.strict_approval_threshold:,.2f} USD. "
                f"Se requiere la rúbrica expresa del CFO o apoderado legal antes del cierre."
            )
        elif not matrix.allow_autonomous_execution and requested_mode == "FULL_AUTONOMY":
            enforced_mode = "HUMAN_GATEKEEPER"
            safeguard_triggered = True
            safeguard_reason = "La directiva corporativa global exige visto bueno humano para todas las cuentas."

        return {
            "case_id": case_id,
            "account_name": acct_meta["name"],
            "account_tier": tier_id,
            "policy": policy,
            "total_disputed_amount": total_dispute,
            "claimable_amount": claimable,
            "max_allowed_concession_pct": policy.max_concession_pct,
            "max_allowed_concession_amount": allowed_concession,
            "requested_mode": requested_mode,
            "enforced_mode": enforced_mode,
            "safeguard_triggered": safeguard_triggered,
            "safeguard_reason": safeguard_reason,
            "max_payment_days": policy.max_payment_days,
            "reciprocal_clauses": policy.reciprocal_clauses_required if policy.require_reciprocal_concession else []
        }

    @classmethod
    def validate_proposed_concession(
        cls,
        case_id: str,
        proposed_concession: Decimal
    ) -> Tuple[bool, str]:
        """
        Valida en tiempo de ejecución si una concesión propuesta respeta la matriz de delegación.
        Retorna (es_valido, motivo_o_error).
        """
        eval_data = cls.evaluate_case_delegation(case_id)
        max_allowed = eval_data["max_allowed_concession_amount"]

        if proposed_concession > max_allowed:
            return (
                False,
                f"Concesión no autorizada: Se propuso conceder ${proposed_concession:,.2f} USD, "
                f"pero el tope máximo autorizado por la Matriz de Delegación para la cuenta "
                f"{eval_data['account_tier']} es de ${max_allowed:,.2f} USD."
            )

        return (True, "Concesión conforme a los parámetros de la Matriz de Delegación.")
