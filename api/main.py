"""
api/main.py
Servidor principal FastAPI para SupplyMind AI Enterprise.
"""

from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config.settings import settings
from api.routes import cases, tribunal, chat, documents, export, sandbox, telemetry, negotiation, erp, fx_leakage, precedents, adversarial, batch, edi, meta_cognition, fiscal, predictive_radar, portal_agent, vision_inspection

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






@app.get("/api/health", tags=["Salud del Sistema"])
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


# Montaje de frontend/dist si ya fue compilado para servir en producción
dist_dir = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if not (dist_dir.exists() and dist_dir.is_dir()):
    dist_dir = Path("frontend/dist")

if dist_dir.exists() and dist_dir.is_dir():
    app.mount("/", StaticFiles(directory=str(dist_dir), html=True), name="frontend")

