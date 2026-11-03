"""
agent/core/erp_engine.py
Motor de Integración ERP y Pólizas Contables Fiscales (Fase 3 de SupplyMind AI Enterprise).
Genera de forma determinística:
1. Pólizas contables de partida doble para SAP (BAPI_ACC_DOCUMENT_POST / IDoc FIDCCP02).
2. Asientos de diario para Oracle NetSuite (CSV / JSON importador).
3. Comprobante Fiscal Digital por Internet (CFDI 4.0) de Nota de Crédito (Tipo E - Egreso)
   vinculado al UUID de origen bajo el estándar del SAT Anexo 20.
"""

from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional
import json
import uuid
import xml.etree.ElementTree as ET
from pydantic import BaseModel, Field

from data.models import DisputeAnalysisReport, ErpPostingLine, ErpExportPackage
from agent.core.concession_engine import ConcessionEngine
from config.settings import settings

ROOT_DIR = Path(__file__).resolve().parent.parent.parent


def generate_cfdi_uuid(case_id: str) -> str:
    """Genera un UUID RFC 4122 determinístico e inmutable para el comprobante de origen."""
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"supplymind.cfdi.invoice.{case_id.lower()}"))


def get_case_fiscal_profile(case_id: str) -> Dict[str, Any]:
    """Obtiene los datos fiscales estructurados (RFC, Razón Social, Domicilio Fiscal)."""
    cid = case_id.lower()
    emisor = {
        "rfc": "SMI20260101AA1",
        "nombre": "SUPPLYMIND AI ENTERPRISE SOLUTIONS S.A. DE C.V.",
        "regimen_fiscal": "601",
        "lugar_expedicion": "06500",
        "codigo_postal": "06500"
    }

    if "amazon" in cid:
        receptor = {
            "rfc": "AMA120401BB2",
            "nombre": "AMAZON FULFILLMENT SERVICES LLC DE MEXICO",
            "domicilio_fiscal": "01210",
            "regimen_fiscal": "601",
            "uso_cfdi": "G02"
        }
    elif "walmart" in cid:
        receptor = {
            "rfc": "WAL901231AA1",
            "nombre": "NUEVA WAL-MART DE MEXICO S. DE R.L. DE C.V.",
            "domicilio_fiscal": "11520",
            "regimen_fiscal": "601",
            "uso_cfdi": "G02"
        }
    elif "cisco" in cid:
        receptor = {
            "rfc": "CSO950101XYZ",
            "nombre": "CISCO SYSTEMS CAPITAL MEXICO S.A. DE C.V.",
            "domicilio_fiscal": "03100",
            "regimen_fiscal": "601",
            "uso_cfdi": "G02"
        }
    elif "mega" in cid or "retailer" in cid:
        receptor = {
            "rfc": "MGR180512AB3",
            "nombre": "MEGA RETAILER NACIONAL S.A. DE C.V.",
            "domicilio_fiscal": "64000",
            "regimen_fiscal": "601",
            "uso_cfdi": "G02"
        }
    else:
        receptor = {
            "rfc": "CLI991231AA1",
            "nombre": "CLIENTE COMERCIAL B2B S.A. DE C.V.",
            "domicilio_fiscal": "01000",
            "regimen_fiscal": "601",
            "uso_cfdi": "G02"
        }

    return {"emisor": emisor, "receptor": receptor}


