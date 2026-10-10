"""
api/routes/chat.py
Endpoint conversacional en tiempo real conectado con Grok 4.7 y fallback determinístico inteligente.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from config.settings import settings
from agent.core.skynet_runner import SkynetRunner
from data.models import DisputeAnalysisReport

router = APIRouter(prefix="/cases", tags=["Chat con Agente"])


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str = Field(..., description="Pregunta del usuario")
    history: List[ChatMessage] = Field(default_factory=list, description="Historial previo")


@router.post("/{case_id}/chat")
def chat_with_agent(case_id: str, request: ChatRequest):
    """
    Envía una pregunta contextual al agente sobre el expediente seleccionado.
    Usa Grok 4.7 vía Platica Gateway o fallback determinístico senior.
    """
    case_path = Path("data/cases") / case_id
    if not case_path.exists():
        raise HTTPException(status_code=404, detail=f"Caso '{case_id}' no encontrado.")

    # 1. Obtener contexto de conciliación del caso
    runner = SkynetRunner(case_id=case_id, fast_path=True, use_cache=True)
    report: DisputeAnalysisReport = runner.run()

    prompt = request.message.strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="El mensaje no puede estar vacío.")

    # 2. Intentar llamar a Grok si la API está configurada
    if settings.is_live_api_ready:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=settings.RETO_KEY, base_url=settings.PLATICA_BASE_URL)

            context = f"""Eres SupplyMind AI Enterprise, analista digital senior de disputas comerciales B2B.
Acabas de auditar el expediente '{case_id}'.

DATOS VERIFICADOS CON PRECISIÓN MATEMÁTICA DECIMAL:
- Monto Facturado: ${report.billed_amount:,.2f} USD
- Monto Recibido: ${report.received_amount:,.2f} USD
- Diferencia Neta: ${report.difference:,.2f} USD
- Deducción Justificada: ${report.justified_amount:,.2f} USD
- Saldo Reclamable a Favor: ${report.claimable_amount:,.2f} USD
- Causa Raíz: {report.root_cause}
- Evidencias: {'; '.join(report.evidence)}
- Acción Recomendada: {report.recommended_action}

DIRECTRICES:
1. Responde con precisión quirúrgica basándote ÚNICAMENTE en los datos anteriores.
2. Cita montos en dólares exactos y cláusulas contractuales aplicables.
3. Tono analítico, senior, objetivo y seguro."""

            messages = [{"role": "system", "content": context}]
            for h in request.history[-6:]:
                messages.append({"role": h.role, "content": h.content})
            messages.append({"role": "user", "content": prompt})

            response = client.chat.completions.create(
                model=settings.MODEL_NAME,
                messages=messages,
                temperature=0.2,
                max_tokens=400,
            )
            bot_reply = response.choices[0].message.content
            return {"reply": bot_reply, "mode": "live", "model": settings.MODEL_NAME}
        except Exception as e:
            # Fallback silencioso a motor local determinístico
            pass

    # 3. Fallback Determinístico Local Senior
    p_lower = prompt.lower()
    if "reclamar" in p_lower or "recuperar" in p_lower or "saldo" in p_lower or "cuánto" in p_lower:
        reply = (
            f"Conforme a la auditoría del expediente {case_id}, el saldo legítimamente reclamable "
            f"a favor de la compañía asciende a **${report.claimable_amount:,.2f} USD** "
            f"(de una retención total de ${report.difference:,.2f} USD, habiendo quedado justificados ${report.justified_amount:,.2f} USD)."
        )
    elif "causa" in p_lower or "por qué" in p_lower or "motivo" in p_lower or "origen" in p_lower:
        reply = f"**Causa Raíz Determinada:** {report.root_cause}"
    elif "cláusula" in p_lower or "contrato" in p_lower or "legal" in p_lower:
        ev_legal = [e for e in report.evidence if "cláusula" in e.lower() or "contractual" in e.lower()]
        ev_text = " y ".join(ev_legal) if ev_legal else "; ".join(report.evidence[:2])
        reply = f"El amparo jurídico contractual aplicable se fundamenta en: **{ev_text}**."
    elif "acción" in p_lower or "cartera" in p_lower or "hacer" in p_lower or "recomienda" in p_lower:
        reply = f"**Acción Operativa Recomendada:** {report.recommended_action}"
    else:
        reply = (
            f"El expediente **{case_id}** arroja una factura de ${report.billed_amount:,.2f} USD "
            f"frente a un pago de ${report.received_amount:,.2f} USD. "
            f"La causa raíz detectada es: {report.root_cause}. "
            f"Acción dictaminada: {report.recommended_action}."
        )

    return {"reply": reply, "mode": "deterministic_fallback", "model": "SupplyMind Deterministic"}
