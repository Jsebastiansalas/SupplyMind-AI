"""
tests/test_phase9_multiregime_fiscal.py
Suite de Pruebas Automatizadas para el Motor Tributario Multirrégimen B2B (Fase 9).
Valida:
1. HU 9.3.1: FiscalRegimeResolver (Detección por caso, SKU, metadatos, código postal y régimen explícito).
2. HU 9.3.2: Pólizas SAP/NetSuite y XML CFDI 4.0 con Nodos <cfdi:Impuestos> exactos y cuadratura contable $0.00 MAE.
3. Simulador PAC (CfdiPacSimulator.stamp_credit_note) multirrégimen y endpoints REST.
"""

from decimal import Decimal
import xml.etree.ElementTree as ET
import pytest
from fastapi.testclient import TestClient

from api.main import app
from agent.core.erp_engine import (
    FiscalTaxProfile,
    FiscalRegimeResolver,
    ErpEngine,
    get_case_fiscal_profile
)
from agent.core.concession_engine import ConcessionEngine
from agent.fiscal.cfdi_pac_simulator import (
    CfdiEmisor,
    CfdiReceptor,
    CfdiPacSimulator,
    StampedCfdi
)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def sample_emisor():
    return CfdiEmisor(
        rfc="SMI20260101AA1",
        nombre="SUPPLYMIND AI ENTERPRISE SOLUTIONS S.A. DE C.V.",
        regimen_fiscal="601"
    )


@pytest.fixture
def sample_receptor():
    return CfdiReceptor(
        rfc="WAL901231AA1",
        nombre="NUEVA WAL-MART DE MEXICO S. DE R.L. DE C.V.",
        domicilio_fiscal_receptor="11520",
        regimen_fiscal_receptor="601",
        uso_cfdi="G02"
    )


# ==============================================================================
# 1. PRUEBAS DEL RESOLUTOR DE RÉGIMEN FISCAL (FiscalRegimeResolver)
# ==============================================================================

def test_fiscal_regime_resolver_explicit_and_aliases():
    """Valida la resolución explícita y normalización de alias para los 5 regímenes."""
    # 1. STANDARD_VAT_16
    p1 = FiscalRegimeResolver.resolve(regime="STANDARD_VAT_16")
    assert p1.regime_code == "STANDARD_VAT_16"
    assert p1.vat_rate == Decimal("0.16")
    assert p1.ieps_rate == Decimal("0.00")
    assert p1.total_tax_factor == Decimal("1.16")
    assert p1.objeto_imp == "02"
    assert p1.exportacion == "01"

    # Alias
    assert FiscalRegimeResolver.resolve(regime="iva_16").regime_code == "STANDARD_VAT_16"
    assert FiscalRegimeResolver.resolve(regime="GENERAL").regime_code == "STANDARD_VAT_16"

    # 2. ZERO_RATED_FOOD_PHARMA_0
    p2 = FiscalRegimeResolver.resolve(regime="ZERO_RATED_FOOD_PHARMA_0")
    assert p2.regime_code == "ZERO_RATED_FOOD_PHARMA_0"
    assert p2.vat_rate == Decimal("0.00")
    assert p2.total_tax_factor == Decimal("1.00")
    assert p2.tax_code_erp == "V0"

    # Alias
    assert FiscalRegimeResolver.resolve(regime="TASA_0").regime_code == "ZERO_RATED_FOOD_PHARMA_0"
    assert FiscalRegimeResolver.resolve(regime="FOOD").regime_code == "ZERO_RATED_FOOD_PHARMA_0"

    # 3. BORDER_REGION_VAT_8
    p3 = FiscalRegimeResolver.resolve(regime="BORDER_REGION_VAT_8")
    assert p3.regime_code == "BORDER_REGION_VAT_8"
    assert p3.vat_rate == Decimal("0.08")
    assert p3.total_tax_factor == Decimal("1.08")
    assert p3.tax_code_erp == "V8"

    # Alias
    assert FiscalRegimeResolver.resolve(regime="FRONTERA").regime_code == "BORDER_REGION_VAT_8"
    assert FiscalRegimeResolver.resolve(regime="8%").regime_code == "BORDER_REGION_VAT_8"

    # 4. IEPS_HIGH_CALORIE_BEVERAGE
    p4 = FiscalRegimeResolver.resolve(regime="IEPS_HIGH_CALORIE_BEVERAGE")
    assert p4.regime_code == "IEPS_HIGH_CALORIE_BEVERAGE"
    assert p4.vat_rate == Decimal("0.16")
    assert p4.ieps_rate == Decimal("0.08")
    assert p4.total_tax_factor == Decimal("1.2528")
    assert p4.tax_code_erp == "VIEPS"

    # Alias
    assert FiscalRegimeResolver.resolve(regime="IEPS").regime_code == "IEPS_HIGH_CALORIE_BEVERAGE"
    assert FiscalRegimeResolver.resolve(regime="BEVERAGE").regime_code == "IEPS_HIGH_CALORIE_BEVERAGE"

    # 5. EXPORT_USMCA_0
    p5 = FiscalRegimeResolver.resolve(regime="EXPORT_USMCA_0")
    assert p5.regime_code == "EXPORT_USMCA_0"
    assert p5.vat_rate == Decimal("0.00")
    assert p5.objeto_imp == "01"
    assert p5.exportacion == "02"
    assert p5.tax_code_erp == "VEXP"

    # Alias
    assert FiscalRegimeResolver.resolve(regime="USMCA").regime_code == "EXPORT_USMCA_0"
    assert FiscalRegimeResolver.resolve(regime="TMEC").regime_code == "EXPORT_USMCA_0"


