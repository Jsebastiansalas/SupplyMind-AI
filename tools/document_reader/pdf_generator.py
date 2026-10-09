"""
Módulo Generador de Documentos Comerciales B2B en formato PDF.
Crea expedientes completos y realistas de disputas comerciales (Factura, Orden de Compra,
Remisión/Bill of Lading, Comprobante de Pago/Remittance y Contrato Marco).
"""

from pathlib import Path
from decimal import Decimal
from typing import Dict, Any, List
from fpdf import FPDF

class B2BDocumentPDF(FPDF):
    """Generador especializado de documentos comerciales B2B con diseño corporativo."""
    
    def __init__(self, doc_type: str, doc_number: str, organization: str):
        super().__init__()
        self.doc_type = doc_type
        self.doc_number = doc_number
        self.organization = organization
        self.set_auto_page_break(auto=True, margin=15)
        
    def header(self):
        # Franja superior
        self.set_fill_color(15, 23, 42) # Slate 900
        self.rect(0, 0, 210, 24, "F")
        
        # Título y Organización
        self.set_xy(10, 6)
        self.set_font("helvetica", "B", 13)
        self.set_text_color(248, 250, 252)
        self.cell(100, 8, f"{self.organization.upper()}", border=False)
        
        self.set_xy(110, 6)
        self.set_font("helvetica", "B", 11)
        self.set_text_color(56, 189, 248) # Cyan
        self.cell(90, 8, f"{self.doc_type.upper()}: {self.doc_number}", border=False, align="R")
        
        self.ln(22)
        self.set_text_color(15, 23, 42)

    def footer(self):
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.set_text_color(100, 116, 139)
        self.cell(0, 10, f"Documento Comercial Oficial B2B - Folio {self.doc_number} | Página {self.page_no()}", align="C")

def create_invoice_pdf(data: Dict[str, Any], output_path: Path) -> Path:
    """Genera factura comercial en PDF."""
    pdf = B2BDocumentPDF("Factura Comercial / Commercial Invoice", data["invoice_id"], data["vendor_id"])
    pdf.add_page()
    
    # Metadata del Documento
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(95, 6, f"Emisor / Proveedor: {data['vendor_id']}", ln=False)
    pdf.cell(95, 6, f"Factura No: {data['invoice_id']}", ln=True, align="R")
    
    pdf.set_font("helvetica", "", 10)
    pdf.cell(95, 6, f"Cliente / Receptor: {data['customer_id']}", ln=False)
    pdf.cell(95, 6, f"Fecha Emision: {data['issue_date']}", ln=True, align="R")
    
    pdf.cell(95, 6, f"Orden de Compra Ref: {data.get('po_reference', 'N/A')}", ln=False)
    pdf.cell(95, 6, f"Moneda: {data.get('currency', 'USD')}", ln=True, align="R")
    pdf.ln(5)
    
    # Tabla de Items
    pdf.set_fill_color(30, 41, 59)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("helvetica", "B", 9)
    pdf.cell(30, 8, "Item ID", border=1, fill=True, align="C")
    pdf.cell(85, 8, "Descripcion", border=1, fill=True)
    pdf.cell(20, 8, "Cant.", border=1, fill=True, align="C")
    pdf.cell(25, 8, "P. Unitario", border=1, fill=True, align="R")
    pdf.cell(30, 8, "Total", border=1, fill=True, align="R")
    pdf.ln()
    
    pdf.set_text_color(15, 23, 42)
    pdf.set_font("helvetica", "", 9)
    fill = False
    for item in data["items"]:
        pdf.set_fill_color(241, 245, 249) if fill else pdf.set_fill_color(255, 255, 255)
        pdf.cell(30, 7, str(item["item_id"]), border=1, fill=fill, align="C")
        pdf.cell(85, 7, str(item["description"]), border=1, fill=fill)
        pdf.cell(20, 7, str(item["quantity"]), border=1, fill=fill, align="C")
        pdf.cell(25, 7, f"${Decimal(str(item['unit_price'])):,.2f}", border=1, fill=fill, align="R")
        pdf.cell(30, 7, f"${Decimal(str(item['total_price'])):,.2f}", border=1, fill=fill, align="R")
        pdf.ln()
        fill = not fill
        
    pdf.ln(4)
    # Resumen Financiero
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(135, 6, "", border=False)
    pdf.cell(25, 6, "Subtotal:", border=0, align="R")
    pdf.cell(30, 6, f"${Decimal(str(data['subtotal'])):,.2f}", border=1, align="R")
    pdf.ln()
    
    pdf.cell(135, 6, "", border=False)
    pdf.cell(25, 6, "Impuestos:", border=0, align="R")
    pdf.cell(30, 6, f"${Decimal(str(data.get('tax', 0))):,.2f}", border=1, align="R")
    pdf.ln()
    
    pdf.set_fill_color(224, 242, 254)
    pdf.cell(135, 7, "", border=False)
    pdf.cell(25, 7, "TOTAL:", border=0, align="R")
    pdf.cell(30, 7, f"${Decimal(str(data['total_amount'])):,.2f}", border=1, fill=True, align="R")
    pdf.ln(10)
    
    # Declaración de validez
    pdf.set_font("helvetica", "I", 8)
    pdf.cell(0, 5, "Validez fiscal y comercial certificada para procesamiento y conciliacion contable.", align="L")
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(output_path))
    return output_path

