"""
tests/test_fiscal_engine.py
Suite de pruebas automatizadas para el Simulador PAC Fiscal CFDI 4.0, Timbre SAT
y Motor de Conciliación Bancaria MT940 / SPEI.
Sprint 5.3 (Frontera 3 de Superinteligencia).
"""

from decimal import Decimal
import pytest
from fastapi.testclient import TestClient

from api.main import app
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
from api.routes.fiscal import SAMPLE_FISCAL_DATA


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def sample_emisor():
    return CfdiEmisor(
        rfc="PRO920101XYZ",
        nombre="PROVEEDOR INDUSTRIAL DE ALIMENTOS S.A. DE C.V.",
        regimen_fiscal="601"
    )


@pytest.fixture
def sample_receptor():
    return CfdiReceptor(
        rfc="NWM9709244W4",
        nombre="NUEVA WAL MART DE MEXICO S. DE R.L. DE C.V.",
        domicilio_fiscal_receptor="06000",
        regimen_fiscal_receptor="601",
        uso_cfdi="G02"
    )


# ==============================================================================
# 1. Pruebas del Simulador PAC Fiscal CFDI 4.0 con Timbre SAT
# ==============================================================================

def test_cfdi_stamp_credit_note(sample_emisor, sample_receptor):
    """Valida la emisión y timbrado de una Nota de Crédito fiscal (TipoDeComprobante='E')."""
    stamped = CfdiPacSimulator.stamp_credit_note(
        dispute_id="CASO-WM-994820",
        emisor=sample_emisor,
        receptor=sample_receptor,
        original_invoice_uuid="4D982F7B-12C0-466A-8A4D-741E0F584C92",
        original_invoice_folio="FAC-2026-8841",
        amount_justified=Decimal("4000.00"),
        adjustment_reason="Ajuste por merma operativa autorizada en muelle",
        currency="USD"
    )

    assert isinstance(stamped, StampedCfdi)
    assert stamped.tipo_comprobante == "E"
    assert stamped.serie == "NC"
    assert len(stamped.uuid) == 36
    assert stamped.total == Decimal("4000.00")
    assert stamped.subtotal == Decimal("4000.00")
    assert stamped.rfc_emisor == "PRO920101XYZ"
    assert stamped.rfc_receptor == "NWM9709244W4"

    # Verificar cadena original y sellos SAT
    assert stamped.cadena_original_tfd.startswith(f"||1.1|{stamped.uuid}|")
    assert len(stamped.sello_sat) > 20
    assert len(stamped.sello_cfd) > 20

    # Verificar URL del Código QR Fiscal del SAT
    assert "verificacfdi.facturaelectronica.sat.gob.mx" in stamped.qr_verification_url
    assert f"id={stamped.uuid}" in stamped.qr_verification_url
    assert f"re={sample_emisor.rfc}" in stamped.qr_verification_url
    assert f"rr={sample_receptor.rfc}" in stamped.qr_verification_url
    assert "tt=4000.00" in stamped.qr_verification_url

    # Validar estructura XML
    assert 'xmlns:cfdi="http://www.sat.gob.mx/cfd/4"' in stamped.xml_content
    assert 'xmlns:tfd="http://www.sat.gob.mx/TimbreFiscalDigital"' in stamped.xml_content
    assert 'TipoDeComprobante="E"' in stamped.xml_content
    assert 'UUID="4D982F7B-12C0-466A-8A4D-741E0F584C92"' in stamped.xml_content


def test_cfdi_stamp_payment_receipt_crp(sample_emisor, sample_receptor):
    """Valida el timbrado del Complemento de Recepción de Pagos (CRP 2.0)."""
    stamped = CfdiPacSimulator.stamp_payment_receipt_crp(
        emisor=sample_emisor,
        receptor=sample_receptor,
        payment_date_iso="2026-10-28T16:30:00",
        amount_paid=Decimal("31750.00"),
        related_invoice_uuid="4D982F7B-12C0-466A-8A4D-741E0F584C92",
        related_invoice_folio="FAC-2026-8841",
        previous_balance=Decimal("35750.00"),
        currency="USD"
    )

    assert stamped.tipo_comprobante == "P"
    assert stamped.serie == "PAG"
    assert stamped.total == Decimal("0.00")  # En CFDI de pago el total del comprobante es 0
    assert 'xmlns:pago20="http://www.sat.gob.mx/Pagos20"' in stamped.xml_content
    assert 'MontoTotalPagos="31750.00"' in stamped.xml_content
    assert 'ImpSaldoAnt="35750.00"' in stamped.xml_content
    assert 'ImpPagado="31750.00"' in stamped.xml_content
    assert 'ImpSaldoInsoluto="4000.00"' in stamped.xml_content  # 35750 - 31750 = 4000.00 exacto