def test_fiscal_regime_resolver_corpus_and_geo_detection():
    """Valida la inferencia inteligente por palabras clave y código postal receptor."""
    # Inferencia por keywords en caso / SKU
    assert FiscalRegimeResolver.resolve(case_id="disputa_bimbo_alimentos_granos").regime_code == "ZERO_RATED_FOOD_PHARMA_0"
    assert FiscalRegimeResolver.resolve(sku="SKU-REFRESCO-SODA-COLA-2L").regime_code == "IEPS_HIGH_CALORIE_BEVERAGE"
    assert FiscalRegimeResolver.resolve(case_id="dhl_crossborder_export_usmca").regime_code == "EXPORT_USMCA_0"
    assert FiscalRegimeResolver.resolve(case_id="cedis_tijuana_frontera_norte").regime_code == "BORDER_REGION_VAT_8"

    # Inferencia geográfica por Código Postal Fronterizo
    assert FiscalRegimeResolver.resolve(postal_code="22000").regime_code == "BORDER_REGION_VAT_8"  # Tijuana BC
    assert FiscalRegimeResolver.resolve(postal_code="32000").regime_code == "BORDER_REGION_VAT_8"  # Cd. Juárez Chih
    assert FiscalRegimeResolver.resolve(postal_code="88000").regime_code == "BORDER_REGION_VAT_8"  # Nuevo Laredo Tamps

    # Fallback default general 16%
    assert FiscalRegimeResolver.resolve(case_id="case_005_amazon_shortage").regime_code == "STANDARD_VAT_16"


# ==============================================================================
# 2. PRUEBAS DE DESGLOSE ARITMÉTICO Y CUADRATURA EXACTA ($0.00 MAE)
# ==============================================================================

