"""
Generador de Caso Real de Prueba para Fase 2: Expediente con Remisión Escaneada / Fotográfica.
Caso: case_008_homedepot_damaged_scanned (Home Depot - Disputa de Mercancía Dañada en Muelle)
Monto Facturado: $42,000 USD | Monto Pagado: $33,800 USD | Retenido: $8,200 USD
- Deducción Justificada: $4,200 USD (20 unidades dañadas acreditadas con sello de patio en POD escaneado)
- Deducción Injustificada: $4,000 USD (Penalización unilateral no pactada en contrato)
"""

import io
from pathlib import Path
from fpdf import FPDF
from PIL import Image, ImageDraw

def generate_scanned_pod_image() -> Image.Image:
    """Genera una imagen realista que simula un remito impreso de papel con sello y anotaciones manuscritas."""
    img = Image.new('RGB', (800, 1000), color=(250, 250, 245))
    draw = ImageDraw.Draw(img)

    # Borde y membrete
    draw.rectangle([(20, 20), (780, 980)], outline=(170, 170, 170), width=2)
    draw.text((40, 40), "REMISIÓN DE ENTREGA FÍSICA (BILL OF LADING / PROOF OF DELIVERY)", fill=(20, 20, 20))
    draw.text((40, 65), "THE HOME DEPOT MÉXICO - LOGISTICS HUB & MUELLE DE DESCARGA", fill=(60, 60, 60))

    # Metadatos del envío
    draw.text((40, 110), "Folio Remision: DEL-HD-2026-8812", fill=(30, 30, 30))
    draw.text((40, 135), "PO Referencia: PO-HD-44091", fill=(30, 30, 30))
    draw.text((40, 160), "Fecha de Recepcion: 2026-03-15", fill=(30, 30, 30))
    draw.text((40, 185), "Bodega / Hub: HUB_CENTRAL_MONTERREY", fill=(30, 30, 30))
    draw.text((40, 210), "Transportista: Transportes Rápidos del Norte S.A.", fill=(30, 30, 30))

    # Tabla de partidas
    draw.rectangle([(40, 260), (760, 295)], fill=(225, 230, 235))
    draw.text((50, 270), "SKU / ITEM", fill=(10, 10, 10))
    draw.text((250, 270), "DESPACHADO", fill=(10, 10, 10))
    draw.text((380, 270), "RECIBIDO", fill=(10, 10, 10))
    draw.text((500, 270), "FALTANTE", fill=(10, 10, 10))
    draw.text((620, 270), "AVERIADO", fill=(10, 10, 10))

    draw.text((50, 320), "SKU-CERAMIC-60X60", fill=(20, 20, 20))
    draw.text((270, 320), "200", fill=(20, 20, 20))
    draw.text((400, 320), "180", fill=(20, 20, 20))
    draw.text((520, 320), "0", fill=(20, 20, 20))
    draw.text((640, 320), "20", fill=(180, 0, 0))

    # Sello de muelle con tinta roja y anotaciones del inspector
    draw.rectangle([(40, 420), (760, 640)], outline=(190, 40, 40), width=3)
    draw.text((60, 440), "[ SELLO OFICIAL DE MUELLE - RECEPCIÓN CON AVERÍA TÉCNICA ]", fill=(190, 30, 30))
    draw.text((60, 475), "ANOTACIÓN DEL INSPECTOR DE PATIO (MANUSCRITO):", fill=(30, 30, 160))
    draw.text((60, 510), "Se constatan 20 cajas de SKU-CERAMIC-60X60 aplastadas por caída en patio.", fill=(20, 20, 140))
    draw.text((60, 540), "Porcelanato totalmente quebrado e inservible. Se rechazan 20 unidades.", fill=(20, 20, 140))
    draw.text((60, 570), "Restante aceptado de conformidad (180 unidades recibidas en buen estado).", fill=(20, 20, 140))
    draw.text((60, 600), "Firma y Sello Receptor: Roberto Gomez (Inspector Muelle) - Cédula: 94812", fill=(20, 20, 140))

    draw.text((40, 700), "ESTADO DE CONCILIACIÓN: DISCREPANCIA REPORTADA EN MUELLE - MERCANCIA DANADA", fill=(180, 20, 20))

    return img