# ==============================================================================
# 2. Pruebas del Motor de Extractos SWIFT MT940
# ==============================================================================

def test_bank_parse_mt940_statement():
    """Valida la decodificación de un extracto bancario SWIFT MT940."""
    raw_mt940 = SAMPLE_FISCAL_DATA["mt940"]
    statement = BankReconciliationEngine.parse_mt940(raw_mt940)

    assert isinstance(statement, Mt940Statement)
    assert statement.statement_number == "00045/001"
    assert statement.account_number == "014180009876543210"
    assert statement.currency == "USD"
    assert statement.opening_balance_amount == Decimal("100000.00")
    assert statement.closing_balance_amount == Decimal("146750.00")
    assert len(statement.transactions) == 2

    # Transacción 1: Walmart ($31,750.00 USD)
    tx1 = statement.transactions[0]
    assert tx1.credit_debit == "CR"
    assert tx1.amount == Decimal("31750.00")
    assert "REF-DEP-WALMART" in tx1.bank_reference
    assert "WALMART" in tx1.detailed_concept
    assert "FAC-2026-8841" in tx1.detailed_concept

    # Transacción 2: Amazon ($15,000.00 USD)
    tx2 = statement.transactions[1]
    assert tx2.credit_debit == "CR"
    assert tx2.amount == Decimal("15000.00")


# ==============================================================================
# 3. Pruebas del CEP SPEI del Banco de México
# ==============================================================================

def test_bank_verify_cep_spei():
    """Valida la certificación del Comprobante Electrónico de Pago de Banxico."""
    cep_payload = SAMPLE_FISCAL_DATA["cep_spei"]
    res = BankReconciliationEngine.verify_cep_spei(cep_payload)

    assert isinstance(res, CepSpeiVerificationResult)
    assert res.is_valid_banxico_cep is True
    assert res.clave_rastreo == "202610280800341890123456789012"
    assert res.monto == Decimal("31750.00")
    assert "BBVA México" in res.institucion_emisora
    assert "Banco Santander México" in res.institucion_receptora
    assert len(res.sello_digital_banxico) > 10
    assert "||2026-10-28 16:35:10|" in res.cadena_original
    assert "liquidación irrevocable y en firme" in res.binding_legal_summary


# ==============================================================================
# 4. Pruebas del Algoritmo de Conciliación Automática
# ==============================================================================

def test_reconcile_dispute_exact_match():
    """Conciliación bancaria exacta con $0.00 MAE."""
    raw_mt940 = SAMPLE_FISCAL_DATA["mt940"]
    statement = BankReconciliationEngine.parse_mt940(raw_mt940)

    # Esperamos el pago neto de Walmart: $31,750.00
    res = BankReconciliationEngine.reconcile_dispute_against_bank(
        expected_settlement_amount=Decimal("31750.00"),
        bank_entries=statement.transactions,
        invoice_reference="FAC-2026-8841"
    )

    assert res.is_reconciled is True
    assert res.reconciliation_status == "CONCILIADO_EXACTO"
    assert res.actual_amount == Decimal("31750.00")
    assert res.variance == Decimal("0.00")
    assert res.matched_entry is not None
    assert "REF-DEP-WALMART" in res.matched_entry.bank_reference
    assert "Fondos liquidados en firme" in res.pericial_certification


def test_reconcile_dispute_fee_variance():
    """Conciliación por referencia de factura con deducción menor de comisión bancaria."""
    # Movimiento con $31,735.00 ($15 USD de comisión bancaria internacional)
    mock_entry = BankTransactionEntry(
        entry_id="TX-FEE-TEST",
        entry_date="2026-10-28",
        value_date="2026-10-28",
        credit_debit="CR",
        amount=Decimal("31735.00"),
        currency="USD",
        bank_reference="DEP-WIRE-WM",
        detailed_concept="TRANSFERENCIA LIQUIDACION FAC-2026-8841 MENOS COMISION",
        source_format="MT940"
    )

    res = BankReconciliationEngine.reconcile_dispute_against_bank(
        expected_settlement_amount=Decimal("31750.00"),
        bank_entries=[mock_entry],
        invoice_reference="FAC-2026-8841",
        fee_tolerance=Decimal("50.00")
    )

    assert res.is_reconciled is True
    assert res.reconciliation_status == "DISCREPANCIA_COMISION"
    assert res.variance == Decimal("15.00")


