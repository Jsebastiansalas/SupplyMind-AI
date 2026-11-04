"""
tests/test_erp_engine.py
Suite de pruebas automatizadas para la Fase 3: Integración ERP y Fiscal CFDI 4.0.
Valida la cuadratura de partida doble bajo NIF C-3 / US GAAP, estructura BAPI SAP,
CSV de Oracle NetSuite y XML válido SAT CFDI 4.0 (Tipo E).
"""

from decimal import Decimal
from pathlib import Path
import xml.etree.ElementTree as ET
import pytest
from fastapi.testclient import TestClient

from api.main import app
from agent.core.erp_engine import (
    ErpEngine,
    generate_cfdi_uuid,
    get_case_fiscal_profile,
)
from agent.core.concession_engine import ConcessionEngine
from data.models import ErpPostingLine, ErpExportPackage

client = TestClient(app)
ROOT_DIR = Path(__file__).resolve().parent.parent


# ============================================================================
# 1. PRUEBAS DE PARTIDA DOBLE ESTRICTA EN CASOS ÉLITE (NIF C-3 / US GAAP)
# ============================================================================

@pytest.mark.parametrize("case_id", [
    "case_005_amazon_shortage",
    "case_006_walmart_otif_pricing",
    "case_007_cisco_large_bundle",
    "case_009_mega_retailer_dispute"
])
def test_erp_posting_lines_double_entry_balance(case_id: str):
    """
    Valida que el asiento contable de partida doble cumpla estrictamente
    sum(Debits) == sum(Credits) == abs(difference) en Decimal.
    """
    report = ConcessionEngine.get_or_create_base_report(case_id)
    total_discrepancy = abs(report.difference)

    lines: list[ErpPostingLine] = ErpEngine.build_erp_posting_lines(report)
    assert len(lines) >= 2

    total_debits = sum((l.debit for l in lines), Decimal("0.00"))
    total_credits = sum((l.credit for l in lines), Decimal("0.00"))

    # Cuadratura estricta al centavo en Decimal
    assert total_debits == total_credits, f"Descuadre contable en {case_id}: Cargos {total_debits} != Abonos {total_credits}"
    assert total_debits == total_discrepancy, f"Total no coincide con retención en {case_id}: {total_debits} != {total_discrepancy}"

    # Verificación de cuentas contables estándar
    account_codes = [l.account_code for l in lines]
    assert "120000" in account_codes  # Clientes (Abono)


# ============================================================================
# 2. PRUEBAS DE ESTRUCTURA SAP (BAPI & IDOC)
# ============================================================================

def test_sap_bapi_payload_and_idoc():
    """Valida la generación de BAPI_ACC_DOCUMENT_POST y el IDoc FIDCCP02."""
    case_id = "case_005_amazon_shortage"
    report = ConcessionEngine.get_or_create_base_report(case_id)
    lines = ErpEngine.build_erp_posting_lines(report)

    # 1. BAPI JSON
    bapi = ErpEngine.generate_sap_bapi_payload(case_id, report, lines)
    header = bapi["DOCUMENTHEADER"]
    assert header["BUS_ACT"] == "RFBU"
    assert header["COMP_CODE"] == "1000"
    assert header["DOC_TYPE"] == "DG"

    # La suma algebraica de CURRENCYAMOUNT debe ser 0.0 (balance neto cero en SAP)
    amounts = [item["AMT_DOCCUR"] for item in bapi["CURRENCYAMOUNT"]]
    assert round(sum(amounts), 2) == 0.0

    # 2. SAP IDoc
    idoc_text = ErpEngine.generate_sap_idoc_text(case_id, report, lines)
    assert "EDI_DC40" in idoc_text
    assert "FIDCCP02" in idoc_text
    assert "E1FIKPF" in idoc_text
    assert "E1FISEG" in idoc_text


# ============================================================================
# 3. PRUEBAS DE ORACLE NETSUITE (JOURNAL ENTRY CSV)
# ============================================================================

def test_netsuite_journal_entry_csv():
    """Valida la estructura y cuadratura del archivo CSV para NetSuite."""
    case_id = "case_006_walmart_otif_pricing"
    report = ConcessionEngine.get_or_create_base_report(case_id)
    lines = ErpEngine.build_erp_posting_lines(report)

    csv_text = ErpEngine.generate_netsuite_csv(case_id, report, lines)
    rows = csv_text.strip().split("\n")
    assert len(rows) >= 3

    header = rows[0]
    assert "ExternalID" in header
    assert "Account" in header
    assert "Debit" in header
    assert "Credit" in header

    # Validar balance de débitos y créditos en el CSV
    debits_sum = Decimal("0.00")
    credits_sum = Decimal("0.00")
    for r in rows[1:]:
        parts = [p.strip().strip('"') for p in r.split(",")]
        # Debit está en columna 7, Credit en columna 8
        debits_sum += Decimal(parts[7])
        credits_sum += Decimal(parts[8])

    assert debits_sum == credits_sum == abs(report.difference)


# ============================================================================
# 4. PRUEBAS DE XML FISCAL CFDI 4.0 NOTA DE CRÉDITO (SAT ANEXO 20)
# ============================================================================

