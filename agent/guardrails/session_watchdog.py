"""
agent/guardrails/session_watchdog.py
Pilar 5: Ancla de Estado Inmutable en el Chat & Watchdog de Ejecución ReAct.

Objetivo:
1. SessionAnchorManager: Mantener una tarjeta de contexto congelada e inmutable
   en cada turno de chat, detectando intentos adversariales de desorientación
   o distorsión de cifras contables e inyectando correcciones periciales instantáneas.
2. ReActExecutionWatchdog: Cortocircuitar bucles infinitos de razonamiento,
   deduplicar llamadas redundantes a herramientas y forzar síntesis ante
   agotamiento de presupuesto de pasos.
"""

from decimal import Decimal
from datetime import datetime, timezone
import hashlib
import json
import re
from typing import Dict, Any, List, Optional, Tuple

from data.models import (
    SessionStateAnchor,
    WatchdogMetrics,
    DisputeAnalysisReport,
    DocumentHealthAudit,
)
from agent.guardrails.arithmetic_verifier import extract_monetary_figures


class SessionAnchorManager:
    """
    Gestor del ancla de sesión inmutable para chats y consultas multi-turno.
    Asegura cero pérdida de contexto y neutraliza preguntas capciosas o manipuladoras.
    """

    @classmethod
    def build_session_anchor(
        cls,
        case_id: str,
        report: Optional[DisputeAnalysisReport] = None,
        health_audit: Optional[DocumentHealthAudit] = None,
    ) -> SessionStateAnchor:
        """Construye un ancla de estado inmutable a partir del expediente oficial."""
        from agent.core.skynet_runner import SkynetRunner

        # Si no se pasó reporte, recuperarlo de caché o ejecutar fast-path
        if report is None:
            runner = SkynetRunner(case_id=case_id, fast_path=True, use_cache=True)
            report = runner.run()

        audit = health_audit or (report.health_audit if isinstance(report.health_audit, DocumentHealthAudit) else None)
        h_status = getattr(audit, "status", "PRISTINE") if audit else "PRISTINE"
        h_score = float(getattr(audit, "health_score", 100.0)) if audit else 100.0
        is_quarantine = (h_status == "QUARANTINE") or bool(getattr(report, "quarantine_docket", None))

        proof = getattr(report, "financial_proof", None)
        p_hash = getattr(proof, "proof_hash", "") if proof else ""
        p_status = getattr(proof, "audit_status", "MATHEMATICALLY_PROVEN") if proof else "MATHEMATICALLY_PROVEN"

        manifest = getattr(report, "evidence_manifest", None)
        ev_ratio = float(getattr(manifest, "backing_ratio_pct", 100.0)) if manifest else 100.0

        return SessionStateAnchor(
            case_id=case_id,
            currency=report.currency if report else "USD",
            billed_amount=report.billed_amount if report else Decimal("0.00"),
            received_amount=report.received_amount if report else Decimal("0.00"),
            difference=report.difference if report else Decimal("0.00"),
            justified_amount=report.justified_amount if report else Decimal("0.00"),
            claimable_amount=report.claimable_amount if report else Decimal("0.00"),
            health_status=h_status,
            health_score=h_score,
            zkp_proof_hash=p_hash,
            zkp_status=p_status,
            is_quarantined=is_quarantine,
            evidence_backing_ratio=ev_ratio,
            anchored_at=datetime.now(timezone.utc).isoformat()
        )

    @classmethod
    def inspect_and_correct_adversarial_query(
        cls,
        user_message: str,
        anchor: SessionStateAnchor
    ) -> Tuple[bool, str]:
        """
        Inspecciona si el mensaje del usuario intenta sembrar datos falsos,
        alucinar montos o confundir al agente sobre las cifras del caso.
        Retorna (es_intento_adversarial, prefacio_correctivo_o_empty_str).
        """
        extracted = extract_monetary_figures(user_message)
        found_decimals: List[Decimal] = []
        for raw_str, val in extracted:
            found_decimals.append(val)

        # Buscar también números aislados >= 100 precedidos o seguidos por palabras contables
        bare_matches = re.findall(
            r"(?:factura|monto|total|pago|saldo|reclamo|acordado|dicho|\$)\s*(?:de\s*)?([0-9]{3,7}(?:\.[0-9]{1,2})?)",
            user_message,
            re.IGNORECASE
        )
        for num_s in bare_matches:
            try:
                found_decimals.append(Decimal(num_s))
            except Exception:
                pass

        valid_figures = {
            round(anchor.billed_amount, 2),
            round(anchor.received_amount, 2),
            round(abs(anchor.difference), 2),
            round(anchor.justified_amount, 2),
            round(anchor.claimable_amount, 2),
        }

        # Si el usuario menciona cifras no autorizadas y usa frases afirmativas de fijación
        suspicious_cues = [
            "facturaste", "facturado era", "factura era", "el total era", "eran $",
            "reclamamos $", "recibimos $", "diferencia de $", "el pago fue de",
            "recuerdo que", "dijiste que", "habías dicho", "habíamos acordado", "habias acordado"
        ]
        msg_lower = user_message.lower()
        has_suspicious_cue = any(cue in msg_lower for cue in suspicious_cues)

        for fig in found_decimals:
            # Si la cifra no está entre las cifras oficiales del expediente y es significativa (>100)
            if fig not in valid_figures and fig > Decimal("100.00"):
                if has_suspicious_cue or any(w in msg_lower for w in ["factur", "pag", "reclam", "total", "acord"]):
                    correction = (
                        f"### 🛡️ ANCLAJE DE GOBERNANZA ACTIVO (PILAR 5 - INMUTABILIDAD CONTABLE)\n\n"
                        f"> ⚠️ **DESVIACIÓN O MONTO NO AUTORIZADO DETECTADO (${fig:,.2f} USD)**\n\n"
                        f"De acuerdo con los documentos auditados del expediente `{anchor.case_id}` y su prueba aritmética ZKP:\n"
                        f"- **Facturado Oficial Inmutable:** `${anchor.billed_amount:,.2f} {anchor.currency}`\n"
                        f"- **Pago Recibido Oficial:** `${anchor.received_amount:,.2f} {anchor.currency}`\n"
                        f"- **Deducción Justificada:** `${anchor.justified_amount:,.2f} {anchor.currency}`\n"
                        f"- **Saldo Reclamable Legítimo:** `${anchor.claimable_amount:,.2f} {anchor.currency}`\n\n"
                        f"*El agente SupplyMind AI opera bajo registro inmutable en memoria; no es posible alterar o negociar cifras oficiales fuera de los documentos probatorios.*"
                    )
                    return True, correction

        return False, ""


