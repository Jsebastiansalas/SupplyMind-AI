"""
Módulo de Ingesta, Extracción y Validación de Documentos PDF para SupplyMind AI.
Convierte documentos PDF no estructurados o semiestructurados en modelos Pydantic
estrictos (Invoice, PurchaseOrder, DeliveryNote, PaymentReceipt, CommercialContract).

Implementa:
1. Extracción de texto puro y tablas con pypdf.
2. Motor determinístico de regex de alta precisión.
3. Fallback inteligente con LLM (Grok / Platica Gateway) si el formato varía.
4. Validación rigurosa con los esquemas Pydantic oficiales del sistema.
"""

import re
import json
from pathlib import Path
from decimal import Decimal
from typing import Dict, Any, List, Optional
import pypdf

from config.settings import settings
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
    ContractClause
)

def _clean_amount(amt_str: str) -> Decimal:
    """Convierte cadenas con símbolos de moneda y comas a Decimal."""
    cleaned = re.sub(r'[^\d.]', '', amt_str.replace(',', ''))
    return Decimal(cleaned) if cleaned else Decimal("0.00")

def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extrae el contenido de texto completo de un archivo PDF, con fallback OCR automático si es escaneado."""
    if not pdf_path.exists():
        raise FileNotFoundError(f"Archivo PDF no encontrado: {pdf_path}")
    reader = pypdf.PdfReader(str(pdf_path))
    pages_text = []
    has_images = False
    for page in reader.pages:
        text = page.extract_text() or ""
        pages_text.append(text)
        if len(page.images) > 0:
            has_images = True
            
    combined = "\n".join(pages_text).strip()
    
    # Si no tiene texto vectorial (< 30 caracteres) y contiene imágenes, es un PDF escaneado (raster)
    if len(combined) < 30 and has_images:
        try:
            from tools.ocr_engine.vision import OCREngine
            ocr = OCREngine()
            scanned_text = ocr.transcribe_scanned_pdf(pdf_path)
            if scanned_text.strip():
                return scanned_text
        except Exception:
            pass
            
    return combined

class PDFCaseParser:
    """Motor agéntico para extracción y conversión de expedientes PDF."""
    
    @classmethod
    def parse_invoice(cls, pdf_path: Path) -> Invoice:
        text = extract_text_from_pdf(pdf_path)
        
        try:
            # Deterministic Extraction
            inv_id_match = re.search(r'Factura No:\s*([A-Za-z0-9\-_]+)', text) or re.search(r'INVOICE:\s*([A-Za-z0-9\-_]+)', text)
            vendor_match = re.search(r'Emisor / Proveedor:\s*([A-Za-z0-9\-_]+)', text) or re.search(r'^([A-Z0-9\-_]+)\s+FACTURA', text, re.M)
            cust_match = re.search(r'Cliente / Receptor:\s*([A-Za-z0-9\-_]+)', text)
            po_match = re.search(r'Orden de Compra Ref:\s*([A-Za-z0-9\-_]+)', text)
            date_match = re.search(r'Fecha Emision:\s*(\d{4}-\d{2}-\d{2})', text)
            cur_match = re.search(r'Moneda:\s*([A-Z]{3})', text)
            
            subtotal_match = re.search(r'Subtotal:\s*\$?([\d,]+\.?\d*)', text)
            tax_match = re.search(r'Impuestos:\s*\$?([\d,]+\.?\d*)', text)
            total_match = re.search(r'TOTAL:\s*\$?([\d,]+\.?\d*)', text)
            
            items: List[InvoiceItem] = []
            # Regex para ítems: Item_ID Descripcion Cantidad Precio Total
            # Ejemplo: SKU-NVME-4TB Enterprise PCIe Gen5 NVMe 4TB SSD 120 $250.00 $30,000.00
            item_pattern = re.compile(
                r'([A-Za-z0-9\-_]+)\s+(.+?)\s+(\d+)\s+\$?([\d,]+\.?\d*)\s+\$?([\d,]+\.?\d*)'
            )
            for line in text.splitlines():
                line_str = line.strip()
                if "Item ID" in line_str or "Subtotal:" in line_str or "TOTAL:" in line_str:
                    continue
                match = item_pattern.search(line_str)
                if match:
                    sku, desc, qty, unit_p, tot_p = match.groups()
                    items.append(
                        InvoiceItem(
                            item_id=sku,
                            description=desc.strip(),
                            quantity=int(qty),
                            unit_price=_clean_amount(unit_p),
                            total_price=_clean_amount(tot_p)
                        )
                    )
            
            if inv_id_match and vendor_match and cust_match and total_match and items:
                return Invoice(
                    invoice_id=inv_id_match.group(1),
                    vendor_id=vendor_match.group(1),
                    customer_id=cust_match.group(1),
                    po_reference=po_match.group(1) if po_match else None,
                    issue_date=date_match.group(1) if date_match else "2026-03-01",
                    currency=cur_match.group(1) if cur_match else "USD",
                    items=items,
                    subtotal=_clean_amount(subtotal_match.group(1)) if subtotal_match else sum(it.total_price for it in items),
                    tax=_clean_amount(tax_match.group(1)) if tax_match else Decimal("0.00"),
                    total_amount=_clean_amount(total_match.group(1))
                )
        except Exception:
            pass
            
        # Fallback a LLM si falló regex determinístico
        return cls._llm_extract(text, "Invoice", Invoice)

    @classmethod
    def parse_purchase_order(cls, pdf_path: Path) -> PurchaseOrder:
        text = extract_text_from_pdf(pdf_path)
        try:
            po_id_match = re.search(r'PO ID:\s*([A-Za-z0-9\-_]+)', text) or re.search(r'PURCHASE ORDER:\s*([A-Za-z0-9\-_]+)', text)
            cust_match = re.search(r'Comprador / Retailer:\s*([A-Za-z0-9\-_]+)', text)
            vendor_match = re.search(r'Proveedor Autorizado:\s*([A-Za-z0-9\-_]+)', text)
            date_match = re.search(r'Fecha de Orden:\s*(\d{4}-\d{2}-\d{2})', text)
            cur_match = re.search(r'Moneda:\s*([A-Z]{3})', text)
            total_match = re.search(r'TOTAL PO:\s*\$?([\d,]+\.?\d*)', text)
            
            items: List[PurchaseOrderItem] = []
            item_pattern = re.compile(
                r'([A-Za-z0-9\-_]+)\s+(.+?)\s+(\d+)\s+\$?([\d,]+\.?\d*)\s+\$?([\d,]+\.?\d*)'
            )
            for line in text.splitlines():
                line_str = line.strip()
                if "Item ID" in line_str or "TOTAL PO:" in line_str:
                    continue
                match = item_pattern.search(line_str)
                if match:
                    sku, desc, qty, unit_p, tot_p = match.groups()
                    items.append(
                        PurchaseOrderItem(
                            item_id=sku,
                            description=desc.strip(),
                            ordered_quantity=int(qty),
                            agreed_unit_price=_clean_amount(unit_p),
                            total_price=_clean_amount(tot_p)
                        )
                    )
                    
            if po_id_match and vendor_match and cust_match and total_match and items:
                return PurchaseOrder(
                    po_id=po_id_match.group(1),
                    vendor_id=vendor_match.group(1),
                    customer_id=cust_match.group(1),
                    order_date=date_match.group(1) if date_match else "2026-03-01",
                    currency=cur_match.group(1) if cur_match else "USD",
                    items=items,
                    total_amount=_clean_amount(total_match.group(1))
                )
        except Exception:
            pass
            
        return cls._llm_extract(text, "PurchaseOrder", PurchaseOrder)

    @classmethod
    def parse_delivery_note(cls, pdf_path: Path) -> DeliveryNote:
        text = extract_text_from_pdf(pdf_path)
        try:
            del_id_match = re.search(r'Folio Remision:\s*([A-Za-z0-9\-_]+)', text) or re.search(r'RECEIVING SLIP:\s*([A-Za-z0-9\-_]+)', text)
            po_match = re.search(r'PO Referencia:\s*([A-Za-z0-9\-_]+)', text)
            date_match = re.search(r'Fecha de Recepcion:\s*(\d{4}-\d{2}-\d{2})', text)
            hub_match = re.search(r'Bodega / Hub:\s*([A-Za-z0-9\-_]+)', text)
            rec_match = re.search(r'Recibido por:\s*([A-Za-z0-9\-_]+)', text)
            disc_reported = "DISCREPANCIA REPORTADA" in text
            
            items: List[DeliveryItem] = []
            # Formato: ItemID Despachado Recibido Faltante Averiado Notas...
            # Ejemplo: SKU-NVME-4TB 120 100 20 0 Faltante físico en muelle...
            item_pattern = re.compile(
                r'([A-Za-z0-9\-_]+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)(?:\s+(.*))?'
            )
            for line in text.splitlines():
                line_str = line.strip()
                if "Item ID" in line_str or "Folio Remision:" in line_str:
                    continue
                match = item_pattern.search(line_str)
                if match:
                    sku, deliv_q, rec_q, miss_q, dam_q, notes = match.groups()
                    items.append(
                        DeliveryItem(
                            item_id=sku,
                            quantity_delivered=int(deliv_q),
                            quantity_received=int(rec_q),
                            missing_quantity=int(miss_q),
                            damaged_quantity=int(dam_q),
                            notes=notes.strip() if notes else None
                        )
                    )
                    
            if del_id_match and po_match and items:
                return DeliveryNote(
                    delivery_id=del_id_match.group(1),
                    po_reference=po_match.group(1),
                    delivery_date=date_match.group(1) if date_match else "2026-03-10",
                    received_by=rec_match.group(1) if rec_match else "RECEIVER",
                    warehouse_location=hub_match.group(1) if hub_match else "MAIN_WAREHOUSE",
                    signed=True,
                    discrepancy_reported=disc_reported,
                    items=items
                )
        except Exception:
            pass
            
        # Si el texto es escaneado o contiene imágenes de remisión con sello, intentar OCREngine
        try:
            from tools.ocr_engine.vision import OCREngine
            ocr = OCREngine()
            if ocr.extract_images_from_pdf(pdf_path):
                return ocr.extract_delivery_note(pdf_path)
        except Exception:
            pass
            
        return cls._llm_extract(text, "DeliveryNote", DeliveryNote)

    @classmethod
    def parse_payment_receipt(cls, pdf_path: Path) -> PaymentReceipt:
        text = extract_text_from_pdf(pdf_path)
        try:
            pay_id_match = re.search(r'Referencia Pago:\s*([A-Za-z0-9\-_]+)', text) or re.search(r'REMITTANCE ADVICE:\s*([A-Za-z0-9\-_]+)', text)
            inv_match = re.search(r'Factura Cancelada:\s*([A-Za-z0-9\-_]+)', text)
            date_match = re.search(r'Fecha de Dispersion:\s*(\d{4}-\d{2}-\d{2})', text)
            cur_match = re.search(r'Moneda:\s*([A-Z]{3})', text)
            paid_match = re.search(r'Monto Efectivo Pagado:\s*\$?([\d,]+\.?\d*)', text)
            
            deductions: List[PaymentDeduction] = []
            in_deductions_section = False
            for line in text.splitlines():
                line_str = line.strip()
                if "Deducciones y Retenciones" in line_str:
                    in_deductions_section = True
                    continue
                if "TOTAL DEDUCCIONES:" in line_str:
                    in_deductions_section = False
                    continue
                if in_deductions_section and "Codigo Deduccion" not in line_str:
                    parts = line_str.split()
                    if len(parts) >= 4 and ("$" in parts[-1] or re.match(r'^\$?[\d,]+\.?\d*$', parts[-1])):
                        amt = _clean_amount(parts[-1])
                        code = parts[0]
                        ref_doc = parts[-2] if parts[-2] != "N/A" else None
                        reason = " ".join(parts[1:-2])
                        deductions.append(
                            PaymentDeduction(
                                code=code,
                                reason=reason.strip(),
                                amount=amt,
                                reference_doc=ref_doc
                            )
                        )
                        
            if pay_id_match and inv_match and paid_match:
                return PaymentReceipt(
                    payment_id=pay_id_match.group(1),
                    invoice_reference=inv_match.group(1),
                    payment_date=date_match.group(1) if date_match else "2026-03-20",
                    currency=cur_match.group(1) if cur_match else "USD",
                    amount_paid=_clean_amount(paid_match.group(1)),
                    deductions=deductions
                )
        except Exception:
            pass
            
        return cls._llm_extract(text, "PaymentReceipt", PaymentReceipt)

    @classmethod
    def parse_contract(cls, pdf_path: Path) -> CommercialContract:
        text = extract_text_from_pdf(pdf_path)
        try:
            contract_id_match = re.search(r'Contrato No:\s*([A-Za-z0-9\-_]+)', text) or re.search(r'MASTER AGREEMENT:\s*([A-Za-z0-9\-_]+)', text)
            vigencia_match = re.search(r'Vigencia:\s*(\d{4}-\d{2}-\d{2})\s+a\s+(\d{4}-\d{2}-\d{2})', text)
            vendor_match = re.search(r'Parte Proveedora:\s*([A-Za-z0-9\-_]+)', text)
            cust_match = re.search(r'Parte Compradora:\s*([A-Za-z0-9\-_]+)', text)
            
            clauses: List[ContractClause] = []
            clause_blocks = re.split(r'CLAUSULA\s+', text)
            for block in clause_blocks[1:]:
                header_line = block.splitlines()[0].strip()
                id_title = header_line.split(':', 1)
                c_id = id_title[0].strip()
                c_title = id_title[1].strip() if len(id_title) > 1 else f"Clausula {c_id}"
                
                text_match = re.search(r'Texto:\s*(.+?)(?=Politica Operativa:|$)', block, re.S)
                c_text = text_match.group(1).strip() if text_match else ""
                
                pol_match = re.search(r'Politica Operativa:\s*([A-Za-z0-9\-_]+)', block)
                c_pol = pol_match.group(1).strip() if pol_match else "GENERAL_COMPLIANCE"
                
                tol_match = re.search(r'Tolerancia Permitida:\s*([\d.]+)%?', block)
                c_tol = Decimal(tol_match.group(1)) if tol_match else Decimal("0.00")
                
                clauses.append(
                    ContractClause(
                        clause_id=c_id,
                        title=c_title,
                        text=c_text,
                        policy=c_pol,
                        tolerance_percentage=c_tol
                    )
                )
                
            if contract_id_match and vendor_match and cust_match and clauses:
                return CommercialContract(
                    contract_id=contract_id_match.group(1),
                    vendor_id=vendor_match.group(1),
                    customer_id=cust_match.group(1),
                    valid_from=vigencia_match.group(1) if vigencia_match else "2026-01-01",
                    valid_to=vigencia_match.group(2) if vigencia_match else "2026-12-31",
                    clauses=clauses
                )
        except Exception:
            pass
            
        return cls._llm_extract(text, "CommercialContract", CommercialContract)

    @classmethod
    def _llm_extract(cls, text: str, model_name: str, model_cls: Any) -> Any:
        """Fallback con LLM Grok en caso de documentos con formato atípico."""
        if not settings.is_live_api_ready:
            raise ValueError(f"No se pudo extraer determinísticamente el modelo {model_name} y la API en vivo no está activa.")
            
        from openai import OpenAI
        client = OpenAI(
            base_url=settings.PLATICA_BASE_URL,
            api_key=settings.RETO_KEY
        )
        prompt = (
            f"Extrae los datos estructurados en formato JSON estricto para el esquema Pydantic '{model_name}'.\n"
            f"Texto del documento:\n\"\"\"\n{text}\n\"\"\"\n"
            f"Responde ÚNICAMENTE con el objeto JSON válido. No uses bloques de markdown adicionales si es posible."
        )
        response = client.chat.completions.create(
            model=settings.MODEL_NAME,
            messages=[
                {"role": "system", "content": "Eres un extractor de datos empresariales de alta precisión. Responde solo con JSON válido."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        data = json.loads(content)
        return model_cls.model_validate(data)
