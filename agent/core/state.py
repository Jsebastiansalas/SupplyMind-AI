from enum import Enum
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict
from data.models import DisputeAnalysisReport, DocumentHealthAudit, WatchdogMetrics
from tools.reconciliation_engine.engine import ReconciliationSummary
from tools.contract_analyzer.rules import ContractEvaluationResult

class ProcessStatus(str, Enum):
    INITIALIZED = "INITIALIZED"
    PERCEIVING = "PERCEIVING"
    READING_DOCUMENTS = "READING_DOCUMENTS"
    RECONCILING = "RECONCILING"
    EVALUATING_CONTRACT = "EVALUATING_CONTRACT"
    SYNTHESIZING = "SYNTHESIZING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class DisputeState(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    case_id: str
    objective: str
    current_status: ProcessStatus = ProcessStatus.INITIALIZED
    
    # Memoria viva del proceso
    loaded_documents: Dict[str, Any] = Field(default_factory=dict)
    health_audit: Optional[DocumentHealthAudit] = None
    reconciliation_summary: Optional[ReconciliationSummary] = None
    contract_evaluation: Optional[ContractEvaluationResult] = None
    final_report: Optional[DisputeAnalysisReport] = None
    
    # Registro de error si ocurriera
    error_message: Optional[str] = None
    
    # Métricas de ejecución y unit economics
    tokens_in: int = 0
    tokens_out: int = 0
    estimated_cost_usd: float = 0.0
    execution_time_seconds: float = 0.0
    watchdog_metrics: Optional[WatchdogMetrics] = None

    # Ingesta Masiva Jerárquica y Map-Reduce (Fase 1)
    is_massive_scale: bool = False
    hierarchical_manifest: Optional[Any] = None
    synthetic_fingerprint: Optional[Any] = None