@pytest.mark.parametrize("regime_code,amount", [
    ("STANDARD_VAT_16", Decimal("1000.00")),
    ("STANDARD_VAT_16", Decimal("1234.57")),
    ("ZERO_RATED_FOOD_PHARMA_0", Decimal("1500.50")),
    ("BORDER_REGION_VAT_8", Decimal("2160.00")),
    ("BORDER_REGION_VAT_8", Decimal("999.99")),
    ("IEPS_HIGH_CALORIE_BEVERAGE", Decimal("1252.80")),
    ("IEPS_HIGH_CALORIE_BEVERAGE", Decimal("3333.33")),
    ("EXPORT_USMCA_0", Decimal("50000.00")),
])
def test_fiscal_tax_profile_breakdown_exactness(regime_code, amount):
    """Garantiza que para cualquier régimen y monto la suma subtotal + impuestos == monto total exacto."""
    profile = FiscalRegimeResolver.resolve(regime=regime_code)
    b = profile.calculate_breakdown(amount)

    assert b["total"] == amount
    assert b["subtotal"] + b["vat"] + b["ieps"] == amount
    assert b["total_tax"] == b["vat"] + b["ieps"]

    if regime_code == "ZERO_RATED_FOOD_PHARMA_0":
        assert b["vat"] == Decimal("0.00")
        assert b["ieps"] == Decimal("0.00")
        assert b["subtotal"] == amount
    elif regime_code == "EXPORT_USMCA_0":
        assert b["vat"] == Decimal("0.00")
        assert b["ieps"] == Decimal("0.00")
        assert b["subtotal"] == amount
    elif regime_code == "IEPS_HIGH_CALORIE_BEVERAGE":
        assert b["ieps"] > Decimal("0.00")
        assert b["vat"] > Decimal("0.00")


# ==============================================================================
# 3. PRUEBAS DE PÓLIZAS ERP Y PARTIDA DOBLE MULTIRRÉGIMEN (HU 9.3.2)
# ==============================================================================

@pytest.mark.parametrize("regime_code", [
    "STANDARD_VAT_16",
    "ZERO_RATED_FOOD_PHARMA_0",
    "BORDER_REGION_VAT_8",
    "IEPS_HIGH_CALORIE_BEVERAGE",
    "EXPORT_USMCA_0",
])
def test_erp_posting_lines_multiregime_double_entry(regime_code):
    """Valida la cuadratura contable NIF C-3 debits == credits == abs(diff) para todos los regímenes."""
    case_id = "case_005_amazon_shortage"
    report = ConcessionEngine.get_or_create_base_report(case_id)
    lines = ErpEngine.build_erp_posting_lines(report, fiscal_regime=regime_code)

    total_debits = sum(l.debit for l in lines)
    total_credits = sum(l.credit for l in lines)
    total_diff = abs(report.difference)

    # Cuadratura contable estricta
    assert total_debits == total_credits
    assert total_debits == total_diff

    # Validar cuentas según régimen
    account_codes = [l.account_code for l in lines]
    assert "410500" in account_codes  # Descuentos y Bonificaciones
    assert "120000" in account_codes  # Cuentas por Cobrar

    if regime_code == "IEPS_HIGH_CALORIE_BEVERAGE":
        assert "210900" in account_codes  # Cuenta contable IEPS
        assert "210800" in account_codes  # Cuenta contable IVA
    elif regime_code in ("STANDARD_VAT_16", "BORDER_REGION_VAT_8"):
        assert "210800" in account_codes  # Cuenta contable IVA
        assert "210900" not in account_codes
    elif regime_code in ("ZERO_RATED_FOOD_PHARMA_0", "EXPORT_USMCA_0"):
        assert "210900" not in account_codes
        assert "210800" not in account_codes


# ==============================================================================
# 4. PRUEBAS DE GENERACIÓN CFDI 4.0 XML MULTIRRÉGIMEN
# ==============================================================================

