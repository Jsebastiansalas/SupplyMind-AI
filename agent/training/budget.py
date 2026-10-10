"""
agent/training/budget.py
Monitoreo Presupuestario y Control de Consumo de Tokens (R5).

Supervisa el gasto económico en USD por consumo de tokens con tarifas Grok 4.7,
aplica un circuit breaker / guardián previo a la inferencia y detiene la ejecución
de forma segura si se alcanza el tope presupuestario asignado.
"""

from typing import Any, Dict, Optional


RATE_INPUT_PER_1K: float = 0.002   # $0.002 USD por 1,000 tokens de entrada ($2.00 / 1M)
RATE_OUTPUT_PER_1K: float = 0.010  # $0.010 USD por 1,000 tokens de salida ($10.00 / 1M)


class BudgetExceededException(Exception):
    """Excepción lanzada cuando el consumo de tokens supera el presupuesto configurado."""

    def __init__(self, message: str = "Presupuesto máximo en USD alcanzado. Deteniendo ejecución."):
        super().__init__(message)
        self.message = message


class BudgetTracker:
    """
    Rastreador de consumo económico y de tokens.
    Permite fijar un tope presupuestario en USD, calcular costos exactos
    y verificar la viabilidad de llamadas a modelos de lenguaje antes de emitirlas.
    """

    def __init__(
        self,
        budget_limit_usd: float = 1.00,
        raise_on_exceeded: bool = False,
    ):
        self.budget_limit_usd: float = float(budget_limit_usd)
        self.raise_on_exceeded: bool = raise_on_exceeded
        self.total_spent_usd: float = 0.0
        self.total_tokens_in: int = 0
        self.total_tokens_out: int = 0

    def calc_cost(self, tokens_in: int, tokens_out: int) -> float:
        """Calcula el costo en USD para una cantidad de tokens dada."""
        cost_in = (tokens_in / 1000.0) * RATE_INPUT_PER_1K
        cost_out = (tokens_out / 1000.0) * RATE_OUTPUT_PER_1K
        return round(cost_in + cost_out, 6)

    def can_proceed(
        self,
        estimated_tokens_in: int = 1000,
        estimated_tokens_out: int = 1000,
    ) -> bool:
        """
        Verifica si queda saldo suficiente para realizar una llamada con la estimación provista.
        Si raise_on_exceeded está activo y el presupuesto se superaría, lanza BudgetExceededException.
        """
        # Si ya se alcanzó o superó el límite, no se puede continuar
        if self.total_spent_usd >= self.budget_limit_usd:
            if self.raise_on_exceeded:
                raise BudgetExceededException(
                    f"Tope presupuestario alcanzado: gastado ${self.total_spent_usd:.4f} USD "
                    f"de límite ${self.budget_limit_usd:.2f} USD."
                )
            return False

        worst_case_cost = self.calc_cost(estimated_tokens_in, estimated_tokens_out)
        projected = self.total_spent_usd + worst_case_cost
        if projected > self.budget_limit_usd:
            if self.raise_on_exceeded:
                raise BudgetExceededException(
                    f"Costo estimado (${worst_case_cost:.4f} USD) superaría el límite restante "
                    f"(${self.budget_remaining_usd:.4f} USD)."
                )
            return False

        return True

    def record_usage(self, tokens_in: int, tokens_out: int) -> float:
        """
        Registra el consumo real de tokens y acumula el costo en USD.
        """
        turn_cost = self.calc_cost(tokens_in, tokens_out)
        self.total_tokens_in += tokens_in
        self.total_tokens_out += tokens_out
        self.total_spent_usd = round(self.total_spent_usd + turn_cost, 6)

        if self.total_spent_usd > self.budget_limit_usd and self.raise_on_exceeded:
            raise BudgetExceededException(
                f"Consumo real acumulado (${self.total_spent_usd:.4f} USD) "
                f"superó el límite asignado (${self.budget_limit_usd:.2f} USD)."
            )

        return turn_cost

    @property
    def budget_remaining_usd(self) -> float:
        """Retorna el presupuesto restante en USD."""
        return max(0.0, round(self.budget_limit_usd - self.total_spent_usd, 6))

    @property
    def is_exhausted(self) -> bool:
        """Indica si el presupuesto se ha agotado por completo."""
        return self.total_spent_usd >= self.budget_limit_usd

    def summary(self) -> Dict[str, Any]:
        """Retorna un resumen estructurado del consumo presupuestario."""
        return {
            "budget_limit_usd": self.budget_limit_usd,
            "total_spent_usd": self.total_spent_usd,
            "budget_remaining_usd": self.budget_remaining_usd,
            "total_tokens_in": self.total_tokens_in,
            "total_tokens_out": self.total_tokens_out,
            "is_exhausted": self.is_exhausted,
        }

    def reset(self) -> None:
        """Reinicia los contadores de consumo."""
        self.total_spent_usd = 0.0
        self.total_tokens_in = 0
        self.total_tokens_out = 0
