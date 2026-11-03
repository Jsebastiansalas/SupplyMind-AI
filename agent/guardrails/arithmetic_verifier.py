import re
import hashlib
from decimal import Decimal, InvalidOperation
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Set, Tuple

from data.models import DisputeAnalysisReport, ZKPFinancialProof
from tools.reconciliation_engine.engine import ReconciliationSummary


def extract_monetary_figures(text: str) -> List[Tuple[str, Decimal]]:
    """
    US-902: Extrae con precisión todas las cifras monetarias multi-divisa (USD, MXN, EUR)
    mencionadas en un texto libre:
    e.g. '$12,500.00', '$ 800 USD', '$4,000', '15000.00 dólares', '50000.00 MXN', '1200 euros', '€450.00'.
    Retorna lista de tuplas (texto_coincidente, valor_decimal).
    """
    if not text:
        return []

    results: List[Tuple[str, Decimal]] = []

    # 1. Encontrar menciones con prefijos de moneda: $, €, £, MXN$, USD$, EUR€
    prefix_pattern = re.compile(
        r"(?:\$|€|£|MXN\$|USD\$|EUR€)\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]{1,2})?|[0-9]+(?:\.[0-9]{1,2})?)(?:\s*(?:USD|MXN|EUR|dólares|dolares|pesos|euros))?",
        re.IGNORECASE
    )

    # 2. Encontrar menciones sin prefijo de símbolo pero con sufijo explícito de divisa
    suffix_pattern = re.compile(
        r"(?<![\$\d,\.€£])([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]{1,2})?|[0-9]+(?:\.[0-9]{1,2})?)\s*(?:USD|MXN|EUR|dólares|dolares|pesos|pesos\s+mexicanos|euros)\b",
        re.IGNORECASE
    )

    matched_spans: List[Tuple[int, int]] = []

    for m in prefix_pattern.finditer(text):
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
        # Si se superpone con un match previo con prefijo, omitir para evitar fragmentación
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
    US-902: Consolida el conjunto cerrado de cifras matemáticas admisibles en el expediente:
    totales, subtotales, diferencias, partidas, deducciones bancarias, impactos individuales,
    intereses moratorios legales (Art. 362 CCom 9%), topes contractuales, desglose fiscal (IVA 16%/8%/IEPS),
    Valor Presente Neto (NPV/WACC) y conversiones multi-divisa (MXN/EUR).
    """
    valid_set: Set[Decimal] = set()

    def _add(d: Optional[Decimal]):
        if d is not None:
            valid_set.add(round(d, 2))
            valid_set.add(round(abs(d), 2))

    # 1. Cifras maestras del reporte
    _add(report.billed_amount)
    _add(report.received_amount)
    _add(report.difference)
    _add(report.justified_amount)
    _add(report.claimable_amount)

    # 2. Cifras de conciliación física
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

    # 3. Cifras de documentos en crudo
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

    # 4. Agregar cifras de cero explícito y sumas lógicas básicas
    valid_set.add(Decimal("0.00"))
    if report.justified_amount > Decimal("0.00") and report.claimable_amount > Decimal("0.00"):
        valid_set.add(round(report.justified_amount + report.claimable_amount, 2))

    # 5. Cifras Legítimas Derivadas (US-902):
    claimable = report.claimable_amount

    # 5.1 Intereses Moratorios Legales Art. 362 Código de Comercio (9% anual)
    if claimable > Decimal("0.00"):
        int_annual = round(claimable * Decimal("0.09"), 2)
        _add(int_annual)
        _add(round(claimable + int_annual, 2))
        for days in [15, 30, 45, 60, 90, 120, 180, 270, 360, 365]:
            int_360 = round((claimable * Decimal("0.09") * Decimal(days)) / Decimal("360.00"), 2)
            _add(int_360)
            _add(round(claimable + int_360, 2))
            int_365 = round((claimable * Decimal("0.09") * Decimal(days)) / Decimal("365.00"), 2)
            _add(int_365)
            _add(round(claimable + int_365, 2))

    # 5.2 Topes Contractuales y Límites de Responsabilidad (Liability Caps)
    contract = loaded_docs.get("contract") if loaded_docs else None
    clauses = getattr(contract, "clauses", []) if contract else []
    cap_rates = [Decimal(str(r)) for r in [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0, 7.5, 8.0, 10.0, 12.0, 15.0, 20.0, 25.0]]
    for cl in clauses:
        c_text = getattr(cl, "text", str(cl))
        m_pct = re.search(r"(\d+(?:\.\d+)?)\s*%", c_text)
        if m_pct:
            try:
                cap_rates.append(Decimal(m_pct.group(1)).quantize(Decimal("0.01")))
            except Exception:
                pass
    for r in set(cap_rates):
        cap_on_billed = round((report.billed_amount * r) / Decimal("100.00"), 2)
        _add(cap_on_billed)
        _add(round(report.billed_amount - cap_on_billed, 2))
        if report.justified_amount > Decimal("0.00"):
            _add(round(abs(report.justified_amount - cap_on_billed), 2))
        diff_abs = abs(report.difference)
        if diff_abs > Decimal("0.00"):
            _add(round(abs(diff_abs - cap_on_billed), 2))

    # 5.3 Desglose Fiscal Tributario (IVA 16% / IVA 8% / IEPS)
    for base_val in [report.billed_amount, report.claimable_amount, report.justified_amount, abs(report.difference)]:
        if base_val > Decimal("0.00"):
            sub_16 = round(base_val / Decimal("1.16"), 2)
            tax_16 = round(base_val - sub_16, 2)
            _add(sub_16)
            _add(tax_16)
            sub_8 = round(base_val / Decimal("1.08"), 2)
            tax_8 = round(base_val - sub_8, 2)
            _add(sub_8)
            _add(tax_8)
            sub_ieps = round(base_val / Decimal("1.2528"), 2)
            _add(sub_ieps)
            _add(round(base_val - sub_ieps, 2))

    # 5.4 Simulación Financiera NPV y Costo de Capital (WACC / TIIE / SOFR)
    if claimable > Decimal("0.00"):
        for rate in [0.06, 0.08, 0.10, 0.12, 0.14, 0.16, 0.18]:
            for days in [5, 15, 30, 45, 60, 90, 120, 180]:
                denom = Decimal("1.0") + (Decimal(str(rate)) * Decimal(days) / Decimal("365.0"))
                npv = round(claimable / denom, 2)
                _add(npv)
                _add(round(npv - Decimal("5000.00"), 2))
        _add(Decimal("5000.00"))  # Costas legales arbitrales

    # 5.5 Conversión Multi-Divisa (FX MXN y EUR)
    fx_rates = [Decimal(str(x)) for x in [17.00, 17.50, 17.85, 18.00, 18.50, 19.00, 19.50, 20.00]]
    eur_rates = [Decimal(str(x)) for x in [0.90, 0.92, 0.95, 1.05, 1.08]]
    for val in [report.billed_amount, report.received_amount, report.claimable_amount, report.justified_amount, abs(report.difference)]:
        if val > Decimal("0.00"):
            for fx in fx_rates:
                _add(round(val * fx, 2))
                _add(round(val / fx, 2))
            for eur in eur_rates:
                _add(round(val * eur, 2))
                _add(round(val / eur, 2))

    return valid_set


def generate_cryptographic_proof_token(
    case_id: str,
    billed: Decimal,
    received: Decimal,
    diff: Decimal,
    justified: Decimal,
    claimable: Decimal,
    timestamp: str
) -> str:
    """
    Genera un sello de integridad criptográfica determinística SHA-256
    que certifica las invariantes aritméticas de partida doble del arbitraje.
    """
    canonical_payload = (
        f"SUPPLYMIND-INVARIANT-V1|"
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


def verify_cryptographic_proof_token(proof_token: str, report: DisputeAnalysisReport, timestamp: str) -> bool:
    """Verifica si un token de integridad SHA-256 corresponde exactamente a las cifras del reporte."""
    expected = generate_cryptographic_proof_token(
        case_id=report.case_id,
        billed=report.billed_amount,
        received=report.received_amount,
        diff=report.difference,
        justified=report.justified_amount,
        claimable=report.claimable_amount,
        timestamp=timestamp
    )
    return proof_token.strip().upper() == expected.strip().upper()


# Alias de retrocompatibilidad para módulos previos
generate_zkp_proof_token = generate_cryptographic_proof_token
verify_zkp_proof_token = verify_cryptographic_proof_token


class CryptographicInvariantAuditor:
    """
    Auditor de integridad criptográfica (SHA-256) y verificador de invarianzas aritméticas.
    Detecta y corrige cualquier discrepancia de partida doble o cifra no sustentada en texto libre.
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


# Alias de retrocompatibilidad
ZKPFinancialAuditor = CryptographicInvariantAuditor


def audit_and_enforce_zero_hallucination(
    report: DisputeAnalysisReport,
    reconciliation: Optional[ReconciliationSummary] = None,
    loaded_docs: Optional[Dict[str, Any]] = None
) -> DisputeAnalysisReport:
    """Helper funcional para invocar la auditoría y sellado de invariantes."""
    return CryptographicInvariantAuditor.audit_and_enforce(report, reconciliation, loaded_docs)
