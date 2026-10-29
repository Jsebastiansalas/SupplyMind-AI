"""
api/routes/erp.py
Endpoints REST para Integración ERP (SAP S/4HANA, NetSuite) y Fiscal CFDI 4.0 (Fase 3).
"""

from decimal import Decimal
from pathlib import Path
from typing import Dict, Any
from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse, Response
from pydantic import BaseModel

from agent.core.erp_engine import ErpEngine, get_case_fiscal_profile
from agent.core.concession_engine import ConcessionEngine

router = APIRouter(prefix="/cases", tags=["Integración ERP & CFDI 4.0"])


def _decimal_to_float(obj: Any) -> Any:
    """Convierte recursivamente Decimals a floats para serialización JSON segura."""
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, dict):
        return {k: _decimal_to_float(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_decimal_to_float(item) for item in obj]
    return obj


@router.get("/{case_id}/erp/sap")
def get_sap_payload_endpoint(case_id: str):
    """Retorna la estructura BAPI_ACC_DOCUMENT_POST y el IDoc FIDCCP02 para SAP."""
    case_path = Path("data/cases") / case_id
    if not case_path.exists():
        raise HTTPException(status_code=404, detail=f"Caso '{case_id}' no encontrado.")

    report = ConcessionEngine.get_or_create_base_report(case_id)
    lines = ErpEngine.build_erp_posting_lines(report)
    sap_bapi = ErpEngine.generate_sap_bapi_payload(case_id, report, lines)
    sap_idoc = ErpEngine.generate_sap_idoc_text(case_id, report, lines)

    return {
        "status": "success",
        "case_id": case_id,
        "format": "SAP_BAPI_ACC_DOCUMENT_POST",
        "bapi_payload": _decimal_to_float(sap_bapi),
        "idoc_text": sap_idoc
    }


@router.get("/{case_id}/erp/netsuite")
def get_netsuite_payload_endpoint(case_id: str):
    """Retorna los asientos contables y el archivo CSV para Oracle NetSuite."""
    case_path = Path("data/cases") / case_id
    if not case_path.exists():
        raise HTTPException(status_code=404, detail=f"Caso '{case_id}' no encontrado.")

    report = ConcessionEngine.get_or_create_base_report(case_id)
    lines = ErpEngine.build_erp_posting_lines(report)
    csv_text = ErpEngine.generate_netsuite_csv(case_id, report, lines)

    return {
        "status": "success",
        "case_id": case_id,
        "format": "ORACLE_NETSUITE_JOURNAL_ENTRY",
        "csv_content": csv_text,
        "lines": _decimal_to_float([l.model_dump(mode="python") for l in lines])
    }


@router.get("/{case_id}/erp/cfdi")
def get_cfdi_xml_endpoint(case_id: str):
    """Genera y descarga el archivo XML fiscal CFDI 4.0 de Nota de Crédito (Tipo E)."""
    case_path = Path("data/cases") / case_id
    if not case_path.exists():
        raise HTTPException(status_code=404, detail=f"Caso '{case_id}' no encontrado.")

    report = ConcessionEngine.get_or_create_base_report(case_id)
    fiscal_profile = get_case_fiscal_profile(case_id)
    xml_str = ErpEngine.generate_cfdi_40_xml(case_id, report, fiscal_profile)

    return Response(content=xml_str, media_type="application/xml")


@router.post("/{case_id}/erp/export")
def export_erp_package_endpoint(case_id: str):
    """
    Genera y almacena todos los artefactos ERP (SAP, NetSuite, CFDI 4.0) en reports/erp_{case_id}/.
    """
    case_path = Path("data/cases") / case_id
    if not case_path.exists():
        raise HTTPException(status_code=404, detail=f"Caso '{case_id}' no encontrado.")

    package = ErpEngine.export_full_erp_package(case_id)
    return {
        "status": "success",
        "case_id": case_id,
        "message": f"Paquete ERP exportado exitosamente a reports/erp_{case_id}/",
        "package": _decimal_to_float(package.model_dump(mode="python"))
    }


@router.post("/{case_id}/erp/sap/post-document")
def post_sap_document_simulation(case_id: str):
    """
    Simulador bidireccional de contabilización directa en SAP S/4HANA (BAPI_ACC_DOCUMENT_POST / RFC).
    Valida partida doble, genera número de documento contable (FI-GL) y retorna confirmación de compensación.
    """
    case_path = Path("data/cases") / case_id
    if not case_path.exists():
        raise HTTPException(status_code=404, detail=f"Caso '{case_id}' no encontrado.")

    report = ConcessionEngine.get_or_create_base_report(case_id)
    lines = ErpEngine.build_erp_posting_lines(report)
    
    # Validar partida doble
    total_debit = sum(l.debit for l in lines)
    total_credit = sum(l.credit for l in lines)
    if total_debit != total_credit:
        raise HTTPException(status_code=400, detail="Descuadre en partida doble contable. Transacción rechazada por SAP.")

    # Generación de identificador único determinístico para SAP S/4HANA
    clean_id = abs(hash(f"SAP-{case_id}-{total_debit}")) % 900000 + 100000
    sap_doc_num = f"1000{clean_id}"
    company_code = "1000"
    fiscal_year = "2026"

    return {
        "status": "SUCCESS_POSTED",
        "system": "SAP S/4HANA Cloud / On-Premise",
        "protocol": "RFC_BAPI_ACC_DOCUMENT_POST",
        "case_id": case_id,
        "confirmation": {
            "sap_document_number": sap_doc_num,
            "company_code": company_code,
            "fiscal_year": fiscal_year,
            "document_type": "DG",  # Credit memo / Nota de débito de deudor
            "reference": f"SM-{case_id.upper()}",
            "posting_status": "CLEARED_IN_SUBLEDGER",
            "currency": "USD",
            "total_posted_usd": float(total_debit),
            "lines_posted_count": len(lines),
            "bapi_return": [
                {
                    "type": "S",
                    "id": "RW",
                    "number": "605",
                    "message": f"Document {sap_doc_num} was successfully posted in company code {company_code} ({fiscal_year})."
                },
                {
                    "type": "S",
                    "id": "FI",
                    "number": "012",
                    "message": "Subledger open items cleared automatically against commercial dispute resolution."
                }
            ],
            "posted_at": "2026-10-28T19:08:00Z"
        }
    }


@router.post("/{case_id}/erp/netsuite/post-journal")
def post_netsuite_journal_simulation(case_id: str):
    """
    Simulador bidireccional de integración con Oracle NetSuite vía SuiteTalk REST Web Services.
    Registra el asiento contable (JournalEntry / CreditMemo) y retorna el Internal ID y TranID de auditoría.
    """
    case_path = Path("data/cases") / case_id
    if not case_path.exists():
        raise HTTPException(status_code=404, detail=f"Caso '{case_id}' no encontrado.")

    report = ConcessionEngine.get_or_create_base_report(case_id)
    lines = ErpEngine.build_erp_posting_lines(report)

    # Validar partida doble
    total_debit = sum(l.debit for l in lines)
    total_credit = sum(l.credit for l in lines)
    if total_debit != total_credit:
        raise HTTPException(status_code=400, detail="Desbalance en partida doble. Oracle NetSuite rechazó la transacción.")

    # Generación de identificador único de NetSuite
    clean_hash = abs(hash(f"NETSUITE-{case_id}-{total_debit}"))
    internal_id = str(clean_hash % 900000 + 100000)
    tran_id = f"JE-2026-{clean_hash % 9000 + 1000}"

    return {
        "status": "APPROVED_POSTED",
        "system": "Oracle NetSuite ERP",
        "protocol": "SuiteTalk REST Web Services (v1)",
        "case_id": case_id,
        "confirmation": {
            "internal_id": internal_id,
            "tran_id": tran_id,
            "record_type": "journalEntry",
            "subsidiary": "SupplyMind LatAm México S.A. de C.V. (Subsidiary ID: 1)",
            "memo": f"SupplyMind AI Autonomous Dispute Conciliation - {case_id.upper()}",
            "posting_status": "APPROVED",
            "currency": "USD",
            "total_posted_usd": float(total_debit),
            "lines_posted_count": len(lines),
            "audit_trail_url": f"https://system.netsuite.com/app/accounting/transactions/journal.nl?id={internal_id}",
            "posted_at": "2026-10-28T19:08:00Z"
        }
    }

