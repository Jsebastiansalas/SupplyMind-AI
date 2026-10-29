"""
tests/test_edi_engine.py
Suite de pruebas automatizadas para el Motor EDI Nativo B2B ANSI X12 y API REST.
Sprint 5.1 (Frontera 2 de Superinteligencia).
"""

from decimal import Decimal
import pytest
from fastapi.testclient import TestClient

from agent.ingestion.edi_engine import (
    EdiSegment,
    EdiEnvelope,
    EdiX12Parser,
    EdiAuditEngine,
    Edi824Generator,
)
from api.main import app
from api.routes.edi import SAMPLE_EDI_TRANSACTIONS


@pytest.fixture
def client():
    return TestClient(app)


# ==============================================================================
# Pruebas Unitarias del Parser ANSI X12
# ==============================================================================

def test_edi_delimiter_detection():
    """Verifica detección autónoma de separador de elementos y fin de segmento."""
    raw_sample = "ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       *261018*0800*U*00401*000001001*0*P*>~GS*PO*SENDER*RECEIVER*20261018*0800*1001*X*004010~"
    elem_sep, seg_term = EdiX12Parser.detect_delimiters(raw_sample)
    assert elem_sep == "*"
    assert seg_term == "~"


def test_edi_segment_model():
    """Valida el acceso indexado 1-based de los elementos EDI."""
    raw_seg = "PO1*1*500*CA*42.50*PE*IN*SKU-ACEITE-VEG-1L"
    seg = EdiSegment(tag="PO1", elements=["1", "500", "CA", "42.50", "PE", "IN", "SKU-ACEITE-VEG-1L"], raw=raw_seg)
    assert seg.tag == "PO1"
    assert seg.get_element(1) == "1"
    assert seg.get_element(2) == "500"
    assert seg.get_element(4) == "42.50"
    assert seg.get_element(7) == "SKU-ACEITE-VEG-1L"
    assert seg.get_element(99, default="DEFAULT") == "DEFAULT"


def test_edi_850_purchase_order_parsing():
    """Audita el parseo completo de una orden de compra EDI 850."""
    raw_850 = SAMPLE_EDI_TRANSACTIONS["850"]
    txs = EdiX12Parser.parse_document(raw_850)

    assert len(txs) == 1
    tx = txs[0]
    assert tx.transaction_type == "850"
    assert tx.reference_number == "PO-994820"
    assert tx.transaction_date == "20261018"
    assert tx.buyer_name == "WALMART SUPERCENTER DC #6014"
    assert tx.seller_name == "PROVEEDOR ALIMENTICIO S.A."
    assert len(tx.items) == 2

    # Línea 1
    item1 = tx.items[0]
    assert item1.sku == "SKU-ACEITE-VEG-1L"
    assert item1.quantity == Decimal("500")
    assert item1.unit_price == Decimal("42.50")
    assert item1.total_amount == Decimal("21250.00")

    # Línea 2
    item2 = tx.items[1]
    assert item2.sku == "SKU-ARROZ-EXTRA-1KG"
    assert item2.quantity == Decimal("250")
    assert item2.unit_price == Decimal("58.00")
    assert item2.total_amount == Decimal("14500.00")

    assert tx.total_amount == Decimal("35750.00")


def test_edi_810_invoice_parsing():
    """Valida el parseo de una factura comercial EDI 810."""
    raw_810 = SAMPLE_EDI_TRANSACTIONS["810"]
    txs = EdiX12Parser.parse_document(raw_810)

    assert len(txs) == 1
    tx = txs[0]
    assert tx.transaction_type == "810"
    assert tx.reference_number == "FAC-2026-8841"
    assert tx.total_amount == Decimal("35750.00")
    assert len(tx.items) == 2
    assert tx.buyer_name == "WALMART MEXICO RETAIL"


