"""
api/routes/edi.py
Endpoints para el Motor EDI Nativo B2B (ANSI X12 850/810/856/861/820/997 y Generador 824).
Frontera 2 de Superinteligencia (Sprint 5.1).
"""

from decimal import Decimal
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from agent.ingestion.edi_engine import (
    EdiX12Parser,
    EdiAuditEngine,
    Edi824Generator,
    EdiParsedTransaction,
)

router = APIRouter(prefix="/edi", tags=["EDI B2B Nativo"])


# ==============================================================================
# Modelos de Petición y Respuesta
# ==============================================================================

class EdiParseRequest(BaseModel):
    raw_edi_content: str = Field(..., description="Cadena de texto sin procesar en formato ANSI X12 o EDIFACT.")


class EdiParseResponse(BaseModel):
    status: str = "success"
    element_separator: str
    segment_terminator: str
    total_segments: int
    total_transactions: int
    transactions: List[Dict[str, Any]]
    transaction_types: List[str]


class EdiAuditAsnRequest(BaseModel):
    asn_raw: str = Field(..., description="Contenido en texto de la transacción EDI 856 (Advance Ship Notice).")
    ack_997_raw: str = Field(..., description="Contenido en texto de la transacción EDI 997 (Functional Acknowledgment).")
    scheduled_dock_time_iso: str = Field(..., description="Timestamp ISO 8601 de la cita de muelle programada.")
    required_lead_hours: float = Field(default=4.0, description="Horas mínimas de antelación requeridas contractualmente.")


class Edi824GenerateRequest(BaseModel):
    dispute_id: str = Field(..., description="Identificador único de la disputa.")
    retailer_sender_id: str = Field(..., description="ID EDI del Retailer (ej. WALMART_01, AMAZON_EDI).")
    supplier_receiver_id: str = Field(..., description="ID EDI del Proveedor (ej. BIMBO_MX, UNILEVER_CORP).")
    invoice_number: str = Field(..., description="Número de factura comercial en disputa.")
    deduction_code: str = Field(..., description="Código de deducción ANSI X12 DE 426 (ej. 86, 59, 01, CS).")
    claimable_amount: Decimal = Field(..., description="Monto reclamado indebidamente en formato numérico/Decimal.")
    rejection_basis: str = Field(..., description="Fundamento contractual o pericial del rechazo.")


class Edi824Response(BaseModel):
    status: str = "success"
    dispute_id: str
    raw_edi_824: str
    segments_count: int
    lines: List[str]


# ==============================================================================
# Muestras EDI de Referencia para Pruebas y UI
# ==============================================================================

