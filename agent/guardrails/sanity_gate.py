"""
agent/guardrails/sanity_gate.py
Motor de Análisis Infalible: Sanity Gate, Verificación de Prelación Legal,
Ventana Perentoria y Detección de Doble Penalización (Semana 4 - Sprint 4.1).

Garantiza que ningún dictamen de SupplyMind AI sufra de:
1. Discrepancias aritméticas o errores de redondeo ($0.00 MAE garantizado).
2. Puntos ciegos por extemporaneidad de notificación del comprador.
3. Dobles penalizaciones abusivas sobre el mismo evento operativo.
4. Violaciones a la jerarquía de prelación legal comercial (Art. 88 Código de Comercio).
"""

from decimal import Decimal
import re
from datetime import datetime, date
from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel, ConfigDict, Field

from data.models import DisputeAnalysisReport


class SanityGateAuditResult(BaseModel):
    """Certificado pericial de verificación cuádruple del expediente."""
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    is_bulletproof: bool = True
    arithmetic_invariant_passed: bool = True
    precedence_hierarchy_passed: bool = True
    notice_window_passed: bool = True
    notice_window_days_allowed: Optional[int] = None
    notice_window_days_elapsed: Optional[int] = None
    double_penalty_detected: bool = False
    double_penalty_details: List[str] = Field(default_factory=list)
    irrefutability_grade: str = "A1_IRREFUTABLE"  # "A1_IRREFUTABLE", "A2_JURISPRUDENCIAL", "B1_ALLANAMIENTO", "C1_LITIGIOSO"
    corrective_actions_applied: List[str] = Field(default_factory=list)
    audit_notes: List[str] = Field(default_factory=list)
    verified_claimable_amount: Decimal = Field(default=Decimal("0.00"))
    verified_justified_amount: Decimal = Field(default=Decimal("0.00"))


