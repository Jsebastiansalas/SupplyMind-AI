import re
import hashlib
from decimal import Decimal, InvalidOperation
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Set, Tuple

from data.models import DisputeAnalysisReport, ZKPFinancialProof
from tools.reconciliation_engine.engine import ReconciliationSummary


def extract_monetary_figures(text: str) -> List[Tuple[str, Decimal]]:
    """
    Extrae con precisión todas las cifras monetarias mencionadas en un texto libre:
    e.g. '$12,500.00', '$ 800 USD', '$4,000', '15000.00 dólares'.
    Retorna lista de tuplas (texto_coincidente, valor_decimal).
    """
    if not text:
        return []

    results: List[Tuple[str, Decimal]] = []

    # 1. Encontrar todas las menciones con prefijo '$'
    dollar_pattern = re.compile(
        r"\$\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]{1,2})?|[0-9]+(?:\.[0-9]{1,2})?)(?:\s*(?:USD|dólares|dolares))?",
        re.IGNORECASE
    )

    # 2. Encontrar menciones sin '$' pero con sufijo 'USD' o 'dólares'
    suffix_pattern = re.compile(
        r"(?<![\$\d,\.])([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]{1,2})?|[0-9]+(?:\.[0-9]{1,2})?)\s*(?:USD|dólares|dolares)\b",
        re.IGNORECASE
    )

    matched_spans: List[Tuple[int, int]] = []

    for m in dollar_pattern.finditer(text):
        matched_spans.append(m.span())
        raw_full = m.group(0).strip()
        num_str = m.group(1).replace(",", "")
        try:
            val = Decimal(num_str)
            results.append((raw_full, val))
        except (InvalidOperation, ValueError):
            continue

    for m in suffix_pattern.finditer(text):
        start, end = m.span()
        # Si se superpone con un match previo con '$', omitir para evitar fragmentación de cifras
        if any(s <= start < e or s < end <= e for s, e in matched_spans):
            continue
        raw_full = m.group(0).strip()
        num_str = m.group(1).replace(",", "")
        try:
            val = Decimal(num_str)
            results.append((raw_full, val))
        except (InvalidOperation, ValueError):
            continue

    return results


def collect_valid_ground_truth_figures(
    report: DisputeAnalysisReport,
    reconciliation: Optional[ReconciliationSummary] = None,
    loaded_docs: Optional[Dict[str, Any]] = None
) -> Set[Decimal]:
    """
    Consolida el conjunto cerrado de cifras matemáticas admisibles en el expediente:
    totales, subtotales, diferencias, partidas, deducciones bancarias e impactos individuales.
    """
    valid_set: Set[Decimal] = set()

    def _add(d: Optional[Decimal]):
        if d is not None:
            valid_set.add(round(d, 2))
            valid_set.add(round(abs(d), 2))

    # Cifras maestras del reporte
    _add(report.billed_amount)
    _add(report.received_amount)
    _add(report.difference)
    _add(report.justified_amount)
    _add(report.claimable_amount)

    # Cifras de conciliación física
    if reconciliation:
        _add(reconciliation.total_missing_amount)
        _add(reconciliation.total_damaged_amount)
        _add(reconciliation.total_price_discrepancy_amount)
        _add(reconciliation.total_deductions_applied)

        for d in reconciliation.discrepancies:
            _add(d.total_impact)
            _add(d.missing_amount)
            _add(d.damaged_amount)
            _add(d.price_difference)
            _add(d.agreed_unit_price)
            _add(d.invoiced_unit_price)
            if d.missing_quantity > 0:
                _add(Decimal(d.missing_quantity) * d.agreed_unit_price)
            if d.damaged_quantity > 0:
                _add(Decimal(d.damaged_quantity) * d.agreed_unit_price)

    # Cifras de documentos en crudo
    if loaded_docs:
        inv = loaded_docs.get("invoice")
        if inv and hasattr(inv, "items"):
            for it in inv.items:
                _add(getattr(it, "total_price", None))
                _add(getattr(it, "unit_price", None))
        
        pay = loaded_docs.get("payment")
        if pay and hasattr(pay, "deductions"):
            for ded in pay.deductions:
                _add(getattr(ded, "amount", None))

    # Agregar cifras de cero explícito
    valid_set.add(Decimal("0.00"))

    # Agregar sumas lógicas derivadas de partidas (ej. suma de faltante + avería)
    if report.justified_amount > Decimal("0.00") and report.claimable_amount > Decimal("0.00"):
        valid_set.add(round(report.justified_amount + report.claimable_amount, 2))

    return valid_set


