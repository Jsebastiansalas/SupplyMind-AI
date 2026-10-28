"""
tests/test_sanity_gate_and_anti_blindspots.py
Suite de pruebas periciales para el Sprint 4.1:
- Sanity Gate de Cuádruple Auditoría Cruzada (Quad-Check Consensus).
- Verificación Aritmética Invariable ($0.00 MAE).
- Matriz de Prelación Legal & Art. 88 Código de Comercio.
- Detección de Ventana Perentoria Extemporánea.
- Detección de Doble Penalización Abusiva (Faltante + OTIF).
- Calificación del Índice de Irrefutabilidad Probatoria (A1, A2, B1).
"""

from decimal import Decimal
from datetime import date
import pytest

from agent.guardrails.sanity_gate import SanityGateEngine, SanityGateAuditResult
from agent.core.skynet_runner import SkynetRunner
from data.models import DisputeAnalysisReport
from tools.report_exporter.exporter import generate_markdown_report


class MockDoc:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def test_arithmetic_invariant_enforcement():
    """Valida que el Sanity Gate fuerce la cuadratura exacta de la invariante B - R = D = J + C."""
    # Reporte con discrepancia intencional (Justificado $2,000 + Reclamable $7,000 != $10,000 diferencia)
    faulty_report = DisputeAnalysisReport(
        case_id="case_test_arithmetic_gate",
        billed_amount=Decimal("50000.00"),
        received_amount=Decimal("40000.00"),
        difference=Decimal("10000.00"),
        root_cause="DEDUCCION_DESAJUSTADA",
        evidence=["Factura SAT"],
        justified_amount=Decimal("2000.00"),
        claimable_amount=Decimal("7000.00"),  # Faltan $1,000 para cuadrar los $10,000
        confidence=0.90,
        recommended_action="Reclamar saldo."
    )

    result: SanityGateAuditResult = SanityGateEngine.audit_and_reinforce_case(faulty_report, docs={})

    assert isinstance(result, SanityGateAuditResult)
    # Debe haber corregido claimable a $8,000.00 para cuadrar exactamente $10,000
    assert faulty_report.claimable_amount == Decimal("8000.00")
    assert faulty_report.justified_amount + faulty_report.claimable_amount == abs(faulty_report.difference)
    assert any("Cuadratura de Invarianza" in note for note in result.audit_notes)


def test_notice_window_peremptory_expiration():
    """Valida la detección de deducciones extemporáneas notificadas fuera de la ventana pactada."""
    report = DisputeAnalysisReport(
        case_id="case_test_extemporaneous",
        billed_amount=Decimal("20000.00"),
        received_amount=Decimal("15000.00"),
        difference=Decimal("5000.00"),
        root_cause="DEDUCCION_TARDIA",
        evidence=["Contrato 2026"],
        justified_amount=Decimal("0.00"),
        claimable_amount=Decimal("5000.00"),
        confidence=0.95,
        recommended_action="Exigir reintegro por extemporaneidad."
    )

    contract = MockDoc(
        raw_content="El comprador dispone de una ventana perentoria de 15 días hábiles para notificar cualquier objeción comercial.",
        clauses=["Cláusula 8.1: Plazo perentorio de 15 días para notificar."]
    )
    delivery = MockDoc(delivery_date="2026-08-01", signed=True)
    payment = MockDoc(payment_date="2026-08-28")  # 27 días transcurridos (> 15 días)

    result = SanityGateEngine.audit_and_reinforce_case(
        report=report,
        docs={"contract": contract, "delivery": delivery, "payment": payment}
    )

    assert result.notice_window_passed is False
    assert result.notice_window_days_allowed == 15
    assert result.notice_window_days_elapsed == 27
    assert any("EXTEMPORANEIDAD CONFIRMADA" in note for note in result.audit_notes)
    assert result.irrefutability_grade == "A1_IRREFUTABLE"


