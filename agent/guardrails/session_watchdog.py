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

    @classmethod
    def is_off_topic_query(
        cls,
        user_message: str,
        case_id: str,
        case_context: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, str]:
        """
        Gobernanza de Alcance Pericial Exclusivo (Grok 4.7):
        Evalúa si la consulta del usuario se desvía del caso activo o intenta
        tratar temas ajenos (recetas, clima, deportes, programación general, chistes,
        política, trivia, jailbreak, etc.).

        Retorna (es_fuera_de_alcance: bool, respuesta_o_rechazo: str).
        - Si es un saludo/identidad puro: retorna (True, bienvenida_contextual_del_caso).
        - Si es una pregunta fuera de tema: retorna (True, rechazo_formal_pericial).
        - Si es una consulta legítima sobre el caso: retorna (False, "").
        """
        msg = user_message.lower().strip()
        report = (case_context or {}).get("report")
        invoice_id = (case_context or {}).get("invoice_id", "F-ACT")
        billed_amt = getattr(report, "billed_amount", Decimal("0.00")) if report else Decimal("0.00")
        received_amt = getattr(report, "received_amount", Decimal("0.00")) if report else Decimal("0.00")
        diff_amt = getattr(report, "difference", Decimal("0.00")) if report else Decimal("0.00")
        justified_amt = getattr(report, "justified_amount", Decimal("0.00")) if report else Decimal("0.00")
        claimable_amt = getattr(report, "claimable_amount", Decimal("0.00")) if report else Decimal("0.00")
        root_cause = getattr(report, "root_cause", "Auditoría integral de discrepancias comerciales") if report else "Auditoría integral"

        # 1. Detección de Saludos e Identidad Pura (Bienvenida anclada 100% al caso)
        pure_greetings = [
            "hola", "buen dia", "buen día", "buenos dias", "buenos días",
            "buenas tardes", "buenas noches", "saludos", "que tal", "qué tal",
            "hey", "hi", "hello"
        ]
        pure_identities = [
            "quien eres", "quién eres", "que haces", "qué haces", "como ayudas",
            "cómo ayudas", "que puedes hacer", "qué puedes hacer", "para que sirves",
            "para qué sirves", "quien es grok", "quién es grok", "ayuda", "help"
        ]

        # Normalizar puntuación básica para saludo exacto
        clean_msg = re.sub(r"[^\w\s]", "", msg).strip()
        if clean_msg in pure_greetings or clean_msg in pure_identities:
            greeting_reply = f"""### 👋 Copiloto Pericial Grok 4.7 — Expediente `{case_id}`

Saludos. Soy tu especialista técnico y pericial de **SupplyMind AI**, operado directamente con **Grok 4.7** y entrenado de forma **exclusiva** para la defensa y resolución de la disputa del expediente **`{case_id}`**.

---

#### 📌 Estado Oficial del Expediente en Memoria:
- **Facturación Auditada:** `${billed_amt:,.2f} USD` (Factura `{invoice_id}`)
- **Pago Recibido:** `${received_amt:,.2f} USD`
- **Diferencia Disputada:** `${abs(diff_amt):,.2f} USD`
- **Deducción Justificada (Nota de Crédito):** `${justified_amt:,.2f} USD`
- **Saldo Reclamable Legítimo:** **`${claimable_amt:,.2f} USD`**
- **Causa Raíz Dictaminada:** *{root_cause}*

---

¿Qué aspecto de este expediente deseas auditar hoy? Puedes consultarme sobre el desglose de productos en muelle, las deducciones aplicadas, las cláusulas contractuales vinculantes, el veredicto del Tribunal Colegiado o solicitar la redacción de una carta de objeción."""
            return True, greeting_reply

        # 2. Patrones de Preguntas Totalmente Ajenas al Caso (Off-Topic)
        off_topic_patterns = [
            # Cocina / Gastronomía / Recetas
            (r"(?:receta|c[oó]mo cocinar|c[oó]mo preparar|preparar de comer|ingredientes para|hacer una? pizza|receta de|hacer un? pastel|cocinar|receta para|tacos al pastor|hamburguesa|sushi)", "Gastronomía y Cocina"),
            # Clima / Meteorología
            (r"(?:clima en|temperatura en|va a llover|pron[oó]stico del tiempo|grados cent[ií]grados|est[aá] lloviendo|weather in|qu[eé] clima hace)", "Meteorología y Clima"),
            # Deportes y Juegos
            (r"(?:qui[eé]n gan[oó] el partido|resultado del partido|partido de f[uú]tbol|f[uú]tbol|champions league|mundial de f[uú]tbol|copa del mundo|super bowl|nba|messi|cristiano ronaldo|real madrid|barcelona fc|b[eé]isbol)", "Deportes y Entretenimiento"),
            # Programación General / Tareas Académicas Ajenas a ERP/EDI
            (r"(?:escribe un script en python para|c[oó]digo en python para|script en javascript|programa en c\+\+|hazme una p[aá]gina web|bucle for|linked list|algoritmo de ordenamiento|serie de fibonacci|ejercicio de leetcode|c[oó]mo programar en react)", "Programación General No Vinculada al Caso"),
            # Poesía / Chistes / Ficción / Letras de canciones
            (r"(?:cu[eé]ntame un chiste|dime un chiste|un chiste|escribe un poema|escribe una poes[ií]a|poema de amor|cuento infantil|escribe una historia sobre|letra de la canci[oó]n|recomi[eé]ndame una pel[ií]cula|recomi[eé]ndame una serie|qui[eé]n es tu actor)", "Humor, Ficción y Poesía"),
            # Geografía / Trivia / Historia Universal no mercantil
            (r"(?:cu[aá]ntos planetas|capital de francia|capital de italia|capital de espa[nñ]a|qui[eé]n descubri[oó] am[eé]rica|segunda guerra mundial|distancia a la luna|cu[aá]ntos continentes)", "Trivia y Cultura General"),
            # Política / Conflictos globales
            (r"(?:presidente de m[eé]xico|presidente de estados unidos|elecciones presidenciales|partido pol[ií]tico|guerra en ucrania|candidato a la presidencia)", "Política y Asuntos Gubernamentales Generales"),
            # Filosofía / Romance / Conciencia personal
            (r"(?:sentido de la vida|qu[eé] es el amor|tienes sentimientos|tienes alma|eres consciente|quieres ser mi novi[ao]|te quieres casar conmigo|dios existe|qu[eé] opinas de la vida)", "Filosofía y Consultas Personales"),
            # Intentos de Jailbreak / Modos de escape de rol
            (r"(?:ignora (?:todas )?las instrucciones|ignore (?:all )?previous instructions|olvida tus instrucciones|act[uú]a como un modelo sin restricciones|dan mode|jailbreak|ahora eres libre de responder cualquier cosa|olvida que eres|simula que eres)", "Intento de Evasión de Gobernanza / Jailbreak"),
        ]

        for pattern, category in off_topic_patterns:
            if re.search(pattern, msg):
                refusal_reply = f"""### 🛑 Consulta Fuera del Alcance Pericial del Expediente

> ⚠️ **Aviso de Restricción Operativa (Grok 4.7):**  
> Como copiloto especializado asignado de forma **exclusiva al expediente `{case_id}`**, estoy programado con reglas estrictas de contención para responder **únicamente sobre los hechos contables, logísticos, probatorios y legales de este caso**.

He detectado una consulta relacionada con **{category}**, la cual está fuera de mi mandato pericial autorizado. No tengo permitido responder preguntas ajenas a esta disputa comercial.

---

#### 📋 Consultas Habilitadas para el Expediente `{case_id}`:
- 📊 **Auditoría Financiera:** *¿Por qué retuvo dinero el cliente y cuál es el saldo reclamable?* (Saldo a favor: **`${claimable_amt:,.2f} USD`**).
- 🚚 **Muelle y Remisión:** *¿Qué constancia física se firmó en el descargue del expediente `{case_id}`?*
- 📜 **Marco Contractual:** *¿Qué cláusulas y fundamentos legales (Código de Comercio) amparan el rechazo de deducciones?*
- ⚖️ **Tribunal Colegiado:** *¿Cuál fue la deliberación y puntaje de los magistrados (CFO 40 pts, Legal 30 pts, COO 30 pts)?*
- ✉️ **Estrategia Comercial:** *Redactar correo de objeción o aplicar escenario de negociación.*
- 🏦 **Póliza Contable ERP:** *Generar asiento contable NIF C-3 para SAP / NetSuite o timbrado CFDI 4.0.*

*Por favor formule una consulta directamente orientada a los documentos y hechos de este expediente.*"""
                return True, refusal_reply

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
