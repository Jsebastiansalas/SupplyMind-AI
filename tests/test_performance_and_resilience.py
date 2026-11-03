"""
tests/test_performance_and_resilience.py
Fase 10 - Sprint 10.4: Pruebas de Rendimiento, Resiliencia, Caché OCR por SHA-256 y Circuit Breaker.

Valida:
1. Rendimiento y persistencia de OcrCache por hash SHA-256 (memoria + disco).
2. Hilo de ejecución con timeout estricto y degradación controlada ante cuelgues de OCR.
3. Máquina de estados del Circuit Breaker (CLOSED -> OPEN -> HALF_OPEN -> CLOSED).
4. Reducción de latencia de case_008_homedepot_damaged_scanned a < 1.0 s con $4,000.00 exacto.
5. Presupuesto de latencia fast-path (p95 < 1.0 s / caso sin caché de reportes).
"""

from decimal import Decimal
import json
from pathlib import Path
import time
from unittest.mock import patch, PropertyMock
import pytest

from agent.core.circuit_breaker import CircuitBreaker, CircuitState, CircuitBreakerOpenException
from agent.core.ocr_cache import OcrCache, DEFAULT_CACHE_DIR
from agent.core.skynet_runner import SkynetRunner
from data.models import DeliveryNote
from tools.ocr_engine.vision import OCREngine

ROOT_DIR = Path(__file__).resolve().parent.parent


def test_ocr_sha256_cache_persistence_and_speed(tmp_path):
    """Valida que OcrCache guarde en memoria y disco, recuperando en < 5ms."""
    try:
        OcrCache.set_cache_dir(tmp_path / "ocr_cache")

        test_content = b"DOCUMENTO DE PRUEBA DE AUDITORIA B2B - REMISION DE EMBARQUE"
        file_hash = OcrCache.compute_hash(test_content)

        # 1. Almacenar datos en caché
        sample_structured = {
            "delivery_id": "DEL-TEST-001",
            "po_reference": "PO-TEST-999",
            "delivery_date": "2026-04-10",
            "received_by": "Auditor Test",
            "warehouse_location": "CEDIS_NORTE",
            "signed": True,
            "discrepancy_reported": True,
            "items": [
                {
                    "item_id": "SKU-TEST-A",
                    "quantity_delivered": 100,
                    "quantity_received": 95,
                    "missing_quantity": 5,
                    "damaged_quantity": 0,
                    "notes": "Faltante en tarima 1"
                }
            ]
        }
        OcrCache.set(
            file_hash,
            text="Transcripción OCR simulada de alta fidelidad.",
            structured=sample_structured
        )

        # 2. Verificar existencia en disco
        disk_file = tmp_path / "ocr_cache" / f"{file_hash}.json"
        assert disk_file.exists(), "El archivo de caché no se persistió en disco"

        # 3. Medir velocidad de recuperación en memoria (< 5ms)
        t0 = time.time()
        retrieved_text = OcrCache.get_text(file_hash)
        t_elapsed = time.time() - t0
        assert t_elapsed < 0.005, f"La recuperación en memoria tardó demasiado: {t_elapsed:.4f}s"
        assert retrieved_text == "Transcripción OCR simulada de alta fidelidad."

        # 4. Limpiar memoria y validar recuperación desde disco
        OcrCache._memory_cache.clear()
        retrieved_structured = OcrCache.get_structured(file_hash)
        assert retrieved_structured is not None
        assert retrieved_structured["delivery_id"] == "DEL-TEST-001"
        assert DeliveryNote.model_validate(retrieved_structured).items[0].missing_quantity == 5
    finally:
        OcrCache.set_cache_dir(DEFAULT_CACHE_DIR)