def create_case_008():
    case_dir = Path("data/cases/case_008_homedepot_damaged_scanned")
    case_dir.mkdir(parents=True, exist_ok=True)

    # 1. Factura Comercial (PDF)
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "CERAMICAS_DEL_NORTE_SA FACTURA", ln=True, align="C")
    pdf.set_font("Helvetica", size=10)
    pdf.cell(0, 7, "Factura No: INV-HD-2026-9041", ln=True)
    pdf.cell(0, 7, "Emisor / Proveedor: CERAMICAS_DEL_NORTE_SA", ln=True)
    pdf.cell(0, 7, "Cliente / Receptor: HOME_DEPOT_MEXICO", ln=True)
    pdf.cell(0, 7, "Orden de Compra Ref: PO-HD-44091", ln=True)
    pdf.cell(0, 7, "Fecha Emision: 2026-03-01", ln=True)
    pdf.cell(0, 7, "Moneda: USD", ln=True)
    pdf.ln(5)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 7, "Item ID / Descripcion / Cantidad / P. Unitario / Total", ln=True)
    pdf.set_font("Helvetica", size=9)
    pdf.cell(0, 7, "SKU-CERAMIC-60X60 Porcelanato Pulido Rectificado 60x60cm 200 $210.00 $42,000.00", ln=True)
    pdf.ln(5)
    pdf.cell(0, 7, "Subtotal: $42,000.00", ln=True)
    pdf.cell(0, 7, "Impuestos: $0.00", ln=True)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, "TOTAL: $42,000.00", ln=True)
    pdf.output(str(case_dir / "invoice.pdf"))

    # 2. Orden de Compra (PDF)
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "THE HOME DEPOT - PURCHASE ORDER", ln=True, align="C")
    pdf.set_font("Helvetica", size=10)
    pdf.cell(0, 7, "PO ID: PO-HD-44091", ln=True)
    pdf.cell(0, 7, "Comprador / Retailer: HOME_DEPOT_MEXICO", ln=True)
    pdf.cell(0, 7, "Proveedor Autorizado: CERAMICAS_DEL_NORTE_SA", ln=True)
    pdf.cell(0, 7, "Fecha de Orden: 2026-02-20", ln=True)
    pdf.cell(0, 7, "Moneda: USD", ln=True)
    pdf.ln(5)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 7, "Item ID / Descripcion / Cantidad Pedida / Precio Pactado / Total", ln=True)
    pdf.set_font("Helvetica", size=9)
    pdf.cell(0, 7, "SKU-CERAMIC-60X60 Porcelanato Pulido Rectificado 60x60cm 200 $210.00 $42,000.00", ln=True)
    pdf.ln(5)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, "TOTAL PO: $42,000.00", ln=True)
    pdf.output(str(case_dir / "purchase_order.pdf"))

    # 3. Remisión Escaneada FÍSICA: delivery.png Y delivery.pdf (Raster / Imagen Única)
    pod_img = generate_scanned_pod_image()
    png_path = case_dir / "delivery.png"
    pod_img.save(str(png_path), format="PNG")

    img_buf = io.BytesIO()
    pod_img.save(img_buf, format="PNG")
    img_buf.seek(0)

    pdf = FPDF()
    pdf.add_page()
    pdf.image(img_buf, x=10, y=10, w=190)
    pdf.output(str(case_dir / "delivery.pdf"))

    # 4. Comprobante de Pago con Deducciones (PDF)
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "HOME DEPOT - REMITTANCE ADVICE / WIRE TRANSFER", ln=True, align="C")
    pdf.set_font("Helvetica", size=10)
    pdf.cell(0, 7, "Referencia Pago: WIRE-HD-2026-33910", ln=True)
    pdf.cell(0, 7, "Factura Cancelada: INV-HD-2026-9041", ln=True)
    pdf.cell(0, 7, "Fecha de Dispersion: 2026-03-25", ln=True)
    pdf.cell(0, 7, "Moneda: USD", ln=True)
    pdf.cell(0, 7, "Monto Efectivo Pagado: $33,800.00", ln=True)
    pdf.ln(5)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 7, "Deducciones y Retenciones:", ln=True)
    pdf.set_font("Helvetica", size=9)
    pdf.cell(0, 7, "Codigo Deduccion / Motivo / Doc Referencia / Monto", ln=True)
    pdf.cell(0, 7, "DED-DAMAGED-DOCK Retencion por 20 unidades averiadas en muelle DEL-HD-2026-8812 $4,200.00", ln=True)
    pdf.cell(0, 7, "DED-UNILAT-DOCK-FEE Penalizacion administrativa descarga no programada N/A $4,000.00", ln=True)
    pdf.ln(5)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, "TOTAL DEDUCCIONES: $8,200.00", ln=True)
    pdf.output(str(case_dir / "payment.pdf"))

    # 5. Contrato Comercial MSA (PDF)
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "CONTRATO MARCO DE SUMINISTRO (MSA)", ln=True, align="C")
    pdf.set_font("Helvetica", size=10)
    pdf.cell(0, 7, "Contrato No: MSA-HD-CERAMIC-2026", ln=True)
    pdf.cell(0, 7, "Vigencia: 2026-01-01 a 2026-12-31", ln=True)
    pdf.cell(0, 7, "Parte Proveedora: CERAMICAS_DEL_NORTE_SA", ln=True)
    pdf.cell(0, 7, "Parte Compradora: HOME_DEPOT_MEXICO", ln=True)
    pdf.ln(5)

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 7, "CLAUSULA 5.1: Politica de Mercancia Danada o Averiada en Muelle", ln=True)
    pdf.set_font("Helvetica", size=9)
    pdf.multi_cell(0, 5, "Texto: El Comprador podra retener o deducir del pago el valor correspondiente a unidades danadas o destruidas en muelle, siempre que conste constancia expresa firmada por el receptor.\nPolitica Operativa: DAMAGED_GOODS_POLICY\nTolerancia Permitida: 0.00%")
    pdf.ln(5)

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 7, "CLAUSULA 7.2: Improcedencia de Penalizaciones Unilaterales", ln=True)
    pdf.set_font("Helvetica", size=9)
    pdf.multi_cell(0, 5, "Texto: Toda penalizacion o cargo por descarga extemporanea requiere acuerdo previo por escrito entre las partes. Las retenciones unilaterales sin adenda seran nulas de pleno derecho.\nPolitica Operativa: GENERAL_COMPLIANCE\nTolerancia Permitida: 0.00%")

    pdf.output(str(case_dir / "contract.pdf"))
    print(f"Caso creado exitosamente en: {case_dir}")

if __name__ == "__main__":
    create_case_008()