def test_cfdi_40_xml_ieps_and_multiregime():
    """Valida que el XML CFDI 4.0 contenga los nodos de impuestos precisos según el régimen."""
    case_id = "case_006_walmart_otif_pricing"
    report = ConcessionEngine.get_or_create_base_report(case_id)
    fiscal_profile = get_case_fiscal_profile(case_id)

    # 1. IEPS + IVA
    xml_ieps = ErpEngine.generate_cfdi_40_xml(case_id, report, fiscal_profile, fiscal_regime="IEPS_HIGH_CALORIE_BEVERAGE")
    root_ieps = ET.fromstring(xml_ieps)
    assert root_ieps.attrib["TipoDeComprobante"] == "E"
    assert root_ieps.attrib["Exportacion"] == "01"

    # Verificar nodos Impuesto 003 (IEPS) y 002 (IVA)
    concepto_ieps = root_ieps.find("{http://www.sat.gob.mx/cfd/4}Conceptos/{http://www.sat.gob.mx/cfd/4}Concepto")
    assert concepto_ieps.attrib["ObjetoImp"] == "02"
    traslados_ieps = concepto_ieps.findall(".//{http://www.sat.gob.mx/cfd/4}Traslado")
    assert len(traslados_ieps) == 2
    impuestos_encontrados = {t.attrib["Impuesto"]: t.attrib["TasaOCuota"] for t in traslados_ieps}
    assert "003" in impuestos_encontrados and impuestos_encontrados["003"] == "0.080000"
    assert "002" in impuestos_encontrados and impuestos_encontrados["002"] == "0.160000"

    # 2. Región Fronteriza 8%
    xml_border = ErpEngine.generate_cfdi_40_xml(case_id, report, fiscal_profile, fiscal_regime="BORDER_REGION_VAT_8")
    root_border = ET.fromstring(xml_border)
    concepto_border = root_border.find(".//{http://www.sat.gob.mx/cfd/4}Concepto")
    assert concepto_border.attrib["ObjetoImp"] == "02"
    traslados_border = concepto_border.findall(".//{http://www.sat.gob.mx/cfd/4}Traslado")
    assert len(traslados_border) == 1
    assert traslados_border[0].attrib["Impuesto"] == "002"
    assert traslados_border[0].attrib["TasaOCuota"] == "0.080000"

    # 3. Tasa 0% Alimentos / Farmacéutica
    xml_zero = ErpEngine.generate_cfdi_40_xml(case_id, report, fiscal_profile, fiscal_regime="ZERO_RATED_FOOD_PHARMA_0")
    root_zero = ET.fromstring(xml_zero)
    concepto_zero = root_zero.find(".//{http://www.sat.gob.mx/cfd/4}Concepto")
    assert concepto_zero.attrib["ObjetoImp"] == "02"
    traslados_zero = concepto_zero.findall(".//{http://www.sat.gob.mx/cfd/4}Traslado")
    assert len(traslados_zero) == 1
    assert traslados_zero[0].attrib["TasaOCuota"] == "0.000000"
    assert traslados_zero[0].attrib["Importe"] == "0.00"

    # 4. Exportación T-MEC
    xml_exp = ErpEngine.generate_cfdi_40_xml(case_id, report, fiscal_profile, fiscal_regime="EXPORT_USMCA_0")
    root_exp = ET.fromstring(xml_exp)
    assert root_exp.attrib["Exportacion"] == "02"
    concepto_exp = root_exp.find(".//{http://www.sat.gob.mx/cfd/4}Concepto")
    assert concepto_exp.attrib["ObjetoImp"] == "01"
    assert concepto_exp.find(".//{http://www.sat.gob.mx/cfd/4}Impuestos") is None


# ==============================================================================
# 5. PRUEBAS DEL SIMULADOR PAC Y TIMBRADO SAT MULTIRRÉGIMEN
# ==============================================================================

