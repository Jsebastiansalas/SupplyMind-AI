import hashlib
from pathlib import Path
from typing import Dict, Optional, Tuple
from data.models import DisputeAnalysisReport
from agent.core.state import DisputeState
from config.settings import settings

class DisputeCache:
    """
    Caché en memoria de alta velocidad para conciliaciones y análisis de contratos.
    Verifica la huella digital (checksum y mtime de archivos en el expediente)
    para invalidar automáticamente la caché si cualquier documento es editado o reemplazado.
    """
    def __init__(self):
        self._cache: Dict[str, Tuple[str, DisputeAnalysisReport, DisputeState]] = {}

    def _compute_case_fingerprint(self, case_id: str) -> str:
        """Calcula un hash MD5 a partir de los archivos del caso y sus marcas temporales."""
        case_name = Path(case_id).name
        case_dir = settings.DATA_DIR / case_name
        if not case_dir.exists():
            provided = Path(case_id)
            if provided.exists() and provided.is_dir():
                case_dir = provided
            else:
                return "no_dir"
            
        hasher = hashlib.md5()
        for f in sorted(case_dir.glob("*")):
            if f.is_file():
                hasher.update(f.name.encode("utf-8"))
                hasher.update(str(f.stat().st_size).encode("utf-8"))
                hasher.update(str(f.stat().st_mtime_ns).encode("utf-8"))
        return hasher.hexdigest()

    def get(self, case_id: str) -> Optional[Tuple[DisputeAnalysisReport, DisputeState]]:
        """Recupera el reporte y estado en caché si la huella digital del expediente es idéntica."""
        clean_id = Path(case_id).name
        if clean_id not in self._cache:
            return None
            
        cached_fp, report, state = self._cache[clean_id]
        current_fp = self._compute_case_fingerprint(case_id)
        if cached_fp == current_fp:
            return report, state
            
        # Si los archivos cambiaron, invalidar entrada obsoleta
        del self._cache[clean_id]
        return None

    def set(self, case_id: str, report: DisputeAnalysisReport, state: DisputeState) -> None:
        """Almacena el resultado junto a la huella digital del expediente."""
        clean_id = Path(case_id).name
        fp = self._compute_case_fingerprint(case_id)
        self._cache[clean_id] = (fp, report, state)

    def clear(self, case_id: Optional[str] = None) -> None:
        """Limpia la memoria caché de un caso específico o de toda la sesión."""
        if case_id:
            clean_id = Path(case_id).name
            self._cache.pop(clean_id, None)
        else:
            self._cache.clear()

dispute_cache = DisputeCache()
