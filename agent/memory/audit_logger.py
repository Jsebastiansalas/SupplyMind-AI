import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict
from config.settings import settings

class AuditStep(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    step_number: int
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    phase: str
    action_type: str  # "THOUGHT", "TOOL_CALL", "TOOL_OUTPUT", "FINAL_DECISION"
    name: str         # Nombre de la herramienta o etapa
    details: Dict[str, Any] = Field(default_factory=dict)
    rationale: Optional[str] = None

class AuditLogger:
    """
    Gestiona la trazabilidad y bitácora auditable de decisiones del agente SupplyMind AI.
    Cumple con el criterio de evaluación de trazabilidad y autonomía del Reto Platica.
    """
    def __init__(self, case_id: str):
        self.case_id = case_id
        self.steps: List[AuditStep] = []
        self._step_counter = 1
        
        # Asegurar directorio de logs
        settings.LOGS_DIR.mkdir(parents=True, exist_ok=True)
        safe_case_id = Path(case_id).name
        self.log_file = settings.LOGS_DIR / f"audit_trail_{safe_case_id}.jsonl"

    def log_step(
        self,
        phase: str,
        action_type: str,
        name: str,
        details: Dict[str, Any],
        rationale: Optional[str] = None
    ) -> AuditStep:
        step = AuditStep(
            step_number=self._step_counter,
            phase=phase,
            action_type=action_type,
            name=name,
            details=details,
            rationale=rationale
        )
        self.steps.append(step)
        self._step_counter += 1
        
        # Persistir en JSONL
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(step.model_dump_json() + "\n")
            
        return step

    def get_summary(self) -> List[Dict[str, Any]]:
        return [s.model_dump() for s in self.steps]