SAMPLE_EDI_TRANSACTIONS = {
    "850": (
        "ISA*00*          *00*          *ZZ*WALMART_EDI    *ZZ*PROVEEDOR_CORP *261018*0800*U*00401*000001001*0*P*>~\n"
        "GS*PO*WALMART_EDI*PROVEEDOR_CORP*20261018*0800*1001*X*004010~\n"
        "ST*850*0001~\n"
        "BEG*00*SA*PO-994820**20261018~\n"
        "CUR*BY*USD~\n"
        "N1*BY*WALMART SUPERCENTER DC #6014*92*WM-6014~\n"
        "N1*SE*PROVEEDOR ALIMENTICIO S.A.*92*PROV-ALIM~\n"
        "PO1*1*500*CA*42.50*PE*IN*SKU-ACEITE-VEG-1L~\n"
        "PO1*2*250*CA*58.00*PE*IN*SKU-ARROZ-EXTRA-1KG~\n"
        "CTT*2*750~\n"
        "SE*8*0001~\n"
        "GE*1*1001~\n"
        "IEA*1*000001001~"
    ),
    "810": (
        "ISA*00*          *00*          *ZZ*PROVEEDOR_CORP *ZZ*WALMART_EDI    *261018*0930*U*00401*000001002*0*P*>~\n"
        "GS*IN*PROVEEDOR_CORP*WALMART_EDI*20261018*0930*1002*X*004010~\n"
        "ST*810*0001~\n"
        "BIG*20261018*FAC-2026-8841*20261018*PO-994820~\n"
        "CUR*SE*USD~\n"
        "N1*RE*PROVEEDOR ALIMENTICIO S.A.*92*PROV-ALIM~\n"
        "N1*BT*WALMART MEXICO RETAIL*92*WM-CORP~\n"
        "IT1*1*500*CA*42.50**IN*SKU-ACEITE-VEG-1L~\n"
        "IT1*2*250*CA*58.00**IN*SKU-ARROZ-EXTRA-1KG~\n"
        "TDS*3575000~\n"
        "SE*8*0001~\n"
        "GE*1*1002~\n"
        "IEA*1*000001002~"
    ),
    "856": (
        "ISA*00*          *00*          *ZZ*PROVEEDOR_CORP *ZZ*WALMART_EDI    *261018*1400*U*00401*000001003*0*P*>~\n"
        "GS*SH*PROVEEDOR_CORP*WALMART_EDI*20261018*1400*1003*X*004010~\n"
        "ST*856*0001~\n"
        "BSN*00*ASN-8841-BOL*20261018*1400*0001~\n"
        "HL*1**S~\n"
        "TD1*CTN*750~\n"
        "HL*2*1*O~\n"
        "PRF*PO-994820~\n"
        "HL*3*2*I~\n"
        "LIN*1*IN*SKU-ACEITE-VEG-1L~\n"
        "SN1*1*500*CA~\n"
        "HL*4*2*I~\n"
        "LIN*2*IN*SKU-ARROZ-EXTRA-1KG~\n"
        "SN1*2*250*CA~\n"
        "CTT*4~\n"
        "SE*13*0001~\n"
        "GE*1*1003~\n"
        "IEA*1*000001003~"
    ),
    "997": (
        "ISA*00*          *00*          *ZZ*WALMART_EDI    *ZZ*PROVEEDOR_CORP *261018*1415*U*00401*000001004*0*P*>~\n"
        "GS*FA*WALMART_EDI*PROVEEDOR_CORP*20261018*1415*1004*X*004010~\n"
        "ST*997*0001~\n"
        "AK1*SH*1003~\n"
        "AK2*856*0001~\n"
        "AK5*A~\n"
        "AK9*A*1*1*1~\n"
        "SE*6*0001~\n"
        "GE*1*1004~\n"
        "IEA*1*000001004~"
    ),
    "861": (
        "ISA*00*          *00*          *ZZ*WALMART_EDI    *ZZ*PROVEEDOR_CORP *261019*1130*U*00401*000001005*0*P*>~\n"
        "GS*RC*WALMART_EDI*PROVEEDOR_CORP*20261019*1130*1005*X*004010~\n"
        "ST*861*0001~\n"
        "BRA*REC-DC6014*20261019*00*1~\n"
        "PRF*PO-994820~\n"
        "RCD*1*500*CA*0*CA*01*480*CA~\n"
        "LIN*1*IN*SKU-ACEITE-VEG-1L~\n"
        "RCD*2*250*CA*0*CA*01*250*CA~\n"
        "LIN*2*IN*SKU-ARROZ-EXTRA-1KG~\n"
        "CTT*2~\n"
        "SE*9*0001~\n"
        "GE*1*1005~\n"
        "IEA*1*000001005~"
    ),
    "820": (
        "ISA*00*          *00*          *ZZ*WALMART_EDI    *ZZ*PROVEEDOR_CORP *261025*1600*U*00401*000001006*0*P*>~\n"
        "GS*RA*WALMART_EDI*PROVEEDOR_CORP*20261025*1600*1006*X*004010~\n"
        "ST*820*0001~\n"
        "BPR*I*31750.00*C*ACH*CTX*01*123456789*DA*987654321*1234567890~\n"
        "TRN*1*CHK-2026-99014*1234567890~\n"
        "RMR*IV*FAC-2026-8841*PO*31750.00*35750.00*4000.00~\n"
        "ADX*4000.00*86*ASN EXTEMPORANEO 4H ANTES DE CITA DC 6014~\n"
        "SE*6*0001~\n"
        "GE*1*1006~\n"
        "IEA*1*000001006~"
    )
}


# ==============================================================================
# Endpoints
# ==============================================================================

