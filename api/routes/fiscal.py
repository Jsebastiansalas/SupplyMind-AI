"""
api/routes/fiscal.py
Endpoints para el Simulador PAC Fiscal CFDI 4.0 y Conciliación Bancaria MT940 / SPEI.
Frontera 3 de Superinteligencia (Sprint 5.3).
"""

from decimal import Decimal
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from agent.fiscal.cfdi_pac_simulator import (
    CfdiEmisor,
    CfdiReceptor,
    StampedCfdi,
    CfdiPacSimulator,
)
from agent.fiscal.bank_reconciliation import (
    BankTransactionEntry,
    Mt940Statement,
    CepSpeiVerificationResult,
    BankReconciliationResult,
    BankReconciliationEngine,
)

router = APIRouter(prefix="/fiscal", tags=["Fiscal SAT CFDI 4.0 & Conciliación Bancaria"])


# ==============================================================================
# Modelos de Petición
# ==============================================================================

class StampCreditNoteRequest(BaseModel):
    dispute_id: str = Field(..., description="Identificador único del caso en disputa.")
    emisor_rfc: str = Field(default="PRO920101XYZ", description="RFC del proveedor emisor.")
    emisor_nombre: str = Field(default="PROVEEDOR ALIMENTICIO S.A. DE C.V.", description="Razón social del emisor.")
    receptor_rfc: str = Field(default="NWM9709244W4", description="RFC del comprador/retailer.")
    receptor_nombre: str = Field(default="NUEVA WAL MART DE MEXICO S. DE R.L. DE C.V.", description="Razón social receptor.")
    original_invoice_uuid: str = Field(default="4D982F7B-12C0-466A-8A4D-741E0F584C92", description="UUID de la factura relacionada.")
    original_invoice_folio: str = Field(default="FAC-2026-8841", description="Folio comercial de la factura.")
    amount_justified: Decimal = Field(..., description="Monto en dinero de la deducción justificada a timbrar.")
    adjustment_reason: str = Field(..., description="Motivo comercial y pericial del ajuste.")
    currency: str = Field(default="USD", description="Moneda fiscal del comprobante.")


class StampPaymentReceiptRequest(BaseModel):
    emisor_rfc: str = Field(default="PRO920101XYZ")
    emisor_nombre: str = Field(default="PROVEEDOR ALIMENTICIO S.A. DE C.V.")
    receptor_rfc: str = Field(default="NWM9709244W4")
    receptor_nombre: str = Field(default="NUEVA WAL MART DE MEXICO S. DE R.L. DE C.V.")
    payment_date_iso: str = Field(default="2026-10-28T16:30:00", description="Fecha y hora de acreditación bancaria.")
    amount_paid: Decimal = Field(..., description="Monto efectivamente liquidado por el retailer.")
    related_invoice_uuid: str = Field(..., description="UUID del CFDI liquidado.")
    related_invoice_folio: str = Field(default="FAC-2026-8841")
    previous_balance: Decimal = Field(..., description="Saldo insoluto previo de la factura.")
    currency: str = Field(default="USD")


class ParseMt940Request(BaseModel):
    raw_mt940_text: str = Field(..., description="Texto sin formato del extracto SWIFT MT940.")


class VerifyCepSpeiRequest(BaseModel):
    clave_rastreo: str = Field(..., description="Clave de rastreo alfanumérica de Banxico (hasta 30 caracteres).")
    institucion_emisora: str = Field(default="40012", description="Clave CASFIM banco emisor (ej. 40012 BBVA).")
    institucion_receptora: str = Field(default="40014", description="Clave CASFIM banco receptor (ej. 40014 Santander).")
    cuenta_ordenante: str = Field(default="012180001234567890", description="CLABE ordenante.")
    cuenta_beneficiaria: str = Field(default="014180009876543210", description="CLABE beneficiaria.")
    monto: Decimal = Field(..., description="Importe de la transferencia electrónica.")
    fecha_operacion: Optional[str] = Field(default=None, description="Fecha de dispersión en formato YYYY-MM-DD HH:MM:SS.")
    concepto_pago: str = Field(default="Liquidacion Conciliada Factura FAC-8841", description="Concepto de la transferencia.")


class ReconcileDisputeRequest(BaseModel):
    expected_amount: Decimal = Field(..., description="Monto en firme acordado o reclamable a conciliar.")
    invoice_reference: str = Field(default="", description="Referencia o folio de la factura comercial.")
    raw_mt940_text: Optional[str] = Field(default=None, description="Extracto MT940 para extraer movimientos.")
    bank_entries: Optional[List[BankTransactionEntry]] = Field(default=None, description="O lista directa de movimientos.")


# ==============================================================================
# Muestras Canónicas de Prueba y UI
# ==============================================================================

SAMPLE_FISCAL_DATA = {
    "mt940": (
        ":20:STMT-2026-OCT-28\n"
        ":25:014180009876543210\n"
        ":28C:00045/001\n"
        ":60F:C261028USD100000,00\n"
        ":61:2610281028CR31750,00NTRFNONREF//REF-DEP-WALMART\n"
        ":86:LIQUIDACION COMPENSADA WALMART FACTURA FAC-2026-8841\n"
        ":61:2610281145CR15000,00NTRFNONREF//REF-DEP-AMAZON\n"
        ":86:ABONO PARCIAL FACTURA FAC-AMZ-9912\n"
        ":62F:C261028USD146750,00"
    ),
    "cep_spei": {
        "clave_rastreo": "202610280800341890123456789012",
        "institucion_emisora": "40012",
        "institucion_receptora": "40014",
        "cuenta_ordenante": "012180001234567890",
        "cuenta_beneficiaria": "014180009876543210",
        "monto": 31750.00,
        "iva": 0.00,
        "fecha_operacion": "2026-10-28 16:35:10",
        "concepto_pago": "LIQUIDACION EN FIRME DISPUTA CASO-WM-994820",
        "sello_digital_banxico": "3A8F9B12C4D5E6F7890123456789ABCDEF0123456789ABCDEF0123456789ABCD"
    }
}


