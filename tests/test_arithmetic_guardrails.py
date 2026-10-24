import pytest
from decimal import Decimal
from datetime import datetime, timezone

from data.models import DisputeAnalysisReport, ZKPFinancialProof
from agent.guardrails.arithmetic_verifier import (
    extract_monetary_figures,
    generate_zkp_proof_token,
    verify_zkp_proof_token,
    ZKPFinancialAuditor,
    audit_and_enforce_zero_hallucination
)
from agent.core.skynet_runner import SkynetRunner


def test_extract_monetary_figures():
    """Valida la extracción exacta de montos monetarios en diversas notaciones de lenguaje natural."""
    sample_text = (
        "El faltante físico de $800.00 USD en PROD-002 está justificado, "
        "mientras que la penalización de $12,500.50 y el cargo de 3000 dólares "
        "fueron aplicados de manera unilateral sin sustento."
    )
    extracted = extract_monetary_figures(sample_text)
    assert len(extracted) == 3
    vals = [val for _, val in extracted]
    assert Decimal("800.00") in vals
    assert Decimal("12500.50") in vals
    assert Decimal("3000.00") in vals


def test_arithmetic_invariant_conservation_ok():
    """Valida que un reporte con matemáticas exactas obtenga la prueba ZKP MATHEMATICALLY_PROVEN."""
    report = DisputeAnalysisReport(
        case_id="case_001",
        currency="USD",
        billed_amount=Decimal("9000.00"),
        received_amount=Decimal("8200.00"),
        difference=Decimal("-800.00"),
        root_cause="Faltante de 10 cajas de Producto B por valor de $800.00 USD.",
        evidence=["Remisión DEL-9912 con sello de faltante"],
        justified_amount=Decimal("800.00"),
        claimable_amount=Decimal("0.00"),
        confidence=0.98,
        recommended_action="Emitir Nota de Crédito comercial por $800.00 USD."
    )
    proof = ZKPFinancialAuditor.audit_report(report)

    assert proof.proof_hash.startswith("SM-PROOF-SHA256-")
    assert proof.invariant_conservation_ok is True
    assert proof.invariant_deductions_ok is True
    assert proof.text_hallucination_detected is False
    assert proof.audit_status == "MATHEMATICALLY_PROVEN"
    assert proof.confidence_penalty == 0.0


def test_arithmetic_invariant_mismatch_detected():
    """Valida que si hay un desbalance aritmético (e.g. justificado + reclamable != retención), se detecte de inmediato."""
    broken_report = DisputeAnalysisReport(
        case_id="case_broken",
        currency="USD",
        billed_amount=Decimal("10000.00"),
        received_amount=Decimal("8000.00"),
        difference=Decimal("-2000.00"),  # Retención real: $2,000
        root_cause="Discrepancia comercial en entrega.",
        evidence=[],
        justified_amount=Decimal("1500.00"),
        claimable_amount=Decimal("1000.00"),  # 1500 + 1000 = 2500 != 2000 (INVARIANTE ROTA)
        confidence=0.95,
        recommended_action="Revisar."
    )
    proof = ZKPFinancialAuditor.audit_report(broken_report)

    assert proof.invariant_deductions_ok is False
    assert proof.audit_status == "ARITHMETIC_MISMATCH"
    assert proof.confidence_penalty > 0.0

    # Al aplicar la auditoría en el reporte, la confianza se penaliza automáticamente
    audited_report = ZKPFinancialAuditor.audit_and_enforce(broken_report)
    assert audited_report.confidence < 0.95


def test_text_hallucination_detection():
    """Valida que si el LLM inventa en su explicación cifras inexistentes en los hechos, se intercepte la alucinación."""
    hallucinating_report = DisputeAnalysisReport(
        case_id="case_001",
        currency="USD",
        billed_amount=Decimal("9000.00"),
        received_amount=Decimal("8200.00"),
        difference=Decimal("-800.00"),
        root_cause="Faltante de $800.00 USD, pero el comprador exige una indemnización de $9,999.00 USD.", # $9,999 inventado
        evidence=[],
        justified_amount=Decimal("800.00"),
        claimable_amount=Decimal("0.00"),
        confidence=0.98,
        recommended_action="Exigir reembolso de $9,999.00 USD."
    )
    proof = ZKPFinancialAuditor.audit_report(hallucinating_report)

    assert proof.text_hallucination_detected is True
    assert proof.audit_status == "HALLUCINATION_INTERCEPTED"
    assert any("9999" in fig for fig in proof.detected_hallucinated_figures)
    assert proof.confidence_penalty > 0.0


