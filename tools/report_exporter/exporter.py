import json
from decimal import Decimal
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional

from data.models import DisputeAnalysisReport
from agent.core.state import DisputeState

REPORTS_DIR = Path(__file__).resolve().parent.parent.parent / "reports"

def generate_markdown_report(report: DisputeAnalysisReport, state: Optional[DisputeState] = None) -> str:
    """Genera un informe formal en Markdown con formato ejecutivo corporativo."""
    rec = state.reconciliation_summary if state else None
    ev = state.contract_evaluation if state else None
    
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    
    lines = [
        f"# 📋 INFORME FORMAL DE CONCILIACIÓN Y ANÁLISIS DE DISPUTA B2B",
        f"> **Expediente:** `{report.case_id}` | **Generado por:** SupplyMind AI (Hermes Agent / Grok 4.7)",
        f"> **Fecha de Emisión:** {timestamp} | **Nivel de Confianza:** {report.confidence * 100:.1f}%\n",
        "---",
        "## 1. RESUMEN FINANCIERO EJECUTIVO\n",
        "| Concepto | Monto | Moneda | Estado de Validación |",
        "| :--- | :---: | :---: | :--- |",
        f"| **Monto Facturado** | **${report.billed_amount:,.2f}** | {report.currency} | Cotejado con Factura Comercial |",
        f"| **Monto Recibido en Pago** | **${report.received_amount:,.2f}** | {report.currency} | Verificado en Comprobante Bancario |",
        f"| **Diferencia Total / Retención** | **${report.difference:,.2f}** | {report.currency} | Desfase cuantitativo neto |",
        f"| **Deducciones Justificadas** | **${report.justified_amount:,.2f}** | {report.currency} | Respaldadas documental/físicamente |",
        f"| **Monto Reclamable al Cliente** | **${report.claimable_amount:,.2f}** | {report.currency} | Retención indebida exigible |",
        "\n---",
        "## 2. DETERMINACIÓN DE LA CAUSA RAÍZ\n",
        f"**Diagnóstico:**  \n{report.root_cause}\n",
        "---",
        "## 3. TRAZABILIDAD Y CADENA DE EVIDENCIAS DOCUMENTALES\n"
    ]
    
    for idx, e in enumerate(report.evidence, start=1):
        lines.append(f"{idx}. {e}")
        
    lines.append("\n---")
    lines.append("## 4. DICTAMEN LEGAL Y CONTRACTUAL\n")
    if ev:
        lines.append(f"- **Evaluación Jurídica:** {ev.summary_legal_assessment}")
        lines.append(f"- **Acción Contractual Sugerida:** {ev.recommended_contract_action}")
        lines.append("\n**Cláusulas Invocadas:**")
        for m in ev.matches:
            status = "AUTORIZADA" if m.is_deduction_authorized else "NO AUTORIZADA / OBJETABLE"
            lines.append(f"- **{m.clause_id} ({m.title})** [{status}]: {m.explanation}")
    else:
        lines.append("- Evaluación procesada conforme a las condiciones comerciales generales pactadas.")
        
    lines.append("\n---")
    lines.append("## 5. PLAN DE ACCIÓN OPERATIVO Y COMERCIAL RECOMENDADO\n")
    lines.append(f"**Recomendación:**  \n{report.recommended_action}\n")
    
    if state and (state.tokens_in > 0 or state.tokens_out > 0):
        lines.append("---")
        lines.append("## 6. MÉTRICAS DE EJECUCIÓN Y EFICIENCIA (UNIT ECONOMICS)\n")
        lines.append(f"- **Tokens de Entrada:** {state.tokens_in:,}")
        lines.append(f"- **Tokens de Salida:** {state.tokens_out:,}")
        lines.append(f"- **Costo Estimado de Inferencia:** ${state.estimated_cost_usd:.5f} USD")
        lines.append(f"- **Tiempo de Resolución:** {state.execution_time_seconds:.2f} s")
        lines.append(f"- **Gobernanza:** Motor determinístico en Python `Decimal` (Cero Alucinación Financiera).")

    lines.append("\n---\n*Documento oficial generado autónomamente por SupplyMind AI para gestión de cartera, operaciones y auditoría B2B.*")
    return "\n".join(lines)


