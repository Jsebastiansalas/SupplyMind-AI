"""
api/routes/cases.py
Endpoints para catálogo, inspección y análisis autónomo de expedientes de disputa.
"""

from pathlib import Path
from decimal import Decimal
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from config.settings import settings
from agent.core.skynet_runner import SkynetRunner
from data.models import DisputeAnalysisReport

router = APIRouter(prefix="/cases", tags=["Casos de Disputa"])

CASES_DIR = Path("data/cases")


def _decimal_to_float(obj: Any) -> Any:
    """Convierte recursivamente Decimals a floats para serialización JSON segura."""
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, dict):
        return {k: _decimal_to_float(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_decimal_to_float(item) for item in obj]
    return obj


class AnalyzeRequest(BaseModel):
    fast_path: bool = Field(default=True, description="Usar motor determinístico acelerado (<1s)")
    use_cache: bool = Field(default=True, description="Usar caché en memoria si no hay cambios")


class CaseSummary(BaseModel):
    case_id: str
    display_name: str
    category: str
    description: str
    document_count: int
    has_pdf: bool
    has_images: bool
    has_ocr: bool


@router.get("", response_model=List[CaseSummary])
def list_cases():
    """Lista todos los expedientes de disputa disponibles clasificados por tipología."""
    if not CASES_DIR.exists():
        return []

    summaries = []
    
    # Metadatos amigables para casos conocidos
    meta_map = {
        "case_001": ("Caso 001 — Faltante Físico Básico", "Básico", "Faltante físico de $800 USD en PROD-002, 100% justificado en remisión DEL-9912."),
        "case_002": ("Caso 002 — Disputa Compleja Alta Cuantía", "Complejo", "Discrepancia de $16,500 USD: $12,500 reclamables por avería no probada y multa ilegal."),
        "case_003": ("Caso 003 — Discrepancia de Precio Unitario", "Precios", "Sobreprecio de $3,000 USD en factura vs PO pactada, Cláusula 3.1 inalterabilidad."),
        "case_004_enterprise": ("Caso 004 — Enterprise RAG & OCR", "Multimodal", "Expediente con contrato en Markdown y remisión escaneada."),
        "case_005_amazon_shortage": ("Caso 005 — Amazon Faltante Real (PDFs)", "Empresarial PDF", "Expediente nativo de Amazon con 5 PDFs vectoriales y deducción por faltante."),
        "case_006_walmart_otif_pricing": ("Caso 006 — Walmart OTIF & Pricing (PDFs)", "Empresarial PDF", "Penalizaciones por entrega a destiempo y discrepancia de precios."),
        "case_007_cisco_large_bundle": ("Caso 007 — Cisco Bundle $125k (PDFs Masivos)", "Empresarial PDF", "Infraestructura corporativa con documentos fiscales CFDI y remisión de Dallas."),
        "case_008_homedepot_damaged_scanned": ("Caso 008 — Home Depot Avería (OCR Escaneado)", "Visión OCR", "Remisión física escaneada con anotaciones manuscritas de patio y fotos de daños."),
        "test_corrupt_json": ("Prueba de Resiliencia — JSON Corrupto", "Pruebas de Estrés", "Expediente sintético con sintaxis JSON rota para validar la tolerancia a fallos del motor."),
        "test_bad_schema": ("Prueba de Resiliencia — Esquema Inválido", "Pruebas de Estrés", "Expediente con estructura y tipos de datos incompatibles para validar la verificación estricta de esquemas Pydantic."),
    }

    for path in sorted(CASES_DIR.iterdir()):
        if not path.is_dir() or path.name.startswith("."):
            continue

        cid = path.name
        docs = list(path.glob("*.*"))
        pdfs = [d for d in docs if d.suffix.lower() == ".pdf"]
        imgs = [d for d in docs if d.suffix.lower() in [".png", ".jpg", ".jpeg"]]
        
        has_pdf = len(pdfs) > 0
        has_images = len(imgs) > 0
        has_ocr = has_images or "ocr" in cid.lower() or "scanned" in cid.lower()

        if cid in meta_map:
            name, cat, desc = meta_map[cid]
        elif cid.startswith("adver_") or cid.startswith("case_adversarial"):
            name = f"Caso Adversarial: {cid}"
            cat = "Adversarial Sintético"
            desc = "Expediente sintético generado por la fábrica de estrés con ground truth estricto."
        else:
            name = f"Expediente: {cid}"
            cat = "General"
            desc = f"Expediente con {len(docs)} documentos adjuntos."

        summaries.append(CaseSummary(
            case_id=cid,
            display_name=name,
            category=cat,
            description=desc,
            document_count=len(docs),
            has_pdf=has_pdf,
            has_images=has_images,
            has_ocr=has_ocr,
        ))

    return summaries


@router.get("/{case_id}")
def get_case_details(case_id: str):
    """Obtiene los detalles y lista de documentos de un caso específico."""
    case_path = CASES_DIR / case_id
    if not case_path.exists() or not case_path.is_dir():
        raise HTTPException(status_code=404, detail=f"Caso '{case_id}' no encontrado.")

    files = []
    for f in sorted(case_path.glob("*.*")):
        files.append({
            "filename": f.name,
            "extension": f.suffix.lower(),
            "size_bytes": f.stat().st_size,
            "is_pdf": f.suffix.lower() == ".pdf",
            "is_image": f.suffix.lower() in [".png", ".jpg", ".jpeg"],
            "is_json": f.suffix.lower() == ".json",
            "is_text": f.suffix.lower() in [".md", ".txt"],
        })

    return {
        "case_id": case_id,
        "files_count": len(files),
        "files": files,
    }


@router.post("/{case_id}/analyze")
def analyze_case(case_id: str, request: AnalyzeRequest = AnalyzeRequest()):
    """Ejecuta el ciclo de resolución autónomo de la disputa comercial."""
    case_path = CASES_DIR / case_id
    if not case_path.exists() or not case_path.is_dir():
        raise HTTPException(status_code=404, detail=f"Caso '{case_id}' no encontrado.")

    try:
        runner = SkynetRunner(
            case_id=case_id,
            fast_path=request.fast_path,
            use_cache=request.use_cache,
        )
        report: Optional[DisputeAnalysisReport] = runner.run()

        if report is None:
            raise HTTPException(
                status_code=422,
                detail=f"El expediente '{case_id}' contiene archivos corruptos o ilegibles y no pudo ser conciliado."
            )

        # Serialización segura de datos numéricos Decimal
        raw_dict = report.model_dump()
        clean_dict = _decimal_to_float(raw_dict)
        clean_dict["execution_time_seconds"] = getattr(runner.state, "execution_time_seconds", 0.15)
        clean_dict["status"] = str(getattr(runner.state, "current_status", "COMPLETED"))

        return clean_dict
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en resolución del agente: {str(e)}")


@router.get("/{case_id}/tribunal")
def get_case_tribunal_scores(case_id: str):
    """Obtiene la evaluación del tribunal colegiado para el caso."""
    from api.routes.tribunal import evaluate_case_tribunal
    return evaluate_case_tribunal(case_id)