class ReActExecutionWatchdog:
    """
    Vigilante de ejecución del bucle ReAct.
    Previene loops infinitos, llamadas redundantes con argumentos idénticos
    y paradas silenciosas por desbordamiento de contexto.
    """

    def __init__(
        self,
        max_total_calls: int = 12,
        max_duplicate_threshold: int = 2,
        max_step_budget: Optional[int] = None,
        max_duplicate_calls: Optional[int] = None,
    ):
        if max_step_budget is not None:
            max_total_calls = max_step_budget
        if max_duplicate_calls is not None:
            max_duplicate_threshold = max_duplicate_calls

        self.max_total_calls = max_total_calls
        self.max_duplicate_threshold = max_duplicate_threshold
        self.call_history: Dict[str, int] = {}
        self.metrics = WatchdogMetrics()

    def record_and_evaluate(self, tool_name: str, arguments: Dict[str, Any]) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Evalúa si la llamada a la herramienta está permitida o debe ser cortocircuitada.
        Retorna (permitida: bool, resultado_cortocircuito_o_none).
        """
        self.metrics.total_tool_calls += 1

        # Generar firma canónica de la llamada
        try:
            sorted_args = json.dumps(arguments, sort_keys=True, default=str)
        except Exception:
            sorted_args = str(arguments)

        call_sig = f"{tool_name}::{hashlib.sha256(sorted_args.encode()).hexdigest()[:12]}"
        prev_count = self.call_history.get(call_sig, 0)
        self.call_history[call_sig] = prev_count + 1
        self.metrics.unique_tool_calls = len(self.call_history)

        # 1. Chequeo de duplicidad redundante
        if self.call_history[call_sig] > self.max_duplicate_threshold:
            self.metrics.deduplicated_calls_count += 1
            self.metrics.circuit_breaker_triggered = True
            warn_msg = (
                f"CIRCUIT_BREAKER_TRIGGERED: Herramienta ya ejecutada {self.max_duplicate_threshold} veces "
                f"con idénticos argumentos ('{tool_name}'). Llamada interceptada para evitar bucle infinito."
            )
            self.metrics.warnings.append(warn_msg)
            return False, {
                "status": "CIRCUIT_BREAKER_TRIGGERED",
                "circuit_breaker": True,
                "message": warn_msg,
                "instruction": "No repitas esta consulta. Procede de inmediato a generar el informe final con los datos ya recolectados."
            }

        # 2. Chequeo de límite total de pasos
        if self.metrics.total_tool_calls > self.max_total_calls:
            self.metrics.circuit_breaker_triggered = True
            warn_msg = f"BUDGET_EXCEEDED: Presupuesto máximo de razonamiento alcanzado ({self.max_total_calls} pasos)."
            self.metrics.warnings.append(warn_msg)
            return False, {
                "status": "BUDGET_EXCEEDED",
                "circuit_breaker": True,
                "message": warn_msg,
                "instruction": "Sintetiza la respuesta inmediatamente invocando generate_final_report."
            }

        return True, None
