"""
agent/planner/cognitive_router.py
Fase 10 - Sprint 10.5: Enrutador Cognitivo Neuro-Simbólico (CognitiveRouter).

Resuelve el Eje B de la retroalimentación técnica:
Dota al agente de criterio autónomo para decidir cuándo ejecutar herramientas
determinísticas en Python (cálculo exacto Decimal, pólizas contables, archivos tabulares)
y cuándo invocar a Grok-4.7 (interpretación semántica de cláusulas ambiguas, correos no
estructurados, notas manuscritas de muelle y argumentación jurídica).
"""

from decimal import Decimal
from enum import Enum
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field

from config.settings import settings
from agent.guardrails.budget_guard import GATEWAY_MEASURED_AVG_COST_PER_REQUEST_USD

ROOT_DIR = Path(__file__).resolve().parent.parent.parent


class ExecutionEngineMode(str, Enum):
    SYMBOLIC_PYTHON = "SYMBOLIC_PYTHON"                # 100% Python Determinístico ($0.00 USD, <200ms)
    HYBRID_NEURO_SYMBOLIC = "HYBRID_NEURO_SYMBOLIC"    # Grok-4.7 (Semántica) + Python Tools (Cálculo Decimal)


# Subtareas que NUNCA deben resolverse con generación libre de tokens sino con Python puro
PYTHON_DETERMINISTIC_SUBTASKS = {
    "arithmetic_reconciliation",
    "double_entry_erp_ledger",
    "tax_vat_ieps_calculation",
    "sha256_integrity_check",
    "npv_discounting",
    "sku_fuzzy_matching",
    "sla_deadline_countdown"
}

# Subtareas que requieren comprensión semántica profunda de Grok-4.7
GROK_SEMANTIC_SUBTASKS = {
    "clause_ambiguity_resolution",
    "unstructured_email_extraction",
    "handwritten_dock_note_interpretation",
    "legal_claim_letter_drafting",
    "adversarial_counterargument",
    "interactive_natural_language_qa"
}

# Códigos de deducción estándar que el motor simbólico resuelve sin ambigüedad
STANDARD_CATALOG_DEDUCTION_CODES = {
    "SHORTAGE", "FALTANTE", "MISSING", "UNDELIVERED",
    "DAMAGED", "AVERIA", "MERMA", "ROTO", "BROKEN",
    "PRICE_DIFF", "PRECIO", "TARIFA", "OVERCHARGE",
    "EARLY_PAY", "PRONTO_PAGO", "DESCUENTO_FINANCIERO",
    "REBATE", "COOP", "VOLUME_DISCOUNT", "OTIF", "LATE_DELIVERY"
}


class RoutingDecision(BaseModel):
    """Dictamen de enrutamiento cognitivo emitido antes de procesar una tarea o expediente."""
    case_id: str
    task_type: str = "full_audit"
    mode: ExecutionEngineMode
    use_llm: bool
    complexity_score: float = Field(ge=0.0, le=1.0)
    triggers: List[str] = Field(default_factory=list)
    arithmetic_lock_active: bool = True
    estimated_cost_usd: Decimal = Decimal("0.000000")
    python_delegated_operations: List[str] = Field(default_factory=list)
    grok_delegated_operations: List[str] = Field(default_factory=list)
    rationale: str

    @property
    def python_symbolic_tasks(self) -> List[str]:
        return self.python_delegated_operations

    @property
    def grok_neural_tasks(self) -> List[str]:
        return self.grok_delegated_operations


