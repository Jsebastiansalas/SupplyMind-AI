"""
agent/planner/precedents.py
Registro y Base de Conocimiento de Precedentes Jurisprudenciales para SupplyMind AI.

Permite registrar precedentes y doctrinas emitidas por el Tribunal Colegiado
e inyectarlas dinámicamente en el System Prompt para calibrar el criterio de decisión.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


DEFAULT_KB_PATH = "data/precedents/precedents_kb.json"


class PrecedentRegistry:
    """
    Registro persistente de precedentes y doctrinas del Tribunal Colegiado.
    Permite registrar fallos, consultar la jurisprudencia acumulada y
    formatearla para inyección contextual en los prompts del agente.
    """

    def __init__(self, kb_path: Optional[str] = DEFAULT_KB_PATH):
        self.kb_path = Path(kb_path) if kb_path else Path(DEFAULT_KB_PATH)
        # Asegurar existencia del directorio contenedor
        parent_dir = self.kb_path.parent
        if parent_dir and not parent_dir.exists():
            parent_dir.mkdir(parents=True, exist_ok=True)

        self._precedents: List[Dict[str, Any]] = []
        self._load()

    def _load(self) -> None:
        """Carga los precedentes desde el archivo JSON si existe."""
        if self.kb_path.exists():
            try:
                with open(self.kb_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self._precedents = data
                    else:
                        self._precedents = []
            except (json.JSONDecodeError, OSError):
                self._precedents = []
        else:
            self._precedents = []

    def _save(self) -> None:
        """Persiste la lista de precedentes al archivo JSON."""
        parent_dir = self.kb_path.parent
        if parent_dir and not parent_dir.exists():
            parent_dir.mkdir(parents=True, exist_ok=True)

        with open(self.kb_path, "w", encoding="utf-8") as f:
            json.dump(self._precedents, f, ensure_ascii=False, indent=2)

    def register_precedent(
        self,
        case_id: str,
        dispute_type: str,
        ruling: str,
        directive: str,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Registra un nuevo precedente jurisprudencial en memoria y en disco.
        """
        now_ts = datetime.now(timezone.utc).isoformat()
        precedent_record: Dict[str, Any] = {
            "case_id": case_id,
            "dispute_type": dispute_type,
            "ruling": ruling,
            "directive": directive,
            "timestamp": now_ts,
        }
        precedent_record.update(kwargs)

        # Evitar duplicados exactos por case_id actualizando si ya existe
        existing_idx = next(
            (i for i, p in enumerate(self._precedents) if p.get("case_id") == case_id),
            None,
        )
        if existing_idx is not None:
            self._precedents[existing_idx] = precedent_record
        else:
            self._precedents.append(precedent_record)

        self._save()
        return precedent_record

    def get_all_precedents(self) -> List[Dict[str, Any]]:
        """Retorna todos los precedentes registrados."""
        self._load()
        return list(self._precedents)

    def format_precedents_for_prompt(self) -> str:
        """
        Formatea los precedentes para inyección contextual limpia en el prompt.
        Retorna string vacío si no existen precedentes registrados.
        """
        precedents = self.get_all_precedents()
        if not precedents:
            return ""

        lines: List[str] = [
            "\nPRECEDENTES JURISPRUDENCIALES Y CALIBRACIÓN DE DOCTRINA:",
            "Las siguientes directrices y precedentes emanados del Tribunal Colegiado son vinculantes:",
        ]
        for p in precedents:
            c_id = p.get("case_id", "PREC-N/A")
            d_type = p.get("dispute_type", "GENERAL")
            ruling = p.get("ruling", "")
            directive = p.get("directive", "")
            lines.append(
                f"- [{c_id}] Tipología: {d_type} | Dictamen: {ruling} | Directriz de calibración: {directive}"
            )
        lines.append("")
        return "\n".join(lines)


def get_registered_precedents_text(kb_path: Optional[str] = None) -> str:
    """Helper global para obtener el texto formateado de precedentes."""
    registry = PrecedentRegistry(kb_path=kb_path)
    return registry.format_precedents_for_prompt()
