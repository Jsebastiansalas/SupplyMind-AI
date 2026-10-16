"""
tools/notice_window_auditor.py
Auditoría jurídica de caducidad y temporalidad (Notice Window Audit) para disputas comerciales B2B.
Evalúa si las deducciones u objeciones del comprador se formularon dentro de la ventana contractual vinculante.
"""

from datetime import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel, ConfigDict


class NoticeWindowAudit(BaseModel):
    model_config = ConfigDict(extra="ignore")

    delivery_date: Optional[str]
    payment_date: Optional[str]
    days_elapsed: int
    contractual_limit_days: int
    is_timely: bool
    status_label: str
    legal_basis: str
    statute_of_limitations_applied: bool


def audit_notice_window(
    delivery_data: Optional[Dict[str, Any]] = None,
    payment_data: Optional[Dict[str, Any]] = None,
    contract_data: Optional[Dict[str, Any]] = None,
    default_limit_days: int = 30,
) -> NoticeWindowAudit:
    """
    Audita la validez temporal del reclamo conforme a la cláusula contractual de notificación.
    Si el comprador dedujo después de la ventana pactada, la deducción es extemporánea y nula.
    """
    deliv_date_str = None
    if delivery_data:
        deliv_date_str = delivery_data.get("delivery_date")

    pay_date_str = None
    if payment_data:
        pay_date_str = payment_data.get("payment_date")

    # Obtener límite contractual si existe cláusula de plazos
    limit_days = default_limit_days
    clause_ref = "Cláusula Marco de Plazos y Notificación de Discrepancias (30 días naturales)"
    if contract_data and "clauses" in contract_data:
        for cl in contract_data["clauses"]:
            cid = cl.get("clause_id", "")
            title = cl.get("title", "").lower()
            text = cl.get("text", "").lower()
            if "8.2" in cid or "plazos" in title or "días" in text or "dias" in text:
                clause_ref = f"{cl.get('clause_id')}: {cl.get('title')}"
                if "15" in text:
                    limit_days = 15
                elif "48" in text or "horas" in text:
                    pass  # para averías inmediatas
                break

    if not deliv_date_str or not pay_date_str:
        return NoticeWindowAudit(
            delivery_date=deliv_date_str,
            payment_date=pay_date_str,
            days_elapsed=0,
            contractual_limit_days=limit_days,
            is_timely=True,
            status_label="FECHAS NO DISPONIBLES (CUMPLIMIENTO PRESUNTO)",
            legal_basis=f"Revisión supletoria bajo {clause_ref}.",
            statute_of_limitations_applied=False,
        )

    try:
        d_deliv = datetime.strptime(deliv_date_str[:10], "%Y-%m-%d")
        d_pay = datetime.strptime(pay_date_str[:10], "%Y-%m-%d")
        days_diff = (d_pay - d_deliv).days
    except Exception:
        days_diff = 0

    if days_diff > limit_days:
        is_timely = False
        status_label = f"EXTEMPORÁNEO ({days_diff} DÍAS &gt; {limit_days} DÍAS LÍMITE)"
        legal_basis = (
            f"El comprador aplicó la deducción trascurrido el plazo máximo de {limit_days} días naturales "
            f"({days_diff} días transcurridos desde recepción). Conforme a {clause_ref}, la deducción es "
            f"extemporánea y legalmente nula, operando la presunción de recepción conforme irrevocable."
        )
        applied = True
    else:
        is_timely = True
        status_label = f"EN PLAZO ({days_diff} DÍAS &le; {limit_days} DÍAS)"
        legal_basis = f"Deducción notificada en tiempo y forma procesal dentro de la ventana de {limit_days} días s/ {clause_ref}."
        applied = False

    return NoticeWindowAudit(
        delivery_date=deliv_date_str,
        payment_date=pay_date_str,
        days_elapsed=days_diff,
        contractual_limit_days=limit_days,
        is_timely=is_timely,
        status_label=status_label,
        legal_basis=legal_basis,
        statute_of_limitations_applied=applied,
    )
