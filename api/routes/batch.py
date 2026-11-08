"""
api/routes/batch.py
Endpoints para Procesamiento Batch Masivo Desatendido (Semana 4 - Sprint 4.2).
"""

from pathlib import Path
import json
from typing import Optional, List, Dict, Any
import asyncio
import zipfile
from tools.batch_processor.rfc3161_timestamp import RFC3161TimestampSealer
from fastapi.responses import FileResponse
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query, WebSocket, WebSocketDisconnect
from tools.batch_processor.telemetry_ws import telemetry_broadcaster
from pydantic import BaseModel, Field

from tools.batch_processor.batch_runner import EnterpriseBatchProcessor
from tools.batch_processor.models import BatchExecutionSummary
from agent.core.portfolio_optimizer import WorkingCapitalPortfolioOptimizer, PortfolioOptimizationSummary
from tools.batch_processor.batch_analytics_visualizer import BatchAnalyticsVisualizer
from tools.batch_processor.batch_audit_sealer import BatchAuditSealer
from scripts.run_small_batch_smoke_test import run_small_batch_smoke_test

router = APIRouter(prefix="/batch", tags=["Procesamiento Batch Masivo"])


class BatchRunRequest(BaseModel):
    cases_count: int = Field(default=100, ge=1, le=1000, description="Cantidad de expedientes a auditar en lote")
    workers: int = Field(default=8, ge=1, le=16, description="Hilos concurrentes de ejecución")


class PortfolioOptimizationRequest(BaseModel):
    case_ids: Optional[List[str]] = Field(default=None, description="Expedientes específicos a incluir en la auditoría")
    wacc_annual: float = Field(default=0.12, ge=0.0, le=1.0, description="Tasa de costo ponderado de capital WACC anual (ejemplo: 0.12 para 12%)")
    target_count: int = Field(default=50, ge=1, le=100, description="Cantidad máxima de expedientes a evaluar")


class BatchActionRequest(BaseModel):
    case_ids: List[str] = Field(..., description="Expedientes sobre los cuales ejecutar la acción masiva")
    action_type: str = Field(default="INTERRUPT_PRESCRIPTION", description="INTERRUPT_PRESCRIPTION, POST_ERP, GENERATE_CAPA")
    operator_name: str = Field(default="Dirección Jurídica & Tesorería B2B", description="Nombre del operador o apoderado legal firmante")


@router.post("/run")
def trigger_batch_execution(request: BatchRunRequest = BatchRunRequest()):
    """
    Ejecuta una corrida batch desatendida de alta concurrencia (hasta 1,000 unidades)
    y genera métricas macroeconómicas consolidadas de la cartera.
    """
    try:
        summary: BatchExecutionSummary = EnterpriseBatchProcessor.execute_batch(
            target_count=request.cases_count,
            max_workers=request.workers
        )
        json_path, md_path = EnterpriseBatchProcessor.export_batch_summary(summary)

        # Retornar dict serializado
        raw_dict = summary.model_dump()
        clean_dict = EnterpriseBatchProcessor._decimal_to_float(raw_dict)
        clean_dict["report_json_path"] = str(json_path)
        clean_dict["report_md_path"] = str(md_path)
        return clean_dict
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en ejecución batch: {str(e)}")


