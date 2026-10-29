"""
tests/test_meta_cognition.py
Suite de pruebas automatizadas para Meta-Cognición Dialéctica, Subagente Crítico Adversarial,
Árbol MCTS de Negociación y Jurisprudencia Transfronteriza (CISG/T-MEC).
Sprint 5.2 (Frontera 1 de Superinteligencia).
"""

from decimal import Decimal
import pytest
from fastapi.testclient import TestClient

from api.main import app
from agent.core.adversarial_critic import AdversarialCritic, AdversarialCritiqueResult
from agent.planner.mcts_negotiator import MCTSNegotiator, MCTSPlanResult
from agent.legal.cross_border_treaties import CrossBorderTreatiesEngine, CrossBorderEvaluationResult
from data.models import DisputeAnalysisReport


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def sample_report():
    return DisputeAnalysisReport(
        case_id="case_001",
        billed_amount=Decimal("50000.00"),
        received_amount=Decimal("35000.00"),
        difference=Decimal("15000.00"),
        root_cause="Faltante de entrega amparado en remisión",
        evidence=["Remisión sellada", "Factura FAC-001"],
        justified_amount=Decimal("15000.00"),
        claimable_amount=Decimal("0.00"),
        confidence=0.98,
        recommended_action="Aceptar deducción por faltante físico amparado en remisión sellada.",
        resolution_notes=["Faltante físico comprobado en muelle de recepción."],
        deduction_type="SHORTAGE"
    )



# ==============================================================================
# 1. Pruebas de Jurisprudencia Transfronteriza (CISG / T-MEC / CCom)
# ==============================================================================

def test_treaties_domestic_mexico_timebar():
    """Valida la caducidad perentoria bajo el Art. 88 del Código de Comercio (México)."""
    res = CrossBorderTreatiesEngine.evaluate_transaction(
        seller_country="MEXICO",
        buyer_country="MEXICO",
        days_elapsed_before_claim=14,  # > 5 días
        claim_type="SHORTAGE"
    )

    assert res.is_cross_border is False
    assert res.governing_regime == "CODIGO_COMERCIO_MEXICO"
    assert res.claim_forfeited is True
    assert res.peremptory_notice_limit_days == 5
    assert "Art. 88 Código de Comercio" in res.binding_legal_thesis
    assert "pérdida de toda acción mercantil" in res.binding_legal_thesis


def test_treaties_cross_border_cisg_tmec():
    """Valida la aplicación imperativa de la Convención de Viena (CISG) y T-MEC en comercio exterior."""
    res = CrossBorderTreatiesEngine.evaluate_transaction(
        seller_country="MEXICO",
        buyer_country="USA",
        days_elapsed_before_claim=18,  # > 10 días plazo razonable
        claim_type="PRICING"
    )

    assert res.is_cross_border is True
    assert res.governing_regime == "CISG_Y_TMEC_USMCA"
    assert res.claim_forfeited is True
    assert res.peremptory_notice_limit_days == 10
    assert any(a.article == "Artículo 38" for a in res.applicable_articles)
    assert any(a.article == "Artículo 39" for a in res.applicable_articles)
    assert any(a.treaty.startswith("T-MEC") for a in res.applicable_articles)
    assert "Cámara de Comercio Internacional (ICC Paris)" in res.recommended_arbitral_venue


def test_treaties_statutory_catalog():
    """Verifica que el catálogo legal exponga todos los preceptos canónicos."""
    catalog = CrossBorderTreatiesEngine.get_statutory_catalog()
    assert "cisg" in catalog
    assert "tmec" in catalog
    assert "ccom" in catalog
    assert "ART_38" in catalog["cisg"]
    assert "ART_39" in catalog["cisg"]
    assert "CAP_20" in catalog["tmec"]
    assert "ART_88" in catalog["ccom"]


# ==============================================================================
# 2. Pruebas del Subagente Crítico Adversarial ("Abogado del Diablo")
# ==============================================================================