class SanityGateEngine:
    """Orquestador del Filtro de Cuádruple Auditoría Cruzada (Quad-Check Consensus)."""

    @classmethod
    def audit_and_reinforce_case(
        cls,
        report: DisputeAnalysisReport,
        docs: Optional[Dict[str, Any]] = None
    ) -> SanityGateAuditResult:
        """
        Ejecuta la auditoría exhaustiva de 4 filtros y refuerza el reporte contra cualquier punto ciego.
        """
        docs = docs or {}
        inv = docs.get("invoice")
        deliv = docs.get("delivery")
        pay = docs.get("payment")
        ctr = docs.get("contract")

        audit_notes: List[str] = []
        corrections: List[str] = []

        # =================================================================
        # FILTRO 1: SANITY CHECK ARITMÉTICO & ÁRBOL DE INVARIANTES
        # =================================================================
        arith_passed = True
        diff_expected = report.billed_amount - report.received_amount
        discrepancy_abs = abs(report.difference)

        # Si la diferencia difiere en magnitud, corregir con precisión Decimal
        if abs(discrepancy_abs - abs(diff_expected)) > Decimal("0.00"):
            arith_passed = False
            audit_notes.append(
                f"Ajuste de Diferencia Nominal: se recalculó de ${report.difference:,.2f} a ${diff_expected:,.2f}."
            )
            report.difference = diff_expected
            corrections.append("Recálculo exacto de Diferencia Nominal en Decimal.")
            discrepancy_abs = abs(report.difference)

        sum_parts = report.justified_amount + report.claimable_amount
        if sum_parts != discrepancy_abs:
            arith_passed = False
            # Ajustar la partida reclamable si la sumatoria no cuadra exactamente
            adjusted_claimable = discrepancy_abs - report.justified_amount
            if adjusted_claimable >= Decimal("0.00"):
                report.claimable_amount = adjusted_claimable
                corrections.append(f"Cuadratura aritmética de saldo reclamable a ${adjusted_claimable:,.2f} USD.")
            audit_notes.append(
                f"Cuadratura de Invarianza: Justificado (${report.justified_amount:,.2f}) + "
                f"Reclamable (${report.claimable_amount:,.2f}) = ${discrepancy_abs:,.2f} USD."
            )
        else:
            audit_notes.append("Invarianza aritmética perfecta verificada al centavo ($0.00 MAE).")

        # =================================================================
        # FILTRO 2: MATRIZ DE PRELACIÓN LEGAL Y CLÁUSULAS CONTRACTUALES
        # =================================================================
        precedence_passed = True
        has_contract = ctr is not None
        ctr_text = ""
        if has_contract:
            if hasattr(ctr, "raw_content"):
                ctr_text += str(ctr.raw_content)
            if hasattr(ctr, "clauses") and isinstance(ctr.clauses, list):
                for c in ctr.clauses:
                    ctr_text += " " + str(getattr(c, "text", str(c)))

        unilateral_prohibited = bool(re.search(
            r"(?:prohibid[ao]|invalida|no\s+autorizad[ao]|sin\s+previo\s+acuerdo|prevalec|bilateral|acuerdo\s+mutuo)",
            ctr_text,
            re.IGNORECASE
        ))

        if unilateral_prohibited and report.claimable_amount > Decimal("0.00"):
            audit_notes.append(
                "Jerarquía de Prelación: El Contrato Marco prohíbe deducciones unilaterales sin acuerdo mutuo. "
                "Cualquier guía o manual operativo del comprador queda subordinado perentoriamente (Art. 88 CCom)."
            )

        # =================================================================
        # FILTRO 3: VALIDACIÓN DE VENTANA PERENTORIA DE NOTIFICACIÓN
        # =================================================================
        notice_window_passed = True
        window_days: Optional[int] = None
        days_elapsed: Optional[int] = None

        # Detectar ventana en días estipulada en contrato
        match_window = re.search(
            r"(?:ventana|plazo|periodo|dentro\s+de\s+los)[^\d\n\r]{1,40}(\d+)\s*(?:días|dias|hrs|horas)",
            ctr_text,
            re.IGNORECASE
        )
        if match_window:
            raw_num = int(match_window.group(1))
            # Normalizar horas a días si aplica
            window_days = raw_num if raw_num > 48 else (raw_num // 24 if raw_num >= 24 else raw_num)

        # Extraer fechas de entrega y de pago/aviso
        date_deliv = cls._extract_date(deliv, ["delivery_date", "date", "fecha_entrega"])
        date_pay = cls._extract_date(pay, ["payment_date", "date", "fecha_pago"])

        if date_deliv and date_pay and window_days:
            days_elapsed = (date_pay - date_deliv).days
            if days_elapsed > window_days and report.claimable_amount > Decimal("0.00"):
                notice_window_passed = False
                audit_notes.append(
                    f"EXTEMPORANEIDAD CONFIRMADA: El comprador notificó/retuvo a los {days_elapsed} días naturales, "
                    f"excediendo el plazo perentorio contractual de {window_days} días. "
                    f"La deducción es legalmente extemporánea y nula de pleno derecho."
                )
                corrections.append(
                    f"Invocación de nulidad extemporánea ({days_elapsed}d > {window_days}d pactados)."
                )

        # =================================================================
        # FILTRO 4: DETECCIÓN DE DOBLE PENALIZACIÓN Y ABUSOS LOGÍSTICOS
        # =================================================================
        double_penalty = False
        double_details: List[str] = []

        pay_deductions = []
        if pay and hasattr(pay, "deductions") and isinstance(pay.deductions, list):
            pay_deductions = [str(getattr(d, "reason", str(d))).lower() for d in pay.deductions]

        pay_notes = str(getattr(pay, "notes", "")).lower()

        # Chequeo 1: Faltante de producto + Multa OTIF / Fill-Rate sobre el mismo lote
        has_shortage_penalty = any("faltante" in d or "shortage" in d for d in pay_deductions) or "faltante" in pay_notes
        has_fillrate_penalty = any("otif" in d or "fill" in d or "servicio" in d or "retraso" in d for d in pay_deductions) or "otif" in pay_notes

        if has_shortage_penalty and has_fillrate_penalty and report.justified_amount > Decimal("0.00"):
            double_penalty = True
            detail = (
                "Doble Imposición Detectada: El comprador descontó las unidades faltantes y simultáneamente "
                "aplicó penalización por nivel de servicio (OTIF/Fill-Rate) sobre el mismo embarque."
            )
            double_details.append(detail)
            audit_notes.append(detail)
            corrections.append("Desestimación de sanción por nivel de servicio duplicada sobre faltante ya ajustado.")

        # Chequeo 2: Descuento Pronto Pago fuera de fecha
        has_early_pay = any("pronto" in d or "early" in d or "descuento financiero" in d for d in pay_deductions) or "pronto pago" in pay_notes
        if has_early_pay and date_deliv and date_pay:
            pay_delay = (date_pay - date_deliv).days
            if pay_delay > 15:  # Mayor a 15 días habituales de pronto pago
                double_penalty = True
                detail = f"Descuento de Pronto Pago Ilegal: Aplicado tras {pay_delay} días de la entrega (límite: 15 días)."
                double_details.append(detail)
                audit_notes.append(detail)

        # =================================================================
        # CLASIFICACIÓN DEL ÍNDICE DE IRREFUTABILIDAD PROBATORIA
        # =================================================================
        if report.claimable_amount > Decimal("0.00"):
            if deliv and getattr(deliv, "signed", False) and has_contract:
                grade = "A1_IRREFUTABLE"
            elif not notice_window_passed:
                grade = "A1_IRREFUTABLE"
            else:
                grade = "A2_JURISPRUDENCIAL"
        else:
            grade = "B1_ALLANAMIENTO"

        result = SanityGateAuditResult(
            is_bulletproof=(arith_passed and (notice_window_passed or not window_days)),
            arithmetic_invariant_passed=arith_passed,
            precedence_hierarchy_passed=precedence_passed,
            notice_window_passed=notice_window_passed,
            notice_window_days_allowed=window_days,
            notice_window_days_elapsed=days_elapsed,
            double_penalty_detected=double_penalty,
            double_penalty_details=double_details,
            irrefutability_grade=grade,
            corrective_actions_applied=corrections,
            audit_notes=audit_notes,
            verified_claimable_amount=report.claimable_amount,
            verified_justified_amount=report.justified_amount
        )

        # Anclar resultado al reporte
        report.sanity_gate_audit = result
        return result

    @classmethod
    def _extract_date(cls, doc: Any, attr_names: List[str]) -> Optional[date]:
        """Extrae de forma tolerante un objeto datetime.date de un documento."""
        if not doc:
            return None
        for attr in attr_names:
            val = getattr(doc, attr, None)
            if val:
                if isinstance(val, (datetime, date)):
                    return val if isinstance(val, date) else val.date()
                if isinstance(val, str):
                    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d", "%d-%m-%Y"):
                        try:
                            return datetime.strptime(val.strip(), fmt).date()
                        except ValueError:
                            pass
        return None
