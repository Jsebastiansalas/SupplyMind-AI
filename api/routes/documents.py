"""
api/routes/documents.py
Servicio de archivos documentales (PDFs, imágenes de remisiones escaneadas, contratos y JSONs)
para el visor split-screen del frontend.
"""

from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

router = APIRouter(prefix="/cases", tags=["Documentos de Expediente"])

CASES_DIR = Path("data/cases")


def _get_media_type(filename: str) -> str:
    ext = Path(filename).suffix.lower()
    mapping = {
        ".pdf": "application/pdf",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".json": "application/json",
        ".md": "text/markdown; charset=utf-8",
        ".txt": "text/plain; charset=utf-8",
    }
    return mapping.get(ext, "application/octet-stream")


@router.get("/{case_id}/documents/{filename}")
def get_document_file(case_id: str, filename: str):
    """
    Sirve el archivo documental solicitado para previsualización directa en el navegador.
    Protegido contra ataques de Directory Traversal.
    """
    case_path = CASES_DIR / case_id
    if not case_path.exists():
        raise HTTPException(status_code=404, detail=f"Caso '{case_id}' no encontrado.")

    file_path = (case_path / filename).resolve()
    
    # Prevenir path traversal
    if not str(file_path).startswith(str(case_path.resolve())):
        raise HTTPException(status_code=400, detail="Acceso denegado a ruta no autorizada.")

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail=f"Archivo '{filename}' no encontrado en el expediente.")

    media_type = _get_media_type(filename)
    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        filename=filename,
    )