@router.get("/latest")
def get_latest_batch_summary():
    """Recupera el resumen consolidado del último lote batch ejecutado."""
    reports_dir = Path("reports")
    batch_files = sorted(reports_dir.glob("batch_summary_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not batch_files:
        raise HTTPException(status_code=404, detail="No se han registrado ejecuciones batch previas.")

    try:
        with open(batch_files[0], "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al leer resumen batch: {str(e)}")


@router.post("/optimize-portfolio")
def optimize_working_capital_portfolio(request: PortfolioOptimizationRequest = PortfolioOptimizationRequest()):
    """
    US-961: Optimiza la cartera de controversias B2B de capital de trabajo, priorizando casos
    por Valor Presente Neto (NPV con WACC anual), riesgo de caducidad SLA (DTP) y salud relacional (RHI).
    """
    try:
        summary = WorkingCapitalPortfolioOptimizer.optimize_portfolio(
            case_ids=request.case_ids,
            wacc_annual=request.wacc_annual,
            target_count=request.target_count
        )
        return summary.model_dump(mode="json")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al optimizar cartera de capital de trabajo: {str(e)}")


@router.get("/portfolio-summary")
def get_portfolio_optimization_summary(target_count: int = 50, wacc: float = 0.12):
    """
    Recupera el resumen consolidado de prelación y War-Room C-Level para los expedientes del portafolio.
    """
    try:
        summary = WorkingCapitalPortfolioOptimizer.optimize_portfolio(
            wacc_annual=wacc,
            target_count=target_count
        )
        return summary.model_dump(mode="json")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar resumen de cartera: {str(e)}")


@router.post("/execute-action")
def execute_batch_action(request: BatchActionRequest):
    """
    Ejecuta acciones masivas en lote (Batch Action Execution):
    - INTERRUPT_PRESCRIPTION: Emisión en lote de avisos Art. 1041 CCom.
    - POST_ERP: Generación masiva de pólizas ERP y paquetes CFDI 4.0.
    - GENERATE_CAPA: Generación masiva de tickets de acción preventiva.
    """
    try:
        result = WorkingCapitalPortfolioOptimizer.execute_batch_action(
            case_ids=request.case_ids,
            action_type=request.action_type,
            operator_name=request.operator_name
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al ejecutar acción masiva: {str(e)}")


# ==============================================================================
# Endpoints de la Jornada Desatendida de 1,024 Unidades / 12 Horas & Smoke Test
# ==============================================================================

class SmokeTestRunRequest(BaseModel):
    units: int = Field(default=6, ge=1, le=20, description="Cantidad de unidades representativas a ejecutar")
    dry_run: bool = Field(default=True, description="Modo dry-run local ultrarrápido o llamadas reales")


@router.get("/unattended/summary")
def get_unattended_batch_summary():
    """
    Retorna el resumen analítico estructurado de la jornada de carga desatendida de 1,024 unidades,
    incluyendo KPIs consolidados, desglose por retailer, invariante $0.00 MAE y sello Merkle Root.
    """
    try:
        visualizer = BatchAnalyticsVisualizer()
        summary_path = visualizer.summary_json_path
        if summary_path.exists():
            with open(summary_path, "r", encoding="utf-8") as f:
                return json.load(f)
        
        # Si aún no existe el archivo cacheado en disco, calcularlo a partir de los registros
        summary = visualizer.compute_analytics_summary()
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener analítica desatendida: {str(e)}")


@router.get("/unattended/heartbeat")
def get_unattended_batch_heartbeat():
    """
    Monitorea el latido (Heartbeat) en tiempo real del proceso desatendido de 12 horas.
    """
    heartbeat_path = Path("reports/unattended_batch_heartbeat.json")
    if not heartbeat_path.exists():
        manifest_path = Path("reports/unattended_batch_audit_manifest.json")
        is_completed = manifest_path.exists()
        return {
            "status": "COMPLETED" if is_completed else "IDLE",
            "active": False,
            "pid": None,
            "current_index": 1024 if is_completed else 0,
            "total_units": 1024,
            "progress_pct": 100.0 if is_completed else 0.0,
            "elapsed_seconds": 43200.0 if is_completed else 0.0,
            "current_task_id": None,
            "last_heartbeat_at": None,
            "message": "Jornada de 1,024 unidades completada y sellada con éxito" if is_completed else "Orquestador desatendido en reposo"
        }
    try:
        with open(heartbeat_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al leer latido: {str(e)}")


@router.post("/unattended/verify-seal")
def verify_unattended_batch_seal():
    """
    Verifica criptográficamente la inmutabilidad de la bitácora:
    - Comprueba la cadena de hashes SHA-256 (Hash Chain) desde el bloque génesis.
    - Recalcula el Árbol de Merkle (Merkle Root) de las 1,024 unidades.
    - Valida que no exista manipulación en montos ni violación al invariante $0.00 MAE.
    - Valida los SHA-256 de los archivos físicos en disco.
    """
    try:
        sealer = BatchAuditSealer()
        result = sealer.verify_batch_integrity()
        return result.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en verificación criptográfica: {str(e)}")


@router.post("/unattended/run-smoke-test")
def trigger_small_batch_smoke_test(request: SmokeTestRunRequest = SmokeTestRunRequest()):
    """
    Ejecuta el Smoke Test de lote pequeño representativo recomendado por Platica.
    Ejecuta de 1 a 20 unidades con materialización física de expedientes de 5 documentos
    (factura, orden de compra, POD/entrega, pago SAT y contrato) y auditoría 3-way match.
    """
    try:
        output_dir = Path("reports/small_batch_smoke_test")
        result = run_small_batch_smoke_test(
            output_dir=output_dir,
            units_count=request.units,
            dry_run=request.dry_run
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al ejecutar smoke test: {str(e)}")


@router.get("/unattended/cases")
def list_unattended_batch_cases(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=5, le=100),
    status: Optional[str] = None,
    search: Optional[str] = None
):
    """
    Lista de tareas procesadas en la jornada de carga con paginación y filtros para la UI.
    """
    try:
        visualizer = BatchAnalyticsVisualizer()
        records = visualizer._load_records_from_disk()
        
        filtered = records
        if status and status.upper() != "ALL":
            filtered = [r for r in filtered if str(r.get("status", "")).upper() == status.upper()]
        
        if search:
            s = search.lower()
            filtered = [
                r for r in filtered
                if s in str(r.get("task_id", "")).lower()
                or s in str(r.get("case_id", "")).lower()
                or s in str(r.get("retailer_name", "")).lower()
                or s in str(r.get("retailer_id", "")).lower()
                or s in str(r.get("category", "")).lower()
            ]
        
        total_items = len(filtered)
        start_idx = max(0, (page - 1) * page_size)
        end_idx = start_idx + page_size
        page_records = filtered[start_idx:end_idx]
        
        return {
            "total_items": total_items,
            "page": page,
            "page_size": page_size,
            "total_pages": (total_items + page_size - 1) // page_size if page_size > 0 else 1,
            "records": page_records
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al listar casos batch: {str(e)}")


@router.get("/unattended/dossier/{case_id}")
def get_unattended_case_dossier(case_id: str):
    """
    Recupera el expediente probatorio físico de 5 documentos (factura, orden de compra,
    entrega/POD, pago SAT, contrato marco y dictamen de resolución) almacenado en disco.
    """
    try:
        paths_to_check = [
            Path("reports/batch_dossiers") / case_id,
            Path("reports/small_batch_smoke_test/batch_dossiers") / case_id,
        ]
        
        target_dir = None
        for p in paths_to_check:
            if p.exists() and p.is_dir():
                target_dir = p
                break
                
        if not target_dir:
            raise HTTPException(status_code=404, detail=f"Expediente físico no encontrado para {case_id}")
            
        docs = {}
        for fname in ["invoice.json", "purchase_order.json", "delivery.json", "payment.json", "contract.json", "audit_resolution_docket.json"]:
            fpath = target_dir / fname
            if fpath.exists():
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        docs[fname.replace(".json", "")] = json.load(f)
                except Exception:
                    with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                        docs[fname.replace(".json", "")] = {"raw_content": f.read()}
            else:
                docs[fname.replace(".json", "")] = None
                
        return {
            "case_id": case_id,
            "dossier_path": str(target_dir),
            "documents": docs
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al leer expediente: {str(e)}")



# ==============================================================================
# Mejora 4: Telemetría en Vivo por WebSockets para la Jornada Desatendida
# ==============================================================================

@router.websocket("/ws/telemetry")
async def batch_telemetry_websocket(websocket: WebSocket):
    """
    Canal dúplex WebSocket de alta frecuencia para transmisión en vivo de la
    supervisión desatendida, latidos de salud, eventos de auditoría y métricas de tokens.
    """
    await telemetry_broadcaster.connect(websocket)
    try:
        initial_hb = telemetry_broadcaster.get_heartbeat_payload()
        await websocket.send_json({
            "type": "INIT_STATE",
            "timestamp": initial_hb.get("last_heartbeat_at"),
            "data": initial_hb
        })

        while True:
            try:
                msg_text = await asyncio.wait_for(websocket.receive_text(), timeout=2.0)
                if msg_text == "ping":
                    await websocket.send_json({"type": "PONG", "data": {"status": "alive"}})
                elif msg_text == "heartbeat":
                    hb = telemetry_broadcaster.get_heartbeat_payload()
                    await websocket.send_json({"type": "HEARTBEAT", "data": hb})
            except asyncio.TimeoutError:
                hb = telemetry_broadcaster.get_heartbeat_payload()
                await websocket.send_json({"type": "HEARTBEAT", "data": hb})
    except WebSocketDisconnect:
        telemetry_broadcaster.disconnect(websocket)
    except Exception:
        telemetry_broadcaster.disconnect(websocket)


# ==============================================================================
# Sello Notarial RFC 3161 y Descarga de Expediente Maestro ZIP
# ==============================================================================

@router.get("/unattended/rfc3161-token")
def get_rfc3161_timestamp_token():
    """
    Retorna el Time-Stamp Token (TST) formal conforme a RFC 3161 y NOM-151-SCFI-2016
    vinculado a la raíz criptográfica de Merkle del lote desatendido de 1,024 unidades.
    """
    try:
        sealer = RFC3161TimestampSealer()
        token = sealer.load_or_issue_token()
        return token
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener sello RFC 3161: {str(e)}")


@router.get("/unattended/download-master-zip")
def download_master_audit_zip():
    """
    Genera y descarga en tiempo real el Expediente Maestro de Auditoría B2B en formato ZIP.
    Empaqueta todas las bitácoras (CSV, JSON), resúmenes ejecutivos, el manifiesto criptográfico Merkle,
    el sello RFC 3161, reportes técnicos semanales y la documentación del agente para evaluación por Platica.
    """
    try:
        reports_dir = Path("reports")
        reports_dir.mkdir(parents=True, exist_ok=True)
        zip_path = reports_dir / "expediente_maestro_auditoria_platica.zip"

        # Emitir o refrescar el sello RFC 3161 antes de empaquetar
        sealer = RFC3161TimestampSealer()
        sealer.issue_timestamp_token()

        files_to_pack = [
            ("unattended_batch_execution_log.csv", reports_dir / "unattended_batch_execution_log.csv"),
            ("unattended_batch_execution_log.json", reports_dir / "unattended_batch_execution_log.json"),
            ("unattended_batch_executive_summary.md", reports_dir / "unattended_batch_executive_summary.md"),
            ("unattended_batch_audit_manifest.json", reports_dir / "unattended_batch_audit_manifest.json"),
            ("unattended_batch_audit_manifest.sha256", reports_dir / "unattended_batch_audit_manifest.sha256"),
            ("unattended_batch_analytics_summary.json", reports_dir / "unattended_batch_analytics_summary.json"),
            ("unattended_batch_rfc3161_token.json", reports_dir / "unattended_batch_rfc3161_token.json"),
            ("README.md", Path("README.md")),
        ]

        # Agregar reportes técnicos de la carpeta docs
        docs_dir = Path("docs")
        if docs_dir.exists():
            for doc_file in docs_dir.glob("*.md"):
                files_to_pack.append((f"documentacion_tecnica/{doc_file.name}", doc_file))

        # Crear archivo ZIP maestro
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for arcname, file_path in files_to_pack:
                if file_path.exists() and file_path.is_file():
                    zf.write(file_path, arcname=arcname)

        if not zip_path.exists():
            raise HTTPException(status_code=500, detail="No se pudo construir el archivo ZIP maestro.")

        return FileResponse(
            path=str(zip_path),
            media_type="application/zip",
            filename="expediente_maestro_auditoria_platica.zip"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar ZIP maestro: {str(e)}")