def create_purchase_order_pdf(data: Dict[str, Any], output_path: Path) -> Path:
    """Genera orden de compra en PDF."""
    pdf = B2BDocumentPDF("Orden de Compra / Purchase Order", data["po_id"], data["customer_id"])
    pdf.add_page()
    
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(95, 6, f"Comprador / Retailer: {data['customer_id']}", ln=False)
    pdf.cell(95, 6, f"PO ID: {data['po_id']}", ln=True, align="R")
    
    pdf.set_font("helvetica", "", 10)
    pdf.cell(95, 6, f"Proveedor Autorizado: {data['vendor_id']}", ln=False)
    pdf.cell(95, 6, f"Fecha de Orden: {data['order_date']}", ln=True, align="R")
    pdf.cell(95, 6, f"Condicion de Pago: Net 30 / Pactado", ln=False)
    pdf.cell(95, 6, f"Moneda: {data.get('currency', 'USD')}", ln=True, align="R")
    pdf.ln(5)
    
    # Tabla Items
    pdf.set_fill_color(30, 41, 59)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("helvetica", "B", 9)
    pdf.cell(30, 8, "Item ID", border=1, fill=True, align="C")
    pdf.cell(85, 8, "Descripcion Aprobada", border=1, fill=True)
    pdf.cell(20, 8, "Cant. Pedida", border=1, fill=True, align="C")
    pdf.cell(25, 8, "Precio Pactado", border=1, fill=True, align="R")
    pdf.cell(30, 8, "Total Pactado", border=1, fill=True, align="R")
    pdf.ln()
    
    pdf.set_text_color(15, 23, 42)
    pdf.set_font("helvetica", "", 9)
    fill = False
    for item in data["items"]:
        pdf.set_fill_color(241, 245, 249) if fill else pdf.set_fill_color(255, 255, 255)
        pdf.cell(30, 7, str(item["item_id"]), border=1, fill=fill, align="C")
        pdf.cell(85, 7, str(item["description"]), border=1, fill=fill)
        pdf.cell(20, 7, str(item["ordered_quantity"]), border=1, fill=fill, align="C")
        pdf.cell(25, 7, f"${Decimal(str(item['agreed_unit_price'])):,.2f}", border=1, fill=fill, align="R")
        pdf.cell(30, 7, f"${Decimal(str(item['total_price'])):,.2f}", border=1, fill=fill, align="R")
        pdf.ln()
        fill = not fill
        
    pdf.ln(4)
    pdf.set_fill_color(224, 242, 254)
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(135, 7, "", border=False)
    pdf.cell(25, 7, "TOTAL PO:", border=0, align="R")
    pdf.cell(30, 7, f"${Decimal(str(data['total_amount'])):,.2f}", border=1, fill=True, align="R")
    pdf.ln(10)
    
    pdf.set_font("helvetica", "I", 8)
    pdf.cell(0, 5, "Aceptacion vinculante sujeta a las condiciones generales de suministro y SLA.", align="L")
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(output_path))
    return output_path

