"""
agent/ingestion/__init__.py
Capa de ingesta autocurativa, reparación de JSONs corruptos y normalización de esquemas polimórficos.
"""
from agent.ingestion.resilient_parser import (
    repair_json_string,
    parse_resilient_decimal,
    normalize_schema_dict,
    impute_missing_document,
    ResilientDocumentLoader,
)

__all__ = [
    "repair_json_string",
    "parse_resilient_decimal",
    "normalize_schema_dict",
    "impute_missing_document",
    "ResilientDocumentLoader",
]