def test_llm_conversational_reply_sanitization():
    """Valida la intercepción y anotación preventiva de cifras alucinadas durante el chat interactivo."""
    report = DisputeAnalysisReport(
        case_id="case_002",
        currency="USD",
        billed_amount=Decimal("54200.00"),
        received_amount=Decimal("37700.00"),
        difference=Decimal("-16500.00"),
        root_cause="Discrepancia mixta: faltante de $4,000.00 USD y retención no autorizada de $12,500.00 USD.",
        evidence=[],
        justified_amount=Decimal("4000.00"),
        claimable_amount=Decimal("12500.00"),
        confidence=0.98,
        recommended_action="Cobrar $12,500.00 USD."
    )
    # LLM inventa que se deben cobrar $50,000
    hallucinated_text = "En este caso podemos recuperar $50,000.00 USD inmediatamente con cobranza coactiva."
    has_hallucination, flagged, sanitized = ZKPFinancialAuditor.audit_llm_conversational_reply(hallucinated_text, report)

    assert has_hallucination is True
    assert len(flagged) == 1
    assert "50,000.00" in flagged[0]
    assert "Cifra no verificada" in sanitized
    assert "12,500.00" in sanitized


def test_zkp_proof_token_tamper_resistance():
    """Valida que cualquier alteración en las cifras invalida la verificación criptográfica del token."""
    ts = datetime.now(timezone.utc).isoformat()
    token = generate_zkp_proof_token(
        case_id="case_001",
        billed=Decimal("9000.00"),
        received=Decimal("8200.00"),
        diff=Decimal("-800.00"),
        justified=Decimal("800.00"),
        claimable=Decimal("0.00"),
        timestamp=ts
    )
    report = DisputeAnalysisReport(
        case_id="case_001",
        currency="USD",
        billed_amount=Decimal("9000.00"),
        received_amount=Decimal("8200.00"),
        difference=Decimal("-800.00"),
        root_cause="Faltante de $800.00 USD",
        evidence=[],
        justified_amount=Decimal("800.00"),
        claimable_amount=Decimal("0.00"),
        confidence=0.98,
        recommended_action="Emitir NC"
    )
    # Verificación válida
    assert verify_zkp_proof_token(token, report, ts) is True

    # Intento de manipulación: alterar billed_amount
    report_tampered = report.model_copy(update={"billed_amount": Decimal("9001.00")})
    assert verify_zkp_proof_token(token, report_tampered, ts) is False


def test_skynet_runner_integration_with_zkp_proof():
    """Valida que la ejecución autónoma de SKYNET genera reportes sellados con prueba ZKP sin alucinaciones."""
    runner = SkynetRunner("case_001", fast_path=True, use_cache=False)
    report = runner.run()

    assert report is not None
    assert report.financial_proof is not None
    proof = report.financial_proof
    proof_hash = getattr(proof, "proof_hash", None) or proof.get("proof_hash")
    status = getattr(proof, "audit_status", None) or proof.get("audit_status")
    hallucination = getattr(proof, "text_hallucination_detected", None) if hasattr(proof, "text_hallucination_detected") else proof.get("text_hallucination_detected")

    assert proof_hash.startswith("SM-PROOF-SHA256-")
    assert status == "MATHEMATICALLY_PROVEN"
    assert hallucination is False

    # Caso complejo 002 con deducciones mixtas
    runner2 = SkynetRunner("case_002", fast_path=True, use_cache=False)
    report2 = runner2.run()
    assert report2 is not None
    assert report2.financial_proof is not None
    proof2 = report2.financial_proof
    status2 = getattr(proof2, "audit_status", None) or proof2.get("audit_status")
    assert status2 == "MATHEMATICALLY_PROVEN"
