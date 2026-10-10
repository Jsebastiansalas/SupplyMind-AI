"""
agent/training/curriculum.py
Bucle de Calibración de Criterio y Aprendizaje por Curriculum (R4).

Gestiona la progresión en 5 niveles de dificultad (Tiers 1-5), genera casos adversariales,
ejecuta la conciliación a través de TrainingRunnerBridge y CollegiateTribunal,
y en caso de desviación o puntaje inferior al umbral de maestría (90.0/100),
extrae directivas de optimización, registra precedentes en la base de conocimiento
y re-evalúa al agente hasta alcanzar la maestría.
"""

from typing import Any, Dict, List, Optional, Tuple, Union
from decimal import Decimal

from agent.planner.precedents import PrecedentRegistry
from agent.training.budget import BudgetTracker
from agent.training.factory.case_synthesizer import AdversarialCaseSynthesizer
from agent.training.runner_bridge import TrainingRunnerBridge
from agent.training.tribunal.models import TribunalVerdict
from agent.training.tribunal.tribunal import CollegiateTribunal


class CurriculumCase:
    """Contenedor de caso sintético para aprendizaje curricular."""

    def __init__(
        self,
        case_id: str,
        case_docs: Dict[str, Any],
        ground_truth: Any,
        tier: int = 1,
    ):
        self.case_id = case_id
        self.case_docs = case_docs
        self.ground_truth = ground_truth
        self.tier = tier

    def __getitem__(self, key: str) -> Any:
        if key == "case_id":
            return self.case_id
        elif key in ("case_docs", "docs"):
            return self.case_docs
        elif key in ("ground_truth", "gt"):
            return self.ground_truth
        elif key == "tier":
            return self.tier
        elif key in self.case_docs:
            return self.case_docs[key]
        raise KeyError(key)

    def __iter__(self):
        yield self.case_docs
        yield self.ground_truth

    def get(self, key: str, default: Any = None) -> Any:
        try:
            return self[key]
        except KeyError:
            return default


class CurriculumManager:
    """
    Gestor de niveles curriculares de entrenamiento adversarial.
    Estructura la progresión pedagógica desde discrepancias básicas
    hasta litigios complejos multi-SKU.
    """

    TIER_DEFINITIONS: List[Dict[str, Any]] = [
        {
            "tier": 1,
            "name": "Tier 1: Basic Physical Shortage",
            "typology": "unsigned_pod",
            "complexity": "Faltante físico en entrega con remisión firmada o controvertida",
            "key_adversarial_edge": "Clean signed POD vs Unsigned POD",
            "mastery_criteria": "Score >= 90.0 (Aceptar deducción justa / Rechazar sin firma)",
        },
        {
            "tier": 2,
            "name": "Tier 2: Catalog Unit Price Mismatch",
            "typology": "price_precedence",
            "complexity": "Discrepancia de precio unitario facturado vs Orden de Compra pactada",
            "key_adversarial_edge": "PO Precedence Clause 3.1",
            "mastery_criteria": "Score >= 90.0 (Reconocer prelación de PO vs lista de precios)",
        },
        {
            "tier": 3,
            "name": "Tier 3: Unproven / Extemporaneous Damage",
            "typology": "extemporaneous_damage",
            "complexity": "Reclamo de avería fuera de la ventana perentoria de 48h o sin fotos",
            "key_adversarial_edge": "48h Notice Window Clause 5.1",
            "mastery_criteria": "Score >= 90.0 (Rechazar reclamo extemporáneo y exigir pago)",
        },
        {
            "tier": 4,
            "name": "Tier 4: Unilateral Administrative Fees",
            "typology": "administrative_penalties",
            "complexity": "Penalización unilateral del comprador por EDI/ASN sin adenda bilateral",
            "key_adversarial_edge": "Prohibited Penalty Clause 7.3",
            "mastery_criteria": "Score >= 90.0 (Invalidar cargo unilateral arbitrario)",
        },
        {
            "tier": 5,
            "name": "Tier 5: Multi-SKU Frontier Bundle",
            "typology": "compound_mixed",
            "complexity": "Expediente compuesto: faltante físico real, precio no pactado y penalización arbitraria",
            "key_adversarial_edge": "Mixed Resolution Split (Credit Note + Collection Letter)",
            "mastery_criteria": "Score >= 90.0 (Resolución dividida con exactitud de centavo)",
        },
    ]

    def __init__(self, synthesizer: Optional[AdversarialCaseSynthesizer] = None):
        self.synthesizer = synthesizer or AdversarialCaseSynthesizer()

    def get_available_tiers(self) -> List[Dict[str, Any]]:
        """Retorna la lista de los 5 niveles curriculares progresivos."""
        return list(self.TIER_DEFINITIONS)

    def get_tier_info(self, tier: int) -> Dict[str, Any]:
        """Retorna los metadatos de un nivel específico (1-5)."""
        idx = max(1, min(5, int(tier))) - 1
        return dict(self.TIER_DEFINITIONS[idx])

    def get_cases_for_tier(
        self,
        tier: int,
        count: int = 1,
    ) -> List[CurriculumCase]:
        """
        Genera casos sintéticos correspondientes a la complejidad del nivel solicitado
        utilizando AdversarialCaseSynthesizer.
        """
        tier_clamped = max(1, min(5, int(tier)))
        tier_meta = self.get_tier_info(tier_clamped)
        typology = tier_meta["typology"]

        cases: List[CurriculumCase] = []
        for i in range(1, count + 1):
            case_id = f"CURR-T{tier_clamped}-{i:03d}"
            docs, gt = self.synthesizer.generate_case(
                case_id=case_id,
                typology=typology,
                difficulty_level=tier_clamped,
            )
            cases.append(CurriculumCase(case_id=case_id, case_docs=docs, ground_truth=gt, tier=tier_clamped))

        return cases


