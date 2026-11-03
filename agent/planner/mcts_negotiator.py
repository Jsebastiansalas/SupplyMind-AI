"""
agent/planner/mcts_negotiator.py
Árbol de Decisión Monte Carlo Tree Search (MCTS) para Negociación Estratégica B2B.
Frontera 1 de Superinteligencia (Sprint 5.2).

Simula y evalúa probabilísticamente múltiples trayectorias de negociación frente a retailers:
- Trayectoria A: Litigio / Arbitraje Coactivo Agresivo (Máximo cobro en efectivo)
- Trayectoria B: Preservación de Relación Comercial (Alianza a largo plazo)
- Trayectoria C: Liquidación Express / Pronto Pago (Optimización de flujo de caja y DSO)
"""

from decimal import Decimal, ROUND_HALF_UP
import math
import random
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class NegotiationTrajectory(BaseModel):
    """Definición y métricas proyectadas de una ruta de negociación con análisis financiero NPV."""
    name: str
    display_title: str
    description: str
    target_recovery_pct: float
    expected_payoff: Decimal
    projected_duration_days: int
    relationship_retention_index: float  # 0.0 a 1.0 (1.0 = relación intacta)
    legal_friction_score: float          # 0.0 a 1.0 (1.0 = fricción máxima/judicial)
    overall_utility_score: float
    strategic_rationale: str
    action_steps: List[str]
    # Métricas financieras avanzadas (HU 9.4.1)
    npv_payoff: Decimal = Decimal("0.00")
    capital_cost_drag: Decimal = Decimal("0.00")
    wacc_annual_pct: float = 12.0
    dso_savings_days: int = 0
    direct_legal_cost: Decimal = Decimal("0.00")
    expected_moratory_interest: Decimal = Decimal("0.00")


class MCTSPlanResult(BaseModel):
    """Resultado del análisis y simulación MCTS para la toma de decisiones ejecutivas del CFO."""
    case_id: str
    recommended_trajectory: str
    expected_net_payoff: Decimal
    projected_duration_days: int
    relationship_retention_index: float
    confidence_score: float
    total_simulations: int
    trajectories_evaluated: List[NegotiationTrajectory]
    executive_synthesis: str
    # Métricas financieras y relacionales consolidadas (HU 9.4.1 y HU 9.4.2)
    npv_payoff: Decimal = Decimal("0.00")
    capital_cost_drag: Decimal = Decimal("0.00")
    wacc_annual_pct: float = 12.0
    dso_savings_days: int = 0
    direct_legal_cost: Decimal = Decimal("0.00")
    expected_moratory_interest: Decimal = Decimal("0.00")
    rhi_score_applied: Optional[float] = None
    rhi_modulation_mode: Optional[str] = None


class MCTSNode:
    """Nodo en el árbol de búsqueda Monte Carlo."""

    def __init__(self, state_name: str, parent: Optional["MCTSNode"] = None):
        self.state_name = state_name
        self.parent = parent
        self.children: List["MCTSNode"] = []
        self.visits: int = 0
        self.total_value: float = 0.0

    @property
    def value(self) -> float:
        return (self.total_value / self.visits) if self.visits > 0 else 0.0

    def ucb1(self, exploration_constant: float = 1.414) -> float:
        """Fórmula Upper Confidence Bound for Trees (UCB1)."""
        if self.visits == 0:
            return float("inf")
        if not self.parent or self.parent.visits == 0:
            return self.value
        return self.value + exploration_constant * math.sqrt(math.log(self.parent.visits) / self.visits)


