"""
agent/planner/mcts_negotiator.py
Árbol de Decisión Monte Carlo Tree Search (MCTS) para Negociación Estratégica B2B.
Frontera 1 de Superinteligencia (Sprint 5.2).

Simula y evalúa probabilísticamente múltiples trayectorias de negociación frente a retailers:
- Trayectoria A: Litigio / Arbitraje Coactivo Agresivo (Máximo cobro en efectivo)
- Trayectoria B: Preservación de Relación Comercial (Alianza a largo plazo)
- Trayectoria C: Liquidación Express / Pronto Pago (Optimización de flujo de caja y DSO)
"""

from decimal import Decimal
import math
import random
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class NegotiationTrajectory(BaseModel):
    """Definición y métricas proyectadas de una ruta de negociación."""
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


class MCTSPlanResult(BaseModel):
    """Resultado del análisis y simulación MCTS para la toma de decisiones ejecutivas."""
    case_id: str
    recommended_trajectory: str
    expected_net_payoff: Decimal
    projected_duration_days: int
    relationship_retention_index: float
    confidence_score: float
    total_simulations: int
    trajectories_evaluated: List[NegotiationTrajectory]
    executive_synthesis: str


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
            "rationale": "Prioriza la recuperación integral del capital cuando la relación comercial ya está desgastada o la deducción es claramente ilegal y arbitraria."
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
            "rationale": "Recomendada cuando el retailer representa >15% de la facturación del proveedor y el costo de perder la cuenta supera el monto disputado."
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
            "rationale": "Óptima cuando la prioridad corporativa es el flujo de caja inmediato y la reducción drástica de días de cartera vencida (DSO)."
        }
    ]

    @classmethod
    def simulate_negotiation(
        cls,
        case_id: str,
        claimable_amount: Decimal,
        retailer_account_weight_pct: float = 20.0,
        supplier_cashflow_priority: str = "BALANCED",  # AGGRESSIVE, BALANCED, CASH_URGENT
        num_simulations: int = 500
    ) -> MCTSPlanResult:
        """
        Ejecuta el ciclo MCTS (Selección, Expansión, Simulación, Retropropagación)
        para determinar la trayectoria óptima.
        """
        claimable = max(Decimal("0.00"), claimable_amount)

        # Configurar ponderaciones según el perfil corporativo
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
        else:  # BALANCED
            # Si la cuenta pesa mucho (>25% de ventas), la retención se vuelve prioritaria
            if retailer_account_weight_pct > 25.0:
                w_cash = 0.35
                w_rel = 0.45
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

            # Función de Utilidad Multi-Atributo Normalizada (0 a 1)
            time_penalty = min(1.0, days_sim / 90.0)
            utility = (
                w_cash * min(1.0, payoff_sim) +
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

        # Construir resultados tipados
        evaluated_trajectories: List[NegotiationTrajectory] = []
        for t_def in cls.TRAJECTORY_DEFINITIONS:
            node = nodes_by_traj[t_def["id"]]
            avg_utility = round(node.value, 4)
            expected_pay = (claimable * Decimal(str(t_def["recovery_pct"]))).quantize(Decimal("0.01"))
            avg_days = int((t_def["days_min"] + t_def["days_max"]) / 2)

            actions = cls._build_action_plan(t_def["id"])

            traj = NegotiationTrajectory(
                name=t_def["id"],
                display_title=t_def["title"],
                description=t_def["desc"],
                target_recovery_pct=t_def["recovery_pct"] * 100.0,
                expected_payoff=expected_pay,
                projected_duration_days=avg_days,
                relationship_retention_index=t_def["retention"],
                legal_friction_score=t_def["friction"],
                overall_utility_score=avg_utility,
                strategic_rationale=t_def["rationale"],
                action_steps=actions
            )
            evaluated_trajectories.append(traj)

        # Elegir la mejor según mayor visitas o utilidad MCTS
        best_traj = max(evaluated_trajectories, key=lambda t: t.overall_utility_score)
        confidence = round(best_traj.overall_utility_score * 100.0, 1)

        synthesis = (
            f"La simulación MCTS ({num_simulations} iteraciones) determina que la trayectoria óptima es "
            f"'{best_traj.display_title}' con un índice de utilidad de {best_traj.overall_utility_score:.3f}. "
            f"Proyecta una recuperación de ${best_traj.expected_payoff:,.2f} USD ({best_traj.target_recovery_pct:.0f}%) "
            f"en aproximadamente {best_traj.projected_duration_days} días naturales, preservando la relación comercial "
            f"en un {best_traj.relationship_retention_index*100:.0f}%."
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
            executive_synthesis=synthesis
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