def test_edi_856_asn_parsing():
    """Valida el parseo del Advance Ship Notice (ASN) EDI 856."""
    raw_856 = SAMPLE_EDI_TRANSACTIONS["856"]
    txs = EdiX12Parser.parse_document(raw_856)

    assert len(txs) == 1
    tx = txs[0]
    assert tx.transaction_type == "856"
    assert tx.reference_number == "ASN-8841-BOL"
    assert len(tx.items) == 2
    assert tx.items[0].quantity == Decimal("500")
    assert tx.items[1].quantity == Decimal("250")


def test_edi_861_receiving_advice_parsing():
    """Valida el parseo de constancia de recepción de muelle EDI 861."""
    raw_861 = SAMPLE_EDI_TRANSACTIONS["861"]
    txs = EdiX12Parser.parse_document(raw_861)

    assert len(txs) == 1
    tx = txs[0]
    assert tx.transaction_type == "861"
    assert tx.reference_number == "REC-DC6014"
    assert len(tx.items) == 2
    # El item 1 recibió 480 unidades de 500
    assert tx.items[0].quantity == Decimal("480")
    # El item 2 recibió 250 unidades
    assert tx.items[1].quantity == Decimal("250")


def test_edi_820_remittance_and_deductions_parsing():
    """Valida el parseo de liquidación de pago EDI 820 y desglose de deducciones."""
    raw_820 = SAMPLE_EDI_TRANSACTIONS["820"]
    txs = EdiX12Parser.parse_document(raw_820)

    assert len(txs) == 1
    tx = txs[0]
    assert tx.transaction_type == "820"
    assert tx.total_amount == Decimal("31750.00")
    assert len(tx.deductions) == 1
    ded = tx.deductions[0]
    assert ded.adjustment_code == "86"
    assert ded.amount_deducted == Decimal("4000.00")
    assert "ASN Extemporáneo" in ded.adjustment_reason


def test_edi_997_functional_acknowledgment_parsing():
    """Valida el acuse de recibo funcional EDI 997."""
    raw_997 = SAMPLE_EDI_TRANSACTIONS["997"]
    txs = EdiX12Parser.parse_document(raw_997)

    assert len(txs) == 1
    tx = txs[0]
    assert tx.transaction_type == "997"
    assert "ACK-GRP-SH-1003" in tx.reference_number
    assert "[STATUS:A]" in tx.reference_number


# ==============================================================================
# Pruebas del Motor Forense de Auditoría EDI (EdiAuditEngine)
# ==============================================================================

def test_audit_asn_timeliness_valid():
    """Prueba de caso donde el ASN fue recibido a tiempo (defensa pericial contundente)."""
    asn_raw = SAMPLE_EDI_TRANSACTIONS["856"]
    # 997 timestamp es 20261018 1415 (14:15 UTC)
    ack_997_raw = SAMPLE_EDI_TRANSACTIONS["997"]
    # Cita de muelle a las 20:00 UTC (5.75 horas después) -> supera umbral de 4.0h
    scheduled_dock = "2026-10-18T20:00:00Z"

    result = EdiAuditEngine.audit_asn_timeliness(
        asn_raw=asn_raw,
        ack_997_raw=ack_997_raw,
        scheduled_dock_time_iso=scheduled_dock,
        required_lead_hours=4.0
    )

    assert result["status"] == "success"
    assert result["is_timely"] is True
    assert result["status_label"] == "ASN_TRANSMITIDO_A_TIEMPO"
    assert result["penalty_applicable"] is False
    assert result["lead_time_hours_achieved"] >= 5.0
    assert "toda deducción o penalización por 'ASN Tardío' es legalmente improcedente" in result["binding_legal_defense"]


def test_audit_asn_timeliness_late():
    """Prueba de caso donde el ASN fue recibido con retraso respecto al SLA."""
    asn_raw = SAMPLE_EDI_TRANSACTIONS["856"]
    ack_997_raw = SAMPLE_EDI_TRANSACTIONS["997"]
    # Cita de muelle a las 15:00 UTC (solo 0.75 horas después del 997 a las 14:15)
    scheduled_dock = "2026-10-18T15:00:00Z"

    result = EdiAuditEngine.audit_asn_timeliness(
        asn_raw=asn_raw,
        ack_997_raw=ack_997_raw,
        scheduled_dock_time_iso=scheduled_dock,
        required_lead_hours=4.0
    )

    assert result["status"] == "success"
    assert result["is_timely"] is False
    assert result["status_label"] == "ASN_EXTEMPORANEO"
    assert result["penalty_applicable"] is True
    assert result["lead_time_hours_achieved"] < 4.0
    assert "habilitando la penalidad comercial" in result["binding_legal_defense"]


