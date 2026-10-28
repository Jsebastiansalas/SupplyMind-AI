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
        f"> **Expediente:** `{report.case_id}` | **Generado por:** SupplyMind AI (SKYNET Framework / Grok 4.7)",
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
        
    # Sección Pilar 3: Anclaje Fáctico Estricto y Certificación de Evidencias (Zero Uncited Claims)
    manifest = report.evidence_manifest
    if manifest:
        mf = manifest if isinstance(manifest, dict) else manifest.model_dump(mode="python")
        verdict = mf.get("binding_verdict", "N/A")
        ratio = mf.get("backing_ratio_pct", 100.0)
        cautelar = mf.get("cautelar_items", [])
        pointers = mf.get("evidence_pointers", [])

        lines.append("\n---")
        lines.append("## 3.1. CERTIFICACIÓN DE ANCLAJE FÁCTICO (PILAR 3 - ZERO UNCITED CLAIMS)\n")
        lines.append(f"- **Veredicto Probatorio:** `{verdict}`")
        lines.append(f"- **Ratio de Respaldo Fáctico:** **{ratio:.1f}%** ({mf.get('backed_claims_count', 0)} acreditadas vs {mf.get('unbacked_claims_count', 0)} cautelares)")
        lines.append(f"- **Total Respaldado:** ${Decimal(str(mf.get('total_backed_amount', 0))):,.2f} {report.currency}")

        if cautelar:
            lines.append("\n> ⚠️ **PARTIDAS CAUTELARES DETECTADAS (Requieren soporte físico de muelle/contrato):**")
            for c in cautelar:
                lines.append(f"> - {c}")

        if pointers:
            lines.append("\n| ID Puntero | Documento | SKU / Concepto | Monto | Estatus Probatorio |")
            lines.append("| :--- | :--- | :---: | :---: | :--- |")
            for p in pointers:
                p_dict = p if isinstance(p, dict) else (p.model_dump(mode="python") if hasattr(p, "model_dump") else {})
                ptr_id = p_dict.get("pointer_id", "PTR")
                doc_t = p_dict.get("doc_type", "DOC")
                sku_val = p_dict.get("item_sku") or p_dict.get("field_ref", "-")
                amt_val = Decimal(str(p_dict.get("amount", 0)))
                st_val = p_dict.get("status", "ACREDITADO")
                st_badge = "✅ ACREDITADO" if st_val == "ACREDITADO" else "⚠️ CAUTELAR NO ACREDITADA"
                lines.append(f"| `{ptr_id}` | {doc_t} | `{sku_val}` | ${amt_val:,.2f} | {st_badge} |")

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
        
    # Pilar 3: Debate Dialéctico Multi-Agente
    adv_verdict = getattr(report, "adversarial_verdict", None)
    if adv_verdict:
        lines.append("\n---")
        lines.append("## 4.1 DEBATE DIALÉCTICO MULTI-AGENTE (ADVERSARIAL COURTROOM)\n")
        lines.append(f"- **Fuerza Probatoria del Proveedor:** {adv_verdict.probative_force_supplier_pct}%\n")
        lines.append(f"- **Dictamen del Magistrado Arbitral:** {adv_verdict.magistrate_summary_ruling}\n")
        if adv_verdict.dismissed_objections:
            lines.append("**Objeciones del Retailer Desestimadas:**")
            for obj in adv_verdict.dismissed_objections:
                lines.append(f"> - 🛡️ {obj}")
        if adv_verdict.sustained_objections:
            lines.append("\n**Objeciones Concedidas en Muelle:**")
            for obj in adv_verdict.sustained_objections:
                lines.append(f"> - ⚖️ {obj}")

    lines.append("\n---")
    lines.append("## 5. PLAN DE ACCIÓN OPERATIVO Y COMERCIAL RECOMENDADO\n")
    lines.append(f"**Recomendación:**  \n{report.recommended_action}\n")

    # Pilar 4: Predicción de Cobro y Simulación de Escenarios
    rec_pred = getattr(report, "recovery_prediction", None)
    if rec_pred:
        lines.append("### 5.1 SCORING PREDICTIVO DE COBRO & SIMULACIÓN (PILAR 4)\n")
        lines.append(f"- **Probabilidad de Cobro:** **{rec_pred.recovery_probability_pct}%** ({rec_pred.confidence_grade})")
        lines.append(f"- **Ruta Estratégica Recomendada:** `{rec_pred.recommended_track}`")
        lines.append(f"- **Plazo Estimado a Liquidación:** {rec_pred.estimated_days_to_cash} días naturales")
        lines.append(f"- **Recuperación Neta Ponderada:** ${rec_pred.expected_net_recovery_usd:,.2f} USD")
        lines.append("\n**Simulación de Escenarios:**")
        lines.append("| Escenario | Monto Proyectado | Concesión | Plazo | Riesgo Legal |")
        lines.append("| :--- | :---: | :---: | :---: | :---: |")
        for sc in rec_pred.scenarios:
            rec_badge = " ⭐ (RECOMENDADO)" if sc.recommended else ""
            lines.append(f"| **{sc.scenario_name}**{rec_badge} | ${sc.projected_recovery_amount:,.2f} USD | ${sc.concession_granted_amount:,.2f} USD | {sc.estimated_days_to_cash}d | {sc.legal_risk_level} |")
        lines.append("")
    
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
    
    # Búsqueda de precedentes históricos en la Red de Memoria
    precedents_block = ""
    try:
        from agent.memory.precedent_matcher import PrecedentMatcher
        matcher = PrecedentMatcher()
        ded_code = None
        if pay and hasattr(pay, "deductions") and pay.deductions:
            ded_code = pay.deductions[0].code
        
        matches = matcher.find_relevant_precedents(
            retailer_id=str(customer_id),
            dispute_type=report.root_cause,
            deduction_code=ded_code,
            top_k=2
        )
        if matches:
            precedents_block = "\n" + PrecedentMatcher.format_precedents_block_for_letter(matches)
    except Exception:
        precedents_block = ""

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
{precedents_block}
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
    Y archiva el fallo en la Red de Memoria de Precedentes (Pilar 2).
    """
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    generated_files = {}
    from pathlib import Path
    safe_case_id = Path(report.case_id).name
    
    # 1. Reporte Markdown
    md_content = generate_markdown_report(report, state)
    md_path = REPORTS_DIR / f"dispute_report_{safe_case_id}.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    generated_files["markdown_report"] = str(md_path)
    
    # 2. Reporte JSON
    json_path = REPORTS_DIR / f"dispute_report_{safe_case_id}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report.model_dump(mode="json"), f, indent=2, ensure_ascii=False)
    generated_files["json_report"] = str(json_path)
    
    # 3. Carta de Reclamación (si hay monto a reclamar)
    if report.claimable_amount > Decimal("0.00"):
        letter_content = generate_reclamation_letter(report, state)
        letter_path = REPORTS_DIR / f"carta_reclamacion_{safe_case_id}.md"
        with open(letter_path, "w", encoding="utf-8") as f:
            f.write(letter_content)
        generated_files["reclamation_letter"] = str(letter_path)

    # 4. Pilar 2: Auto-aprendizaje en la Red de Memoria de Precedentes
    try:
        from agent.memory.precedent_graph import DisputeMemoryNetwork
        memory = DisputeMemoryNetwork()
        docs = state.loaded_documents if state else {}
        memory.record_case_resolution(
            case_id=report.case_id,
            report=report,
            docs=docs
        )
    except Exception:
        pass
        
    return generated_files

