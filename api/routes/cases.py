"""
api/routes/cases.py
Endpoints para catálogo, inspección, creación, carga y análisis autónomo de expedientes de disputa.
"""

import re
import json
import shutil
from pathlib import Path
from decimal import Decimal
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query, UploadFile, File, Form
from pydantic import BaseModel, Field

from config.settings import settings
from agent.core.skynet_runner import SkynetRunner
from data.models import DisputeAnalysisReport

router = APIRouter(prefix="/cases", tags=["Casos de Disputa"])

CASES_DIR = settings.DATA_DIR


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


class GuidedCaseItem(BaseModel):
    item_id: str = "PROD-001"
    description: str = "Producto Comercial"
    ordered_quantity: int = Field(default=100, ge=0)
    delivered_quantity: int = Field(default=90, ge=0)
    missing_quantity: int = Field(default=10, ge=0)
    damaged_quantity: int = Field(default=0, ge=0)
    agreed_unit_price: float = Field(default=50.0, ge=0)
    invoiced_unit_price: Optional[float] = Field(default=None, ge=0)


class GuidedCaseRequest(BaseModel):
    case_id: str = Field(..., description="ID del caso, ej: case_cliente_x")
    display_name: str = Field(default="Mi Caso de Disputa")
    category: str = Field(default="Personalizado")
    description: str = Field(default="Expediente creado por el usuario")
    vendor_id: str = Field(default="VEN-PROV-01")
    customer_id: str = Field(default="CUST-RETAIL-01")
    po_reference: str = Field(default="PO-9910")
    currency: str = Field(default="USD")
    items: List[GuidedCaseItem] = Field(default_factory=lambda: [GuidedCaseItem()])
    amount_paid: Optional[float] = None
    unauthorized_penalty: float = Field(default=0.0, ge=0)
    unauthorized_penalty_reason: str = Field(default="Penalización no estipulada")
    delivery_signed: bool = Field(default=True)
    days_to_claim: int = Field(default=15, ge=0)
    contract_tolerance: float = Field(default=0.0, ge=0)


# Cartera de élite activa (2 más exigentes + 2 reales)
ELITE_CASE_IDS = [
    "case_009_mega_retailer_dispute",  # Exigente 1: 40 SKUs ($385k)
    "case_007_cisco_large_bundle",     # Exigente 2: Cisco Infrastructure ($125k)
    "case_005_amazon_shortage",        # Real 1: Amazon Logistics ($48k)
    "case_006_walmart_otif_pricing",   # Real 2: Walmart OTIF ($64.5k)
]

# Metadatos amigables para casos conocidos
CASE_META_MAP = {
    "case_009_mega_retailer_dispute": ("Caso 009 — Mega Retailer 40 SKUs (Exigente)", "Exigente Multi-SKU", "Expediente corporativo masivo de $385,000 USD con 40 SKUs, faltante en muelle y multas no pactadas."),
    "case_007_cisco_large_bundle": ("Caso 007 — Cisco Bundle $125k (Exigente)", "Exigente PDF Masivo", "Infraestructura corporativa de alta cuantía con documentos fiscales CFDI y remisión de Dallas."),
    "case_005_amazon_shortage": ("Caso 005 — Amazon Faltante Real (Real)", "Real Empresarial", "Expediente nativo de Amazon con 5 PDFs vectoriales y deducción por faltante."),
    "case_006_walmart_otif_pricing": ("Caso 006 — Walmart OTIF & Pricing (Real)", "Real Empresarial", "Penalizaciones por entrega a destiempo y discrepancia de precios."),
    "case_001": ("Caso 001 — Faltante Físico Básico", "Básico", "Faltante físico de $800 USD en PROD-002, 100% justificado en remisión DEL-9912."),
    "case_002": ("Caso 002 — Disputa Compleja Alta Cuantía", "Complejo", "Discrepancia de $16,500 USD: $12,500 reclamables por avería no probada y multa ilegal."),
    "case_003": ("Caso 003 — Discrepancia de Precio Unitario", "Precios", "Sobreprecio de $3,000 USD en factura vs PO pactada, Cláusula 3.1 inalterabilidad."),
    "case_004_enterprise": ("Caso 004 — Enterprise RAG & OCR", "Multimodal", "Expediente con contrato en Markdown y remisión escaneada."),
    "case_008_homedepot_damaged_scanned": ("Caso 008 — Home Depot Avería (OCR Escaneado)", "Visión OCR", "Remisión física escaneada con anotaciones manuscritas de patio y fotos de daños."),
}