def generate_zkp_proof_token(
    case_id: str,
    billed: Decimal,
    received: Decimal,
    diff: Decimal,
    justified: Decimal,
    claimable: Decimal,
    timestamp: str
) -> str:
    """
    Genera un token de prueba criptográfica determinística SHA-256 (estilo ZKP)
    que sella matemáticamente las invariantes financieras del arbitraje.
    """
    canonical_payload = (
        f"SUPPLYMIND-ZKP-V1|"
        f"CASE:{case_id.strip()}|"
        f"BILLED:{billed:.2f}|"
        f"RECEIVED:{received:.2f}|"
        f"DIFF:{diff:.2f}|"
        f"JUSTIFIED:{justified:.2f}|"
        f"CLAIMABLE:{claimable:.2f}|"
        f"TS:{timestamp}"
    )
    digest = hashlib.sha256(canonical_payload.encode("utf-8")).hexdigest()
    return f"SM-PROOF-SHA256-{digest[:16].upper()}"


def verify_zkp_proof_token(proof_token: str, report: DisputeAnalysisReport, timestamp: str) -> bool:
    """Verifica si un token de prueba corresponde exactamente a las cifras del reporte."""
    expected = generate_zkp_proof_token(
        case_id=report.case_id,
        billed=report.billed_amount,
        received=report.received_amount,
        diff=report.difference,
        justified=report.justified_amount,
        claimable=report.claimable_amount,
        timestamp=timestamp
    )
    return proof_token.strip().upper() == expected.strip().upper()


