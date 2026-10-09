import os
from pathlib import Path
from fpdf import FPDF
from agent.core.skynet_runner import SkynetReport

class PDFReport(FPDF):
    def header(self):
        self.set_font("helvetica", "B", 15)
        self.cell(0, 10, "SKYNET - INFORME LEGAL Y FINANCIERO", border=False, align="C")
        self.ln(20)

    def footer(self):
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.cell(0, 10, f"Generado automáticamente por SKYNET AI - Página {self.page_no()}", align="C")

class CommunicationEngine:
    def __init__(self):
        pass
        
    def generate_pdf_report(self, report: SkynetReport, output_dir: str) -> str:
        """Genera un archivo PDF con el dictamen formal."""
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        pdf = PDFReport()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        pdf.set_font("helvetica", "B", 12)
        pdf.cell(0, 10, f"Expediente: {Path(report.case_id).name}", ln=True)
        pdf.ln(5)
        
        # Resumen Financiero
        pdf.set_font("helvetica", "B", 11)
        pdf.cell(0, 10, "1. RESUMEN FINANCIERO", ln=True)
        pdf.set_font("helvetica", "", 10)
        pdf.cell(0, 8, f"Monto Facturado: ${report.billed_amount:,.2f}", ln=True)
        pdf.cell(0, 8, f"Monto Recibido: ${report.received_amount:,.2f}", ln=True)
        pdf.cell(0, 8, f"Diferencia (Deducción): ${report.difference:,.2f}", ln=True)
        
        pdf.ln(5)
        pdf.set_font("helvetica", "B", 10)
        pdf.set_text_color(200, 0, 0) if report.justified_amount > 0 else pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 8, f"Deducción Justificada Contractualmente: ${report.justified_amount:,.2f}", ln=True)
        
        pdf.set_text_color(0, 150, 0) if report.claimable_amount > 0 else pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 8, f"Monto Reclamable (A Favor): ${report.claimable_amount:,.2f}", ln=True)
        pdf.set_text_color(0, 0, 0)
        
        pdf.ln(10)
        
        # Causa Raíz
        pdf.set_font("helvetica", "B", 11)
        pdf.cell(0, 10, "2. CAUSA RAÍZ Y HALLAZGOS", ln=True)
        pdf.set_font("helvetica", "", 10)
        pdf.multi_cell(0, 8, report.root_cause)
        pdf.ln(5)
        
        # Evidencia
        pdf.set_font("helvetica", "B", 11)
        pdf.cell(0, 10, "3. EVIDENCIA TÉCNICA", ln=True)
        pdf.set_font("helvetica", "", 10)
        for ev in report.evidence:
            pdf.multi_cell(0, 8, f"- {ev}")
        pdf.ln(5)
        
        # Accion
        pdf.set_font("helvetica", "B", 11)
        pdf.cell(0, 10, "4. ACCIÓN RECOMENDADA (Veredicto SKYNET)", ln=True)
        pdf.set_font("helvetica", "I", 10)
        pdf.multi_cell(0, 8, report.recommended_action)
        pdf.ln(5)
        
        file_path = os.path.join(output_dir, f"Dictamen_{Path(report.case_id).name}.pdf")
        pdf.output(file_path)
        return file_path

    def generate_email_draft(self, report: SkynetReport, client_name: str = "Estimado Cliente") -> str:
        """Genera un borrador de correo corporativo para enviar al cliente."""
        
        if report.claimable_amount > 0:
            asunto = f"Reclamación de Diferencias en Pago - {Path(report.case_id).name}"
            cuerpo = f"""{client_name},

Espero se encuentre muy bien.

Nos dirigimos a usted en relación con las deducciones aplicadas recientemente a nuestras facturas en el expediente {Path(report.case_id).name}.
Tras una auditoría exhaustiva realizada por nuestro sistema autónomo SKYNET, hemos identificado que existe un monto de ${report.claimable_amount:,.2f} deducido sin justificación física ni amparo contractual.

A continuación detallamos el hallazgo:
{report.root_cause}

Por tal motivo, solicitamos amablemente el pago complementario de ${report.claimable_amount:,.2f} a la brevedad posible. Adjuntamos a este correo el dictamen formal en formato PDF con la evidencia documental y las cláusulas analizadas.

Quedamos a su disposición para agendar una llamada si requieren aclarar este punto.

Atentamente,
Departamento de Cobranza (Impulsado por SKYNET AI)"""
        else:
            asunto = f"Aceptación de Nota de Crédito - {Path(report.case_id).name}"
            cuerpo = f"""{client_name},

Espero se encuentre muy bien.

Le confirmamos que nuestro sistema automatizado de conciliación (SKYNET) ha validado exitosamente las deducciones aplicadas por su equipo en el expediente {Path(report.case_id).name}.
Hemos comprobado que el monto retenido de ${report.justified_amount:,.2f} se encuentra amparado bajo los acuerdos comerciales vigentes.

Causa de la validación:
{report.root_cause}

Procederemos a emitir la Nota de Crédito correspondiente para sanear su cuenta y que los saldos queden en cero.

Atentamente,
Departamento de Cobranza (Impulsado por SKYNET AI)"""
        
        return asunto, cuerpo