# ==============================================================================
# Pruebas del Generador ANSI X12 824
# ==============================================================================

def test_generate_edi_824_application_advice():
    """Valida que el generador de 824 produzca segmentos estándar válidos."""
    edi_824 = Edi824Generator.generate_rejection_824(
        dispute_id="CASO-WM-994820",
        retailer_sender_id="WALMART_01",
        supplier_receiver_id="BIMBO_MX",
        invoice_number="FAC-2026-8841",
        deduction_code="86",
        claimable_amount=Decimal("4000.00"),
        rejection_basis="ASN 856 acreditado oportunamente via 997 UTC"
    )

    assert "ISA*" in edi_824
    assert "GS*AG*" in edi_824
    assert "ST*824*" in edi_824
    assert "BGN*00*DISP-CASO-WM-994820*" in edi_824
    assert "OTI*TR*TN*FAC-2026-8841*" in edi_824
    assert "TED*024*RECHAZO DEDUCCION 86~" in edi_824
    assert "AMT*2*4000.00~" in edi_824
    assert "SE*" in edi_824
    assert "GE*1*" in edi_824
    assert "IEA*1*" in edi_824


# ==============================================================================
# Pruebas Endpoints API REST (/api/edi/...)
# ==============================================================================

def test_api_edi_parse_endpoint(client):
    """Prueba el endpoint /api/edi/parse con una orden de compra 850."""
    response = client.post(
        "/api/edi/parse",
        json={"raw_edi_content": SAMPLE_EDI_TRANSACTIONS["850"]}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["total_transactions"] == 1
    assert data["transaction_types"] == ["850"]
    tx = data["transactions"][0]
    assert tx["reference_number"] == "PO-994820"
    assert len(tx["items"]) == 2


def test_api_edi_audit_asn_endpoint(client):
    """Prueba el endpoint /api/edi/audit-asn."""
    response = client.post(
        "/api/edi/audit-asn",
        json={
            "asn_raw": SAMPLE_EDI_TRANSACTIONS["856"],
            "ack_997_raw": SAMPLE_EDI_TRANSACTIONS["997"],
            "scheduled_dock_time_iso": "2026-10-18T22:00:00Z",
            "required_lead_hours": 4.0
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_timely"] is True
    assert data["penalty_applicable"] is False
    assert data["lead_time_hours_achieved"] > 4.0


def test_api_edi_generate_824_endpoint(client):
    """Prueba el endpoint /api/edi/generate-824."""
    response = client.post(
        "/api/edi/generate-824",
        json={
            "dispute_id": "DSP-8841",
            "retailer_sender_id": "WALMART_EDI",
            "supplier_receiver_id": "PROVEEDOR_CORP",
            "invoice_number": "FAC-2026-8841",
            "deduction_code": "86",
            "claimable_amount": 4000.0,
            "rejection_basis": "Acuse 997 certifica recepcion previa a cita"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["dispute_id"] == "DSP-8841"
    assert "ST*824*" in data["raw_edi_824"]
    assert data["segments_count"] >= 10


def test_api_edi_samples_endpoint(client):
    """Prueba la consulta de muestras EDI soportadas."""
    for edi_type in ["850", "810", "856", "861", "820", "997"]:
        res = client.get(f"/api/edi/samples/{edi_type}")
        assert res.status_code == 200
        assert res.json()["transaction_type"] == edi_type

    # 404 para tipo inexistente
    res_bad = client.get("/api/edi/samples/99999")
    assert res_bad.status_code == 404