def create_delivery_note_pdf(data: Dict[str, Any], output_path: Path) -> Path:
    """Genera remisión / comprobante de recepción de almacén en PDF."""
    pdf = B2BDocumentPDF("Remision de Entrega / Receiving Slip", data["delivery_id"], data["warehouse_location"])
    pdf.add_page()
    
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(95, 6, f"Folio Remision: {data['delivery_id']}", ln=False)
    pdf.cell(95, 6, f"PO Referencia: {data['po_reference']}", ln=True, align="R")
    
    pdf.set_font("helvetica", "", 10)
    pdf.cell(95, 6, f"Fecha de Recepcion: {data['delivery_date']}", ln=False)
    pdf.cell(95, 6, f"Bodega / Hub: {data['warehouse_location']}", ln=True, align="R")
    
    pdf.cell(95, 6, f"Recibido por: {data['received_by']}", ln=False)
    status_disp = "DISCREPANCIA REPORTADA" if data.get("discrepancy_reported") else "CONFORME / SIN NOVEDAD"
    pdf.cell(95, 6, f"Estado en Muelle: {status_disp}", ln=True, align="R")
    pdf.ln(5)
    
    # Tabla Items
    pdf.set_fill_color(30, 41, 59)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("helvetica", "B", 8)
    pdf.cell(25, 8, "Item ID", border=1, fill=True, align="C")
    pdf.cell(25, 8, "Despachado", border=1, fill=True, align="C")
    pdf.cell(25, 8, "Recibido", border=1, fill=True, align="C")
    pdf.cell(25, 8, "Faltante", border=1, fill=True, align="C")
    pdf.cell(25, 8, "Averiado", border=1, fill=True, align="C")
    pdf.cell(65, 8, "Notas de Inspeccion de Muelle", border=1, fill=True)
    pdf.ln()
    
    pdf.set_text_color(15, 23, 42)
    pdf.set_font("helvetica", "", 8)
    fill = False
    for item in data["items"]:
        pdf.set_fill_color(241, 245, 249) if fill else pdf.set_fill_color(255, 255, 255)
        pdf.cell(25, 7, str(item["item_id"]), border=1, fill=fill, align="C")
        pdf.cell(25, 7, str(item["quantity_delivered"]), border=1, fill=fill, align="C")
        pdf.cell(25, 7, str(item["quantity_received"]), border=1, fill=fill, align="C")
        pdf.cell(25, 7, str(item.get("missing_quantity", 0)), border=1, fill=fill, align="C")
        pdf.cell(25, 7, str(item.get("damaged_quantity", 0)), border=1, fill=fill, align="C")
        note = item.get("notes") or "Recibido conforme en tarima sellada."
        pdf.cell(65, 7, str(note)[:45], border=1, fill=fill)
        pdf.ln()
        fill = not fill
        
    pdf.ln(8)
    # Bloque de Firma y Sellos
    pdf.set_font("helvetica", "B", 9)
    pdf.cell(95, 6, "Constancia de Recepcion Fisica:", border=0)
    pdf.cell(95, 6, "Sello de Bodega y Seguridad:", border=0, align="R")
    pdf.ln()
    
    pdf.set_font("helvetica", "", 9)
    pdf.cell(95, 6, f"[FIRMADO DIGITALMENTE POR: {data['received_by']}]", border=1)
    pdf.cell(95, 6, f"[SELLO MUELLE: {data['warehouse_location']} - VERIFICADO]", border=1, align="R")
    pdf.ln(10)
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(output_path))
    return output_path