def test_reconcile_dispute_unmatched_pending():
    """Caso donde no se ha recibido el depósito bancario."""
    raw_mt940 = SAMPLE_FISCAL_DATA["mt940"]
    statement = BankReconciliationEngine.parse_mt940(raw_mt940)

    # Reclamamos $99,999.00 no existente
    res = BankReconciliationEngine.reconcile_dispute_against_bank(
        expected_settlement_amount=Decimal("99999.00"),
        bank_entries=statement.transactions,
        invoice_reference="FAC-INEXISTENTE"
    )

    assert res.is_reconciled is False
    assert res.reconciliation_status == "NO_CONCILIADO_PENDIENTE"
    assert res.actual_amount == Decimal("0.00")
    assert res.variance == Decimal("99999.00")


# ==============================================================================
# 5. Pruebas Endpoints API REST (/api/fiscal/...)
# ==============================================================================

def test_api_fiscal_stamp_credit_note_endpoint(client):
    """Prueba el endpoint /api/fiscal/cfdi/stamp-credit-note."""
    response = client.post(
        "/api/fiscal/cfdi/stamp-credit-note",
        json={
            "dispute_id": "DISP-WM-001",
            "amount_justified": 4000.0,
            "adjustment_reason": "Merma operativa aceptada en muelle",
            "original_invoice_uuid": "4D982F7B-12C0-466A-8A4D-741E0F584C92",
            "original_invoice_folio": "FAC-2026-8841"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["tipo_comprobante"] == "E"
    assert data["serie"] == "NC"
    assert len(data["uuid"]) == 36
    assert Decimal(data["total"]) == Decimal("4000.00")
    assert "TimbreFiscalDigital" in data["xml_content"]



def test_api_fiscal_stamp_payment_receipt_endpoint(client):
    """Prueba el endpoint /api/fiscal/cfdi/stamp-payment-receipt."""
    response = client.post(
        "/api/fiscal/cfdi/stamp-payment-receipt",
        json={
            "amount_paid": 31750.0,
            "related_invoice_uuid": "4D982F7B-12C0-466A-8A4D-741E0F584C92",
            "related_invoice_folio": "FAC-2026-8841",
            "previous_balance": 35750.0
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["tipo_comprobante"] == "P"
    assert "Pagos20" in data["xml_content"]


def test_api_fiscal_parse_mt940_endpoint(client):
    """Prueba el endpoint /api/fiscal/bank/parse-mt940."""
    response = client.post(
        "/api/fiscal/bank/parse-mt940",
        json={"raw_mt940_text": SAMPLE_FISCAL_DATA["mt940"]}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["statement_number"] == "00045/001"
    assert len(data["transactions"]) == 2


def test_api_fiscal_verify_cep_spei_endpoint(client):
    """Prueba el endpoint /api/fiscal/bank/verify-cep-spei."""
    response = client.post(
        "/api/fiscal/bank/verify-cep-spei",
        json=SAMPLE_FISCAL_DATA["cep_spei"]
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid_banxico_cep"] is True
    assert data["clave_rastreo"] == "202610280800341890123456789012"


def test_api_fiscal_reconcile_endpoint(client):
    """Prueba el endpoint /api/fiscal/bank/reconcile."""
    response = client.post(
        "/api/fiscal/bank/reconcile",
        json={
            "expected_amount": 31750.0,
            "invoice_reference": "FAC-2026-8841",
            "raw_mt940_text": SAMPLE_FISCAL_DATA["mt940"]
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_reconciled"] is True
    assert data["reconciliation_status"] == "CONCILIADO_EXACTO"
    assert Decimal(data["actual_amount"]) == Decimal("31750.00")



def test_api_fiscal_samples_endpoint(client):
    """Prueba la consulta de muestras fiscales."""
    for s_type in ["mt940", "cep_spei"]:
        res = client.get(f"/api/fiscal/samples/{s_type}")
        assert res.status_code == 200
        assert res.json()["sample_type"] == s_type