class CurriculumTrainer:
    """
    Entrenador curricular de SupplyMind AI.
    Ejecuta el bucle continuo de resolución, evaluación colegiada y calibración de criterio:
    1. Resuelve el caso mediante TrainingRunnerBridge (Decimal determinístico).
    2. Audita el dictamen con CollegiateTribunal (CFO, Legal, Supply Chain).
    3. Si el puntaje es < 90.0:
       - Extrae directivas de optimización.
       - Registra los precedentes en PrecedentRegistry (data/precedents/precedents_kb.json).
       - Re-ejecuta la evaluación hasta alcanzar el umbral de maestría o límite de iteraciones.
    """

    def __init__(
        self,
        budget_tracker: Optional[BudgetTracker] = None,
        precedent_registry: Optional[PrecedentRegistry] = None,
        mastery_threshold: float = 90.0,
        max_calibration_iterations: int = 3,
    ):
        self.budget_tracker = budget_tracker or BudgetTracker()
        self.precedent_registry = precedent_registry or PrecedentRegistry()
        self.mastery_threshold = float(mastery_threshold)
        self.max_calibration_iterations = int(max_calibration_iterations)

        self.curriculum_manager = CurriculumManager()
        self.runner_bridge = TrainingRunnerBridge()
        self.tribunal = CollegiateTribunal()

    def train_case(
        self,
        case_id: str,
        case_docs: Dict[str, Any],
        ground_truth: Any,
        simulate: bool = True,
    ) -> Dict[str, Any]:
        """
        Ejecuta el ciclo de entrenamiento y calibración para un caso individual.
        Si la evaluación inicial no alcanza maestría (score < 90), itera calibrando
        criterios y registrando precedentes hasta lograr la maestría.
        """
        iteration = 0
        precedents_registered: List[Dict[str, Any]] = []
        final_verdict: Optional[TribunalVerdict] = None
        final_report: Optional[Any] = None

        while iteration < self.max_calibration_iterations:
            iteration += 1

            # 1. Control presupuestario previo a la ejecución
            if not simulate and not self.budget_tracker.can_proceed(estimated_tokens_in=1000, estimated_tokens_out=1000):
                break

            # 2. Ejecución de la conciliación determinística
            report = self.runner_bridge.run_case(
                case_docs=case_docs,
                ground_truth=ground_truth,
                simulate=simulate,
            )
            final_report = report

            if not simulate:
                # Registrar consumo de tokens de la inferencia
                self.budget_tracker.record_usage(tokens_in=1200, tokens_out=800)

            # 3. Auditoría colegiada por el tribunal
            contract = case_docs.get("contract")
            verdict = self.tribunal.evaluate_case(
                report=report,
                ground_truth=ground_truth,
                contract=contract,
            )
            final_verdict = verdict

            # 4. Verificación del umbral de maestría
            if verdict.total_score >= self.mastery_threshold:
                # Maestría alcanzada exitosamente
                break

            # 5. Calibración iterativa: extracción de directivas y registro de precedente
            dispute_type = str(getattr(ground_truth, "category", "DISPUTE_GENERAL"))
            directives = verdict.calibration_directives or verdict.deficiencies
            directive_str = (
                "; ".join(directives)
                if directives
                else f"Alinear resolución del caso {case_id} con la jerarquía probatoria y contrato."
            )
            ruling_str = (
                f"Dictamen Colegiado: Puntaje {verdict.total_score}/100. "
                f"CFO: {verdict.cfo_evaluation.score}/40, "
                f"Legal: {verdict.legal_evaluation.score}/30, "
                f"COO: {verdict.operations_evaluation.score}/30."
            )

            saved_prec = self.precedent_registry.register_precedent(
                case_id=case_id,
                dispute_type=dispute_type,
                ruling=ruling_str,
                directive=directive_str,
            )
            precedents_registered.append(saved_prec)

        total_score = final_verdict.total_score if final_verdict else 0.0
        passed = (total_score >= self.mastery_threshold)

        return {
            "case_id": case_id,
            "verdict": final_verdict,
            "report": final_report,
            "total_score": total_score,
            "passed_mastery": passed,
            "iterations": iteration,
            "precedents_registered": precedents_registered,
            "cfo_score": final_verdict.cfo_evaluation.score if final_verdict else 0.0,
            "legal_score": final_verdict.legal_evaluation.score if final_verdict else 0.0,
            "operations_score": final_verdict.operations_evaluation.score if final_verdict else 0.0,
        }

    def train_tier(
        self,
        tier: int,
        count: int = 1,
        simulate: bool = True,
    ) -> List[Dict[str, Any]]:
        """Ejecuta el entrenamiento para todos los casos de un nivel curricular."""
        cases = self.curriculum_manager.get_cases_for_tier(tier=tier, count=count)
        results: List[Dict[str, Any]] = []

        for case in cases:
            res = self.train_case(
                case_id=case.case_id,
                case_docs=case.case_docs,
                ground_truth=case.ground_truth,
                simulate=simulate,
            )
            results.append(res)

        return results

    def train_full_curriculum(
        self,
        cases_per_tier: int = 1,
        simulate: bool = True,
    ) -> Dict[str, Any]:
        """
        Ejecuta el recorrido completo de los 5 niveles del curriculum.
        """
        all_results: List[Dict[str, Any]] = []
        tier_summaries: List[Dict[str, Any]] = []

        for tier_def in self.curriculum_manager.get_available_tiers():
            t_num = tier_def["tier"]
            tier_res = self.train_tier(tier=t_num, count=cases_per_tier, simulate=simulate)
            all_results.extend(tier_res)

            avg_score = (
                sum(r["total_score"] for r in tier_res) / len(tier_res)
                if tier_res
                else 0.0
            )
            all_passed = all(r["passed_mastery"] for r in tier_res)

            tier_summaries.append({
                "tier": t_num,
                "name": tier_def["name"],
                "cases_evaluated": len(tier_res),
                "avg_score": round(avg_score, 2),
                "mastery_achieved": all_passed,
            })

        overall_avg = (
            sum(r["total_score"] for r in all_results) / len(all_results)
            if all_results
            else 0.0
        )
        total_passed = sum(1 for r in all_results if r["passed_mastery"])

        return {
            "total_cases": len(all_results),
            "passed_cases": total_passed,
            "overall_average_score": round(overall_avg, 2),
            "all_passed_mastery": total_passed == len(all_results),
            "tier_summaries": tier_summaries,
            "results": all_results,
            "budget_summary": self.budget_tracker.summary(),
        }