def test_cfdi_40_xml_structure_and_sat_compliance():
    """Valida la sintaxis XML y atributos requeridos por el SAT Anexo 20."""
    case_id = "case_005_amazon_shortage"
    report = ConcessionEngine.get_or_create_base_report(case_id)
    fiscal_profile = get_case_fiscal_profile(case_id)

    xml_content = ErpEngine.generate_cfdi_40_xml(case_id, report, fiscal_profile)
    assert xml_content.startswith("<?xml")

    # Parsear como XML real
    root = ET.fromstring(xml_content)
    assert root.tag == "{http://www.sat.gob.mx/cfd/4}Comprobante"
    assert root.attrib["Version"] == "4.0"
    assert root.attrib["TipoDeComprobante"] == "E"
    assert root.attrib["FormaPago"] == "15"
    assert root.attrib["MetodoPago"] == "PUE"
    assert root.attrib["Moneda"] == "USD"

    # Validar documento relacionado con UUID
    relacionados = root.find("{http://www.sat.gob.mx/cfd/4}CfdiRelacionados")
    assert relacionados is not None
    assert relacionados.attrib["TipoRelacion"] == "01"
    relacionado = relacionados.find("{http://www.sat.gob.mx/cfd/4}CfdiRelacionado")
    assert relacionado is not None
    expected_uuid = generate_cfdi_uuid(case_id).upper()
    assert relacionado.attrib["UUID"] == expected_uuid

    # Validar concepto con clave SAT de saneamiento
    conceptos = root.find("{http://www.sat.gob.mx/cfd/4}Conceptos")
    assert conceptos is not None
    concepto = conceptos.find("{http://www.sat.gob.mx/cfd/4}Concepto")
    assert concepto is not None
    assert concepto.attrib["ClaveProdServ"] == "84111506"
    assert concepto.attrib["ClaveUnidad"] == "ACT"
    assert concepto.attrib["ObjetoImp"] == "02"


# ============================================================================
# 5. PRUEBAS DE INTEGRACIÓN DE ENDPOINTS API REST (Fase 3)
# ============================================================================

def test_api_erp_endpoints():
    """Valida los endpoints REST /api/cases/{case_id}/erp/*."""
    case_id = "case_005_amazon_shortage"

    # 1. Endpoint SAP
    resp_sap = client.get(f"/api/cases/{case_id}/erp/sap")
    assert resp_sap.status_code == 200
    assert resp_sap.json()["format"] == "SAP_BAPI_ACC_DOCUMENT_POST"

    # 2. Endpoint NetSuite
    resp_ns = client.get(f"/api/cases/{case_id}/erp/netsuite")
    assert resp_ns.status_code == 200
    assert resp_ns.json()["format"] == "ORACLE_NETSUITE_JOURNAL_ENTRY"

    # 3. Endpoint CFDI 4.0 XML
    resp_cfdi = client.get(f"/api/cases/{case_id}/erp/cfdi")
    assert resp_cfdi.status_code == 200
    assert "xml" in resp_cfdi.headers["content-type"]
    assert "cfdi:Comprobante" in resp_cfdi.text

    # 4. Endpoint Exportación integral
    resp_exp = client.post(f"/api/cases/{case_id}/erp/export")
    assert resp_exp.status_code == 200
    assert resp_exp.json()["status"] == "success"

    # Verificar existencia física de archivos exportados
    erp_dir = ROOT_DIR / "reports" / f"erp_{case_id}"
    assert (erp_dir / "sap_bapi_post.json").exists()
    assert (erp_dir / "sap_idoc_fidccp02.txt").exists()
    assert (erp_dir / "netsuite_journal_entry.csv").exists()
    assert (erp_dir / "cfdi_40_nota_credito.xml").exists()
    assert (erp_dir / "poliza_contable_nif_c3.md").exists()


def test_api_chat_erp_query():
    """Valida la respuesta a consultas conversacionales sobre ERP y pólizas."""
    case_id = "case_005_amazon_shortage"
    payload = {
        "message": "¿Cómo se contabiliza esta partida bajo NIF C-3 y qué póliza de SAP se genera?",
        "role": "senior_analyst"
    }
    resp = client.post(f"/api/cases/{case_id}/chat", json=payload)
    assert resp.status_code == 200
    reply = resp.json()["reply"]
    assert "Póliza Contable de Saneamiento y Timbrado Fiscal" in reply
    assert "410500" in reply
    assert "120000" in reply
    assert "SAP S/4HANA" in reply
    assert "CFDI 4.0" in reply



# ============================================================================
# 6. PRUEBAS DEL EXPORTADOR FISCAL CFDI 4.0 TIMBRADO & B2B EDI 812 (Eje 3)
# ============================================================================

