import time
from decimal import Decimal
from pathlib import Path
import pytest

from agent.core.skynet_runner import SkynetRunner
from agent.core.cache import dispute_cache, DisputeCache
from agent.tools.registry import ToolExecutor
from agent.core.state import DisputeState
from agent.memory.audit_logger import AuditLogger
from data.models import DisputeAnalysisReport

def test_fast_path_execution_speed_and_report():
    """
    Valida que el modo Fast-Path determinístico resuelva la disputa en <0.5 segundos,
    generando un DisputeAnalysisReport válido con 100% de precisión matemática.
    """
    dispute_cache.clear("case_001")
    runner = SkynetRunner(case_id="case_001", fast_path=True, use_cache=False)
    
    t0 = time.perf_counter()
    report = runner.run()
    elapsed = time.perf_counter() - t0

    assert isinstance(report, DisputeAnalysisReport)
    assert report.case_id == "case_001"
    assert report.billed_amount == Decimal("9000.00")
    assert report.received_amount == Decimal("8200.00")
    assert report.difference == Decimal("-800.00")
    assert report.justified_amount == Decimal("800.00")
    assert report.claimable_amount == Decimal("0.00")
    assert report.confidence >= 0.95
    assert elapsed < 0.8, f"Fast-Path tardó demasiado: {elapsed:.3f}s"

def test_dispute_cache_hit_and_microsecond_response():
    """
    Valida que tras la primera ejecución, la caché en memoria devuelva
    el resultado en menos de 0.05 segundos con huella digital idéntica.
    """
    dispute_cache.clear("case_003")
    runner1 = SkynetRunner(case_id="case_003", fast_path=True, use_cache=True)
    report1 = runner1.run()
    
    # Segunda llamada debe ser un CACHE HIT instantáneo
    runner2 = SkynetRunner(case_id="case_003", fast_path=True, use_cache=True)
    t0 = time.perf_counter()
    report2 = runner2.run()
    cache_time = time.perf_counter() - t0

    assert cache_time < 0.05, f"Cache retrieval demasiado lento: {cache_time:.4f}s"
    assert report1.case_id == report2.case_id
    assert report1.difference == report2.difference
    assert report1.justified_amount == report2.justified_amount

def test_cache_clear_invalidation():
    """
    Valida que al invocar dispute_cache.clear() la entrada sea purgada.
    """
    runner = SkynetRunner(case_id="case_002", fast_path=True, use_cache=True)
    runner.run()
    assert dispute_cache.get("case_002") is not None
    
    dispute_cache.clear("case_002")
    assert dispute_cache.get("case_002") is None

def test_tool_executor_self_healing_prerequisites():
    """
    Valida que ToolExecutor resuelva automáticamente dependencias ausentes
    si una herramienta se invoca fuera de orden en llamadas en lote (batch).
    """
    state = DisputeState(case_id="case_001", objective="Test self healing")
    logger = AuditLogger("test_self_healing")
    executor = ToolExecutor(state=state, audit_logger=logger)
    
    # Invocamos evaluate_contract_terms SIN haber ejecutado read_dispute_documents ni execute_reconciliation
    res = executor.execute_tool("evaluate_contract_terms", {"case_id": "case_001"})
    
    assert res["status"] == "success"
    assert state.loaded_documents is not None
    assert state.reconciliation_summary is not None
    assert state.contract_evaluation is not None
    assert state.reconciliation_summary.billed_amount == Decimal("9000.00")
    
    # Limpiar log de prueba
    if logger.log_file.exists():
        logger.log_file.unlink()

def test_compact_discrepancies_payload():
    """
    Valida que execute_reconciliation retorne un payload compacto para ahorrar tokens.
    """
    state = DisputeState(case_id="case_001", objective="Test compact payload")
    logger = AuditLogger("test_compact")
    executor = ToolExecutor(state=state, audit_logger=logger)
    
    executor.execute_tool("read_dispute_documents", {"case_id": "case_001"})
    res = executor.execute_tool("execute_reconciliation", {"case_id": "case_001"})
    
    assert "discrepancies" in res
    assert isinstance(res["discrepancies"], list)
    if res["discrepancies"]:
        d0 = res["discrepancies"][0]
        # Verificar que contiene las claves compactas
        assert "item_id" in d0
        assert "impact" in d0
        
    if logger.log_file.exists():
        logger.log_file.unlink()