def test_pac_simulator_stamp_credit_note_with_breakdown(sample_emisor, sample_receptor):
    """Valida el timbrado PAC de Nota de Crédito con desglose de impuestos activo."""
    # Stamping con IEPS
    stamped = CfdiPacSimulator.stamp_credit_note(
        dispute_id="CASO-BEVERAGE-IEPS-101",
        emisor=sample_emisor,
        receptor=sample_receptor,
        original_invoice_uuid="9C694E25-0E37-4D2A-949B-E2B4B28FD111",
        original_invoice_folio="FAC-2026-9099",
        amount_justified=Decimal("1252.80"),
        adjustment_reason="Ajuste por merma en bebidas saborizadas y energéticas",
        currency="USD",
        fiscal_regime="IEPS_HIGH_CALORIE_BEVERAGE",
        breakdown_taxes=True
    )

    assert isinstance(stamped, StampedCfdi)
    assert stamped.total == Decimal("1252.80")
    assert stamped.subtotal < Decimal("1252.80")  # Subtotal debe ser ~1000.00
    assert stamped.subtotal == Decimal("1000.00")
    assert len(stamped.uuid) == 36
    assert len(stamped.sello_sat) > 20
    assert len(stamped.sello_cfd) > 20

    # Parsear XML retornado
    root = ET.fromstring(stamped.xml_content)
    assert root.attrib["Total"] == "1252.80"
    assert root.attrib["SubTotal"] == "1000.00"

    # Verificar traslados en Comprobante
    impuestos_nodo = root.find("{http://www.sat.gob.mx/cfd/4}Impuestos")
    assert impuestos_nodo is not None
    assert Decimal(impuestos_nodo.attrib["TotalImpuestosTrasladados"]) == Decimal("252.80")


# ==============================================================================
# 6. PRUEBAS DE INTEGRACIÓN DE ENDPOINTS REST CON QUERY PARAMS FISCALES
# ==============================================================================

def test_api_erp_and_fiscal_endpoints_multiregime(client):
    """Valida la interacción HTTP con los endpoints REST pasando régimen fiscal."""
    case_id = "case_005_amazon_shortage"

    # 1. Endpoint CFDI XML con régimen Frontera 8%
    resp_cfdi = client.get(f"/api/cases/{case_id}/erp/cfdi?fiscal_regime=BORDER_REGION_VAT_8")
    assert resp_cfdi.status_code == 200
    assert "0.080000" in resp_cfdi.text

    # 2. Endpoint SAP BAPI con IEPS
    resp_sap = client.get(f"/api/cases/{case_id}/erp/sap?fiscal_regime=IEPS_HIGH_CALORIE_BEVERAGE")
    assert resp_sap.status_code == 200
    sap_gl = resp_sap.json()["bapi_payload"]["ACCOUNTGL"]
    gl_accounts = [item["GL_ACCOUNT"] for item in sap_gl]
    assert "0000210900" in gl_accounts  # Cuenta contable IEPS
    assert "0000210800" in gl_accounts  # Cuenta contable IVA

    # 3. Endpoint PAC Stamp Credit Note con desglose
    payload = {
        "dispute_id": "DISP-API-TEST-99",
        "emisor_rfc": "PRO920101XYZ",
        "emisor_nombre": "PROVEEDOR INDUSTRIAL S.A.",
        "receptor_rfc": "NWM9709244W4",
        "receptor_nombre": "NUEVA WAL MART DE MEXICO",
        "original_invoice_uuid": "4D982F7B-12C0-466A-8A4D-741E0F584C92",
        "original_invoice_folio": "FAC-8841",
        "amount_justified": 1080.00,
        "adjustment_reason": "Ajuste frontera norte",
        "currency": "USD",
        "fiscal_regime": "BORDER_REGION_VAT_8",
        "breakdown_taxes": True
    }
    resp_pac = client.post("/api/fiscal/cfdi/stamp-credit-note", json=payload)
    assert resp_pac.status_code == 200
    data = resp_pac.json()
    assert Decimal(str(data["total"])) == Decimal("1080.00")
    assert Decimal(str(data["subtotal"])) == Decimal("1000.00")
    assert "0.080000" in data["xml_content"]