def test_edi_812_message_structure_and_compliance():
    """Valida la generación del mensaje ANSI ASC X12 812 (Credit/Debit Adjustment) para retailers (Eje 3)."""
    case_id = "case_005_amazon_shortage"
    report = ConcessionEngine.get_or_create_base_report(case_id)
    edi_msg = ErpEngine.generate_edi_812_message(case_id, report)

    assert "ISA*00*" in edi_msg
    assert "GS*CD*SUPPLYMIND" in edi_msg
    assert "ST*812*0001~" in edi_msg
    assert f"BCD*20" in edi_msg
    assert "*CR*" in edi_msg
    assert "CUR*SE*USD~" in edi_msg
    assert "REF*IV*" in edi_msg
    assert "REF*TN*CASE_005_AMAZON_SHORTAGE~" in edi_msg
    assert "N1*SE*SUPPLYMIND" in edi_msg
    assert "N1*BY*AMAZON" in edi_msg
    assert "CDD*C*" in edi_msg
    assert f"AMT*TT*{abs(report.difference):.2f}~" in edi_msg
    assert f"AMT*JD*{report.justified_amount:.2f}~" in edi_msg
    assert f"AMT*RC*{report.claimable_amount:.2f}~" in edi_msg
    assert "SE*14*0001~" in edi_msg
    assert "IEA*1*" in edi_msg


def test_edifact_adjustment_message_structure():
    """Valida el mensaje internacional UN/EDIFACT CREMUL / INVOIC Adjustment (Eje 3)."""
    case_id = "case_006_walmart_otif_pricing"
    report = ConcessionEngine.get_or_create_base_report(case_id)
    edifact_msg = ErpEngine.generate_edifact_adjustment_message(case_id, report)

    assert "UNB+UNOA:3+SUPPLYMIND:ZZ+WALMART:ZZ+" in edifact_msg
    assert "UNH+1+CREMUL:D:03B:UN:EAN008'" in edifact_msg
    assert "BGM+451+NC-CASE_006_WALMART_OTIF_PRICING+9'" in edifact_msg
    assert f"MOA+9:{report.justified_amount:.2f}:USD'" in edifact_msg
    assert "UNT+10+1'" in edifact_msg
    assert "UNZ+1+" in edifact_msg


def test_certified_cfdi_pac_with_sat_timbre():
    """Valida la certificación del CFDI 4.0 con Timbre Fiscal Digital (TFD 1.1) y QR SAT (Eje 3)."""
    case_id = "case_005_amazon_shortage"
    report = ConcessionEngine.get_or_create_base_report(case_id)
    stamped = ErpEngine.generate_certified_cfdi_pac(case_id, report)

    assert stamped.uuid != ""
    assert stamped.tipo_comprobante == "E"
    assert "tfd:TimbreFiscalDigital" in stamped.xml_content
    assert stamped.sello_cfd != ""
    assert stamped.sello_sat != ""
    assert stamped.no_certificado_sat == "00001000000504465028"
    assert stamped.qr_verification_url.startswith("https://verificacfdi.facturaelectronica.sat.gob.mx/default.aspx?id=")


def test_export_full_erp_package_includes_edi_and_certified_cfdi():
    """Valida que export_full_erp_package persista físicamente todos los 9 artefactos del Eje 3."""
    case_id = "case_005_amazon_shortage"
    pkg = ErpEngine.export_full_erp_package(case_id)

    assert pkg.edi_812_x12 is not None
    assert pkg.edifact_message is not None
    assert pkg.cfdi_timbrado_xml is not None
    assert pkg.qr_verification_url is not None

    erp_dir = ROOT_DIR / "reports" / f"erp_{case_id}"
    assert (erp_dir / "edi_812_credit_debit_adjustment.x12").exists()
    assert (erp_dir / "edifact_credit_advice.edi").exists()
    assert (erp_dir / "cfdi_40_timbrado_sat.xml").exists()
    assert (erp_dir / "cfdi_40_nota_credito.xml").exists()
    assert (erp_dir / "sap_bapi_post.json").exists()
    assert (erp_dir / "sap_idoc_fidccp02.txt").exists()
    assert (erp_dir / "netsuite_journal_entry.csv").exists()
    assert (erp_dir / "netsuite_journal_entry.json").exists()
    assert (erp_dir / "poliza_contable_nif_c3.md").exists()


def test_api_edi_and_certified_cfdi_endpoints():
    """Valida los nuevos endpoints REST para descarga directa de EDI 812, EDIFACT y CFDI timbrado (Eje 3)."""
    case_id = "case_005_amazon_shortage"

    # 1. Endpoint EDI 812
    res_edi = client.get(f"/api/cases/{case_id}/erp/edi-812")
    assert res_edi.status_code == 200
    assert "ST*812*0001~" in res_edi.text
    assert "BCD*" in res_edi.text

    # 2. Endpoint EDIFACT
    res_edifact = client.get(f"/api/cases/{case_id}/erp/edifact")
    assert res_edifact.status_code == 200
    assert "CREMUL" in res_edifact.text

    # 3. Endpoint CFDI Timbrado SAT
    res_cfdi = client.get(f"/api/cases/{case_id}/erp/cfdi-timbrado")
    assert res_cfdi.status_code == 200
    assert "TimbreFiscalDigital" in res_cfdi.text
    assert res_cfdi.headers.get("X-SAT-UUID") is not None
    assert "https://verificacfdi.facturaelectronica.sat.gob.mx" in res_cfdi.headers.get("X-SAT-QR-URL", "")