class MCTSNegotiator:
    """
    Motor Monte Carlo Tree Search para la optimización de decisiones estratégicas
    en disputas y arbitrajes B2B.
    """

    TRAJECTORY_DEFINITIONS = [
        {
            "id": "LITIGIO_AGRESIVO",
            "title": "Litigio / Arbitraje Coactivo Agresivo",
            "desc": "Reclamo del 100% de la deducción con apercibimiento formal y citación a mediación ICC/CANACO.",
            "recovery_pct": 1.00,
            "days_min": 45,
            "days_max": 90,
            "retention": 0.45,
            "friction": 0.90,
            "rationale": "Prioriza la recuperación integral del capital cuando la relación comercial ya está desgastada o la deducción es claramente ilegal y arbitraria.",
            "accrues_moratory_interest": True
        },
        {
            "id": "PRESERVACION_RELACION",
            "title": "Preservación de Alianza Comercial Estratégica",
            "desc": "Concesión negociada (absorber 15% de merma) a cambio de volumen garantizado en la siguiente orden de compra.",
            "recovery_pct": 0.85,
            "days_min": 15,
            "days_max": 30,
            "retention": 0.95,
            "friction": 0.15,
            "rationale": "Recomendada cuando el retailer representa >15% de la facturación del proveedor y el costo de perder la cuenta supera el monto disputado.",
            "accrues_moratory_interest": False
        },
        {
            "id": "LIQUIDACION_EXPRESS",
            "title": "Liquidación Express / Pronto Pago (DSO Acelerado)",
            "desc": "Descuento transaccional del 8% por pago total a 5 días hábiles mediante acuerdo transaccional vinculante.",
            "recovery_pct": 0.92,
            "days_min": 5,
            "days_max": 10,
            "retention": 0.80,
            "friction": 0.25,
            "rationale": "Óptima cuando la prioridad corporativa es el flujo de caja inmediato y la reducción drástica de días de cartera vencida (DSO).",
            "accrues_moratory_interest": False
        }
    ]

    @classmethod
    def calculate_trajectory_npv(
        cls,
        claimable_amount: Decimal,
        recovery_pct: float,
        duration_days: int,
        wacc_annual_pct: float = 12.0,
        is_litigation: bool = False,
        direct_legal_cost_override: Optional[Decimal] = None
    ) -> Dict[str, Any]:
        """
        Calcula con precisión Decimal ($0.00 MAE) los flujos financieros descontados por WACC (HU 9.4.1):
        NPV = (Nominal / (1 + WACC/365)^days) - Costos Legales Directos + Interés Moratorio (Art. 362 CCom).
        """
        nominal_recovered = (claimable_amount * Decimal(str(recovery_pct))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        days = max(1, duration_days)

        wacc_norm = Decimal(str(wacc_annual_pct / 100.0 if wacc_annual_pct > 1.0 else wacc_annual_pct))
        daily_wacc = wacc_norm / Decimal("365")

        # Factor de descuento exacto en Decimal
        discount_factor = (Decimal("1.0") + daily_wacc) ** days
        discounted_cash_flow = (nominal_recovered / discount_factor).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        capital_cost_drag = (nominal_recovered - discounted_cash_flow).quantize(Decimal("0.01"))

        # Costo legal directo
        if is_litigation:
            if direct_legal_cost_override is not None:
                direct_legal_cost = direct_legal_cost_override.quantize(Decimal("0.01"))
            else:
                direct_legal_cost = (claimable_amount * Decimal("0.04") + Decimal("500.00")).quantize(Decimal("0.01"))
        else:
            direct_legal_cost = Decimal("0.00")

        # Interés moratorio legal esperado (Art. 362 CCom: 9% anual acumulado en litigio)
        if is_litigation:
            daily_moratory = Decimal("0.09") / Decimal("365")
            moratory_interest = (nominal_recovered * daily_moratory * Decimal(days)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        else:
            moratory_interest = Decimal("0.00")

        # Valor Presente Neto (NPV)
        npv_payoff = (discounted_cash_flow - direct_legal_cost + moratory_interest).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # Días de ahorro en DSO frente al horizonte máximo de litigio (90 días)
        dso_savings_days = max(0, 90 - days)

        return {
            "nominal_recovered": nominal_recovered,
            "discounted_cash_flow": discounted_cash_flow,
            "capital_cost_drag": capital_cost_drag,
            "direct_legal_cost": direct_legal_cost,
            "expected_moratory_interest": moratory_interest,
            "npv_payoff": npv_payoff,
            "dso_savings_days": dso_savings_days,
            "wacc_annual_pct": float(wacc_annual_pct if wacc_annual_pct > 1.0 else wacc_annual_pct * 100.0)
        }

    @classmethod
    def simulate_negotiation(
        cls,
        case_id: str,
        claimable_amount: Decimal,
        retailer_account_weight_pct: Optional[float] = None,
        supplier_cashflow_priority: str = "BALANCED",  # AGGRESSIVE, BALANCED, CASH_URGENT
        num_simulations: int = 500,
        wacc_annual_pct: float = 12.0,
        rhi_score: Optional[float] = None,
        direct_legal_cost_override: Optional[Decimal] = None
    ) -> MCTSPlanResult:
        """
        Ejecuta el ciclo MCTS (Selección, Expansión, Simulación, Retropropagación)
        integrando descuento por WACC, NPV, DSO y acoplamiento dinámico con RHI (HU 9.4.1 y HU 9.4.2).
        """
        claimable = max(Decimal("0.00"), claimable_amount)

        # 1. Consulta y acoplamiento dinámico con RelationalHealthEngine (HU 9.4.2)
        applied_rhi = rhi_score
        rhi_modulation = None

        if applied_rhi is None:
            try:
                from agent.core.relational_health_engine import RelationalHealthEngine
                rhi_rep = RelationalHealthEngine.evaluate_relational_health(case_id)
                applied_rhi = rhi_rep.rhi_score
                rhi_modulation = rhi_rep.modulation_mode
                if retailer_account_weight_pct is None:
                    retailer_account_weight_pct = rhi_rep.share_of_wallet_pct
            except Exception:
                applied_rhi = 65.0
                rhi_modulation = "FIRM_COMMERCIAL"
        else:
            try:
                from agent.core.relational_health_engine import RelationalHealthEngine
                rhi_rep = RelationalHealthEngine.evaluate_relational_health(case_id, override_rhi_score=applied_rhi)
                rhi_modulation = rhi_rep.modulation_mode
            except Exception:
                rhi_modulation = "DIPLOMATIC_PRESERVATION" if applied_rhi > 80.0 else ("ASSERTIVE_LITIGIOUS" if applied_rhi < 50.0 else "FIRM_COMMERCIAL")

        if retailer_account_weight_pct is None:
            retailer_account_weight_pct = 20.0

        # 2. Configurar ponderaciones según el perfil corporativo y el índice RHI
        if supplier_cashflow_priority == "AGGRESSIVE":
            w_cash = 0.70
            w_rel = 0.10
            w_time = 0.10
            w_fric = 0.10
        elif supplier_cashflow_priority == "CASH_URGENT":
            w_cash = 0.40
            w_rel = 0.15
            w_time = 0.35
            w_fric = 0.10
        else:  # BALANCED (Modulado dinámicamente por RHI y concentración)
            if applied_rhi > 80.0 or retailer_account_weight_pct > 25.0:
                # Cuenta Tier-1 estratégica: preservación de relación prioritaria
                w_cash = 0.35
                w_rel = 0.45
                w_time = 0.10
                w_fric = 0.10
            elif applied_rhi < 50.0:
                # Cuenta desgastada / prescindible: litigio coactivo o recuperación rápida
                w_cash = 0.65
                w_rel = 0.15
                w_time = 0.10
                w_fric = 0.10
            else:
                w_cash = 0.50
                w_rel = 0.30
                w_time = 0.10
                w_fric = 0.10

        # Árbol MCTS
        root = MCTSNode("ROOT")
        nodes_by_traj: Dict[str, MCTSNode] = {}
        for t_def in cls.TRAJECTORY_DEFINITIONS:
            child = MCTSNode(t_def["id"], parent=root)
            root.children.append(child)
            nodes_by_traj[t_def["id"]] = child

        wacc_norm = Decimal(str(wacc_annual_pct / 100.0 if wacc_annual_pct > 1.0 else wacc_annual_pct))

        # Simulación Monte Carlo
        random.seed(42)  # Determinismo en las pruebas
        for _ in range(num_simulations):
            # 1. Selección (UCB1)
            selected = max(root.children, key=lambda c: c.ucb1())

            # 2. Simulación / Rollout
            t_def = next(t for t in cls.TRAJECTORY_DEFINITIONS if t["id"] == selected.state_name)

            # Variabilidad estocástica en la negociación
            payoff_sim = t_def["recovery_pct"] * random.uniform(0.95, 1.02)
            days_sim = random.uniform(t_def["days_min"], t_def["days_max"])
            retention_sim = t_def["retention"] * random.uniform(0.90, 1.05)
            friction_sim = t_def["friction"] * random.uniform(0.90, 1.10)

            # Descuento financiero estocástico en la simulación (NPV ratio con WACC)
            discount_sim = (1.0 + float(wacc_norm) / 365.0) ** days_sim
            legal_cost_pct = 0.045 if t_def.get("accrues_moratory_interest") else 0.0
            moratory_pct = (0.09 / 365.0) * days_sim if t_def.get("accrues_moratory_interest") else 0.0
            npv_ratio = (payoff_sim / discount_sim) - legal_cost_pct + moratory_pct

            # Función de Utilidad Multi-Atributo Normalizada (0 a 1)
            time_penalty = min(1.0, days_sim / 90.0)
            utility = (
                w_cash * min(1.0, max(0.0, npv_ratio)) +
                w_rel * min(1.0, retention_sim) -
                w_time * time_penalty -
                w_fric * min(1.0, friction_sim)
            )
            # Asegurar rango positivo
            utility = max(0.01, utility)

            # 3. Retropropagación (Backpropagation)
            selected.visits += 1
            selected.total_value += utility
            root.visits += 1

        # Construir resultados tipados con métricas financieras exactas
        evaluated_trajectories: List[NegotiationTrajectory] = []
        for t_def in cls.TRAJECTORY_DEFINITIONS:
            node = nodes_by_traj[t_def["id"]]
            avg_utility = round(node.value, 4)
            avg_days = int((t_def["days_min"] + t_def["days_max"]) / 2)
            is_lit = (t_def["id"] == "LITIGIO_AGRESIVO")

            fin_metrics = cls.calculate_trajectory_npv(
                claimable_amount=claimable,
                recovery_pct=t_def["recovery_pct"],
                duration_days=avg_days,
                wacc_annual_pct=wacc_annual_pct,
                is_litigation=is_lit,
                direct_legal_cost_override=direct_legal_cost_override
            )

            actions = cls._build_action_plan(t_def["id"])

            traj = NegotiationTrajectory(
                name=t_def["id"],
                display_title=t_def["title"],
                description=t_def["desc"],
                target_recovery_pct=t_def["recovery_pct"] * 100.0,
                expected_payoff=fin_metrics["nominal_recovered"],
                projected_duration_days=avg_days,
                relationship_retention_index=t_def["retention"],
                legal_friction_score=t_def["friction"],
                overall_utility_score=avg_utility,
                strategic_rationale=t_def["rationale"],
                action_steps=actions,
                npv_payoff=fin_metrics["npv_payoff"],
                capital_cost_drag=fin_metrics["capital_cost_drag"],
                wacc_annual_pct=fin_metrics["wacc_annual_pct"],
                dso_savings_days=fin_metrics["dso_savings_days"],
                direct_legal_cost=fin_metrics["direct_legal_cost"],
                expected_moratory_interest=fin_metrics["expected_moratory_interest"]
            )
            evaluated_trajectories.append(traj)

        # Elegir la mejor según mayor visitas o utilidad MCTS
        best_traj = max(evaluated_trajectories, key=lambda t: t.overall_utility_score)
        confidence = round(best_traj.overall_utility_score * 100.0, 1)

        wacc_display = float(wacc_annual_pct if wacc_annual_pct > 1.0 else wacc_annual_pct * 100.0)
        synthesis = (
            f"La simulación MCTS ({num_simulations} iteraciones, WACC {wacc_display:.1f}%, RHI {applied_rhi:.1f} pts) "
            f"determina que la trayectoria óptima es '{best_traj.display_title}' con un índice de utilidad de {best_traj.overall_utility_score:.3f}. "
            f"Proyecta una recuperación nominal de ${best_traj.expected_payoff:,.2f} USD ({best_traj.target_recovery_pct:.0f}%) "
            f"con un Valor Presente Neto (NPV) de ${best_traj.npv_payoff:,.2f} USD en {best_traj.projected_duration_days} días naturales "
            f"(ahorro de {best_traj.dso_savings_days} días de DSO), preservando la relación comercial en un {best_traj.relationship_retention_index*100:.0f}%."
        )

        return MCTSPlanResult(
            case_id=case_id,
            recommended_trajectory=best_traj.name,
            expected_net_payoff=best_traj.expected_payoff,
            projected_duration_days=best_traj.projected_duration_days,
            relationship_retention_index=best_traj.relationship_retention_index,
            confidence_score=confidence,
            total_simulations=num_simulations,
            trajectories_evaluated=evaluated_trajectories,
            executive_synthesis=synthesis,
            npv_payoff=best_traj.npv_payoff,
            capital_cost_drag=best_traj.capital_cost_drag,
            wacc_annual_pct=best_traj.wacc_annual_pct,
            dso_savings_days=best_traj.dso_savings_days,
            direct_legal_cost=best_traj.direct_legal_cost,
            expected_moratory_interest=best_traj.expected_moratory_interest,
            rhi_score_applied=applied_rhi,
            rhi_modulation_mode=rhi_modulation
        )

    @classmethod
    def _build_action_plan(cls, traj_id: str) -> List[str]:
        if traj_id == "LITIGIO_AGRESIVO":
            return [
                "1. Emitir Requerimiento Formal de Pago por conducto notarial o vía AS2 con plazo de 5 días hábiles.",
                "2. Adjuntar Dossier Pericial Foliado con transcripción de acuses EDI 997 y constancia de muelle.",
                "3. Iniciar solicitud de mediación formal ante el Centro de Arbitraje CANACO o ICC."
            ]
        elif traj_id == "PRESERVACION_RELACION":
            return [
                "1. Agendar mesa de trabajo ejecutiva con el Gerente de Compras del Retailer.",
                "2. Reconocer el porcentaje técnico de merma pactada (15%) a cambio de renovación de contrato marco.",
                "3. Obtener orden de compra subsecuente con incremento de volumen mínimo garantizado."
            ]
        else:  # LIQUIDACION_EXPRESS
            return [
                "1. Enviar propuesta de Convenio Transaccional con descuento pronto pago del 8%.",
                "2. Condicionar el beneficio a la dispersión de fondos vía transferencia SPEI en 5 días hábiles.",
                "3. Emitir Nota de Crédito fiscal complementaria una vez acreditado el depósito bancario."
            ]
