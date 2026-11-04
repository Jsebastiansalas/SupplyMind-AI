"""
agent/guardrails/budget_guard.py
Fase 10 - Sprint 10.5: Guardarraíl Presupuestario y Telemetría de Costo Real (TaskBudgetGuard).

Resuelve el Eje D de la retroalimentación técnica:
1. Calibra el costo por tarea utilizando la telemetría real medida en Platica Gateway
   (USD $10.66 en 940 peticiones = $0.011340 USD promedio por petición).
2. Impone un tope estricto de presupuesto y llamadas por tarea para evitar que un bucle
   ReAct o un prompt extenso dispare el consumo por encima de lo permitido.
3. Si una tarea alcanza su límite presupuestario, corta las llamadas subsecuentes al LLM
   y fuerza el cierre determinístico seguro en Python ($0.00 costo adicional).
"""

from decimal import Decimal, ROUND_HALF_UP
import logging
import threading
from typing import Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

logger = logging.getLogger("supplymind.budget_guard")

# Telemetría histórica oficial reportada en la pasarela Platica Gateway
GATEWAY_HISTORICAL_TOTAL_USD = Decimal("10.66")
GATEWAY_HISTORICAL_SPEND_USD = GATEWAY_HISTORICAL_TOTAL_USD
GATEWAY_HISTORICAL_REQUESTS = 940
GATEWAY_MEASURED_AVG_COST_PER_REQUEST_USD = (
    GATEWAY_HISTORICAL_TOTAL_USD / Decimal(str(GATEWAY_HISTORICAL_REQUESTS))
).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)  # $0.011340 USD

# Tarifas por 1K tokens calibradas exactamente con la pasarela real
# (1,200 prompt tokens * $0.005 + 356 completion tokens * $0.015 = $0.011340 USD/req)
CALIBRATED_PROMPT_1K_USD = Decimal("0.005000")
CALIBRATED_COMPLETION_1K_USD = Decimal("0.015000")
MIN_GATEWAY_REQUEST_FLOOR_USD = Decimal("0.002500")

# Presupuesto máximo predeterminado por expediente/tarea ($0.10 USD ~= 6-8 llamadas reales a Grok)
DEFAULT_TASK_BUDGET_CAP_USD = Decimal("0.1000")
DEFAULT_MAX_LLM_CALLS_PER_TASK = 6


class BudgetExceededException(Exception):
    """Excepción emitida cuando una tarea intenta superar su presupuesto máximo asignado."""
    pass


class LLMCallRecord(BaseModel):
    """Registro individual de una llamada medida a Grok-4.7 en la pasarela."""
    call_index: int
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    measured_cost_usd: Decimal
    latency_ms: float = 0.0


class TaskBudgetSummary(BaseModel):
    """Resumen auditado del consumo económico real de una tarea o expediente."""
    task_id: str
    requests_count: int = 0
    max_requests_allowed: int = DEFAULT_MAX_LLM_CALLS_PER_TASK
    prompt_tokens_total: int = 0
    completion_tokens_total: int = 0
    total_tokens: int = 0
    measured_cost_usd: Decimal = Decimal("0.000000")
    gateway_baseline_equivalent_usd: Decimal = Decimal("0.000000")
    budget_cap_usd: Decimal = DEFAULT_TASK_BUDGET_CAP_USD
    budget_utilization_pct: float = 0.0
    status: str = "OK"  # "OK" | "WARNING_80_PCT" | "THROTTLED_CAP_REACHED"
    was_throttled: bool = False
    throttle_reason: Optional[str] = None
    calls_history: List[LLMCallRecord] = Field(default_factory=list)