@router.post("/parse", response_model=EdiParseResponse)
def parse_edi_content(request: EdiParseRequest):
    """
    Decodifica y analiza transacciones ANSI X12 o EDIFACT de forma autónoma.
    Detecta automáticamente delimitadores y extrae las transacciones tipadas
    (850, 810, 856, 861, 820, 997).
    """
    if not request.raw_edi_content or not request.raw_edi_content.strip():
        raise HTTPException(status_code=400, detail="El contenido EDI proporcionado está vacío.")

    elem_sep, seg_term = EdiX12Parser.detect_delimiters(request.raw_edi_content)
    segments = EdiX12Parser.parse_segments(request.raw_edi_content)
    txs = EdiX12Parser.parse_document(request.raw_edi_content)

    tx_dicts = [tx.model_dump(mode="json") for tx in txs]
    types = [tx.transaction_type for tx in txs]

    return EdiParseResponse(
        element_separator=elem_sep,
        segment_terminator=repr(seg_term),
        total_segments=len(segments),
        total_transactions=len(txs),
        transactions=tx_dicts,
        transaction_types=types
    )


@router.post("/audit-asn")
def audit_asn_timeliness(request: EdiAuditAsnRequest):
    """
    Realiza una auditoría forense comparando el Advance Ship Notice (EDI 856)
    contra el acuse técnico Functional Acknowledgment (EDI 997) y la cita de muelle.
    Desmantela legalmente reclamos de 'ASN Extemporáneo' o 'Late ASN Penalty'.
    """
    if not request.asn_raw or not request.ack_997_raw:
        raise HTTPException(status_code=400, detail="Se requiere tanto el EDI 856 como el EDI 997.")

    audit_result = EdiAuditEngine.audit_asn_timeliness(
        asn_raw=request.asn_raw,
        ack_997_raw=request.ack_997_raw,
        scheduled_dock_time_iso=request.scheduled_dock_time_iso,
        required_lead_hours=request.required_lead_hours
    )

    if not audit_result.get("valid", True) and "error" in audit_result:
        raise HTTPException(status_code=422, detail=audit_result["error"])

    return audit_result


@router.post("/generate-824", response_model=Edi824Response)
def generate_edi_824(request: Edi824GenerateRequest):
    """
    Genera un archivo ANSI X12 824 Application Advice formal para el rechazo
    electrónico e inapelable de deducciones arbitrarias frente a portales EDI de retailers.
    """
    if request.claimable_amount <= Decimal("0.00"):
        raise HTTPException(status_code=400, detail="El monto reclamado debe ser mayor a cero.")

    raw_edi = Edi824Generator.generate_rejection_824(
        dispute_id=request.dispute_id,
        retailer_sender_id=request.retailer_sender_id,
        supplier_receiver_id=request.supplier_receiver_id,
        invoice_number=request.invoice_number,
        deduction_code=request.deduction_code,
        claimable_amount=request.claimable_amount,
        rejection_basis=request.rejection_basis
    )

    lines = [line.strip() for line in raw_edi.split("\n") if line.strip()]

    return Edi824Response(
        dispute_id=request.dispute_id,
        raw_edi_824=raw_edi,
        segments_count=len(lines),
        lines=lines
    )


@router.get("/samples/{edi_type}")
def get_sample_edi(edi_type: str):
    """
    Retorna transacciones EDI de ejemplo reales para pruebas y demostraciones en vivo.
    Soporta: 850, 810, 856, 861, 820, 997.
    """
    edi_type_clean = edi_type.strip()
    if edi_type_clean not in SAMPLE_EDI_TRANSACTIONS:
        raise HTTPException(
            status_code=404,
            detail=f"Muestra EDI no encontrada para tipo '{edi_type}'. Tipos disponibles: {list(SAMPLE_EDI_TRANSACTIONS.keys())}"
        )

    return {
        "transaction_type": edi_type_clean,
        "description": {
            "850": "Purchase Order (Orden de Compra)",
            "810": "Commercial Invoice (Factura Comercial)",
            "856": "Ship Notice / Manifest (Advance Ship Notice - ASN)",
            "861": "Receiving Advice (Constancia de Recepción en Muelle)",
            "820": "Payment Order / Remittance Advice (Liquidación y Deducciones)",
            "997": "Functional Acknowledgment (Acuse Técnico UTC)"
        }.get(edi_type_clean, "Transacción EDI ANSI X12"),
        "raw_edi": SAMPLE_EDI_TRANSACTIONS[edi_type_clean]
    }