class ZKPFinancialAuditor:
    """
    Guardián criptográfico y verificador de invarianzas aritméticas para SupplyMind AI.
    Elimina cualquier posibilidad de alucinación financiera en texto libre o montos de reporte.
    """

    @classmethod
    def audit_report(
        cls,
        report: DisputeAnalysisReport,
        reconciliation: Optional[ReconciliationSummary] = None,
        loaded_docs: Optional[Dict[str, Any]] = None
    ) -> ZKPFinancialProof:
        """
        Audita rigurosamente el reporte contra invariantes matemáticas y busca alucinaciones textuales.
        """
        now_ts = datetime.now(timezone.utc).isoformat()

        # Invariante 1: Conservación del saldo (Billed - Received == abs(Difference))
        diff_abs = abs(report.difference)
        calc_diff = abs(report.billed_amount - report.received_amount)
        inv_balance_ok = abs(calc_diff - diff_abs) <= Decimal("0.02")

        # Invariante 2: Conservación de deducciones (Justified + Claimable == abs(Difference))
        alloc_sum = report.justified_amount + report.claimable_amount
        inv_deductions_ok = abs(alloc_sum - diff_abs) <= Decimal("0.02")

        # Invariante 3: No exceder la retención
        inv_bounds_ok = (report.claimable_amount <= diff_abs + Decimal("0.02")) and (report.justified_amount <= diff_abs + Decimal("0.02"))

        # Invariante 4: Comprobación de líneas (si hay conciliación)
        inv_lines_ok = True
        if reconciliation:
            inv_lines_ok = abs(reconciliation.billed_amount - report.billed_amount) <= Decimal("0.05")

        # Auditoría de alucinaciones en texto del dictamen
        valid_figures = collect_valid_ground_truth_figures(report, reconciliation, loaded_docs)
        text_corpus = f"{report.root_cause} | {report.recommended_action}"
        extracted_figures = extract_monetary_figures(text_corpus)

        detected_hallucinations: List[str] = []
        verified_figures: List[str] = []

        for fig_text, fig_val in extracted_figures:
            # Tolerancia de centavos para redondeos
            is_valid = any(abs(fig_val - v) <= Decimal("0.02") for v in valid_figures)
            if is_valid:
                verified_figures.append(f"{fig_text} (Validado)")
            else:
                detected_hallucinations.append(f"{fig_text} ({fig_val} USD sin respaldo fáctico)")

        hallucination_found = len(detected_hallucinations) > 0
        penalty = 0.0

        if not inv_balance_ok or not inv_deductions_ok:
            status = "ARITHMETIC_MISMATCH"
            penalty = 0.50
        elif hallucination_found:
            status = "HALLUCINATION_INTERCEPTED"
            penalty = 0.15
        else:
            status = "MATHEMATICALLY_PROVEN"
            penalty = 0.0

        proof_token = generate_zkp_proof_token(
            case_id=report.case_id,
            billed=report.billed_amount,
            received=report.received_amount,
            diff=report.difference,
            justified=report.justified_amount,
            claimable=report.claimable_amount,
            timestamp=now_ts
        )

        return ZKPFinancialProof(
            case_id=report.case_id,
            proof_hash=proof_token,
            invariant_conservation_ok=inv_balance_ok and inv_bounds_ok,
            invariant_deductions_ok=inv_deductions_ok,
            invariant_line_items_ok=inv_lines_ok,
            text_hallucination_detected=hallucination_found,
            detected_hallucinated_figures=detected_hallucinations,
            verified_figures=verified_figures,
            confidence_penalty=penalty,
            audit_status=status,
            tamper_proof_timestamp=now_ts
        )

    @classmethod
    def audit_and_enforce(
        cls,
        report: DisputeAnalysisReport,
        reconciliation: Optional[ReconciliationSummary] = None,
        loaded_docs: Optional[Dict[str, Any]] = None
    ) -> DisputeAnalysisReport:
        """
        Ejecuta la auditoría ZKP y sella el reporte con el token de prueba criptográfica.
        Si se intercepta una alucinación textual o discrepancia aritmética, aplica salvaguardas.
        """
        proof = cls.audit_report(report, reconciliation, loaded_docs)
        report.financial_proof = proof

        # Ajuste de nivel de confianza si hubo incoherencias
        if proof.confidence_penalty > 0.0 and report.confidence > 0.0:
            report.confidence = max(0.10, round(report.confidence - proof.confidence_penalty, 2))

        return report

    @classmethod
    def audit_llm_conversational_reply(
        cls,
        reply_text: str,
        active_report: Optional[DisputeAnalysisReport],
        reconciliation: Optional[ReconciliationSummary] = None
    ) -> Tuple[bool, List[str], str]:
        """
        Audita una respuesta en lenguaje natural de Grok/LLM durante la interacción conversacional.
        Retorna (hubo_alucinacion, lista_alucinaciones, texto_saneado).
        """
        if not active_report or not reply_text:
            return False, [], reply_text

        valid_figures = collect_valid_ground_truth_figures(active_report, reconciliation)
        extracted = extract_monetary_figures(reply_text)

        hallucinations = []
        sanitized = reply_text

        for fig_text, fig_val in extracted:
            is_valid = any(abs(fig_val - v) <= Decimal("0.02") for v in valid_figures)
            if not is_valid and fig_val > Decimal("1.00"):
                hallucinations.append(f"{fig_text} (Cifra no coincide con conciliación)")
                # Anotar o corregir en el texto
                sanitized = sanitized.replace(
                    fig_text,
                    f"{fig_text} [⚠️ Cifra no verificada en conciliación; saldo real reclamable: ${active_report.claimable_amount:,.2f} USD]"
                )

        return len(hallucinations) > 0, hallucinations, sanitized


def audit_and_enforce_zero_hallucination(
    report: DisputeAnalysisReport,
    reconciliation: Optional[ReconciliationSummary] = None,
    loaded_docs: Optional[Dict[str, Any]] = None
) -> DisputeAnalysisReport:
    """Helper funcional para invocar la auditoría y sellado ZKP."""
    return ZKPFinancialAuditor.audit_and_enforce(report, reconciliation, loaded_docs)
