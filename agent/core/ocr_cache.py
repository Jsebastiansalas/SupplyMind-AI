"""
agent/core/ocr_cache.py
Fase 10 - Sprint 10.4: Sistema de Caché Persistente por SHA-256 para OCR y Visión Multimodal.

Elimina cuellos de botella bloqueantes (como el OCR sincrónico de case_008)
almacenando en memoria y disco las transcripciones y extracciones estructuradas
indexadas por el hash criptográfico SHA-256 del archivo físico o flujo de bytes.
"""

import hashlib
import io
import json
import logging
from pathlib import Path
import threading
from typing import Any, Dict, Optional, Union
from PIL import Image

logger = logging.getLogger("supplymind.ocr_cache")
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_CACHE_DIR = ROOT_DIR / "data" / "cache" / "ocr"


class OcrCache:
    """Gestor de caché en dos niveles (memoria RAM + disco local) indexado por SHA-256."""

    _memory_cache: Dict[str, Dict[str, Any]] = {}
    _lock = threading.RLock()
    _cache_dir: Path = DEFAULT_CACHE_DIR

    @classmethod
    def set_cache_dir(cls, custom_dir: Path) -> None:
        with cls._lock:
            cls._cache_dir = Path(custom_dir)
            cls._cache_dir.mkdir(parents=True, exist_ok=True)

    @classmethod
    def _ensure_dir(cls) -> Path:
        if not cls._cache_dir.exists():
            cls._cache_dir.mkdir(parents=True, exist_ok=True)
        return cls._cache_dir

    @classmethod
    def compute_hash(cls, source: Union[str, Path, bytes, Image.Image]) -> str:
        """
        Calcula el hash SHA-256 determinístico de un archivo, bytes o imagen en memoria.
        """
        hasher = hashlib.sha256()

        if isinstance(source, (str, Path)):
            p = Path(source)
            if p.exists() and p.is_file():
                with open(p, "rb") as f:
                    while chunk := f.read(65536):
                        hasher.update(chunk)
                return hasher.hexdigest()
            else:
                hasher.update(str(source).encode("utf-8"))
                return hasher.hexdigest()

        elif isinstance(source, bytes):
            hasher.update(source)
            return hasher.hexdigest()

        elif isinstance(source, Image.Image):
            buf = io.BytesIO()
            source.save(buf, format="PNG")
            hasher.update(buf.getvalue())
            return hasher.hexdigest()

        raise TypeError(f"Tipo no soportado para cómputo de SHA-256: {type(source)}")

    @classmethod
    def get(cls, sha256_hash: str) -> Optional[Dict[str, Any]]:
        """
        Recupera una entrada de caché por su SHA-256.
        Consulta primero la memoria (0ms) y luego el disco (<1ms).
        """
        with cls._lock:
            # 1. Memoria RAM
            if sha256_hash in cls._memory_cache:
                return cls._memory_cache[sha256_hash]

            # 2. Disco
            cls._ensure_dir()
            cache_file = cls._cache_dir / f"{sha256_hash}.json"
            if not cache_file.exists() and cls._cache_dir != DEFAULT_CACHE_DIR:
                alt_file = DEFAULT_CACHE_DIR / f"{sha256_hash}.json"
                if alt_file.exists():
                    cache_file = alt_file

            if cache_file.exists():
                try:
                    data = json.loads(cache_file.read_text(encoding="utf-8"))
                    cls._memory_cache[sha256_hash] = data
                    return data
                except Exception as e:
                    logger.warning(f"Error al leer caché OCR de disco ({cache_file}): {e}")
                    return None

            return None

    @classmethod
    def get_text(cls, sha256_hash: str) -> Optional[str]:
        """Recupera únicamente el texto transcrito si existe en caché."""
        entry = cls.get(sha256_hash)
        if entry and "text" in entry:
            return entry["text"]
        return None

    @classmethod
    def get_structured(cls, sha256_hash: str) -> Optional[Dict[str, Any]]:
        """Recupera el diccionario con el modelo estructurado si existe en caché."""
        entry = cls.get(sha256_hash)
        if entry and "structured" in entry:
            return entry["structured"]
        return None

    @classmethod
    def set(
        cls,
        sha256_hash: str,
        text: Optional[str] = None,
        structured: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Guarda o actualiza una entrada en caché (memoria y disco).
        """
        with cls._lock:
            existing = cls.get(sha256_hash) or {}
            payload = {
                "sha256": sha256_hash,
                "text": text if text is not None else existing.get("text"),
                "structured": structured if structured is not None else existing.get("structured"),
                "metadata": metadata or existing.get("metadata", {})
            }

            # Guardar en memoria
            cls._memory_cache[sha256_hash] = payload

            # Persistir a disco
            cls._ensure_dir()
            cache_file = cls._cache_dir / f"{sha256_hash}.json"
            try:
                cache_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            except Exception as e:
                logger.warning(f"Error al escribir caché OCR en disco ({cache_file}): {e}")

    @classmethod
    def has(cls, sha256_hash: str) -> bool:
        """Indica si el hash se encuentra presente en la caché."""
        return cls.get(sha256_hash) is not None

    @classmethod
    def clear(cls) -> None:
        """Limpia la memoria RAM y elimina los archivos JSON de disco."""
        with cls._lock:
            cls._memory_cache.clear()
            cls._ensure_dir()
            for p in cls._cache_dir.glob("*.json"):
                try:
                    p.unlink(missing_ok=True)
                except Exception:
                    pass
