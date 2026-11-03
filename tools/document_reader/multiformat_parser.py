"""
tools/document_reader/multiformat_parser.py
Fase 10 - Sprint 10.6: Motor de Ingesta Multiformato (.csv, .xlsx, .txt, .eml).

Permite que SupplyMind AI clasifique y parsee de forma nativa expedientes B2B heterogéneos
con múltiples formatos de archivo reales:
- Hojas de cálculo Excel OpenXML (.xlsx) sin requerir dependencias externas frágiles.
- Archivos separados por comas (.csv) de manifiestos ERP / WMS (ej. DataCo Supply Chain Dataset).
- Archivos de texto plano (.txt) y correos electrónicos (.eml) de disputas de muelle, avisos
  de liquidación bancaria y anexos contractuales.
"""

import csv
from decimal import Decimal, InvalidOperation
import re
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape as xml_escape
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from data.models import (
    Invoice,
    InvoiceItem,
    PurchaseOrder,
    PurchaseOrderItem,
    DeliveryNote,
    DeliveryItem,
    PaymentReceipt,
    PaymentDeduction,
    CommercialContract,
    ContractClause,
)


def _to_dec(val: Any, default: str = "0.00") -> Decimal:
    if val is None:
        return Decimal(default)
    s = str(val).strip().replace("$", "").replace(",", "").replace("USD", "").strip()
    if not s:
        return Decimal(default)
    try:
        return Decimal(s)
    except (InvalidOperation, ValueError):
        return Decimal(default)


def _to_int(val: Any, default: int = 0) -> int:
    if val is None:
        return default
    s = str(val).strip().replace(",", "")
    if not s:
        return default
    try:
        return int(float(s))
    except (ValueError, TypeError):
        return default


def _to_bool(val: Any, default: bool = True) -> bool:
    if isinstance(val, bool):
        return val
    if val is None:
        return default
    s = str(val).strip().lower()
    if s in ("true", "1", "yes", "si", "sí", "firmado", "signed"):
        return True
    if s in ("false", "0", "no", "unsigned", "sin firma"):
        return False
    return default