# ==============================================================================
# Endpoints
# ==============================================================================

@router.post("/cfdi/stamp-credit-note", response_model=StampedCfdi)
def stamp_credit_note(request: StampCreditNoteRequest):
    """
    Emite y timbra una Nota de Crédito fiscal (CFDI 4.0 TipoDeComprobante='E')
    con Timbre Fiscal Digital del SAT (TFD 1.1), Folio Fiscal UUID y Código QR oficial.
    """
    if request.amount_justified <= Decimal("0.00"):
        raise HTTPException(status_code=400, detail="El monto de la nota de crédito debe ser mayor a cero.")

    emisor = CfdiEmisor(rfc=request.emisor_rfc, nombre=request.emisor_nombre)
    receptor = CfdiReceptor(rfc=request.receptor_rfc, nombre=request.receptor_nombre)

    stamped = CfdiPacSimulator.stamp_credit_note(
        dispute_id=request.dispute_id,
        emisor=emisor,
        receptor=receptor,
        original_invoice_uuid=request.original_invoice_uuid,
        original_invoice_folio=request.original_invoice_folio,
        amount_justified=request.amount_justified,
        adjustment_reason=request.adjustment_reason,
        currency=request.currency
    )
    return stamped


@router.post("/cfdi/stamp-payment-receipt", response_model=StampedCfdi)
def stamp_payment_receipt(request: StampPaymentReceiptRequest):
    """
    Emite y timbra un Recibo Electrónico de Pago con Complemento de Recepción
    de Pagos (CRP 2.0 / TipoDeComprobante='P') acreditando la liquidación bancaria en firme.
    """
    if request.amount_paid <= Decimal("0.00"):
        raise HTTPException(status_code=400, detail="El monto pagado debe ser mayor a cero.")

    emisor = CfdiEmisor(rfc=request.emisor_rfc, nombre=request.emisor_nombre)
    receptor = CfdiReceptor(rfc=request.receptor_rfc, nombre=request.receptor_nombre)

    stamped = CfdiPacSimulator.stamp_payment_receipt_crp(
        emisor=emisor,
        receptor=receptor,
        payment_date_iso=request.payment_date_iso,
        amount_paid=request.amount_paid,
        related_invoice_uuid=request.related_invoice_uuid,
        related_invoice_folio=request.related_invoice_folio,
        previous_balance=request.previous_balance,
        currency=request.currency
    )
    return stamped


@router.post("/bank/parse-mt940", response_model=Mt940Statement)
def parse_mt940_statement(request: ParseMt940Request):
    """
    Decodifica y parsea un extracto bancario multilínea SWIFT MT940 / MT942,
    extrayendo saldos iniciales, saldos finales y cada movimiento clasificado.
    """
    if not request.raw_mt940_text or not request.raw_mt940_text.strip():
        raise HTTPException(status_code=400, detail="El contenido MT940 está vacío.")

    statement = BankReconciliationEngine.parse_mt940(request.raw_mt940_text)
    return statement


@router.post("/bank/verify-cep-spei", response_model=CepSpeiVerificationResult)
def verify_cep_spei(request: VerifyCepSpeiRequest):
    """
    Verifica pericialmente un Comprobante Electrónico de Pago (CEP) del SPEI de Banxico.
    Acredita de forma irrefutable la dispersión electrónica de fondos interbancarios.
    """
    res = BankReconciliationEngine.verify_cep_spei(request.model_dump())
    return res


@router.post("/bank/reconcile", response_model=BankReconciliationResult)
def reconcile_dispute(request: ReconcileDisputeRequest):
    """
    Concilia automáticamente el importe acordado de una disputa contra
    un extracto SWIFT MT940 o una lista de transacciones bancarias.
    """
    entries = request.bank_entries or []
    if request.raw_mt940_text:
        parsed_stmt = BankReconciliationEngine.parse_mt940(request.raw_mt940_text)
        entries.extend(parsed_stmt.transactions)

    if not entries:
        raise HTTPException(status_code=400, detail="Debe suministrar 'raw_mt940_text' o 'bank_entries'.")

    result = BankReconciliationEngine.reconcile_dispute_against_bank(
        expected_settlement_amount=request.expected_amount,
        bank_entries=entries,
        invoice_reference=request.invoice_reference
    )
    return result


@router.get("/samples/{sample_type}")
def get_sample_fiscal(sample_type: str):
    """
    Retorna muestras canónicas de extractos MT940 y comprobantes CEP SPEI.
    """
    clean_type = sample_type.strip().lower()
    if clean_type not in SAMPLE_FISCAL_DATA:
        raise HTTPException(
            status_code=404,
            detail=f"Muestra '{sample_type}' no encontrada. Disponibles: {list(SAMPLE_FISCAL_DATA.keys())}"
        )

    return {
        "sample_type": clean_type,
        "content": SAMPLE_FISCAL_DATA[clean_type]
    }