def generate_reclamation_letter(report: DisputeAnalysisReport, state: Optional[DisputeState] = None) -> str:
    """Genera una carta formal corporativa de objeción comercial y reclamación de cartera."""
    date_str = datetime.now().strftime("%d de %B de %Y")
    docs = state.loaded_documents if state else {}
    
    inv = docs.get("invoice")
    pay = docs.get("payment")
    deliv = docs.get("delivery")
    ctr = docs.get("contract")
    
    vendor_id = inv.vendor_id if inv else "PROVEEDOR-DISTRIBUIDOR"
    customer_id = inv.customer_id if inv else "DEPARTAMENTO DE CUENTAS POR PAGAR"
    inv_id = inv.invoice_id if inv else "INV-S/N"
    pay_id = pay.payment_id if pay else "PAY-S/N"
    del_id = deliv.delivery_id if deliv else "DEL-S/N"
    ctr_id = ctr.contract_id if ctr else "CTR-MARCO"
    
    letter = f"""# 📑 NOTIFICACIÓN FORMAL DE DISPUTA COMERCIAL Y REQUERIMIENTO DE PAGO
**Ref: Expediente de Cartera {report.case_id} / Factura {inv_id}**  
**Fecha:** {date_str}  
**De:** Departamento de Cartera y Asuntos Comerciales — {vendor_id}  
**Para:** Gerencia de Cuentas por Pagar y Conciliación — {customer_id}  

---

### Estimados señores de {customer_id}:

Por medio de la presente, acusamos recibo del comprobante de liquidación y pago **{pay_id}** por valor de **${report.received_amount:,.2f} USD**, aplicado contra nuestra factura comercial **{inv_id}** emitida por **${report.billed_amount:,.2f} USD**.

Habiendo realizado la auditoría técnica y contractual correspondiente, les comunicamos que existe una diferencia no conciliada de **${abs(report.difference):,.2f} USD**, respecto de la cual fijamos nuestra posición formal:

#### 1. Deducciones Aceptadas y Justificadas: **${report.justified_amount:,.2f} USD**
Aceptamos de plena conformidad la deducción por valor de **${report.justified_amount:,.2f} USD**, debidamente amparada en las constancias físicas de entrega del documento **{del_id}** y conforme a lo pactado contractualmente. Para sanear este importe, estaremos emitiendo a su favor la respectiva **Nota de Crédito comercial**.

#### 2. Deducciones Objetadas y Saldo Reclamable: **${report.claimable_amount:,.2f} USD**
Rechazamos formalmente las deducciones adicionales aplicadas por un importe total de **${report.claimable_amount:,.2f} USD**, por carecer de soporte probatorio y contrariar los términos del contrato comercial **{ctr_id}**:
- **Causa Raíz:** {report.root_cause}
- **Fundamentación Contractual:** {state.contract_evaluation.summary_legal_assessment if state and state.contract_evaluation else 'Deducción unilateral no convenida ni acreditada en muelle de recepción.'}

#### 3. Requerimiento de Pago
En virtud de lo anterior, solicitamos comedidamente realizar la programación y transferencia del saldo retenido injustificadamente por valor de:

### 👉 **MONTO TOTAL A REINTEGRAR: ${report.claimable_amount:,.2f} USD**

Agradecemos que dicho pago se haga efectivo dentro de los siguientes **quince (15) días hábiles** a la recepción de la presente comunicación, o en su defecto, coordinar una mesa técnica de conciliación con nuestro equipo de cartera.

Anexamos a la presente el informe técnico pormenorizado y las copias de la remisión y contrato.

Atentamente,

**ÁREA DE CONCILIACIÓN DE CARTERA Y DISPUTAS COMERCIALES**  
*{vendor_id}*  
*Trazabilidad auditable respaldada por SupplyMind AI*
"""
    return letter


def export_dispute_artifacts(report: DisputeAnalysisReport, state: Optional[DisputeState] = None) -> Dict[str, str]:
    """
    Exporta los artefactos de la resolución a la carpeta reports/:
    - dispute_report_<case_id>.md
    - dispute_report_<case_id>.json
    - carta_reclamacion_<case_id>.md (si claimable_amount > 0)
    """
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    generated_files = {}
    
    # 1. Reporte Markdown
    md_content = generate_markdown_report(report, state)
    md_path = REPORTS_DIR / f"dispute_report_{report.case_id}.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    generated_files["markdown_report"] = str(md_path)
    
    # 2. Reporte JSON
    json_path = REPORTS_DIR / f"dispute_report_{report.case_id}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report.model_dump(mode="json"), f, indent=2, ensure_ascii=False)
    generated_files["json_report"] = str(json_path)
    
    # 3. Carta de Reclamación (si hay monto a reclamar)
    if report.claimable_amount > Decimal("0.00"):
        letter_content = generate_reclamation_letter(report, state)
        letter_path = REPORTS_DIR / f"carta_reclamacion_{report.case_id}.md"
        with open(letter_path, "w", encoding="utf-8") as f:
            f.write(letter_content)
        generated_files["reclamation_letter"] = str(letter_path)
        
    return generated_files