class CognitiveRouter:
    """
    Orquestador de decisiones neuro-simbólicas.
    Evalúa la naturaleza de los documentos del expediente y la tarea solicitada
    para asignar cada responsabilidad al motor óptimo (Python vs. Grok-4.7).
    """

    @classmethod
    def _locate_case_dir(cls, case_id: Union[str, Path]) -> Optional[Path]:
        if isinstance(case_id, Path):
            if case_id.exists() and case_id.is_dir():
                return case_id
            case_id = str(case_id)
        candidates = [
            Path(case_id),
            settings.DATA_DIR / case_id,
            ROOT_DIR / "data" / "cases" / case_id,
            ROOT_DIR / "data" / "holdout_cases" / case_id,
            ROOT_DIR / "data" / "real_supply_chain_cases" / case_id,
        ]
        for c in candidates:
            if c.exists() and c.is_dir():
                return c
        return None

    @classmethod
    def evaluate_routing(
        cls,
        case_id: Union[str, Path],
        task_type: str = "full_audit",
        user_query: Optional[str] = None,
        interactive_query: Optional[str] = None,
        force_llm: bool = False,
        force_symbolic: bool = False
    ) -> RoutingDecision:
        """
        Analiza el expediente y determina si requiere invocación de Grok-4.7 o si puede
        resolverse íntegramente mediante el pipeline simbólico determinista en Python.
        """
        effective_query = user_query if user_query is not None else interactive_query
        case_id_str = case_id.name if isinstance(case_id, Path) else str(case_id)
        triggers: List[str] = []
        complexity = 0.10

        python_ops = [
            "read_dispute_documents",
            "execute_reconciliation (Decimal)",
            "calculate_double_entry_ledger",
            "verify_cryptographic_invariants"
        ]
        grok_ops: List[str] = []

        if force_symbolic:
            return RoutingDecision(
                case_id=case_id_str,
                task_type=task_type,
                mode=ExecutionEngineMode.SYMBOLIC_PYTHON,
                use_llm=False,
                complexity_score=0.10,
                triggers=["FORCED_SYMBOLIC_MODE"],
                arithmetic_lock_active=True,
                estimated_cost_usd=Decimal("0.000000"),
                python_delegated_operations=python_ops,
                grok_delegated_operations=[],
                rationale=(
                    "Ejecución simbólica determinística solicitada explícitamente. "
                    "Cálculo exacto en Python (Decimal) con costo $0.00 USD."
                )
            )

        # 1. Evaluar naturaleza de la tarea solicitada
        if task_type in ("interactive_qa", "negotiation_duel", "legal_argumentation", "clause_interpretation"):
            complexity += 0.45
            triggers.append(f"SEMANTIC_TASK:{task_type.upper()}")
            grok_ops.append(f"semantic_reasoning:{task_type}")

        if effective_query and len(effective_query.strip()) > 0:
            q_low = effective_query.lower()
            # Si la pregunta pide opinión legal, estrategia o explicación compleja
            if any(w in q_low for w in ["por que", "por qué", "quien tiene la razon", "quién tiene la razón", "estrategia", "argumento", "alegato", "arbitraje", "clausula", "cláusula", "negociar", "carta"]):
                complexity += 0.40
                triggers.append("NATURAL_LANGUAGE_LEGAL_INQUIRY")
                grok_ops.append("natural_language_explanation_and_strategy")

        # 2. Inspeccionar archivos físicos del expediente
        case_dir = cls._locate_case_dir(case_id)
        if case_dir:
            files = [f for f in case_dir.iterdir() if f.is_file() and f.name != "ground_truth.json"]
            exts = {f.suffix.lower() for f in files}

            # A) Archivos de texto libre, correos o contratos extensos en Markdown
            if ".txt" in exts or ".eml" in exts:
                complexity += 0.35
                triggers.append("UNSTRUCTURED_TEXT_OR_EMAIL_EVIDENCE")
                grok_ops.append("unstructured_evidence_synthesis")

            if ".md" in exts:
                for md_file in case_dir.glob("*.md"):
                    if md_file.stat().st_size > 3000:
                        complexity += 0.30
                        triggers.append("EXTENSIVE_UNSTRUCTURED_CONTRACT_MD")
                        grok_ops.append("rag_contract_clause_interpretation")

            # B) Imágenes escaneadas de muelle o fotografías
            if exts.intersection({".png", ".jpg", ".jpeg", ".webp"}):
                complexity += 0.25
                triggers.append("SCANNED_DOCK_IMAGE_EVIDENCE")
                grok_ops.append("multimodal_dock_stamp_verification")

            # C) Inspección de códigos de deducción y notas en payment.json si existe
            pay_json = case_dir / "payment.json"
            if pay_json.exists():
                try:
                    pay_data = json.loads(pay_json.read_text(encoding="utf-8", errors="replace"))
                    deductions = pay_data.get("deductions", [])
                    for ded in deductions:
                        code_str = str(ded.get("code", "")).upper()
                        desc_str = str(ded.get("description", "")).upper()
                        combined_ded = f"{code_str} {desc_str}"
                        # Verificar si el código es totalmente ajeno al catálogo estándar
                        if not any(std in combined_ded for std in STANDARD_CATALOG_DEDUCTION_CODES):
                            complexity += 0.30
                            triggers.append(f"ATYPICAL_DEDUCTION_CODE:{code_str or 'UNKNOWN'}")
                            grok_ops.append("atypical_deduction_semantic_classification")
                except Exception:
                    complexity += 0.25
                    triggers.append("MALFORMED_PAYMENT_SCHEMA")

            # D) Si todos los documentos son tabulares/estructurados (.json, .csv, .xlsx) sin disparadores semánticos
            if not triggers and exts.issubset({".json", ".csv", ".xlsx", ".xls", ".pdf"}):
                triggers.append("STRUCTURED_TABULAR_DOCUMENTS")
                triggers.append("TYPIFIED_CATALOG_DEDUCTIONS")

        if force_llm:
            complexity = max(complexity, 0.75)
            triggers.append("FORCED_NEURAL_EVALUATION")
            if not grok_ops:
                grok_ops.append("full_react_orchestration_and_legal_synthesis")

        complexity = min(1.0, round(complexity, 2))
        use_llm = complexity >= 0.35 or force_llm
        estimated_cost = (Decimal("2") * GATEWAY_MEASURED_AVG_COST_PER_REQUEST_USD) if use_llm else Decimal("0.000000")

        if use_llm:
            mode = ExecutionEngineMode.HYBRID_NEURO_SYMBOLIC
            rationale = (
                f"Enrutamiento Neuro-Simbólico activado (complejidad={complexity:.2f}, disparadores={triggers}). "
                f"Grok-4.7 asume la interpretación semántica y argumentación contractual ({grok_ops}), "
                f"mientras delega el 100% de las operaciones aritméticas y contables a herramientas Python ({python_ops})."
            )
        else:
            mode = ExecutionEngineMode.SYMBOLIC_PYTHON
            rationale = (
                f"Enrutamiento Simbólico Puro seleccionado (complejidad={complexity:.2f}, disparadores={triggers}). "
                f"Expediente estructurado con reglas contractuales determinísticas; resuelto por Python Tools "
                f"con precisión Decimal exacta ($0.00 MAE), latencia < 200ms y costo $0.00 USD."
            )

        return RoutingDecision(
            case_id=case_id_str,
            task_type=task_type,
            mode=mode,
            use_llm=use_llm,
            complexity_score=complexity,
            triggers=triggers,
            arithmetic_lock_active=True,
            estimated_cost_usd=estimated_cost,
            python_delegated_operations=python_ops,
            grok_delegated_operations=grok_ops,
            rationale=rationale
        )

    @classmethod
    def should_delegate_subtask_to_python(cls, subtask_name: str) -> bool:
        """
        Determina si una subtarea específica debe ejecutarse obligatoriamente en Python
        en lugar de permitir que el LLM la resuelva en texto.
        """
        norm = subtask_name.strip().lower()
        if norm in PYTHON_DETERMINISTIC_SUBTASKS:
            return True
        tokens = set(norm.replace("-", "_").split("_"))
        exact_tokens = {"math", "sum", "erp", "tax", "vat", "hash", "sha256", "decimal", "ledger", "catalog", "lookup"}
        if tokens.intersection(exact_tokens):
            return True
        if any(k in norm for k in ["calculate", "reconcil", "deduction_code", "double_entry"]):
            return True
        return False

    @classmethod
    def get_neuro_symbolic_system_directive(cls) -> str:
        """
        Directiva inyectada al System Prompt de Grok-4.7 para garantizar la separación
        de responsabilidades entre el modelo neuronal y las herramientas simbólicas.
        """
        return (
            "DIRECTIVA DE ARQUITECTURA NEURO-SIMBÓLICA (OBLIGATORIA):\n"
            "1. ROL DE GROK-4.7 (CEREBRO SEMÁNTICO): Tu función es interpretar cláusulas contractuales ambiguas, "
            "analizar notas de muelle no estructuradas, evaluar excusas comerciales y redactar dictámenes legales.\n"
            "2. ROL DE PYTHON TOOLS (MOTOR MATEMÁTICO): Tienes ESTRICTAMENTE PROHIBIDO realizar sumas, restas, "
            "multiplicaciones, cálculo de impuestos o saldos mentalmente. SIEMPRE debes invocar las herramientas "
            "'read_dispute_documents', 'execute_reconciliation' y 'evaluate_contract_terms' y tomar sus montos "
            "retornados en precisión Decimal como única fuente de verdad numérica.\n"
            "3. RECONOCIMIENTO DE LÍMITES: Si un documento carece de evidencia suficiente o presenta contradicciones "
            "insalvables, repórtalo explícitamente en lugar de suponer o inventar datos."
        )
