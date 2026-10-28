"""
tests/test_adversarial_courtroom.py
Suite de pruebas periciales para la Fase 3:
- Pilar 3: Debate Dialéctico Multi-Agente (Adversarial Courtroom: Fiscal, Defensor, Magistrado).
- Pilar 4: Motor Predictivo de Cobro & Simulación de Concesiones Financieras.
- Integración en Reporte Markdown y Exposición en Endpoints API REST.
"""

from decimal import Decimal
import pytest
from fastapi.testclient import TestClient

from agent.courtroom.models import AdversarialRole, AdversarialVerdict, AdversarialArgument
from agent.courtroom.adversarial_engine import AdversarialCourtroomEngine
from agent.predictive.models import RecoveryTrack, SettlementScenario, RecoveryPredictionResult
from agent.predictive.recovery_scorer import RecoveryPredictor
from agent.memory.precedent_matcher import PrecedentMatcher
from agent.memory.precedent_graph import RetailerPrecedentProfile
from agent.core.skynet_runner import SkynetRunner
from data.models import DisputeAnalysisReport
from tools.report_exporter.exporter import generate_markdown_report
from api.main import app

client = TestClient(app)


def test_adversarial_debate_structure_and_roles():
    """Valida que el careo dialéctico orqueste las tres rondas entre Fiscal, Defensor y Magistrado."""
    mock_report = DisputeAnalysisReport(
        case_id="case_mock_adversarial",
        billed_amount=Decimal("10000.00"),
        received_amount=Decimal("7000.00"),
        difference=Decimal("3000.00"),
        root_cause="DEDUCCION_UNILATERAL_ASN",
        evidence=["Contrato Marco Maestro 2026", "Remisión Sello Muelle"],
        justified_amount=Decimal("1000.00"),
        claimable_amount=Decimal("2000.00"),
        confidence=0.95,
        recommended_action="Reclamar $2,000.00 USD por cobro indebido y emitir NC por $1,000.00 USD."
    )

    verdict: AdversarialVerdict = AdversarialCourtroomEngine.conduct_debate(
        report=mock_report,
        docs={}
    )

    assert isinstance(verdict, AdversarialVerdict)
    assert verdict.case_id == "case_mock_adversarial"
    assert verdict.courtroom_session_id.startswith("CRT-")
    assert verdict.disputed_amount == Decimal("3000.00")
    assert verdict.justified_amount == Decimal("1000.00")
    assert verdict.claimable_amount == Decimal("2000.00")

    # Verificar argumentos del Fiscal y del Defensor
    assert len(verdict.prosecutor_arguments) >= 1
    assert any(a.role == AdversarialRole.PROSECUTOR for a in verdict.prosecutor_arguments)
    assert len(verdict.advocate_counterarguments) >= 1
    assert any(a.role == AdversarialRole.DEFENDER for a in verdict.advocate_counterarguments)

    # Verificar objeciones sostenidas y desestimadas
    assert len(verdict.sustained_objections) >= 1  # Faltante justificado concedido
    assert len(verdict.dismissed_objections) >= 1  # Deducción unilateral desestimada

    # Dictamen y doctrina judicial vinculante
    assert "Magistrado" in AdversarialCourtroomEngine.MAGISTRATE_NAME
    assert len(verdict.magistrate_summary_ruling) > 20
    assert "DOCTRINA COMERCIAL VINCULANTE" in verdict.final_legal_doctrine
    assert 0.0 <= verdict.probative_force_supplier_pct <= 100.0


def test_probative_force_high_on_unauthorized_penalty():
    """Valida que una retención no autorizada otorgue al defensor fuerza probatoria >= 85%."""
    runner = SkynetRunner(case_id="case_002", fast_path=True, use_cache=True)
    report = runner.run()

    assert report.claimable_amount > Decimal("0.00")
    verdict: AdversarialVerdict = report.adversarial_verdict
    assert verdict is not None
    # En caso 002, el reclamo es altamente fundamentado (falta de prueba de daño y penalización ilegal)
    assert verdict.probative_force_supplier_pct >= 85.0
    assert any("RECLAMABLE" in obj or "IMPROCEDENTE" in obj for obj in verdict.dismissed_objections)


def test_recovery_prediction_scoring_and_drivers():
    """Valida el cálculo determinístico de probabilidad y los drivers de riesgo y fortaleza."""
    mock_report = DisputeAnalysisReport(
        case_id="case_mock_predictive",
        billed_amount=Decimal("50000.00"),
        received_amount=Decimal("40000.00"),
        difference=Decimal("10000.00"),
        root_cause="PENALIDAD_ASN",
        evidence=["POD Sellado", "Contrato 2026"],
        justified_amount=Decimal("0.00"),
        claimable_amount=Decimal("10000.00"),
        confidence=0.92,
        recommended_action="Exigir reintegro inmediato en portal B2B."
    )

    profile = RetailerPrecedentProfile(
        retailer_id="WALMART_MEXICO",
        retailer_name="Walmart México",
        total_cases=10,
        cases_won=9,
        cases_split=1,
        cases_lost=0,
        overall_success_rate_pct=90.0,
        total_recovered_amount=Decimal("150000.00")
    )

    prediction: RecoveryPredictionResult = RecoveryPredictor.calculate_prediction(
        report=mock_report,
        docs={},
        retailer_profile=profile
    )

    assert isinstance(prediction, RecoveryPredictionResult)
    assert prediction.case_id == "case_mock_predictive"
    assert 5.0 <= prediction.recovery_probability_pct <= 98.5
    assert prediction.confidence_grade in ("ALTA_CERTEZA", "MODERADA", "RIESGO_ELEVADO")
    assert isinstance(prediction.recommended_track, RecoveryTrack)
    assert prediction.target_claimable_amount == Decimal("10000.00")
    assert prediction.expected_net_recovery_usd > Decimal("0.00")
    assert prediction.estimated_days_to_cash > 0
    assert len(prediction.positive_drivers) > 0