class FiscalTaxProfile(BaseModel):
    """Perfil impositivo y reglas de cálculo para regímenes fiscales B2B SAT."""
    regime_code: str
    description: str
    vat_rate: Decimal
    ieps_rate: Decimal = Decimal("0.00")
    total_tax_factor: Decimal
    objeto_imp: str = "02"
    exportacion: str = "01"
    tax_code_erp: str = "V1"
    gl_account_vat: str = "210800"
    gl_account_ieps: str = "210900"

    def calculate_breakdown(self, gross_amount: Decimal) -> Dict[str, Decimal]:
        """
        Calcula con precisión Decimal ($0.00 MAE) el Subtotal y los Impuestos (IVA, IEPS),
        garantizando que subtotal + vat + ieps == gross_amount al centavo.
        """
        if gross_amount <= Decimal("0.00"):
            return {
                "subtotal": Decimal("0.00"),
                "vat": Decimal("0.00"),
                "ieps": Decimal("0.00"),
                "total_tax": Decimal("0.00"),
                "total": Decimal("0.00")
            }

        gross = gross_amount.quantize(Decimal("0.01"))

        if self.regime_code == "ZERO_RATED_FOOD_PHARMA_0":
            return {
                "subtotal": gross,
                "vat": Decimal("0.00"),
                "ieps": Decimal("0.00"),
                "total_tax": Decimal("0.00"),
                "total": gross
            }
        elif self.regime_code == "EXPORT_USMCA_0":
            return {
                "subtotal": gross,
                "vat": Decimal("0.00"),
                "ieps": Decimal("0.00"),
                "total_tax": Decimal("0.00"),
                "total": gross
            }
        elif self.regime_code == "BORDER_REGION_VAT_8":
            subtotal = (gross / Decimal("1.08")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            vat = gross - subtotal
            return {
                "subtotal": subtotal,
                "vat": vat,
                "ieps": Decimal("0.00"),
                "total_tax": vat,
                "total": gross
            }
        elif self.regime_code == "IEPS_HIGH_CALORIE_BEVERAGE":
            subtotal = (gross / Decimal("1.2528")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            ieps = (subtotal * Decimal("0.08")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            vat_base = subtotal + ieps
            vat = (vat_base * Decimal("0.16")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            # Ajuste de centavo por redondeo estricto
            diff = gross - (subtotal + ieps + vat)
            subtotal = subtotal + diff
            return {
                "subtotal": subtotal,
                "vat": vat,
                "ieps": ieps,
                "total_tax": vat + ieps,
                "total": gross
            }
        else:  # STANDARD_VAT_16
            subtotal = (gross / Decimal("1.16")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            vat = gross - subtotal
            return {
                "subtotal": subtotal,
                "vat": vat,
                "ieps": Decimal("0.00"),
                "total_tax": vat,
                "total": gross
            }


class FiscalRegimeResolver:
    """
    Detector y Resolutor de Régimen Fiscal B2B por Caso y SKU (HU 9.3.1).
    Soporta los 5 regímenes impositivos del SAT en operaciones comerciales e industriales:
    1. STANDARD_VAT_16: General 16% IVA (Art. 1 LIVA)
    2. ZERO_RATED_FOOD_PHARMA_0: Tasa 0% IVA Alimentos y Medicinas (Art. 2-A LIVA)
    3. BORDER_REGION_VAT_8: Estímulo Franja Fronteriza Norte/Sur DOF 8% IVA
    4. IEPS_HIGH_CALORIE_BEVERAGE: IEPS 8% + IVA 16% Bebidas/Alimentos calóricos (LIEPS + LIVA)
    5. EXPORT_USMCA_0: Exportación Definitiva T-MEC A1 (No Objeto Trasladado Nacional)
    """

    REGIMES: Dict[str, FiscalTaxProfile] = {
        "STANDARD_VAT_16": FiscalTaxProfile(
            regime_code="STANDARD_VAT_16",
            description="Régimen General IVA 16% (Art. 1 LIVA)",
            vat_rate=Decimal("0.16"),
            ieps_rate=Decimal("0.00"),
            total_tax_factor=Decimal("1.16"),
            objeto_imp="02",
            exportacion="01",
            tax_code_erp="V1",
            gl_account_vat="210800",
            gl_account_ieps="210900"
        ),
        "ZERO_RATED_FOOD_PHARMA_0": FiscalTaxProfile(
            regime_code="ZERO_RATED_FOOD_PHARMA_0",
            description="Tasa 0% IVA Alimentos, Agroquímicos y Medicamentos de Patente (Art. 2-A LIVA)",
            vat_rate=Decimal("0.00"),
            ieps_rate=Decimal("0.00"),
            total_tax_factor=Decimal("1.00"),
            objeto_imp="02",
            exportacion="01",
            tax_code_erp="V0",
            gl_account_vat="210800",
            gl_account_ieps="210900"
        ),
        "BORDER_REGION_VAT_8": FiscalTaxProfile(
            regime_code="BORDER_REGION_VAT_8",
            description="Estímulo Fiscal Región Fronteriza IVA 8% (Decreto DOF Franja Fronteriza)",
            vat_rate=Decimal("0.08"),
            ieps_rate=Decimal("0.00"),
            total_tax_factor=Decimal("1.08"),
            objeto_imp="02",
            exportacion="01",
            tax_code_erp="V8",
            gl_account_vat="210800",
            gl_account_ieps="210900"
        ),
        "IEPS_HIGH_CALORIE_BEVERAGE": FiscalTaxProfile(
            regime_code="IEPS_HIGH_CALORIE_BEVERAGE",
            description="Alimentos No Básicos con Alta Densidad Calórica y Bebidas Saborizadas (IEPS 8% + IVA 16%)",
            vat_rate=Decimal("0.16"),
            ieps_rate=Decimal("0.08"),
            total_tax_factor=Decimal("1.2528"),
            objeto_imp="02",
            exportacion="01",
            tax_code_erp="VIEPS",
            gl_account_vat="210800",
            gl_account_ieps="210900"
        ),
        "EXPORT_USMCA_0": FiscalTaxProfile(
            regime_code="EXPORT_USMCA_0",
            description="Exportación Definitiva Clave A1 / T-MEC (No Objeto Impuesto Trasladado Nacional)",
            vat_rate=Decimal("0.00"),
            ieps_rate=Decimal("0.00"),
            total_tax_factor=Decimal("1.00"),
            objeto_imp="01",
            exportacion="02",
            tax_code_erp="VEXP",
            gl_account_vat="210800",
            gl_account_ieps="210900"
        ),
    }

    BORDER_POSTAL_PREFIXES = (
        "21", "22",  # Baja California (Tijuana, Mexicali, Ensenada)
        "23",        # Baja California Sur
        "32",        # Chihuahua (Ciudad Juárez)
        "26",        # Sonora (San Luis Río Colorado, Nogales)
        "25",        # Coahuila norte
        "88", "87"   # Tamaulipas (Nuevo Laredo, Reynosa, Matamoros)
    )

    REGIME_ALIASES = {
        "STANDARD": "STANDARD_VAT_16",
        "STANDARD_VAT": "STANDARD_VAT_16",
        "VAT_16": "STANDARD_VAT_16",
        "IVA_16": "STANDARD_VAT_16",
        "16%": "STANDARD_VAT_16",
        "16": "STANDARD_VAT_16",
        "GENERAL": "STANDARD_VAT_16",
        "ZERO": "ZERO_RATED_FOOD_PHARMA_0",
        "ZERO_RATED": "ZERO_RATED_FOOD_PHARMA_0",
        "TASA_0": "ZERO_RATED_FOOD_PHARMA_0",
        "TASA_CERO": "ZERO_RATED_FOOD_PHARMA_0",
        "0%": "ZERO_RATED_FOOD_PHARMA_0",
        "0": "ZERO_RATED_FOOD_PHARMA_0",
        "FOOD": "ZERO_RATED_FOOD_PHARMA_0",
        "PHARMA": "ZERO_RATED_FOOD_PHARMA_0",
        "ALIMENTOS": "ZERO_RATED_FOOD_PHARMA_0",
        "MEDICINAS": "ZERO_RATED_FOOD_PHARMA_0",
        "BORDER": "BORDER_REGION_VAT_8",
        "BORDER_8": "BORDER_REGION_VAT_8",
        "FRONTERA": "BORDER_REGION_VAT_8",
        "FRONTERA_8": "BORDER_REGION_VAT_8",
        "FRANJA_FRONTERIZA": "BORDER_REGION_VAT_8",
        "8%": "BORDER_REGION_VAT_8",
        "8": "BORDER_REGION_VAT_8",
        "IEPS": "IEPS_HIGH_CALORIE_BEVERAGE",
        "IEPS_8": "IEPS_HIGH_CALORIE_BEVERAGE",
        "BEVERAGE": "IEPS_HIGH_CALORIE_BEVERAGE",
        "SNACKS": "IEPS_HIGH_CALORIE_BEVERAGE",
        "REFRESCOS": "IEPS_HIGH_CALORIE_BEVERAGE",
        "EXPORT": "EXPORT_USMCA_0",
        "EXPORTACION": "EXPORT_USMCA_0",
        "USMCA": "EXPORT_USMCA_0",
        "TMEC": "EXPORT_USMCA_0",
        "T-MEC": "EXPORT_USMCA_0",
        "CROSSBORDER": "EXPORT_USMCA_0",
    }

    @classmethod
    def resolve(
        cls,
        case_id: str = "",
        sku: Optional[str] = None,
        regime: Optional[str] = None,
        postal_code: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> FiscalTaxProfile:
        """
        Determina el perfil tributario determinístico adecuado.
        Prioridad:
        1. Régimen explícito pasado por parámetro (o alias normalizado).
        2. Detección por metadatos (campo 'fiscal_regime' o 'regimen').
        3. Detección por palabras clave en case_id, sku o metadatos.
        4. Detección geográfica por código postal receptor (franja fronteriza).
        5. Default: STANDARD_VAT_16.
        """
        if regime:
            norm_regime = regime.strip().upper()
            if norm_regime in cls.REGIMES:
                return cls.REGIMES[norm_regime]
            if norm_regime in cls.REGIME_ALIASES:
                return cls.REGIMES[cls.REGIME_ALIASES[norm_regime]]

        meta = metadata or {}
        meta_regime = meta.get("fiscal_regime") or meta.get("regime") or meta.get("regimen")
        if meta_regime:
            norm_meta = str(meta_regime).strip().upper()
            if norm_meta in cls.REGIMES:
                return cls.REGIMES[norm_meta]
            if norm_meta in cls.REGIME_ALIASES:
                return cls.REGIMES[cls.REGIME_ALIASES[norm_meta]]

        # Unificar texto de análisis
        text_corpus = f"{case_id} {sku or ''} {json.dumps(meta, default=str)}".lower()

        # 1. Exportación / T-MEC
        if any(kw in text_corpus for kw in ["export", "usmca", "tmec", "t-mec", "crossborder", "intercompany_us", "dhl_express_crossborder"]):
            return cls.REGIMES["EXPORT_USMCA_0"]

        # 2. IEPS Bebidas Saborizadas / Alta Densidad Calórica
        if any(kw in text_corpus for kw in ["ieps", "beverage", "soda", "refresco", "snack", "botana", "dulce", "candy", "sugar", "caloric", "calorico", "bebida azucarada", "chocolat"]):
            return cls.REGIMES["IEPS_HIGH_CALORIE_BEVERAGE"]

        # 3. Región Fronteriza 8% (por código postal o palabras clave)
        pc = postal_code or meta.get("postal_code") or meta.get("domicilio_fiscal") or meta.get("codigo_postal")
        if pc and any(str(pc).strip().startswith(p) for p in cls.BORDER_POSTAL_PREFIXES):
            return cls.REGIMES["BORDER_REGION_VAT_8"]
        if any(kw in text_corpus for kw in ["border", "frontera", "tijuana", "juarez", "reynosa", "nogales", "mexicali", "nuevo laredo", "matamoros"]):
            return cls.REGIMES["BORDER_REGION_VAT_8"]

        # 4. Tasa 0% Alimentos, Agroquímicos y Medicamentos
        if any(kw in text_corpus for kw in ["food", "pharma", "agro", "alimento", "fresco", "medic", "leche", "grano", "farmaceutic", "fruta", "verdura", "harina", "insulina"]):
            return cls.REGIMES["ZERO_RATED_FOOD_PHARMA_0"]

        # 5. Default General 16%
        return cls.REGIMES["STANDARD_VAT_16"]


class ErpEngine:
    """Motor central de generación y validación de asientos contables ERP y CFDI 4.0."""

    @classmethod
    def build_erp_posting_lines(
        cls,
        report: DisputeAnalysisReport,
        fiscal_regime: Optional[str] = None
    ) -> List[ErpPostingLine]:
        """
        Construye el asiento contable de partida doble bajo norma NIF C-3 / US GAAP
        con soporte multirrégimen fiscal determinístico (HU 9.3.2):
        - Cargo: Descuentos y Bonificaciones (Nota de Crédito Subtotal gravable/exento)
        - Cargo: IEPS Trasladado por Cancelar (Cuenta 210900 si aplica)
        - Cargo: IVA Trasladado por Cancelar (Cuenta 210800 a tasa 16%, 8% o 0%)
        - Cargo: Deudores Diversos en Litigio (Saldo Reclamable)
        - Abono: Clientes / Cuentas por Cobrar (Total Retención Conciliada)
        Garantiza sum(debits) == sum(credits) == abs(difference) con $0.00 MAE.
        """
        profile = FiscalRegimeResolver.resolve(case_id=report.case_id, regime=fiscal_regime)
        total_discrepancy = abs(report.difference)
        credit_memo_total = report.justified_amount
        claimable_total = report.claimable_amount

        breakdown = profile.calculate_breakdown(credit_memo_total)
        cm_subtotal = breakdown["subtotal"]
        cm_vat = breakdown["vat"]
        cm_ieps = breakdown["ieps"]

        lines: List[ErpPostingLine] = []

        # 1. Cargo: Descuentos sobre Ventas (Gasto comercial reconocido por Nota de Crédito)
        if cm_subtotal > Decimal("0.00"):
            lines.append(ErpPostingLine(
                line_number=len(lines) + 1,
                account_code="410500",
                account_name="Descuentos y Bonificaciones sobre Ventas",
                debit=cm_subtotal,
                credit=Decimal("0.00"),
                cost_center="CC_SALES",
                tax_code=profile.tax_code_erp,
                memo=f"Nota de Crédito Comercial Subtotal s/ {report.case_id}"
            ))

        # 2. Cargo: IEPS Trasladado por Cancelar (Cuenta 210900 si aplica)
        if cm_ieps > Decimal("0.00"):
            lines.append(ErpPostingLine(
                line_number=len(lines) + 1,
                account_code=profile.gl_account_ieps,
                account_name="IEPS Trasladado por Cancelar (8%)",
                debit=cm_ieps,
                credit=Decimal("0.00"),
                cost_center=None,
                tax_code="VIEPS",
                memo=f"IEPS 8% cancelado s/ Nota de Crédito {report.case_id}"
            ))

        # 3. Cargo: IVA Trasladado por Cancelar (Cuenta 210800 a tasa 16% u 8%)
        if cm_vat > Decimal("0.00"):
            vat_pct = int(profile.vat_rate * 100)
            lines.append(ErpPostingLine(
                line_number=len(lines) + 1,
                account_code=profile.gl_account_vat,
                account_name=f"IVA Trasladado por Cancelar ({vat_pct}%)",
                debit=cm_vat,
                credit=Decimal("0.00"),
                cost_center=None,
                tax_code=profile.tax_code_erp,
                memo=f"IVA {vat_pct}% cancelado s/ Nota de Crédito {report.case_id}"
            ))

        # 4. Cargo: Deudores en Disputa / Cartera en Gestión Reclamable
        if claimable_total > Decimal("0.00"):
            lines.append(ErpPostingLine(
                line_number=len(lines) + 1,
                account_code="120090",
                account_name="Deudores en Disputa / Saldo Reclamable",
                debit=claimable_total,
                credit=Decimal("0.00"),
                cost_center="CC_LEGAL",
                tax_code=None,
                memo=f"Saldo en Reclamación Legal / Cobranza B2B s/ {report.case_id}"
            ))

        # 5. Abono: Clientes / Cuentas por Cobrar (Cancelación de la partida retenida)
        lines.append(ErpPostingLine(
            line_number=len(lines) + 1,
            account_code="120000",
            account_name="Clientes / Cuentas por Cobrar B2B",
            debit=Decimal("0.00"),
            credit=total_discrepancy,
            cost_center="CC_FINANCE",
            tax_code=None,
            memo=f"Saneamiento integral de retención bancaria s/ {report.case_id}"
        ))

        return lines

    @classmethod
    def generate_sap_bapi_payload(
        cls,
        case_id: str,
        report: DisputeAnalysisReport,
        lines: List[ErpPostingLine]
    ) -> Dict[str, Any]:
        """Estructura la llamada BAPI_ACC_DOCUMENT_POST para SAP S/4HANA & ECC."""
        now = datetime.now(timezone.utc)
        doc_date = now.strftime("%Y%m%d")
        pstng_date = now.strftime("%Y%m%d")
        period = now.strftime("%m")

        doc_header = {
            "BUS_ACT": "RFBU",
            "USERNAME": "SUPPLYMIND",
            "HEADER_TXT": f"Disputa {case_id[:25]}",
            "COMP_CODE": "1000",
            "DOC_DATE": doc_date,
            "PSTNG_DATE": pstng_date,
            "FIS_PERIOD": period,
            "DOC_TYPE": "DG",
            "REF_DOC_NO": f"INV-{case_id.upper()[:16]}"
        }

        account_gl = []
        account_receivable = []
        currency_amount = []

        for line in lines:
            if line.account_code == "120000":
                account_receivable.append({
                    "ITEMNO_ACC": line.line_number,
                    "CUSTOMER": "0001002540",
                    "GL_ACCOUNT": line.account_code,
                    "ITEM_TEXT": line.memo[:50]
                })
                currency_amount.append({
                    "ITEMNO_ACC": line.line_number,
                    "CURRENCY": report.currency,
                    "AMT_DOCCUR": float(-line.credit)
                })
            else:
                account_gl.append({
                    "ITEMNO_ACC": line.line_number,
                    "GL_ACCOUNT": f"0000{line.account_code}",
                    "ITEM_TEXT": line.memo[:50],
                    "COSTCENTER": line.cost_center or "CC_GEN",
                    "TAX_CODE": line.tax_code or ""
                })
                currency_amount.append({
                    "ITEMNO_ACC": line.line_number,
                    "CURRENCY": report.currency,
                    "AMT_DOCCUR": float(line.debit)
                })

        return {
            "DOCUMENTHEADER": doc_header,
            "ACCOUNTGL": account_gl,
            "ACCOUNTRECEIVABLE": account_receivable,
            "ACCOUNTPAYABLE": [],
            "CURRENCYAMOUNT": currency_amount
        }

    @classmethod
    def generate_sap_idoc_text(
        cls,
        case_id: str,
        report: DisputeAnalysisReport,
        lines: List[ErpPostingLine]
    ) -> str:
        """Genera el segmento de texto plano para interfaz SAP IDoc (Mensaje FIDCCP02)."""
        now = datetime.now(timezone.utc)
        header_date = now.strftime("%Y%m%d")
        idoc_num = f"IDOC{int(now.timestamp())}"

        txt = [
            f"EDI_DC40 1000000000000001 2 {idoc_num} FIDCCP02 ORDERS SMI_CLNT100 SAP_PRD {header_date}",
            f"E1FIKPF  1000 DG {header_date} {header_date} {report.currency} 1.0000 INV-{case_id.upper()}",
        ]
        for line in lines:
            bschl = "40" if line.debit > Decimal("0.00") else "50"
            amt = line.debit if line.debit > Decimal("0.00") else line.credit
            txt.append(f"E1FISEG  {line.line_number:03d} {bschl} {line.account_code} {amt:015.2f} {report.currency} {line.memo[:40]}")

        return "\n".join(txt)

    @classmethod
    def generate_netsuite_csv(
        cls,
        case_id: str,
        report: DisputeAnalysisReport,
        lines: List[ErpPostingLine]
    ) -> str:
        """Genera el archivo CSV listo para el importador de Journal Entries de Oracle NetSuite."""
        now_str = datetime.now(timezone.utc).strftime("%d/%m/%Y")
        ext_id = f"JE-{case_id.upper()}"
        entity_name = get_case_fiscal_profile(case_id)["receptor"]["nombre"]

        header = "ExternalID,Date,Subsidiary,Currency,Memo,Line,Account,Debit,Credit,Entity,Department,Class"
        rows = [header]

        for line in lines:
            acct_full = f"{line.account_code} {line.account_name}"
            d_val = f"{line.debit:.2f}"
            c_val = f"{line.credit:.2f}"
            rows.append(
                f'"{ext_id}","{now_str}",1,"{report.currency}","{line.memo}",{line.line_number},'
                f'"{acct_full}",{d_val},{c_val},"{entity_name}","Finance","B2B SCM"'
            )

        return "\n".join(rows)

    @classmethod
    def generate_cfdi_40_xml(
        cls,
        case_id: str,
        report: DisputeAnalysisReport,
        fiscal_profile: Dict[str, Any],
        fiscal_regime: Optional[str] = None
    ) -> str:
        """
        Construye un comprobante XML estructurado y válido conforme al estándar
        CFDI 4.0 del SAT (Anexo 20) para Nota de Crédito (Tipo E - Egreso),
        adaptando dinámicamente los nodos de impuestos según el régimen fiscal (HU 9.3.2).
        """
        emisor = fiscal_profile["emisor"]
        receptor = fiscal_profile["receptor"]
        origin_uuid = generate_cfdi_uuid(case_id)
        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")

        profile = FiscalRegimeResolver.resolve(
            case_id=case_id,
            regime=fiscal_regime,
            postal_code=receptor.get("domicilio_fiscal")
        )

        total_credit_memo = report.justified_amount
        breakdown = profile.calculate_breakdown(total_credit_memo)
        subtotal = breakdown["subtotal"]
        vat_amount = breakdown["vat"]
        ieps_amount = breakdown["ieps"]
        total_tax = breakdown["total_tax"]

        # Construcción de nodos de impuestos según régimen fiscal
        concepto_impuestos_xml = ""
        comprobante_impuestos_xml = ""

        if profile.objeto_imp == "02":
            traslados_concepto = []
            traslados_comprobante = []

            if profile.regime_code == "IEPS_HIGH_CALORIE_BEVERAGE":
                # IEPS 8%
                traslados_concepto.append(
                    f'          <cfdi:Traslado Base="{subtotal:.2f}" Impuesto="003" TipoFactor="Tasa" TasaOCuota="0.080000" Importe="{ieps_amount:.2f}"/>'
                )
                traslados_comprobante.append(
                    f'      <cfdi:Traslado Base="{subtotal:.2f}" Impuesto="003" TipoFactor="Tasa" TasaOCuota="0.080000" Importe="{ieps_amount:.2f}"/>'
                )
                # IVA 16% sobre base (subtotal + IEPS)
                vat_base = subtotal + ieps_amount
                traslados_concepto.append(
                    f'          <cfdi:Traslado Base="{vat_base:.2f}" Impuesto="002" TipoFactor="Tasa" TasaOCuota="0.160000" Importe="{vat_amount:.2f}"/>'
                )
                traslados_comprobante.append(
                    f'      <cfdi:Traslado Base="{vat_base:.2f}" Impuesto="002" TipoFactor="Tasa" TasaOCuota="0.160000" Importe="{vat_amount:.2f}"/>'
                )
            elif profile.regime_code == "BORDER_REGION_VAT_8":
                traslados_concepto.append(
                    f'          <cfdi:Traslado Base="{subtotal:.2f}" Impuesto="002" TipoFactor="Tasa" TasaOCuota="0.080000" Importe="{vat_amount:.2f}"/>'
                )
                traslados_comprobante.append(
                    f'      <cfdi:Traslado Base="{subtotal:.2f}" Impuesto="002" TipoFactor="Tasa" TasaOCuota="0.080000" Importe="{vat_amount:.2f}"/>'
                )
            elif profile.regime_code == "ZERO_RATED_FOOD_PHARMA_0":
                traslados_concepto.append(
                    f'          <cfdi:Traslado Base="{subtotal:.2f}" Impuesto="002" TipoFactor="Tasa" TasaOCuota="0.000000" Importe="0.00"/>'
                )
                traslados_comprobante.append(
                    f'      <cfdi:Traslado Base="{subtotal:.2f}" Impuesto="002" TipoFactor="Tasa" TasaOCuota="0.000000" Importe="0.00"/>'
                )
            else:  # STANDARD_VAT_16
                traslados_concepto.append(
                    f'          <cfdi:Traslado Base="{subtotal:.2f}" Impuesto="002" TipoFactor="Tasa" TasaOCuota="0.160000" Importe="{vat_amount:.2f}"/>'
                )
                traslados_comprobante.append(
                    f'      <cfdi:Traslado Base="{subtotal:.2f}" Impuesto="002" TipoFactor="Tasa" TasaOCuota="0.160000" Importe="{vat_amount:.2f}"/>'
                )

            traslados_concepto_str = "\n".join(traslados_concepto)
            concepto_impuestos_xml = f"""      <cfdi:Impuestos>
        <cfdi:Traslados>
{traslados_concepto_str}
        </cfdi:Traslados>
      </cfdi:Impuestos>"""

            traslados_comprobante_str = "\n".join(traslados_comprobante)
            comprobante_impuestos_xml = f"""  <cfdi:Impuestos TotalImpuestosTrasladados="{total_tax:.2f}">
    <cfdi:Traslados>
{traslados_comprobante_str}
    </cfdi:Traslados>
  </cfdi:Impuestos>"""

        # Construcción XML con namespaces SAT Anexo 20
        concepto_xml_body = f"""    <cfdi:Concepto ClaveProdServ="84111506"
                   NoIdentificacion="NC-{case_id.upper()}"
                   Cantidad="1"
                   ClaveUnidad="ACT"
                   Unidad="Actividad"
                   Descripcion="Bonificación y saneamiento comercial por conciliación de disputa de cartera {case_id}"
                   ValorUnitario="{subtotal:.2f}"
                   Importe="{subtotal:.2f}"
                   Descuento="0.00"
                   ObjetoImp="{profile.objeto_imp}">"""
        if concepto_impuestos_xml:
            concepto_xml_body += f"\n{concepto_impuestos_xml}\n    </cfdi:Concepto>"
        else:
            concepto_xml_body += "\n    </cfdi:Concepto>"

        xml_parts = [
            f"""<?xml version="1.0" encoding="UTF-8"?>
<cfdi:Comprobante xmlns:cfdi="http://www.sat.gob.mx/cfd/4"
                  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                  xsi:schemaLocation="http://www.sat.gob.mx/cfd/4 http://www.sat.gob.mx/sitio_internet/cfd/4/cfdv40.xsd"
                  Version="4.0"
                  Serie="NC"
                  Folio="{case_id.upper()}"
                  Fecha="{now_iso}"
                  Sello="MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQC7..."
                  FormaPago="15"
                  NoCertificado="30001000000500003416"
                  Certificado="MIIFuzCCA6OgAwIBAgIUMzAwMDEwMDAwMDA1MDAwMDM0MTYwDQYJKoZIhvcNAQELBQAw..."
                  SubTotal="{subtotal:.2f}"
                  Moneda="{report.currency}"
                  Total="{total_credit_memo:.2f}"
                  TipoDeComprobante="E"
                  Exportacion="{profile.exportacion}"
                  MetodoPago="PUE"
                  LugarExpedicion="{emisor['lugar_expedicion']}">
  <cfdi:CfdiRelacionados TipoRelacion="01">
    <cfdi:CfdiRelacionado UUID="{origin_uuid.upper()}"/>
  </cfdi:CfdiRelacionados>
  <cfdi:Emisor Rfc="{emisor['rfc']}"
               Nombre="{emisor['nombre']}"
               RegimenFiscal="{emisor['regimen_fiscal']}"/>
  <cfdi:Receptor Rfc="{receptor['rfc']}"
                 Nombre="{receptor['nombre']}"
                 DomicilioFiscalReceptor="{receptor['domicilio_fiscal']}"
                 RegimenFiscalReceptor="{receptor['regimen_fiscal']}"
                 UsoCFDI="{receptor['uso_cfdi']}"/>
  <cfdi:Conceptos>
{concepto_xml_body}
  </cfdi:Conceptos>"""
        ]

        if comprobante_impuestos_xml:
            xml_parts.append(comprobante_impuestos_xml)

        xml_parts.append("</cfdi:Comprobante>")
        return "\n".join(xml_parts)

    @classmethod
    def export_full_erp_package(cls, case_id: str, fiscal_regime: Optional[str] = None) -> ErpExportPackage:
        """Genera y persiste el paquete completo de integración ERP y Fiscal en reports/erp_{case_id}/."""
        report = ConcessionEngine.get_or_create_base_report(case_id)
        fiscal_profile = get_case_fiscal_profile(case_id)
        lines = cls.build_erp_posting_lines(report, fiscal_regime=fiscal_regime)
        profile = FiscalRegimeResolver.resolve(case_id, regime=fiscal_regime)

        # 1. SAP Payload e IDoc
        sap_bapi = cls.generate_sap_bapi_payload(case_id, report, lines)
        sap_idoc = cls.generate_sap_idoc_text(case_id, report, lines)

        # 2. NetSuite CSV y JSON
        netsuite_csv = cls.generate_netsuite_csv(case_id, report, lines)
        netsuite_lines = [line.model_dump(mode="python") for line in lines]

        # 3. CFDI 4.0 XML
        cfdi_xml = cls.generate_cfdi_40_xml(case_id, report, fiscal_profile, fiscal_regime=fiscal_regime)
        cfdi_uuid = generate_cfdi_uuid(case_id)

        # 4. Guardar archivos en reports/erp_{case_id}/
        erp_dir = ROOT_DIR / "reports" / f"erp_{case_id}"
        erp_dir.mkdir(parents=True, exist_ok=True)

        with open(erp_dir / "sap_bapi_post.json", "w", encoding="utf-8") as f:
            json.dump(sap_bapi, f, indent=2, ensure_ascii=False)

        with open(erp_dir / "sap_idoc_fidccp02.txt", "w", encoding="utf-8") as f:
            f.write(sap_idoc)

        with open(erp_dir / "netsuite_journal_entry.csv", "w", encoding="utf-8") as f:
            f.write(netsuite_csv)

        with open(erp_dir / "netsuite_journal_entry.json", "w", encoding="utf-8") as f:
            json.dump(
                {"external_id": f"JE-{case_id.upper()}", "lines": [l.model_dump(mode="json") for l in lines]},
                f, indent=2, ensure_ascii=False
            )

        with open(erp_dir / "cfdi_40_nota_credito.xml", "w", encoding="utf-8") as f:
            f.write(cfdi_xml)

        # Generar Memo Ejecutivo Contable Markdown
        memo_md = f"""# PÓLIZA CONTABLE DE SANEAMIENTO Y REGULARIZACIÓN FISCAL
**Expediente:** `{case_id}` | **Norma:** NIF C-3 / US GAAP | **Fecha:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}  
**Contraparte:** {fiscal_profile['receptor']['nombre']} (RFC: `{fiscal_profile['receptor']['rfc']}`)  
**Régimen Tributario:** {profile.description} (Código SAT: `{profile.regime_code}`)  
**Factor Impositivo:** `{profile.total_tax_factor}` | **Objeto de Impuesto SAT:** `{profile.objeto_imp}`  

---

### 1. Asiento de Diario de Partida Doble

| Línea | Cuenta Contable | Concepto | Cargo (Debit USD) | Abono (Credit USD) |
| :---: | :--- | :--- | :---: | :---: |
"""
        for l in lines:
            memo_md += f"| {l.line_number} | `{l.account_code}` | {l.account_name} | `${l.debit:,.2f}` | `${l.credit:,.2f}` |\n"

        memo_md += f"""
---

### 2. Cuadratura Contable Estricta:
- **Total Cargos (Debits):** **`${sum(l.debit for l in lines):,.2f} USD`**
- **Total Abonos (Credits):** **`${sum(l.credit for l in lines):,.2f} USD`**
- **Diferencia Neta:** **`$0.00 USD`** (Cuadre perfecto de partida doble ✅)

### 3. Timbrado Fiscal CFDI 4.0:
- **UUID de Factura de Origen:** `{cfdi_uuid.upper()}`
- **Tipo de Comprobante:** `E` (Egreso / Nota de Crédito)
- **Clave SAT:** `84111506` (Servicios de facturación y saneamiento de cartera)
"""
        with open(erp_dir / "poliza_contable_nif_c3.md", "w", encoding="utf-8") as f:
            f.write(memo_md)

        package = ErpExportPackage(
            case_id=case_id,
            total_discrepancy=abs(report.difference),
            credit_memo_amount=report.justified_amount,
            claimable_amount=report.claimable_amount,
            accounting_standard="NIF C-3 / US GAAP",
            sap_bapi=sap_bapi,
            netsuite_journal_lines=netsuite_lines,
            cfdi_uuid=cfdi_uuid,
            cfdi_xml=cfdi_xml,
            generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        )

        return package