def test_adversarial_critic_evaluates_pristine_case(sample_report):
    """Evalúa un caso prístino con documentación en regla."""
    critique = AdversarialCritic.critique_report(
        report=sample_report,
        seller_country="MEXICO",
        buyer_country="MEXICO",
        days_to_claim=3,
        has_edi_997=True
    )

    assert critique.case_id == "case_001"
    assert critique.robustness_score >= 85.0
    assert critique.passed is True
    assert len(critique.audit_trail) > 0


def test_adversarial_critic_detects_unsigned_pod(sample_report):
    """Detecta vulnerabilidad por falta de firma autógrafa en la remisión."""
    class MockDelivery:
        signed = False

    critique = AdversarialCritic.critique_report(
        report=sample_report,
        docs={"delivery": MockDelivery()},
        seller_country="MEXICO",
        buyer_country="MEXICO",
        days_to_claim=3
    )

    assert critique.robustness_score < 85.0
    assert critique.passed is False
    assert any(v.category == "PROOF_INTEGRITY" for v in critique.vulnerabilities_detected)
    assert any("firma autógrafa" in v.critic_argument for v in critique.vulnerabilities_detected)


def test_adversarial_critic_detects_missing_edi_997_on_logistics_penalty():
    """Detecta falta de acuse EDI 997 cuando se disputa una penalización OTIF / Cita."""
    report = DisputeAnalysisReport(
        case_id="case_otif_001",
        billed_amount=Decimal("40000.00"),
        received_amount=Decimal("36000.00"),
        difference=Decimal("4000.00"),
        root_cause="Penalización OTIF por presunta entrega fuera de ventana",
        evidence=["Reporte de muelle"],
        justified_amount=Decimal("0.00"),
        claimable_amount=Decimal("4000.00"),
        confidence=0.95,
        recommended_action="Cobro íntegro por penalización unilateral indebida.",
        deduction_type="PENALIZACION_OTIF_CITA",
        resolution_notes=["La entrega llegó a la caseta a tiempo."]
    )


    critique = AdversarialCritic.critique_report(
        report=report,
        has_edi_997=False
    )

    assert any(v.category == "EDI_PROOF" for v in critique.vulnerabilities_detected)
    assert any("EDI 997" in v.critic_argument for v in critique.vulnerabilities_detected)


def test_adversarial_critic_auto_harden_report(sample_report):
    """Valida el ciclo de auto-refuerzo e inyección del escudo preventivo."""
    class MockDelivery:
        signed = False

    critique = AdversarialCritic.critique_report(
        report=sample_report,
        docs={"delivery": MockDelivery()},
        seller_country="MEXICO",
        buyer_country="USA",
        days_to_claim=20
    )

    hardened = AdversarialCritic.auto_harden_report(sample_report, critique)

    assert len(hardened.resolution_notes) > len(sample_report.resolution_notes)
    notes_text = " ".join(hardened.resolution_notes)
    assert "ESCUDO JURÍDICO ADVERSARIAL" in notes_text
    assert "CISG_Y_TMEC_USMCA" in notes_text
    assert "Contra-Argumento Previsto" in notes_text


# ==============================================================================
# 3. Pruebas del Árbol MCTS de Negociación Estratégica (MCTSNegotiator)
# ==============================================================================

def test_mcts_negotiation_simulation_runs():
    """Valida la ejecución de 500 iteraciones MCTS y selección de mejor trayectoria."""
    result = MCTSNegotiator.simulate_negotiation(
        case_id="case_002",
        claimable_amount=Decimal("45000.00"),
        retailer_account_weight_pct=15.0,
        supplier_cashflow_priority="BALANCED",
        num_simulations=500
    )

    assert isinstance(result, MCTSPlanResult)
    assert result.case_id == "case_002"
    assert result.total_simulations == 500
    assert len(result.trajectories_evaluated) == 3
    assert result.recommended_trajectory in ["LITIGIO_AGRESIVO", "PRESERVACION_RELACION", "LIQUIDACION_EXPRESS"]
    assert result.expected_net_payoff > Decimal("0.00")
    assert result.projected_duration_days > 0