class MultiFormatParser:
    """
    Parser determinístico y generador OpenXML nativo para archivos .csv, .xlsx, .txt y .eml.
    """

    # =========================================================================
    # 1. ESCRITURA Y LECTURA NATIVA DE EXCEL OPENXML (.xlsx)
    # =========================================================================
    @classmethod
    def write_xlsx_workbook(
        cls,
        file_path: Path,
        headers: List[str],
        rows: List[List[Any]],
        metadata: Optional[Dict[str, Any]] = None,
        sheet_name: str = "SupplyChainData"
    ) -> Path:
        """
        Genera un archivo .xlsx OpenXML estándar (compatible con Excel, LibreOffice y Google Sheets)
        utilizando únicamente la librería estándar de Python (zipfile + XML inlineStr).
        """
        file_path.parent.mkdir(parents=True, exist_ok=True)
        all_grid_rows: List[List[str]] = []

        if metadata:
            for k, v in metadata.items():
                all_grid_rows.append([f"META:{k}", str(v)])
            all_grid_rows.append(["---", "---"])

        all_grid_rows.append([str(h) for h in headers])
        for r in rows:
            all_grid_rows.append([str(cell) if cell is not None else "" for cell in r])

        def _col_letter(idx: int) -> str:
            res = ""
            n = idx + 1
            while n > 0:
                n, rem = divmod(n - 1, 26)
                res = chr(65 + rem) + res
            return res

        sheet_rows_xml = []
        for r_idx, row_vals in enumerate(all_grid_rows, start=1):
            cells_xml = []
            for c_idx, cell_val in enumerate(row_vals):
                col_ref = f"{_col_letter(c_idx)}{r_idx}"
                safe_val = xml_escape(str(cell_val))
                cells_xml.append(
                    f'<c r="{col_ref}" t="inlineStr"><is><t>{safe_val}</t></is></c>'
                )
            sheet_rows_xml.append(f'<row r="{r_idx}">{"".join(cells_xml)}</row>')

        worksheet_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            f'<sheetData>{"".join(sheet_rows_xml)}</sheetData>'
            '</worksheet>'
        )

        content_types_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
            '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
            '</Types>'
        )

        root_rels_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
            '</Relationships>'
        )

        workbook_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            f'<sheets><sheet name="{xml_escape(sheet_name)}" sheetId="1" r:id="rId1"/></sheets>'
            '</workbook>'
        )

        workbook_rels_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
            '</Relationships>'
        )

        with zipfile.ZipFile(file_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("[Content_Types].xml", content_types_xml)
            zf.writestr("_rels/.rels", root_rels_xml)
            zf.writestr("xl/workbook.xml", workbook_xml)
            zf.writestr("xl/_rels/workbook.xml.rels", workbook_rels_xml)
            zf.writestr("xl/worksheets/sheet1.xml", worksheet_xml)

        return file_path

    @classmethod
    def read_xlsx_grid(cls, file_path: Path) -> Tuple[Dict[str, str], List[Dict[str, str]], str]:
        """
        Lee cualquier archivo .xlsx (tanto inlineStr como sharedStrings.xml) y devuelve:
        (metadata_dict, list_of_row_dicts, full_plain_text).
        """
        ns = {"main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
        shared_strings: List[str] = []

        with zipfile.ZipFile(file_path, "r") as zf:
            if "xl/sharedStrings.xml" in zf.namelist():
                ss_root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
                for si in ss_root.findall("main:si", ns):
                    texts = [t.text or "" for t in si.findall(".//main:t", ns)]
                    shared_strings.append("".join(texts))

            sheet_path = "xl/worksheets/sheet1.xml"
            if sheet_path not in zf.namelist():
                worksheet_files = [n for n in zf.namelist() if n.startswith("xl/worksheets/sheet") and n.endswith(".xml")]
                sheet_path = worksheet_files[0]

            sheet_root = ET.fromstring(zf.read(sheet_path))

        raw_rows: List[List[str]] = []
        for row_el in sheet_root.findall(".//main:row", ns):
            current_row: List[str] = []
            for c_el in row_el.findall("main:c", ns):
                c_type = c_el.attrib.get("t", "")
                val = ""
                if c_type == "inlineStr":
                    t_el = c_el.find(".//main:t", ns)
                    val = (t_el.text or "") if t_el is not None else ""
                elif c_type == "s":
                    v_el = c_el.find("main:v", ns)
                    if v_el is not None and v_el.text is not None:
                        idx = int(v_el.text)
                        if 0 <= idx < len(shared_strings):
                            val = shared_strings[idx]
                else:
                    v_el = c_el.find("main:v", ns)
                    val = (v_el.text or "") if v_el is not None else ""
                current_row.append(val.strip())
            if any(current_row):
                raw_rows.append(current_row)

        metadata: Dict[str, str] = {}
        table_start_idx = 0
        for idx, r in enumerate(raw_rows):
            if len(r) >= 2 and r[0].startswith("META:"):
                key = r[0].split("META:", 1)[1].strip()
                metadata[key] = r[1].strip()
                table_start_idx = idx + 1
            elif len(r) >= 1 and r[0] == "---":
                table_start_idx = idx + 1
                break
            else:
                break

        dict_rows: List[Dict[str, str]] = []
        if table_start_idx < len(raw_rows):
            headers = [h.strip() for h in raw_rows[table_start_idx]]
            for data_row in raw_rows[table_start_idx + 1:]:
                row_map = {}
                for i, h in enumerate(headers):
                    if h:
                        row_map[h] = data_row[i].strip() if i < len(data_row) else ""
                if any(row_map.values()):
                    dict_rows.append(row_map)

        full_text_lines = [f"{k}: {v}" for k, v in metadata.items()]
        for r in raw_rows:
            full_text_lines.append(" | ".join(r))
        return metadata, dict_rows, "\n".join(full_text_lines)

    # =========================================================================
    # 2. LECTURA DE ARCHIVOS CSV (.csv) CON METADATOS Y CABECERAS ERP
    # =========================================================================
    @classmethod
    def read_csv_grid(cls, file_path: Path) -> Tuple[Dict[str, str], List[Dict[str, str]], str]:
        """
        Lee un archivo .csv (con soporte para comentarios '# META:key=value' o columnas ERP)
        y devuelve (metadata_dict, list_of_row_dicts, full_plain_text).
        """
        raw_text = file_path.read_text(encoding="utf-8", errors="replace")
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]

        metadata: Dict[str, str] = {}
        csv_lines: List[str] = []

        for line in lines:
            if line.startswith("#"):
                clean = line.lstrip("#").strip()
                if ":" in clean:
                    k, v = clean.split(":", 1)
                    metadata[k.strip()] = v.strip()
                elif "=" in clean:
                    k, v = clean.split("=", 1)
                    metadata[k.strip()] = v.strip()
            else:
                csv_lines.append(line)

        dict_rows: List[Dict[str, str]] = []
        if csv_lines:
            reader = csv.DictReader(csv_lines)
            for row in reader:
                clean_row = {str(k).strip(): str(v).strip() for k, v in row.items() if k is not None and v is not None}
                if any(clean_row.values()):
                    dict_rows.append(clean_row)

        return metadata, dict_rows, raw_text

    # =========================================================================
    # 3. EXTRACCIÓN DE TEXTO PLANO PARA EL CLASIFICADOR DOCUMENTAL
    # =========================================================================
    @classmethod
    def extract_text_any_format(cls, file_path: Path) -> str:
        """Extrae texto completo de .csv, .xlsx, .txt o .eml para clasificación semántica."""
        ext = file_path.suffix.lower()
        if ext == ".xlsx":
            _, _, text = cls.read_xlsx_grid(file_path)
            return text
        if ext == ".csv":
            _, _, text = cls.read_csv_grid(file_path)
            return text
        if ext in (".txt", ".eml", ".md"):
            return file_path.read_text(encoding="utf-8", errors="replace")
        return ""

    # =========================================================================
    # 4. CONVERSIÓN TABULAR (.csv / .xlsx) A MODELOS PYDANTIC
    # =========================================================================
    @classmethod
    def parse_tabular_document(cls, file_path: Path, role: str) -> Any:
        ext = file_path.suffix.lower()
        if ext == ".xlsx":
            meta, rows, _ = cls.read_xlsx_grid(file_path)
        elif ext == ".csv":
            meta, rows, _ = cls.read_csv_grid(file_path)
        else:
            raise ValueError(f"Formato tabular no soportado: {file_path}")

        first_row = rows[0] if rows else {}

        def _meta_or_col(key: str, default: str = "") -> str:
            if key in meta and meta[key]:
                return meta[key]
            if key in first_row and first_row[key]:
                return first_row[key]
            return default

        if role == "invoice":
            items: List[InvoiceItem] = []
            for r in rows:
                if not r.get("item_id") and not r.get("sku"):
                    continue
                qty = _to_int(r.get("quantity") or r.get("qty"), 0)
                u_price = _to_dec(r.get("unit_price") or r.get("price"), "0.00")
                t_price = _to_dec(r.get("total_price") or r.get("line_total"), str(Decimal(qty) * u_price))
                items.append(
                    InvoiceItem(
                        item_id=r.get("item_id") or r.get("sku") or "SKU-001",
                        description=r.get("description") or r.get("product_name") or "Item Supply Chain",
                        quantity=qty,
                        unit_price=u_price,
                        total_price=t_price,
                    )
                )
            calc_sub = sum((it.total_price for it in items), Decimal("0.00"))
            subtotal = _to_dec(_meta_or_col("subtotal", str(calc_sub)))
            tax = _to_dec(_meta_or_col("tax", "0.00"))
            total_amount = _to_dec(_meta_or_col("total_amount", str(subtotal + tax)))
            return Invoice(
                invoice_id=_meta_or_col("invoice_id", "INV-DATACO-001"),
                vendor_id=_meta_or_col("vendor_id", "VENDOR-DATACO"),
                customer_id=_meta_or_col("customer_id", "BUYER-DATACO"),
                po_reference=_meta_or_col("po_reference", "PO-DATACO-001"),
                issue_date=_meta_or_col("issue_date", "2026-01-15"),
                currency=_meta_or_col("currency", "USD"),
                items=items,
                subtotal=subtotal,
                tax=tax,
                total_amount=total_amount,
            )

        if role == "purchase_order":
            items_po: List[PurchaseOrderItem] = []
            for r in rows:
                if not r.get("item_id") and not r.get("sku"):
                    continue
                qty = _to_int(r.get("ordered_quantity") or r.get("quantity"), 0)
                u_price = _to_dec(r.get("agreed_unit_price") or r.get("unit_price"), "0.00")
                t_price = _to_dec(r.get("total_price") or r.get("line_total"), str(Decimal(qty) * u_price))
                items_po.append(
                    PurchaseOrderItem(
                        item_id=r.get("item_id") or r.get("sku") or "SKU-001",
                        description=r.get("description") or r.get("product_name") or "Item Supply Chain",
                        ordered_quantity=qty,
                        agreed_unit_price=u_price,
                        total_price=t_price,
                    )
                )
            calc_tot = sum((it.total_price for it in items_po), Decimal("0.00"))
            return PurchaseOrder(
                po_id=_meta_or_col("po_id", "PO-DATACO-001"),
                vendor_id=_meta_or_col("vendor_id", "VENDOR-DATACO"),
                customer_id=_meta_or_col("customer_id", "BUYER-DATACO"),
                order_date=_meta_or_col("order_date", "2026-01-10"),
                currency=_meta_or_col("currency", "USD"),
                items=items_po,
                total_amount=_to_dec(_meta_or_col("total_amount", str(calc_tot))),
            )

        if role == "delivery":
            items_del: List[DeliveryItem] = []
            for r in rows:
                if not r.get("item_id") and not r.get("sku"):
                    continue
                q_deliv = _to_int(r.get("quantity_delivered") or r.get("dispatched_qty"), 0)
                q_rec = _to_int(r.get("quantity_received") or r.get("received_qty"), 0)
                q_miss = _to_int(r.get("missing_quantity") or r.get("shortage_qty"), max(0, q_deliv - q_rec))
                q_dam = _to_int(r.get("damaged_quantity") or r.get("damaged_qty"), 0)
                items_del.append(
                    DeliveryItem(
                        item_id=r.get("item_id") or r.get("sku") or "SKU-001",
                        quantity_delivered=q_deliv,
                        quantity_received=q_rec,
                        missing_quantity=q_miss,
                        damaged_quantity=q_dam,
                        notes=r.get("notes") or r.get("dock_inspection_notes") or None,
                    )
                )
            has_disc = any((it.missing_quantity > 0 or it.damaged_quantity > 0) for it in items_del)
            return DeliveryNote(
                delivery_id=_meta_or_col("delivery_id", "BOL-DATACO-001"),
                po_reference=_meta_or_col("po_reference", "PO-DATACO-001"),
                delivery_date=_meta_or_col("delivery_date", "2026-01-14"),
                received_by=_meta_or_col("received_by", "Dock Supervisor DataCo"),
                warehouse_location=_meta_or_col("warehouse_location", "Distribution Hub"),
                signed=_to_bool(_meta_or_col("signed", "true"), True),
                discrepancy_reported=_to_bool(_meta_or_col("discrepancy_reported", str(has_disc)), has_disc),
                items=items_del,
            )

        if role == "payment":
            deductions: List[PaymentDeduction] = []
            for r in rows:
                code = r.get("code") or r.get("deduction_code")
                if not code:
                    continue
                deductions.append(
                    PaymentDeduction(
                        code=code,
                        reason=r.get("reason") or r.get("description") or "Deducción aplicada en liquidación",
                        amount=_to_dec(r.get("amount") or r.get("deducted_amount"), "0.00"),
                        reference_doc=r.get("reference_doc") or _meta_or_col("invoice_reference", None),
                    )
                )
            return PaymentReceipt(
                payment_id=_meta_or_col("payment_id", "PAY-DATACO-001"),
                invoice_reference=_meta_or_col("invoice_reference", "INV-DATACO-001"),
                payment_date=_meta_or_col("payment_date", "2026-01-25"),
                currency=_meta_or_col("currency", "USD"),
                amount_paid=_to_dec(_meta_or_col("amount_paid", "0.00")),
                deductions=deductions,
            )

        if role == "contract":
            clauses: List[ContractClause] = []
            for r in rows:
                cid = r.get("clause_id")
                if not cid:
                    continue
                clauses.append(
                    ContractClause(
                        clause_id=cid,
                        title=r.get("title") or "Cláusula Operativa",
                        text=r.get("text") or "",
                        policy=r.get("policy") or "GENERAL_TERMS",
                        tolerance_percentage=_to_dec(r.get("tolerance_percentage"), "0.00"),
                    )
                )
            return CommercialContract(
                contract_id=_meta_or_col("contract_id", "MSA-DATACO-001"),
                vendor_id=_meta_or_col("vendor_id", "VENDOR-DATACO"),
                customer_id=_meta_or_col("customer_id", "BUYER-DATACO"),
                valid_from=_meta_or_col("valid_from", "2025-01-01"),
                valid_to=_meta_or_col("valid_to", "2026-12-31"),
                clauses=clauses,
            )

        raise ValueError(f"Rol documental desconocido: {role}")

    # =========================================================================
    # 5. PARSER DE ARCHIVOS DE TEXTO PLANO Y CORREOS (.txt / .eml)
    # =========================================================================
    @classmethod
    def parse_text_document(cls, file_path: Path, role: str) -> Any:
        """
        Parsea documentos .txt o .eml (contratos MSA en texto plano, avisos de pago por correo
        o reportes de recepción en muelle) extrayendo sus metadatos y cláusulas/partidas.
        """
        text = file_path.read_text(encoding="utf-8", errors="replace")
        meta: Dict[str, str] = {}

        for line in text.splitlines():
            m = re.match(r"^\s*([A-Za-z0-9_]+)\s*:\s*(.+?)\s*$", line)
            if m:
                meta[m.group(1).strip().lower()] = m.group(2).strip()

        if role == "contract":
            clauses: List[ContractClause] = []
            # Patrón estructurado por bloques CLAUSE_ID | TITLE | POLICY | TOLERANCE | TEXT
            block_matches = re.findall(
                r"\[CLAUSE\s+([^\|]+)\|([^\|]+)\|([^\|]+)\|([^\]]+)\]\s*\n(.+?)(?=\n\[CLAUSE|\Z)",
                text,
                flags=re.DOTALL,
            )
            for cid, title, policy, tol, ctext in block_matches:
                clauses.append(
                    ContractClause(
                        clause_id=cid.strip(),
                        title=title.strip(),
                        text=ctext.strip(),
                        policy=policy.strip(),
                        tolerance_percentage=_to_dec(tol.strip(), "0.00"),
                    )
                )

            if not clauses:
                # Fallback para texto libre de contratos
                clauses.append(
                    ContractClause(
                        clause_id="CL-01",
                        title="Términos Generales de Suministro",
                        text=text.strip()[:2000],
                        policy=meta.get("policy", "STRICT_POD_REQUIRED"),
                        tolerance_percentage=_to_dec(meta.get("tolerance_percentage", "0.00")),
                    )
                )

            return CommercialContract(
                contract_id=meta.get("contract_id", "MSA-TXT-001"),
                vendor_id=meta.get("vendor_id", "VENDOR-DATACO"),
                customer_id=meta.get("customer_id", "BUYER-DATACO"),
                valid_from=meta.get("valid_from", "2025-01-01"),
                valid_to=meta.get("valid_to", "2026-12-31"),
                clauses=clauses,
                raw_content=text,
            )

        if role == "payment":
            deductions: List[PaymentDeduction] = []
            for m in re.finditer(
                r"DEDUCTION\s*\|\s*code=([^\|]+)\|\s*amount=([^\|]+)\|\s*reason=([^|\n]+)(?:\|\s*ref=([^\n]+))?",
                text,
            ):
                deductions.append(
                    PaymentDeduction(
                        code=m.group(1).strip(),
                        amount=_to_dec(m.group(2).strip()),
                        reason=m.group(3).strip(),
                        reference_doc=m.group(4).strip() if m.group(4) else meta.get("invoice_reference"),
                    )
                )
            return PaymentReceipt(
                payment_id=meta.get("payment_id", "PAY-TXT-001"),
                invoice_reference=meta.get("invoice_reference", "INV-DATACO-001"),
                payment_date=meta.get("payment_date", "2026-01-25"),
                currency=meta.get("currency", "USD"),
                amount_paid=_to_dec(meta.get("amount_paid", "0.00")),
                deductions=deductions,
            )

        if role == "delivery":
            items_del: List[DeliveryItem] = []
            for m in re.finditer(
                r"ITEM\s*\|\s*sku=([^\|]+)\|\s*delivered=(\d+)\s*\|\s*received=(\d+)\s*\|\s*missing=(\d+)\s*\|\s*damaged=(\d+)(?:\s*\|\s*notes=(.+))?",
                text,
            ):
                items_del.append(
                    DeliveryItem(
                        item_id=m.group(1).strip(),
                        quantity_delivered=int(m.group(2)),
                        quantity_received=int(m.group(3)),
                        missing_quantity=int(m.group(4)),
                        damaged_quantity=int(m.group(5)),
                        notes=m.group(6).strip() if m.group(6) else None,
                    )
                )
            has_disc = any((it.missing_quantity > 0 or it.damaged_quantity > 0) for it in items_del)
            return DeliveryNote(
                delivery_id=meta.get("delivery_id", "BOL-TXT-001"),
                po_reference=meta.get("po_reference", "PO-DATACO-001"),
                delivery_date=meta.get("delivery_date", "2026-01-14"),
                received_by=meta.get("received_by", "Dock Supervisor"),
                warehouse_location=meta.get("warehouse_location", "Hub Central"),
                signed=_to_bool(meta.get("signed", "true"), True),
                discrepancy_reported=_to_bool(meta.get("discrepancy_reported", str(has_disc)), has_disc),
                items=items_del,
            )

        raise ValueError(f"Soporte de texto plano no implementado para rol: {role}")
