"""
agent/core/circuit_breaker.py
Fase 10 - Sprint 10.4: Patrón Circuit Breaker y Reintentos con Backoff Exponencial.

Protege las llamadas a APIs externas (Grok / Platica Gateway LLM y Visión Multimodal)
de caídas de red, cuelgues indefinidos y sobrecargas, garantizando una degradación
controlada hacia métodos determinísticos locales con cero latencia residual.
"""

from enum import Enum
import logging
import threading
import time
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger("supplymind.circuit_breaker")


class CircuitState(str, Enum):
    CLOSED = "CLOSED"          # Operación normal: las llamadas fluyen hacia la API
    OPEN = "OPEN"              # Circuito abierto: llamadas bloqueadas, fallback inmediato
    HALF_OPEN = "HALF_OPEN"    # Periodo de prueba: permite 1 llamada piloto para verificar recuperación


class CircuitBreakerOpenException(Exception):
    """Excepción lanzada cuando se intenta ejecutar una llamada con el circuito abierto."""
    pass


class CircuitBreaker:
    """
    Implementación segura para hilos del patrón Circuit Breaker con backoff exponencial.
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 3,
        recovery_timeout: float = 30.0,
        half_open_max_trials: int = 1,
        max_retries: int = 2,
        backoff_factor: float = 0.5
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_trials = half_open_max_trials
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor

        self._state = CircuitState.CLOSED
        self._consecutive_failures = 0
        self._last_failure_time = 0.0
        self._half_open_trials = 0
        self._lock = threading.RLock()

    @property
    def state(self) -> CircuitState:
        with self._lock:
            if self._state == CircuitState.OPEN:
                # Comprobar si ya expiró el tiempo de enfriamiento (cooldown)
                if (time.time() - self._last_failure_time) >= self.recovery_timeout:
                    self._state = CircuitState.HALF_OPEN
                    self._half_open_trials = 0
                    logger.info(f"[{self.name}] Enfriamiento cumplido. Transición OPEN -> HALF_OPEN (Prueba piloto).")
            return self._state

    def record_success(self) -> None:
        """Registra una ejecución exitosa y resetea el circuito a CLOSED."""
        with self._lock:
            prev_state = self._state
            self._consecutive_failures = 0
            self._half_open_trials = 0
            self._state = CircuitState.CLOSED
            if prev_state != CircuitState.CLOSED:
                logger.info(f"[{self.name}] Servicio recuperado. Transición {prev_state} -> CLOSED.")

    def record_failure(self, error: Optional[Exception] = None) -> None:
        """Registra una falla y actualiza el estado del circuito."""
        with self._lock:
            self._consecutive_failures += 1
            self._last_failure_time = time.time()
            logger.warning(
                f"[{self.name}] Fallo registrado ({self._consecutive_failures}/{self.failure_threshold}). "
                f"Error: {error or 'Unknown'}"
            )

            if self._state in (CircuitState.CLOSED, CircuitState.HALF_OPEN):
                if self._consecutive_failures >= self.failure_threshold or self._state == CircuitState.HALF_OPEN:
                    self._state = CircuitState.OPEN
                    logger.error(
                        f"[{self.name}] Umbral de fallos excedido. Circuito DISPARADO -> OPEN "
                        f"(Enfriamiento: {self.recovery_timeout}s)."
                    )

    def can_attempt(self) -> bool:
        """Verifica si se permite realizar una llamada externa en este instante."""
        curr_state = self.state
        if curr_state == CircuitState.CLOSED:
            return True
        if curr_state == CircuitState.HALF_OPEN:
            with self._lock:
                if self._half_open_trials < self.half_open_max_trials:
                    self._half_open_trials += 1
                    return True
                return False
        return False

    def execute(
        self,
        func: Callable[..., Any],
        *args: Any,
        fallback: Optional[Callable[..., Any]] = None,
        **kwargs: Any
    ) -> Any:
        """
        Ejecuta `func` con reintentos y protección de Circuit Breaker.
        Si el circuito está OPEN o se agotan los reintentos, invoca `fallback` o lanza excepción.
        """
        if not self.can_attempt():
            logger.warning(f"[{self.name}] Circuito {self._state}. Desvío inmediato al fallback.")
            if fallback is not None:
                return fallback(*args, **kwargs) if callable(fallback) else fallback
            raise CircuitBreakerOpenException(
                f"Circuito '{self.name}' se encuentra en estado {self._state}. Llamada bloqueada."
            )

        last_exc: Optional[Exception] = None
        for attempt in range(self.max_retries + 1):
            try:
                result = func(*args, **kwargs)
                self.record_success()
                return result
            except Exception as e:
                last_exc = e
                # Esperar antes del siguiente reintento si no es el último
                if attempt < self.max_retries:
                    sleep_time = self.backoff_factor * (2 ** attempt)
                    logger.info(f"[{self.name}] Reintento {attempt + 1}/{self.max_retries} en {sleep_time:.2f}s...")
                    time.sleep(sleep_time)

        # Si agotó todos los reintentos
        self.record_failure(last_exc)
        if fallback is not None:
            logger.warning(f"[{self.name}] Todos los intentos fallaron. Ejecutando fallback controlado.")
            return fallback(*args, **kwargs) if callable(fallback) else fallback
        raise last_exc or RuntimeError(f"Falla de ejecución en circuito {self.name}")

    def reset(self) -> None:
        """Fuerza el reseteo manual a estado CLOSED."""
        with self._lock:
            self._state = CircuitState.CLOSED
            self._consecutive_failures = 0
            self._half_open_trials = 0
            self._last_failure_time = 0.0


class CircuitBreakerRegistry:
    """Registro global centralizado de instancias CircuitBreaker por dominio."""

    _instances: Dict[str, CircuitBreaker] = {}
    _lock = threading.Lock()

    @classmethod
    def get(
        cls,
        name: str,
        failure_threshold: int = 3,
        recovery_timeout: float = 30.0,
        max_retries: int = 2,
        backoff_factor: float = 0.5
    ) -> CircuitBreaker:
        with cls._lock:
            if name not in cls._instances:
                cls._instances[name] = CircuitBreaker(
                    name=name,
                    failure_threshold=failure_threshold,
                    recovery_timeout=recovery_timeout,
                    max_retries=max_retries,
                    backoff_factor=backoff_factor
                )
            return cls._instances[name]

    @classmethod
    def reset_all(cls) -> None:
        with cls._lock:
            for cb in cls._instances.values():
                cb.reset()