def test_ocr_timeout_and_controlled_degradation():
    """Valida que un OCR colgado se interrumpa dentro del timeout y degrade con gracia."""
    from config.settings import Settings
    ocr = OCREngine(timeout=0.2)

    def slow_hung_vision():
        time.sleep(2.0)
        return "Respuesta tardía que nunca debe llegar"

    dummy_image_bytes = b"IMAGEN_CON_FALLA_SIMULADA_POR_LATENCIA_EXTREMA"

    t0 = time.time()
    with patch.object(Settings, "is_live_api_ready", new_callable=PropertyMock, return_value=True):
        with patch.object(ocr.circuit_breaker, "execute", side_effect=slow_hung_vision):
            text = ocr.transcribe_image(dummy_image_bytes, timeout=0.25)
    t_elapsed = time.time() - t0

    # Debe abortar en aproximadamente ~0.25-0.50 s, NO en 2.0 s
    assert t_elapsed < 0.8, f"El timeout no contuvo la ejecución a tiempo: {t_elapsed:.3f}s"
    assert isinstance(text, str)
    assert len(text) > 10, "La transcripción degradada no debe estar vacía"


def test_circuit_breaker_state_machine_and_recovery():
    """Valida las transiciones CLOSED -> OPEN -> HALF_OPEN -> CLOSED."""
    cb = CircuitBreaker(
        name="test_circuit",
        failure_threshold=2,
        recovery_timeout=0.2,
        max_retries=0
    )

    assert cb.state == CircuitState.CLOSED
    assert cb.can_attempt() is True

    # 1. Primer fallo
    cb.record_failure(ValueError("Error 1"))
    assert cb.state == CircuitState.CLOSED

    # 2. Segundo fallo -> Disparo a OPEN
    cb.record_failure(ValueError("Error 2"))
    assert cb.state == CircuitState.OPEN
    assert cb.can_attempt() is False

    # 3. Llamada en OPEN invoca fallback de inmediato (0ms)
    def dummy_fallback():
        return "FALLBACK_SUCCESS"

    t0 = time.time()
    res = cb.execute(lambda: 1 / 0, fallback=dummy_fallback)
    t_elapsed = time.time() - t0
    assert res == "FALLBACK_SUCCESS"
    assert t_elapsed < 0.005

    # 4. Esperar que expire el recovery_timeout (cooldown)
    time.sleep(0.25)
    assert cb.state == CircuitState.HALF_OPEN
    assert cb.can_attempt() is True

    # 5. Ejecución exitosa en prueba piloto restaura a CLOSED
    cb.record_success()
    assert cb.state == CircuitState.CLOSED


def test_case_008_homedepot_damaged_scanned_latency_and_accuracy():
    """Valida que case_008 se resuelva en < 1.0s sin caché de reporte y concilie $4,000.00 exactos."""
    t0 = time.time()
    rep = SkynetRunner(
        case_id="case_008_homedepot_damaged_scanned",
        fast_path=True,
        use_cache=False
    ).run()
    elapsed = time.time() - t0

    assert elapsed < 1.0, f"case_008 excedió el presupuesto de 1.0s: {elapsed:.3f}s"
    assert rep.claimable_amount == Decimal("4000.00"), f"Monto reclamable incorrecto: {rep.claimable_amount}"
    assert rep.case_id == "case_008_homedepot_damaged_scanned"


def test_fast_path_latency_budget_sample_cases():
    """Valida que el p95 de latencia en fast-path sin caché de reportes sea < 1.0s por caso."""
    sample_cases = [
        "case_001",
        "case_002",
        "case_005_amazon_shortage",
        "case_006_walmart_otif_pricing",
        "case_008_homedepot_damaged_scanned",
        "case_016_nestle_cuarentena_lab",
        "case_021_samsung_fx_variance"
    ]

    latencies = []
    for cid in sample_cases:
        t0 = time.time()
        rep = SkynetRunner(case_id=cid, fast_path=True, use_cache=False).run()
        dt = time.time() - t0
        latencies.append(dt)
        assert rep is not None

    latencies.sort()
    # Calcular percentil 95
    p95_index = int(len(latencies) * 0.95)
    p95_val = latencies[min(p95_index, len(latencies) - 1)]
    avg_val = sum(latencies) / len(latencies)

    print(f"\n[LATENCY STATS] Casos: {len(sample_cases)} | Promedio: {avg_val:.3f}s | p95: {p95_val:.3f}s | Máx: {latencies[-1]:.3f}s")
    assert p95_val < 1.0, f"El percentil 95 ({p95_val:.3f}s) supera el umbral de 1.0s"
    assert avg_val < 0.6, f"El promedio ({avg_val:.3f}s) supera el umbral de 0.6s"