def test_double_penalty_detection_shortage_and_otif():
    """Valida la detección de doble penalización ilegal (Faltante físico + Penalización OTIF sobre el mismo lote)."""
    report = DisputeAnalysisReport(
        case_id="case_test_double_penalty",
        billed_amount=Decimal("30000.00"),
        received_amount=Decimal("25000.00"),
        difference=Decimal("5000.00"),
        root_cause="DOBLE_PENALIZACION",
        evidence=["Remisión muelle"],
        justified_amount=Decimal("2000.00"),  # Faltante físico de $2,000
        claimable_amount=Decimal("3000.00"),  # Multa OTIF duplicada de $3,000
        confidence=0.92,
        recommended_action="Desestimar multa OTIF duplicada."
    )

    payment = MockDoc(
        deductions=[
            MockDoc(reason="Deducción por Faltante de producto en muelle", amount=Decimal("2000.00")),
            MockDoc(reason="Penalización OTIF Fill-Rate por entrega incompleta", amount=Decimal("3000.00"))
        ],
        notes="Retención aplicada por faltante físico y sanción OTIF."
    )

    result = SanityGateEngine.audit_and_reinforce_case(
        report=report,
        docs={"payment": payment}
    )

    assert result.double_penalty_detected is True
    assert len(result.double_penalty_details) >= 1
    assert any("Doble Imposición Detectada" in d for d in result.double_penalty_details)


def test_legal_precedence_hierarchy_enforcement():
    """Valida que la prohibición de deducciones unilaterales invoque el Art. 88 Código de Comercio."""
    report = DisputeAnalysisReport(
        case_id="case_test_precedence",
        billed_amount=Decimal("40000.00"),
        received_amount=Decimal("35000.00"),
        difference=Decimal("5000.00"),
        root_cause="MULTA_UNILATERAL",
        evidence=["Contrato Bilateral"],
        justified_amount=Decimal("0.00"),
        claimable_amount=Decimal("5000.00"),
        confidence=0.94,
        recommended_action="Reclamar nulidad de cargo unilateral."
    )

    contract = MockDoc(
        raw_content="Quedan expresamente prohibidas las penalidades o deducciones unilaterales sin previo acuerdo mutuo y por escrito.",
        clauses=[]
    )

    result = SanityGateEngine.audit_and_reinforce_case(
        report=report,
        docs={"contract": contract}
    )

    assert result.precedence_hierarchy_passed is True
    assert any("Jerarquía de Prelación" in note for note in result.audit_notes)


def test_irrefutability_index_classification():
    """Valida la clasificación de solidez jurídica de los fondos auditados."""
    # 1. Caso con POD firmado y contrato -> A1_IRREFUTABLE
    rep_a1 = DisputeAnalysisReport(
        case_id="rep_a1",
        billed_amount=Decimal("10000.00"),
        received_amount=Decimal("5000.00"),
        difference=Decimal("5000.00"),
        root_cause="UNILATERAL",
        evidence=["POD"],
        justified_amount=Decimal("0.00"),
        claimable_amount=Decimal("5000.00"),
        confidence=0.95,
        recommended_action="Reclamar."
    )
    res_a1 = SanityGateEngine.audit_and_reinforce_case(
        rep_a1,
        docs={"delivery": MockDoc(signed=True), "contract": MockDoc(raw_content="Contrato")}
    )
    assert res_a1.irrefutability_grade == "A1_IRREFUTABLE"

    # 2. Caso donde 100% es faltante físico justificado -> B1_ALLANAMIENTO
    rep_b1 = DisputeAnalysisReport(
        case_id="rep_b1",
        billed_amount=Decimal("10000.00"),
        received_amount=Decimal("8000.00"),
        difference=Decimal("2000.00"),
        root_cause="FALTANTE_JUSTIFICADO",
        evidence=["Remisión"],
        justified_amount=Decimal("2000.00"),
        claimable_amount=Decimal("0.00"),
        confidence=0.98,
        recommended_action="Emitir NC."
    )
    res_b1 = SanityGateEngine.audit_and_reinforce_case(rep_b1, docs={})
    assert res_b1.irrefutability_grade == "B1_ALLANAMIENTO"


def test_end_to_end_skynet_runner_integration():
    """Valida que el runner de Skynet ejecute el Sanity Gate en casos reales y lo exponga en el reporte Markdown."""
    runner = SkynetRunner(case_id="case_002", fast_path=True, use_cache=True)
    report = runner.run()

    assert report.sanity_gate_audit is not None
    assert isinstance(report.sanity_gate_audit, SanityGateAuditResult)
    assert report.sanity_gate_audit.arithmetic_invariant_passed is True

    md = generate_markdown_report(report, state=runner.state)
    assert "## 4.2 SANITY GATE DE CUÁDRUPLE AUDITORÍA (SEMANA 4)" in md
    assert "Índice de Irrefutabilidad Probatoria:" in md
    assert "Invarianza Aritmética Cuadrada:" in md
    assert "Prelación Jerárquica Contractual:" in md