class TaskBudgetGuard:
    """
    Controlador de presupuesto por tarea y contabilizador de costo real de pasarela.
    Seguro para hilos (Thread-safe).
    """

    _tasks: Dict[str, TaskBudgetSummary] = {}
    _lock = threading.RLock()

    @classmethod
    def calculate_call_cost_usd(cls, prompt_tokens: int, completion_tokens: int) -> Decimal:
        """
        Calcula el costo real en USD de una llamada individual a Grok-4.7.
        Si el servidor reporta 0 tokens (por omisión de cabeceras), aplica el costo
        promedio medido oficial de la pasarela ($0.011340 USD).
        """
        if prompt_tokens <= 0 and completion_tokens <= 0:
            return GATEWAY_MEASURED_AVG_COST_PER_REQUEST_USD

        cost_in = (Decimal(str(prompt_tokens)) / Decimal("1000")) * CALIBRATED_PROMPT_1K_USD
        cost_out = (Decimal(str(completion_tokens)) / Decimal("1000")) * CALIBRATED_COMPLETION_1K_USD
        raw_cost = cost_in + cost_out

        # Asegurar piso mínimo de pasarela y redondeo a 6 decimales
        final_cost = max(MIN_GATEWAY_REQUEST_FLOOR_USD, raw_cost)
        return final_cost.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)

    @classmethod
    def init_task(
        cls,
        task_id: str,
        budget_cap_usd: Optional[Decimal] = None,
        max_calls: Optional[int] = None,
        reset_if_exists: bool = False
    ) -> TaskBudgetSummary:
        """Inicializa o recupera el contenedor presupuestario de una tarea."""
        with cls._lock:
            if task_id not in cls._tasks or reset_if_exists:
                cls._tasks[task_id] = TaskBudgetSummary(
                    task_id=task_id,
                    budget_cap_usd=budget_cap_usd if budget_cap_usd is not None else DEFAULT_TASK_BUDGET_CAP_USD,
                    max_requests_allowed=max_calls if max_calls is not None else DEFAULT_MAX_LLM_CALLS_PER_TASK
                )
            return cls._tasks[task_id]

    @classmethod
    def can_make_request(cls, task_id: str) -> Tuple[bool, str]:
        """
        Verifica antes de invocar a Grok si la tarea tiene presupuesto y turnos disponibles.
        Retorna (permitido: bool, motivo: str).
        """
        with cls._lock:
            summary = cls.init_task(task_id)

            if summary.requests_count >= summary.max_requests_allowed:
                reason = (
                    f"[BUDGET GUARD] Límite de peticiones por tarea alcanzado "
                    f"({summary.requests_count}/{summary.max_requests_allowed}) en '{task_id}'. "
                    f"Cortando bucle LLM y delegando cierre a Python determinístico."
                )
                summary.was_throttled = True
                summary.status = "THROTTLED_CAP_REACHED"
                summary.throttle_reason = reason
                logger.warning(reason)
                return False, reason

            if summary.measured_cost_usd >= summary.budget_cap_usd:
                reason = (
                    f"[BUDGET GUARD] Tope presupuestario por tarea alcanzado "
                    f"(${summary.measured_cost_usd:.4f} / ${summary.budget_cap_usd:.4f} USD) en '{task_id}'. "
                    f"Bloqueando llamada adicional a Grok para evitar sobrecosto."
                )
                summary.was_throttled = True
                summary.status = "THROTTLED_CAP_REACHED"
                summary.throttle_reason = reason
                logger.warning(reason)
                return False, reason

            # Comprobar si el costo proyectado de una llamada más superaría drásticamente el tope
            projected = summary.measured_cost_usd + MIN_GATEWAY_REQUEST_FLOOR_USD
            if projected > summary.budget_cap_usd and summary.requests_count > 0:
                reason = (
                    f"[BUDGET GUARD] Presupuesto restante insuficiente "
                    f"(Gastado: ${summary.measured_cost_usd:.4f}, Tope: ${summary.budget_cap_usd:.4f} USD). "
                    f"Conmutando a resolución determinística."
                )
                summary.was_throttled = True
                summary.status = "THROTTLED_CAP_REACHED"
                summary.throttle_reason = reason
                logger.warning(reason)
                return False, reason

            return True, "Presupuesto disponible"

    @classmethod
    def record_request(
        cls,
        task_id: str,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        latency_ms: float = 0.0
    ) -> TaskBudgetSummary:
        """
        Registra el consumo real de una llamada completada a Grok y actualiza el estado del presupuesto.
        """
        with cls._lock:
            summary = cls.init_task(task_id)
            call_cost = cls.calculate_call_cost_usd(prompt_tokens, completion_tokens)

            summary.requests_count += 1
            summary.prompt_tokens_total += max(0, prompt_tokens)
            summary.completion_tokens_total += max(0, completion_tokens)
            summary.total_tokens = summary.prompt_tokens_total + summary.completion_tokens_total
            summary.measured_cost_usd = (summary.measured_cost_usd + call_cost).quantize(
                Decimal("0.000001"), rounding=ROUND_HALF_UP
            )
            summary.gateway_baseline_equivalent_usd = (
                Decimal(str(summary.requests_count)) * GATEWAY_MEASURED_AVG_COST_PER_REQUEST_USD
            ).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)

            if summary.budget_cap_usd > Decimal("0.00"):
                util = float((summary.measured_cost_usd / summary.budget_cap_usd) * Decimal("100.0"))
                summary.budget_utilization_pct = round(util, 2)
            else:
                summary.budget_utilization_pct = 100.0

            record = LLMCallRecord(
                call_index=summary.requests_count,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
                measured_cost_usd=call_cost,
                latency_ms=round(latency_ms, 2)
            )
            summary.calls_history.append(record)

            if summary.measured_cost_usd >= summary.budget_cap_usd or summary.requests_count >= summary.max_requests_allowed:
                summary.status = "THROTTLED_CAP_REACHED"
                summary.was_throttled = True
            elif summary.budget_utilization_pct >= 80.0:
                summary.status = "WARNING_80_PCT"
                logger.info(
                    f"[BUDGET WARNING] Tarea '{task_id}' al {summary.budget_utilization_pct}% "
                    f"de su presupuesto (${summary.measured_cost_usd:.4f}/${summary.budget_cap_usd:.4f} USD)."
                )
            else:
                summary.status = "OK"

            return summary

    @classmethod
    def configure_case(
        cls,
        case_id: str,
        budget_cap_usd: Optional[Decimal] = None,
        max_requests: Optional[int] = None
    ) -> TaskBudgetSummary:
        """Alias declarativo de init_task con reinicio para configurar un expediente."""
        return cls.init_task(
            task_id=case_id,
            budget_cap_usd=budget_cap_usd,
            max_calls=max_requests,
            reset_if_exists=True
        )

    @classmethod
    def can_invoke_llm(cls, case_id: str) -> bool:
        """Retorna True si la tarea aún puede realizar peticiones a Grok dentro de su presupuesto."""
        allowed, _ = cls.can_make_request(case_id)
        return allowed

    @classmethod
    def record_llm_call(
        cls,
        case_id: str,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        model: str = "grok-4.7",
        purpose: str = "react_step",
        latency_ms: float = 0.0
    ) -> TaskBudgetSummary:
        """Alias enriquecido de record_request."""
        return cls.record_request(
            task_id=case_id,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            latency_ms=latency_ms
        )

    @classmethod
    def get_summary(cls, task_id: str) -> TaskBudgetSummary:
        """Retorna el resumen presupuestario actual de la tarea."""
        with cls._lock:
            return cls.init_task(task_id)

    @classmethod
    def get_global_telemetry(cls) -> Dict[str, any]:
        """Consolida el consumo de todas las tareas ejecutadas en la sesión actual."""
        with cls._lock:
            total_reqs = sum(t.requests_count for t in cls._tasks.values())
            total_tokens_in = sum(t.prompt_tokens_total for t in cls._tasks.values())
            total_tokens_out = sum(t.completion_tokens_total for t in cls._tasks.values())
            total_cost = sum((t.measured_cost_usd for t in cls._tasks.values()), Decimal("0.000000"))
            throttled_tasks = sum(1 for t in cls._tasks.values() if t.was_throttled)

            return {
                "gateway_historical_reference": {
                    "total_spend_usd": float(GATEWAY_HISTORICAL_TOTAL_USD),
                    "total_requests": GATEWAY_HISTORICAL_REQUESTS,
                    "avg_cost_per_request_usd": float(GATEWAY_MEASURED_AVG_COST_PER_REQUEST_USD)
                },
                "session_metrics": {
                    "tasks_tracked": len(cls._tasks),
                    "total_requests": total_reqs,
                    "prompt_tokens": total_tokens_in,
                    "completion_tokens": total_tokens_out,
                    "total_tokens": total_tokens_in + total_tokens_out,
                    "measured_total_cost_usd": float(total_cost),
                    "avg_cost_per_task_usd": float(total_cost / Decimal(str(len(cls._tasks)))) if cls._tasks else 0.0,
                    "throttled_tasks_count": throttled_tasks
                },
                "session_total_requests": total_reqs,
                "session_measured_cost_usd": float(total_cost),
                "throttled_cases_count": throttled_tasks
            }

    @classmethod
    def get_global_session_telemetry(cls) -> Dict[str, any]:
        """Alias directo de get_global_telemetry."""
        return cls.get_global_telemetry()

    @classmethod
    def reset_all(cls) -> None:
        """Limpia los registros presupuestarios en memoria."""
        with cls._lock:
            cls._tasks.clear()