def test_settlement_scenarios_simulation_math():
    """Valida que la simulación de escenarios cumpla con la precisión monetaria Decimal."""
    mock_report = DisputeAnalysisReport(
        case_id="case_mock_scenarios",
        billed_amount=Decimal("20000.00"),
        received_amount=Decimal("10000.00"),
        difference=Decimal("10000.00"),
        root_cause="DEDUCCION_UNILATERAL",
        evidence=["Contrato"],
        justified_amount=Decimal("0.00"),
        claimable_amount=Decimal("10000.00"),
        confidence=0.90,
        recommended_action="Proceder con conciliación."
    )

    prediction = RecoveryPredictor.calculate_prediction(
        report=mock_report,
        docs={}
    )

    assert len(prediction.scenarios) == 3
    s1, s2, s3 = prediction.scenarios

    # Escenario 1: Cobro íntegro
    assert s1.projected_recovery_amount == Decimal("10000.00")
    assert s1.concession_granted_amount == Decimal("0.00")
    assert s1.recovery_rate_pct == 100.0

    # Escenario 2: Concesión 15%
    assert s2.concession_granted_amount == Decimal("1500.00")
    assert s2.projected_recovery_amount == Decimal("8500.00")
    assert s2.projected_recovery_amount + s2.concession_granted_amount == mock_report.claimable_amount
    assert s2.recovery_rate_pct == 85.0
    assert s2.estimated_days_to_cash == 5

    # Escenario 3: Escalamiento legal NIF C-3
    assert s3.projected_recovery_amount == Decimal("10000.00")
    assert s3.estimated_days_to_cash == 45

    # Exactamente un escenario recomendado
    recommended_count = sum(1 for s in prediction.scenarios if s.recommended)
    assert recommended_count == 1


def test_markdown_report_includes_courtroom_and_predictive_sections():
    """Valida que el reporte exportado en Markdown incorpore las secciones 4.1 y 5.1."""
    runner = SkynetRunner(case_id="case_001", fast_path=True, use_cache=True)
    report = runner.run()

    md = generate_markdown_report(report, state=runner.state)

    assert "## 4.1 DEBATE DIALÉCTICO MULTI-AGENTE (ADVERSARIAL COURTROOM)" in md
    assert "Fuerza Probatoria del Proveedor:" in md
    assert "Dictamen del Magistrado Arbitral:" in md
    assert "### 5.1 SCORING PREDICTIVO DE COBRO & SIMULACIÓN (PILAR 4)" in md
    assert "Probabilidad de Cobro:" in md
    assert "Ruta Estratégica Recomendada:" in md
    assert "| Escenario | Monto Proyectado | Concesión | Plazo | Riesgo Legal |" in md


def test_adversarial_courtroom_and_recovery_api_endpoints():
    """Valida los endpoints REST /api/cases/{case_id}/adversarial-courtroom y recovery-prediction."""
    # 1. Endpoint Courtroom
    res_court = client.get("/api/cases/case_001/adversarial-courtroom")
    assert res_court.status_code == 200
    data_court = res_court.json()
    assert "courtroom_session_id" in data_court
    assert "probative_force_supplier_pct" in data_court
    assert "prosecutor_arguments" in data_court
    assert "advocate_counterarguments" in data_court
    assert "magistrate_summary_ruling" in data_court
    assert "final_legal_doctrine" in data_court

    # 2. Alias Courtroom /api/adversarial/{case_id}
    res_alias_court = client.get("/api/adversarial/case_001")
    assert res_alias_court.status_code == 200
    assert res_alias_court.json()["case_id"] == "case_001"

    # 3. Endpoint Recovery Prediction
    res_pred = client.get("/api/cases/case_001/recovery-prediction")
    assert res_pred.status_code == 200
    data_pred = res_pred.json()
    assert "recovery_probability_pct" in data_pred
    assert "confidence_grade" in data_pred
    assert "recommended_track" in data_pred
    assert "scenarios" in data_pred
    assert len(data_pred["scenarios"]) == 3
    assert "expected_net_recovery_usd" in data_pred

    # 4. Alias Predictive /api/predictive/{case_id}
    res_alias_pred = client.get("/api/predictive/case_001")
    assert res_alias_pred.status_code == 200
    assert res_alias_pred.json()["case_id"] == "case_001"

    # 5. Caso no existente retorna 404
    res_not_found = client.get("/api/cases/case_inexistente_999/adversarial-courtroom")
    assert res_not_found.status_code == 404