@router.get("", response_model=List[CaseSummary])
def list_cases(elite_only: bool = Query(False, description="Filtrar exclusivamente la cartera élite de 4 casos")):
    """Lista los expedientes de disputa disponibles priorizando la cartera activa de élite al inicio."""
    if not CASES_DIR.exists():
        return []

    summaries = []
    
    if elite_only:
        target_dirs = [CASES_DIR / cid for cid in ELITE_CASE_IDS if (CASES_DIR / cid).exists()]
    else:
        # Priorizar siempre los 4 casos de élite al inicio del catálogo
        all_dirs = [p for p in sorted(CASES_DIR.iterdir()) if p.is_dir()]
        elite_set = set(ELITE_CASE_IDS)
        target_dirs = [CASES_DIR / cid for cid in ELITE_CASE_IDS if (CASES_DIR / cid).exists()]
        target_dirs += [p for p in all_dirs if p.name not in elite_set]

    for path in target_dirs:
        if not path.is_dir() or path.name.startswith("."):
            continue

        cid = path.name
        docs = list(path.glob("*.*"))
        pdfs = [d for d in docs if d.suffix.lower() == ".pdf"]
        imgs = [d for d in docs if d.suffix.lower() in [".png", ".jpg", ".jpeg", ".webp"]]
        
        has_pdf = len(pdfs) > 0
        has_images = len(imgs) > 0
        has_ocr = has_images or "ocr" in cid.lower() or "scanned" in cid.lower()

        meta_file = path / "meta.json"
        if meta_file.exists():
            try:
                with open(meta_file, "r", encoding="utf-8") as mf:
                    m = json.load(mf)
                    name = m.get("display_name", f"Expediente: {cid}")
                    cat = m.get("category", "Personalizado")
                    desc = m.get("description", f"Expediente con {len(docs)} documentos adjuntos.")
            except Exception:
                name = f"Expediente: {cid}"
                cat = "Personalizado"
                desc = f"Expediente con {len(docs)} documentos adjuntos."
        elif cid in CASE_META_MAP:
            name, cat, desc = CASE_META_MAP[cid]
        elif cid.startswith("adver_") or cid.startswith("case_adversarial"):
            name = f"Caso Adversarial: {cid}"
            cat = "Adversarial Sintético"
            desc = "Expediente sintético generado por la fábrica de estrés con ground truth estricto."
        else:
            name = f"Expediente: {cid}"
            cat = "Personalizado"
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
    """Obtiene los detalles, resumen inicial y lista de documentos de un caso específico."""
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
            "is_image": f.suffix.lower() in [".png", ".jpg", ".jpeg", ".webp"],
            "is_json": f.suffix.lower() == ".json",
            "is_text": f.suffix.lower() in [".md", ".txt"],
        })

    # Resumen y metadatos
    display_name = case_id.replace("_", " ").title()
    category = "General"
    description = f"Expediente con {len(files)} documentos adjuntos."

    meta_file = case_path / "meta.json"
    if meta_file.exists():
        try:
            with open(meta_file, "r", encoding="utf-8") as mf:
                m = json.load(mf)
                display_name = m.get("display_name", display_name)
                category = m.get("category", category)
                description = m.get("description", description)
        except Exception:
            pass
    elif case_id in CASE_META_MAP:
        display_name, category, description = CASE_META_MAP[case_id]

    # Clasificación preliminar de documentos
    from tools.document_reader.classifier import DocumentClassifier
    mapped_docs = {}
    try:
        mapped = DocumentClassifier.classify_and_map_case_directory(case_path)
        mapped_docs = {k: v.name for k, v in mapped.items()}
    except Exception:
        pass

    return {
        "case_id": case_id,
        "display_name": display_name,
        "category": category,
        "description": description,
        "files_count": len(files),
        "files": files,
        "mapped_documents": mapped_docs,
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

        # Enriquecimiento SKU y Caducidad
        def _to_dict(obj):
            if hasattr(obj, "model_dump"):
                return obj.model_dump()
            return obj if isinstance(obj, dict) else {}

        inv_d = _to_dict(runner.state.loaded_documents.get("invoice", {}))
        del_d = _to_dict(runner.state.loaded_documents.get("delivery", {}))
        po_d = _to_dict(runner.state.loaded_documents.get("purchase_order", {}))
        ctr_d = _to_dict(runner.state.loaded_documents.get("contract", {}))
        pay_d = _to_dict(runner.state.loaded_documents.get("payment", {}))

        if inv_d:
            try:
                from tools.sku_matcher import perform_sku_level_matching
                sku_res = perform_sku_level_matching(inv_d, del_d, po_d)
                clean_dict["sku_matching"] = _decimal_to_float(sku_res.model_dump())
            except Exception:
                pass

        try:
            from tools.notice_window_auditor import audit_notice_window
            window_res = audit_notice_window(del_d, pay_d, ctr_d)
            clean_dict["notice_window_audit"] = window_res.model_dump()
        except Exception:
            pass

        return clean_dict
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en resolución del agente: {str(e)}")


@router.get("/{case_id}/health")
def get_case_document_health(case_id: str, allow_imputation: bool = True):
    """
    Evalúa la integridad física y sintáctica de los documentos del caso,
    generando una auditoría de salud (DocumentHealthAudit) con score de 0 a 100.
    """
    case_path = CASES_DIR / case_id
    if not case_path.exists() or not case_path.is_dir():
        raise HTTPException(status_code=404, detail=f"Caso '{case_id}' no encontrado.")

    try:
        from tools.document_reader.reader import load_case_documents_with_health
        _, health_audit = load_case_documents_with_health(case_id, allow_imputation=allow_imputation)
        return health_audit.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al auditar salud de documentos: {str(e)}")


@router.get("/{case_id}/proof")
def get_case_financial_proof(case_id: str):
    """
    Obtiene la prueba criptográfica e invarianza matemática determinística (ZKP)
    para verificar que no existe ninguna alucinación financiera en el caso.
    """
    case_path = CASES_DIR / case_id
    if not case_path.exists() or not case_path.is_dir():
        raise HTTPException(status_code=404, detail=f"Caso '{case_id}' no encontrado.")

    try:
        runner = SkynetRunner(case_id=case_id, fast_path=True, use_cache=True)
        report = runner.run()
        if not report or not report.financial_proof:
            raise HTTPException(status_code=422, detail="No se pudo generar prueba de invarianza para este caso.")
        
        proof_obj = report.financial_proof
        proof_dict = proof_obj.model_dump() if hasattr(proof_obj, "model_dump") else proof_obj
        return _decimal_to_float(proof_dict)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al verificar prueba ZKP: {str(e)}")


@router.get("/{case_id}/evidence-manifest")
def get_case_evidence_manifest(case_id: str):
    """
    Obtiene el manifiesto de anclaje fáctico estricto (Pilar 3: Evidence Binding & Zero Uncited Claims)
    con el detalle de cada puntero probatorio acreditado y partidas cautelares.
    """
    case_path = CASES_DIR / case_id
    if not case_path.exists() or not case_path.is_dir():
        raise HTTPException(status_code=404, detail=f"Caso '{case_id}' no encontrado.")

    try:
        runner = SkynetRunner(case_id=case_id, fast_path=True, use_cache=True)
        report = runner.run()
        if not report or not report.evidence_manifest:
            raise HTTPException(status_code=422, detail="No se pudo compilar manifiesto de evidencia para este caso.")
        
        manifest_obj = report.evidence_manifest
        manifest_dict = manifest_obj.model_dump() if hasattr(manifest_obj, "model_dump") else manifest_obj
        return _decimal_to_float(manifest_dict)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al compilar manifiesto de anclaje probatorio: {str(e)}")


@router.get("/{case_id}/quarantine-docket")
def get_case_quarantine_docket(case_id: str):
    """
    Obtiene el expediente pericial de cuarentena forense (Pilar 4: Quarantine Protocol).
    Si el caso presenta inconsistencias críticas, retorna el detalle de bloqueos y remediación.
    """
    case_path = CASES_DIR / case_id
    if not case_path.exists() or not case_path.is_dir():
        raise HTTPException(status_code=404, detail=f"Caso '{case_id}' no encontrado.")

    try:
        runner = SkynetRunner(case_id=case_id, fast_path=True, use_cache=True)
        report = runner.run()

        docket = None
        if report and report.quarantine_docket:
            docket = report.quarantine_docket
        elif getattr(runner.state, "health_audit", None) and runner.state.health_audit.quarantine_docket:
            docket = runner.state.health_audit.quarantine_docket

        if docket:
            docket_dict = docket.model_dump() if hasattr(docket, "model_dump") else docket
            return {
                "status": "QUARANTINED",
                "is_settlement_blocked": True,
                "docket": _decimal_to_float(docket_dict)
            }
        else:
            return {
                "status": "NOT_QUARANTINED",
                "is_settlement_blocked": False,
                "case_id": case_id,
                "message": "El expediente cuenta con integridad admisible y no requiere aislamiento forense."
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al auditar cuarentena forense: {str(e)}")


@router.get("/{case_id}/tribunal")
def get_case_tribunal_scores(case_id: str):
    """Obtiene la evaluación del tribunal colegiado para el caso."""
    from api.routes.tribunal import evaluate_case_tribunal
    return evaluate_case_tribunal(case_id)


@router.post("/upload")
async def upload_case(
    case_id: str = Form(...),
    display_name: Optional[str] = Form(None),
    category: Optional[str] = Form("Personalizado"),
    description: Optional[str] = Form("Expediente subido por el usuario"),
    files: List[UploadFile] = File(...)
):
    """
    Permite al usuario subir archivos para un caso nuevo (PDFs, JSONs, imágenes de remisiones).
    Los archivos se guardan en data/cases/{case_id} y se registra su metadato en meta.json.
    """
    safe_id = re.sub(r'[^a-zA-Z0-9_\-]', '', case_id.strip().replace(" ", "_")).lower()
    if not safe_id:
        raise HTTPException(status_code=400, detail="El identificador del caso contiene caracteres inválidos.")
    if not safe_id.startswith("case_"):
        safe_id = f"case_{safe_id}"

    target_dir = CASES_DIR / safe_id
    target_dir.mkdir(parents=True, exist_ok=True)

    saved_files = []
    for file in files:
        if not file.filename:
            continue
        clean_filename = Path(file.filename).name
        dest = target_dir / clean_filename
        content = await file.read()
        with open(dest, "wb") as f:
            f.write(content)
        saved_files.append(clean_filename)

    meta = {
        "case_id": safe_id,
        "display_name": display_name or safe_id.replace("_", " ").title(),
        "category": category or "Personalizado",
        "description": description or f"Expediente con {len(saved_files)} documentos adjuntos.",
    }
    with open(target_dir / "meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)

    return {
        "status": "success",
        "case_id": safe_id,
        "display_name": meta["display_name"],
        "files_saved": saved_files,
        "message": f"Caso '{safe_id}' cargado exitosamente con {len(saved_files)} documentos."
    }


@router.post("/create-guided")
def create_guided_case(req: GuidedCaseRequest):
    """
    Crea un caso completo estructurando automáticamente los 5 documentos comerciales
    (invoice.json, purchase_order.json, delivery.json, payment.json, contract.json)
    a partir de especificaciones ingresadas por el usuario.
    """
    safe_id = re.sub(r'[^a-zA-Z0-9_\-]', '', req.case_id.strip().replace(" ", "_")).lower()
    if not safe_id:
        raise HTTPException(status_code=400, detail="ID de caso inválido.")
    if not safe_id.startswith("case_"):
        safe_id = f"case_{safe_id}"

    target_dir = CASES_DIR / safe_id
    target_dir.mkdir(parents=True, exist_ok=True)

    po_items = []
    inv_items = []
    del_items = []
    po_total = Decimal("0.00")
    inv_total = Decimal("0.00")
    total_missing_val = Decimal("0.00")
    total_damaged_val = Decimal("0.00")

    for it in req.items:
        agreed_price = Decimal(str(round(it.agreed_unit_price, 2)))
        inv_price = Decimal(str(round(it.invoiced_unit_price, 2))) if it.invoiced_unit_price is not None else agreed_price

        po_line_total = Decimal(it.ordered_quantity) * agreed_price
        po_total += po_line_total
        po_items.append({
            "item_id": it.item_id,
            "description": it.description,
            "ordered_quantity": it.ordered_quantity,
            "agreed_unit_price": float(agreed_price),
            "total_price": float(po_line_total),
        })

        inv_line_total = Decimal(it.ordered_quantity) * inv_price
        inv_total += inv_line_total
        inv_items.append({
            "item_id": it.item_id,
            "description": it.description,
            "quantity": it.ordered_quantity,
            "unit_price": float(inv_price),
            "total_price": float(inv_line_total),
        })

        del_items.append({
            "item_id": it.item_id,
            "quantity_delivered": it.ordered_quantity,
            "quantity_received": it.delivered_quantity,
            "missing_quantity": it.missing_quantity,
            "damaged_quantity": it.damaged_quantity,
            "notes": "Entrega con faltante verificado en muelle" if (it.missing_quantity > 0 or it.damaged_quantity > 0) else "Entrega conforme"
        })

        total_missing_val += Decimal(it.missing_quantity) * inv_price
        total_damaged_val += Decimal(it.damaged_quantity) * inv_price

    deductions = []
    short_code = safe_id.replace("case_", "")[:6].upper() or "GEN"
    if total_missing_val > Decimal("0.00"):
        deductions.append({
            "code": "DED-FALTANTE",
            "reason": f"Deducción por faltante físico en recepción s/ remisión DEL-{short_code}",
            "amount": float(total_missing_val),
            "reference_doc": f"DEL-{short_code}"
        })
    if total_damaged_val > Decimal("0.00"):
        deductions.append({
            "code": "DED-AVARIA",
            "reason": "Deducción por avería reportada en recepción",
            "amount": float(total_damaged_val),
            "reference_doc": f"DEL-{short_code}"
        })
    if req.unauthorized_penalty > 0:
        deductions.append({
            "code": "DED-PENALTY",
            "reason": req.unauthorized_penalty_reason,
            "amount": float(round(req.unauthorized_penalty, 2)),
            "reference_doc": "AVISO-RETENCION"
        })

    total_deductions = sum(Decimal(str(d["amount"])) for d in deductions)
    if req.amount_paid is not None:
        actual_paid = Decimal(str(round(req.amount_paid, 2)))
    else:
        actual_paid = max(Decimal("0.00"), inv_total - total_deductions)

    invoice_doc = {
        "invoice_id": f"INV-{short_code}-101",
        "vendor_id": req.vendor_id,
        "customer_id": req.customer_id,
        "po_reference": req.po_reference,
        "issue_date": "2026-09-01",
        "currency": req.currency,
        "items": inv_items,
        "subtotal": float(inv_total),
        "tax": 0.00,
        "total_amount": float(inv_total),
    }

    po_doc = {
        "po_id": req.po_reference,
        "vendor_id": req.vendor_id,
        "customer_id": req.customer_id,
        "order_date": "2026-08-25",
        "currency": req.currency,
        "items": po_items,
        "total_amount": float(po_total),
    }

    delivery_doc = {
        "delivery_id": f"DEL-{short_code}",
        "po_reference": req.po_reference,
        "delivery_date": "2026-09-03",
        "received_by": "Jefe de Almacén Central",
        "warehouse_location": "Centro de Distribución Muelle Principal",
        "signed": req.delivery_signed,
        "discrepancy_reported": bool(total_missing_val > 0 or total_damaged_val > 0),
        "items": del_items,
    }

    payment_doc = {
        "payment_id": f"PAY-{short_code}",
        "invoice_reference": invoice_doc["invoice_id"],
        "payment_date": "2026-09-25",
        "currency": req.currency,
        "amount_paid": float(actual_paid),
        "deductions": deductions,
    }

    contract_doc = {
        "contract_id": f"CTR-{short_code}-2026",
        "vendor_id": req.vendor_id,
        "customer_id": req.customer_id,
        "valid_from": "2026-01-01",
        "valid_to": "2026-12-31",
        "clauses": [
            {
                "clause_id": "CLAUSE-3.1",
                "title": "Condiciones de Precios",
                "text": "Los precios pactados en la Orden de Compra son inalterables sin previa autorización escrita.",
                "policy": "STRICT_MATCH",
                "tolerance_percentage": float(req.contract_tolerance),
            },
            {
                "clause_id": "CLAUSE-4.2",
                "title": "Faltantes Físicos",
                "text": "Las deducciones por faltante físico solo son procedentes si constan en remisión firmada con sello de discrepancia en muelle.",
                "policy": "DEDUCTION_ALLOWED_ON_SIGNED_DISCREPANCY",
                "tolerance_percentage": 0.00,
            },
            {
                "clause_id": "CLAUSE-8.2",
                "title": "Ventana de Notificación y Pago",
                "text": "Toda objeción o retención debe ser notificada dentro del plazo pactado tras la entrega.",
                "policy": "NET_30_DAYS",
                "tolerance_percentage": 0.00,
            }
        ]
    }

    with open(target_dir / "invoice.json", "w", encoding="utf-8") as f:
        json.dump(invoice_doc, f, indent=2, ensure_ascii=False)
    with open(target_dir / "purchase_order.json", "w", encoding="utf-8") as f:
        json.dump(po_doc, f, indent=2, ensure_ascii=False)
    with open(target_dir / "delivery.json", "w", encoding="utf-8") as f:
        json.dump(delivery_doc, f, indent=2, ensure_ascii=False)
    with open(target_dir / "payment.json", "w", encoding="utf-8") as f:
        json.dump(payment_doc, f, indent=2, ensure_ascii=False)
    with open(target_dir / "contract.json", "w", encoding="utf-8") as f:
        json.dump(contract_doc, f, indent=2, ensure_ascii=False)

    meta = {
        "case_id": safe_id,
        "display_name": req.display_name or safe_id.replace("_", " ").title(),
        "category": req.category,
        "description": req.description,
    }
    with open(target_dir / "meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)

    return {
        "status": "success",
        "case_id": safe_id,
        "display_name": meta["display_name"],
        "message": f"Caso '{safe_id}' generado exitosamente con sus 5 documentos comerciales verificados.",
    }


@router.delete("/{case_id}")
def delete_case(case_id: str):
    """Elimina un caso personalizado si no es uno de los casos del benchmark base."""
    protected = {
        "case_001", "case_002", "case_003", "case_004_enterprise",
        "case_005_amazon_shortage", "case_006_walmart_otif_pricing",
        "case_007_cisco_large_bundle", "case_008_homedepot_damaged_scanned",
        "test_corrupt_json", "test_bad_schema"
    }
    if case_id in protected:
        raise HTTPException(status_code=403, detail="No está permitido eliminar los casos protegidos del benchmark.")
    target_dir = CASES_DIR / case_id
    if not target_dir.exists() or not target_dir.is_dir():
        raise HTTPException(status_code=404, detail=f"Caso '{case_id}' no encontrado.")
    shutil.rmtree(target_dir)
    return {"status": "success", "message": f"Caso '{case_id}' eliminado exitosamente."}

