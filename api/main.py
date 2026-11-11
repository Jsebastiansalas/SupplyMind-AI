"""
api/main.py
Servidor principal FastAPI para SupplyMind AI Enterprise.
"""

from pathlib import Path
from typing import Any, Dict, Optional
from fastapi import FastAPI, Body, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config.settings import settings
from agent.core.harness_adapter import HarnessAdapter
from api.routes import cases, tribunal, chat, documents, export, sandbox, telemetry, negotiation, erp, fx_leakage, precedents, adversarial, batch, edi, meta_cognition, fiscal, predictive_radar, portal_agent, vision_inspection, remittance

app = FastAPI(
    title="SupplyMind AI Enterprise API",
    description="API REST corporativa para conciliación autónoma de disputas B2B en cadenas de suministro.",
    version="2.0.0",
)

# Configuración CORS permisiva para desarrollo frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registro de Routers bajo prefijo /api
app.include_router(cases.router, prefix="/api")
app.include_router(tribunal.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(negotiation.router, prefix="/api")
app.include_router(negotiation.governance_router, prefix="/api")
app.include_router(erp.router, prefix="/api")
app.include_router(fx_leakage.router, prefix="/api")
app.include_router(documents.router, prefix="/api")
app.include_router(export.router, prefix="/api")
app.include_router(sandbox.router, prefix="/api")
app.include_router(telemetry.router, prefix="/api")
app.include_router(precedents.router, prefix="/api")
app.include_router(adversarial.router, prefix="/api")
app.include_router(batch.router, prefix="/api")
app.include_router(edi.router, prefix="/api")
app.include_router(meta_cognition.router, prefix="/api")
app.include_router(fiscal.router, prefix="/api")
app.include_router(predictive_radar.router, prefix="/api")
app.include_router(portal_agent.router, prefix="/api")
app.include_router(vision_inspection.router, prefix="/api")
app.include_router(remittance.router, prefix="/api")






@app.get("/api/health", tags=["Salud del Sistema"])
@app.get("/health", tags=["Salud del Sistema"])
def health_check():
    """Estado del sistema, motor determinístico y pasarela con Grok 4.7."""
    return {
        "status": "online",
        "version": "2.0.0",
        "gateway_url": settings.PLATICA_BASE_URL,
        "model_name": settings.MODEL_NAME,
        "live_api_ready": settings.is_live_api_ready,
        "deterministic_engine": "Decimal exact (IEEE 754 float-free)",
        "tribunal_magistrates": ["CFO (40 pts)", "Legal Counsel (30 pts)", "VP Operations (30 pts)"],
        "mastery_threshold": 90.0,
        "active_cases_dir": str(settings.DATA_DIR),
    }


@app.post("/api/evaluate", tags=["Evaluación Harness Platica"])
@app.post("/evaluate", tags=["Evaluación Harness Platica"])
def evaluate_harness_case(payload: Optional[Dict[str, Any]] = Body(default=None)):
    """
    Endpoint Universal de Evaluación para el Harness de Platica.
    Acepta:
    - `case_id` (ej. `"case_001"`, `"case_005_amazon_shortage"`)
    - `case_dir` o `input` (ruta a carpeta o archivo JSON local)
    - Documentos en línea (`invoice`, `purchase_order`, `delivery`, `payment`, `contract`)
    - O parámetros de disputa (`billed_amount`, `amount_paid`, `items`, `unauthorized_penalty`)
    """
    try:
        body = payload or {}
        fast_path = bool(body.get("fast_path", False))
        question = body.get("question") or body.get("prompt") or body.get("query")
        target: Any = body.get("input") or body.get("case_dir") or body.get("case_path")
        if not target:
            has_inline_docs = any(
                k in body
                for k in [
                    "invoice", "factura", "purchase_order", "delivery", "payment",
                    "contract", "items", "billed_amount", "unauthorized_penalty"
                ]
            )
            if has_inline_docs:
                target = body
            else:
                target = body.get("case_id", "case_001")
        return HarnessAdapter.evaluate(
            target=target,
            fast_path=fast_path,
            question=question,
            silent_stdout=True,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al evaluar caso en Harness: {str(e)}")


# Montaje de frontend/dist si ya fue compilado para servir en producción
dist_dir = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if not (dist_dir.exists() and dist_dir.is_dir()):
    dist_dir = Path("frontend/dist")

if dist_dir.exists() and dist_dir.is_dir():
    app.mount("/", StaticFiles(directory=str(dist_dir), html=True), name="frontend")

