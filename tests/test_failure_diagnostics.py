"""
tests/test_failure_diagnostics.py
Pruebas unitarias para el subsistema de diagnóstico transparente de fallos y límites operacionales (Hito S3).

Verifica que el agente:
1. Reconozca abiertamente errores y anomalías en lugar de ocultarlos ("reconocerlo suma, esconderlo resta").
2. Degrade la confianza a 0.00% y exija intervención humana en expedientes en cuarentena o contaminados.
3. Clasifique con precisión los modos de fallo (inyección de prompt, contaminación entre entidades, etc.).
4. Reporte honestamente la caída o fallback de gateway LLM.
5. Calcule la distinción cuantitativa entre cálculo simbólico en Python vs inferencia neuronal en Grok.
"""

from decimal import Decimal
import pytest
from data.models import DisputeAnalysisReport, DocumentHealthAudit
from agent.guardrails.failure_diagnostics import (
    FailureDiagnosticsManager,
    FailureMode,
    FailureDiagnosticRecord
)


def test_failure_diagnostics_normal_clean_resolution():
    """Un expediente limpio y conciliado debe reportar resolución normal y autonomía plena."""
    report = DisputeAnalysisReport(
        case_id="case_clean_001",
        billed_amount=Decimal("15000.00"),
        received_amount=Decimal("12000.00"),
        difference=Decimal("3000.00"),
        claimable_amount=Decimal("3000.00"),
        justified_amount=Decimal("0.00"),
        root_cause="UNAUTHORIZED_DISCOUNT",
        evidence=["Factura FAC-001 vs Pago TX-001"],
        recommended_action="REJECT_AND_CLAIM",
        confidence=0.98
    )

    enriched = FailureDiagnosticsManager.evaluate_and_attach(report)
    assert enriched.failure_diagnostics is not None
    diag = enriched.failure_diagnostics
    assert diag["is_fully_autonomous"] is True
    assert diag["requires_human_in_the_loop"] is False
    assert diag["failure_severity"] == "NORMAL_RESOLUTION"
    assert enriched.confidence == 0.98


def test_failure_diagnostics_mixed_caution_margin():
    """Un caso con faltante real y cobro indebido debe marcar CAUTION_MARGIN."""
    report = DisputeAnalysisReport(
        case_id="case_mixed_002",
        billed_amount=Decimal("20000.00"),
        received_amount=Decimal("15000.00"),
        difference=Decimal("5000.00"),
        claimable_amount=Decimal("3500.00"),
        justified_amount=Decimal("1500.00"),
        root_cause="MIXED_SHORTAGE_AND_FEE",
        evidence=["Remisión REM-001", "Factura FAC-002"],
        recommended_action="PARTIAL_ACCEPTANCE",
        confidence=0.92
    )

    enriched = FailureDiagnosticsManager.evaluate_and_attach(report)
    diag = enriched.failure_diagnostics
    assert diag["is_fully_autonomous"] is True
    assert diag["failure_severity"] == "CAUTION_MARGIN"


def test_failure_diagnostics_quarantine_prompt_injection():
    """Un caso con inyección de prompt debe degradar confianza a 0.00% y exigir escalación humana."""
    audit = DocumentHealthAudit(
        case_id="case_031_adversarial",
        health_score=0.0,
        status="QUARANTINE",
        is_healthy=False,
        repaired_issues=[],
        imputed_documents=[],
        documents_present=[],
        documents_missing=[],
        schema_warnings=["Ataque prompt injection detectado"],
        execution_safety_level="HOLD_SETTLEMENT_DOCUMENT_AUDIT_REQUIRED",
        generated_at="2026-11-04T00:00:00Z"
    )

    class MockDocket:
        blocking_reasons = ["Intento de inyección de prompt adversarial detectado en remisión"]
        violated_invariants = ["PROMPT_INJECTION_SHIELD"]
        severity = "CRITICAL_ADVERSARIAL_ATTACK"

    report = DisputeAnalysisReport(
        case_id="case_031_adversarial",
        billed_amount=Decimal("0.00"),
        received_amount=Decimal("0.00"),
        difference=Decimal("0.00"),
        claimable_amount=Decimal("0.00"),
        justified_amount=Decimal("0.00"),
        root_cause="FORENSIC_QUARANTINE: CRITICAL_ADVERSARIAL_ATTACK",
        evidence=["Alerta de inyección"],
        recommended_action="🚨 PROTOCOLO FORENSE ACTIVADO: Expediente en CUARENTENA PREVENTIVA.",
        confidence=0.95,
        health_audit=audit,
        quarantine_docket=MockDocket()
    )

    enriched = FailureDiagnosticsManager.evaluate_and_attach(report)
    assert enriched.confidence == 0.00  # Confianza degradada honestamente a cero
    diag = enriched.failure_diagnostics
    assert diag["is_fully_autonomous"] is False
    assert diag["requires_human_in_the_loop"] is True
    assert diag["failure_severity"] == "CRITICAL_BLOCKED"
    assert FailureMode.ADVERSARIAL_ATTACK_DETECTED.value in diag["detected_failure_modes"]
    assert "LÍMITE OPERACIONAL RECONOCIDO" in enriched.resolution_notes[-1]


def test_failure_diagnostics_quarantine_cross_contamination():
    """Un caso con contaminación de datos entre empresas debe clasificar CROSS_ENTITY_CONTAMINATION."""
    class MockDocket:
        blocking_reasons = ["Contaminacion cruzada de cliente detectada: RFC no coincide con comprador"]
        violated_invariants = ["CLIENT_ENTITY_INTEGRITY"]
        severity = "CRITICAL_CROSS_CONTAMINATION"

    report = DisputeAnalysisReport(
        case_id="case_032_cross_contamination",
        billed_amount=Decimal("0.00"),
        received_amount=Decimal("0.00"),
        difference=Decimal("0.00"),
        claimable_amount=Decimal("0.00"),
        justified_amount=Decimal("0.00"),
        root_cause="FORENSIC_QUARANTINE: CROSS_CONTAMINATION",
        evidence=["Factura de otra entidad"],
        recommended_action="🚨 PROTOCOLO FORENSE ACTIVADO: Expediente en CUARENTENA PREVENTIVA.",
        confidence=0.90,
        quarantine_docket=MockDocket()
    )

    enriched = FailureDiagnosticsManager.evaluate_and_attach(report)
    assert enriched.confidence == 0.00
    diag = enriched.failure_diagnostics
    assert diag["is_fully_autonomous"] is False
    assert FailureMode.CROSS_ENTITY_CONTAMINATION.value in diag["detected_failure_modes"]


def test_failure_diagnostics_circuit_breaker_budget():
    """Si el watchdog corta la ejecución por superar el presupuesto, se reporta LLM_INFERENCE_BUDGET_CAP_REACHED."""
    class MockWatchdog:
        circuit_breaker_triggered = True

    class MockState:
        watchdog_metrics = MockWatchdog()

    report = DisputeAnalysisReport(
        case_id="case_budget_cap",
        billed_amount=Decimal("5000.00"),
        received_amount=Decimal("5000.00"),
        difference=Decimal("0.00"),
        claimable_amount=Decimal("0.00"),
        justified_amount=Decimal("0.00"),
        root_cause="BUDGET_EXHAUSTED",
        evidence=[],
        recommended_action="ACCEPT_AND_CREDIT",
        confidence=0.70
    )

    enriched = FailureDiagnosticsManager.evaluate_and_attach(report, state=MockState())
    diag = enriched.failure_diagnostics
    assert FailureMode.LLM_INFERENCE_BUDGET_CAP_REACHED.value in diag["detected_failure_modes"]