def create_payment_receipt_pdf(data: Dict[str, Any], output_path: Path) -> Path:
    """Genera comprobante de pago / Remittance Advice en PDF."""
    pdf = B2BDocumentPDF("Comprobante de Pago / Remittance Advice", data["payment_id"], "Cuentas por Pagar / AP")
    pdf.add_page()
    
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(95, 6, f"Referencia Pago: {data['payment_id']}", ln=False)
    pdf.cell(95, 6, f"Factura Cancelada: {data['invoice_reference']}", ln=True, align="R")
    
    pdf.set_font("helvetica", "", 10)
    pdf.cell(95, 6, f"Fecha de Dispersion: {data['payment_date']}", ln=False)
    pdf.cell(95, 6, f"Moneda: {data.get('currency', 'USD')}", ln=True, align="R")
    
    pdf.set_font("helvetica", "B", 10)
    pdf.set_fill_color(220, 252, 231)
    pdf.cell(95, 7, f"Monto Efectivo Pagado: ${Decimal(str(data['amount_paid'])):,.2f}", border=1, fill=True, ln=True)
    pdf.ln(5)
    
    # Detalle de deducciones
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(0, 6, "Deducciones y Retenciones Aplicadas al Pago:", ln=True)
    
    pdf.set_fill_color(30, 41, 59)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("helvetica", "B", 9)
    pdf.cell(35, 8, "Codigo Deduccion", border=1, fill=True, align="C")
    pdf.cell(85, 8, "Motivo Comercial / Operativo", border=1, fill=True)
    pdf.cell(35, 8, "Doc. Referencia", border=1, fill=True, align="C")
    pdf.cell(35, 8, "Monto Deducido", border=1, fill=True, align="R")
    pdf.ln()
    
    pdf.set_text_color(15, 23, 42)
    pdf.set_font("helvetica", "", 9)
    fill = False
    total_ded = Decimal("0.00")
    for ded in data.get("deductions", []):
        amt = Decimal(str(ded["amount"]))
        total_ded += amt
        pdf.set_fill_color(254, 242, 242) if fill else pdf.set_fill_color(255, 255, 255)
        pdf.cell(35, 7, str(ded["code"]), border=1, fill=fill, align="C")
        pdf.cell(85, 7, str(ded["reason"])[:45], border=1, fill=fill)
        pdf.cell(35, 7, str(ded.get("reference_doc") or "N/A"), border=1, fill=fill, align="C")
        pdf.cell(35, 7, f"${amt:,.2f}", border=1, fill=fill, align="R")
        pdf.ln()
        fill = not fill
        
    pdf.ln(4)
    pdf.set_fill_color(254, 226, 226)
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(120, 7, "", border=False)
    pdf.cell(35, 7, "TOTAL DEDUCCIONES:", border=0, align="R")
    pdf.cell(35, 7, f"${total_ded:,.2f}", border=1, fill=True, align="R")
    pdf.ln(10)
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(output_path))
    return output_path

def create_contract_pdf(data: Dict[str, Any], output_path: Path) -> Path:
    """Genera Contrato Marco de Suministro (MSA) en PDF."""
    pdf = B2BDocumentPDF("Contrato Marco de Suministro / Master Agreement", data["contract_id"], "Acuerdo Legal Vinculante")
    pdf.add_page()
    
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(95, 6, f"Contrato No: {data['contract_id']}", ln=False)
    pdf.cell(95, 6, f"Vigencia: {data['valid_from']} a {data['valid_to']}", ln=True, align="R")
    
    pdf.set_font("helvetica", "", 10)
    pdf.cell(95, 6, f"Parte Proveedora: {data['vendor_id']}", ln=False)
    pdf.cell(95, 6, f"Parte Compradora: {data['customer_id']}", ln=True, align="R")
    pdf.ln(5)
    
    pdf.set_font("helvetica", "B", 11)
    pdf.cell(0, 7, "TERMINOS Y CONDICIONES GENERALES DE OPERACION", ln=True)
    pdf.ln(2)
    
    for clause in data["clauses"]:
        pdf.set_fill_color(241, 245, 249)
        pdf.set_font("helvetica", "B", 10)
        pdf.cell(0, 7, f"CLAUSULA {clause['clause_id']}: {clause['title']}", border=1, fill=True, ln=True)
        
        pdf.set_font("helvetica", "", 9)
        pdf.multi_cell(0, 6, f"Texto: {clause['text']}", border="LRB")
        
        pdf.set_font("helvetica", "I", 8)
        tol = Decimal(str(clause.get("tolerance_percentage", 0)))
        pdf.cell(0, 5, f"Politica Operativa: {clause['policy']} | Tolerancia Permitida: {tol}%", border="LRB", ln=True)
        pdf.ln(4)
        
    output_path.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(output_path))
    return output_path
