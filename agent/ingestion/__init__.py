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
from agent.ingestion.edi_engine import (
    EdiSegment,
    EdiEnvelope,
    EdiItemLine,
    EdiDeductionLine,
    EdiParsedTransaction,
    EdiX12Parser,
    EdiAuditEngine,
    Edi824Generator,
)

__all__ = [
    "repair_json_string",
    "parse_resilient_decimal",
    "normalize_schema_dict",
    "impute_missing_document",
    "ResilientDocumentLoader",
    "EdiSegment",
    "EdiEnvelope",
    "EdiItemLine",
    "EdiDeductionLine",
    "EdiParsedTransaction",
    "EdiX12Parser",
    "EdiAuditEngine",
    "Edi824Generator",
]