def test_mcts_prioritizes_relationship_on_concentrated_account():
    """Si el retailer representa >25% de ventas, MCTS favorece la preservación de alianza."""
    result = MCTSNegotiator.simulate_negotiation(
        case_id="case_walmart_key",
        claimable_amount=Decimal("30000.00"),
        retailer_account_weight_pct=40.0,  # Cuenta estratégica concentrada
        supplier_cashflow_priority="BALANCED",
        num_simulations=300
    )

    assert result.recommended_trajectory == "PRESERVACION_RELACION"
    assert result.relationship_retention_index >= 0.90


def test_mcts_prioritizes_speed_on_cash_urgent():
    """Si la prioridad es liquidez urgente (DSO), MCTS favorece Liquidación Express."""
    result = MCTSNegotiator.simulate_negotiation(
        case_id="case_sme_liquidity",
        claimable_amount=Decimal("20000.00"),
        retailer_account_weight_pct=10.0,
        supplier_cashflow_priority="CASH_URGENT",
        num_simulations=300
    )

    assert result.recommended_trajectory == "LIQUIDACION_EXPRESS"
    assert result.projected_duration_days <= 10


# ==============================================================================
# 4. Pruebas Endpoints API REST (/api/meta-cognition/...)
# ==============================================================================

def test_api_meta_cognition_critique_endpoint(client):
    """Prueba el endpoint /api/meta-cognition/critique sobre case_001."""
    response = client.post(
        "/api/meta-cognition/critique",
        json={
            "case_id": "case_001",
            "seller_country": "MEXICO",
            "buyer_country": "MEXICO",
            "days_to_claim": 12,
            "has_edi_997": True
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["case_id"] == "case_001"
    assert "robustness_score" in data
    assert "passed" in data
    assert "cross_border_assessment" in data


def test_api_meta_cognition_auto_harden_endpoint(client):
    """Prueba el endpoint /api/meta-cognition/auto-harden sobre case_001."""
    response = client.post(
        "/api/meta-cognition/auto-harden",
        json={
            "case_id": "case_001",
            "seller_country": "MEXICO",
            "buyer_country": "USA",
            "days_to_claim": 25,
            "has_edi_997": False
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["is_hardened"] is True
    assert "hardened_resolution_notes" in data


def test_api_meta_cognition_mcts_simulate_endpoint(client):
    """Prueba el endpoint /api/meta-cognition/mcts-simulate."""
    response = client.post(
        "/api/meta-cognition/mcts-simulate",
        json={
            "case_id": "case_001",
            "claimable_amount": 15000.0,
            "retailer_account_weight_pct": 20.0,
            "supplier_cashflow_priority": "BALANCED",
            "num_simulations": 100
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["case_id"] == "case_001"
    assert "recommended_trajectory" in data
    assert len(data["trajectories_evaluated"]) == 3


def test_api_meta_cognition_treaties_endpoint(client):
    """Prueba el endpoint /api/meta-cognition/treaties."""
    response = client.get("/api/meta-cognition/treaties")
    assert response.status_code == 200
    data = response.json()
    assert "cisg" in data
    assert "tmec" in data
    assert "ccom" in data


def test_api_meta_cognition_evaluate_cross_border_endpoint(client):
    """Prueba el endpoint /api/meta-cognition/evaluate-cross-border."""
    response = client.post(
        "/api/meta-cognition/evaluate-cross-border",
        json={
            "seller_country": "MEXICO",
            "buyer_country": "CANADA",
            "days_elapsed": 20,
            "claim_type": "SHORTAGE",
            "contract_has_arbitration": True
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_cross_border"] is True
    assert data["claim_forfeited"] is True
    assert data["governing_regime"] == "CISG_Y_TMEC_USMCA"
