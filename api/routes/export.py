"""
api/routes/export.py
Endpoints para exportación de Carta de Reclamación, borradores de correo y reportes JSON.
"""

from pathlib import Path
from decimal import Decimal
from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse

from agent.core.skynet_runner import SkynetRunner
from data.models import DisputeAnalysisReport
from tools.report_exporter import export_dispute_artifacts

router = APIRouter(prefix="/cases", tags=["Exportación de Entregables"])


@router.get("/{case_id}/claim-letter")
def get_claim_letter(case_id: str):
    """Obtiene el texto oficial de la Carta Formal de Reclamación para el caso."""
    runner = SkynetRunner(case_id=case_id, fast_path=True, use_cache=True)
    report: DisputeAnalysisReport = runner.run()

    # Verificar si ya existe en reports/
    letter_path = Path("reports") / f"carta_reclamacion_{case_id}.md"
    if letter_path.exists():
        return PlainTextResponse(letter_path.read_text(encoding="utf-8"), media_type="text/markdown")

    # Si no existe, generarla al vuelo
    export_dispute_artifacts(report)
    if letter_path.exists():
        return PlainTextResponse(letter_path.read_text(encoding="utf-8"), media_type="text/markdown")

    if report.claimable_amount <= Decimal("0"):
        return PlainTextResponse(
            f"# NOTIFICACIÓN DE SALDO SANEADO — EXPEDIENTE {case_id}\n\n"
            f"El expediente no presenta saldo reclamable a favor. Toda la retención (${report.justified_amount:,.2f} USD) "
            f"se encuentra amparada contractualmente. No procede emisión de carta de reclamación coactiva.",
            media_type="text/markdown"
        )

    raise HTTPException(status_code=404, detail="No fue posible generar la carta de reclamación.")


@router.get("/{case_id}/email-draft")
def get_email_draft(case_id: str):
    """Genera un borrador formal de correo electrónico B2B para notificar a la contraparte."""
    runner = SkynetRunner(case_id=case_id, fast_path=True, use_cache=True)
    report: DisputeAnalysisReport = runner.run()

    if report.claimable_amount > Decimal("0"):
        subject = f"[NOTIFICACIÓN FORMAL] Disputa Comercial y Objeción de Deducción — Expediente {case_id}"
        body = f"""Estimado equipo de Cuentas por Pagar y Cartera,

Por medio de la presente, nos dirigimos a ustedes en relación con la liquidación bancaria del expediente {case_id}.

Tras la auditoría exhaustiva realizada por nuestra Dirección de Conciliación Comercial (SupplyMind AI), se determinó que de la retención total de ${abs(report.difference):,.2f} USD aplicada sobre nuestra factura, un importe de ${report.claimable_amount:,.2f} USD carece de respaldo probatorio y vulnera los acuerdos contractuales vinculantes.

Causa raíz del saldo en reclamación:
{report.root_cause}

Solicitamos respetuosamente la regularización y transferencia del saldo a favor de ${report.claimable_amount:,.2f} USD dentro de los próximos 15 días hábiles, o en su defecto, la documentación probatoria que acredite dicha retención.

Atentamente,
Departamento de Conciliación y Cartera B2B
SupplyMind AI Operations"""
    else:
        subject = f"[CONCILIACIÓN EXITOSA] Aceptación de Deducción y Cierre de Cuenta — Expediente {case_id}"
        body = f"""Estimado equipo de Cuentas por Pagar,

Confirmamos la recepción de la liquidación del expediente {case_id}.

Nuestra auditoría comercial determinó que la deducción de ${report.justified_amount:,.2f} USD se encuentra debidamente soportada en la remisión de entrega y amparada por las cláusulas contractuales vigentes ({report.root_cause}).

Procedemos a emitir la Nota de Crédito comercial correspondiente por dicho valor para el saneamiento definitivo de la cuenta por cobrar.

Agradecemos su continua colaboración comercial.

Atentamente,
Departamento de Conciliación y Cartera B2B
SupplyMind AI Operations"""

    return {"subject": subject, "body": body}
