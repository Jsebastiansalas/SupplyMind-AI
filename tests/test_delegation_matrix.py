"""
tests/test_delegation_matrix.py
Suite de pruebas automatizadas para la Matriz de Delegación Financiera & Dualidad de Gobernanza (Sprint 6.2).
Verifica:
1. Políticas jerárquicas por nivel de cuenta (Tier 1 Estratégica, Tier 2 Regular, Tier 3 Alto Riesgo).
2. Salvaguarda financiera estricta: Casos >= $10,000 USD fuerzan obligatoriamente Human Gatekeeper.
3. Reciprocidad comercial vinculante en convenios mercantiles de finiquito.
4. Sellado ZKP SHA-256 e invariantes contables de partida doble ($0.00 MAE).
5. Eficacia jurídica de cosa juzgada conforme al Código de Comercio.
6. Endpoints REST de consulta/calibración de la matriz y conmutación de gobernanza.
"""

import pytest
from decimal import Decimal
from pathlib import Path
from fastapi.testclient import TestClient

from api.main import app
from agent.core.delegation_matrix_engine import DelegationMatrixEngine, DEFAULT_TIER_POLICIES
from agent.core.settlement_agreement_generator import SettlementAgreementGenerator
from agent.core.bilateral_negotiation_engine import BilateralNegotiationEngine
from agent.core.concession_engine import ConcessionEngine
from data.models import FinancialDelegationMatrix

client = TestClient(app)


def test_delegation_tier_policies_structure():
    """Valida la configuración de límites por Tier y reciprocidad requerida."""
    matrix = DelegationMatrixEngine.get_active_matrix()
    assert matrix.strict_approval_threshold == Decimal("10000.00")
    assert "TIER_1_STRATEGIC" in matrix.tier_policies
    assert "TIER_2_REGULAR" in matrix.tier_policies
    assert "TIER_3_HIGH_RISK" in matrix.tier_policies

    # Tier 1: Concesión estratégica hasta 50% con reciprocidad
    t1 = matrix.tier_policies["TIER_1_STRATEGIC"]
    assert t1.max_concession_pct == 50.0
    assert t1.max_concession_fixed_cap == Decimal("15000.00")
    assert t1.require_reciprocal_concession is True
    assert len(t1.reciprocal_clauses_required) >= 2

    # Tier 2: Concesión moderada hasta 25%
    t2 = matrix.tier_policies["TIER_2_REGULAR"]
    assert t2.max_concession_pct == 25.0
    assert t2.max_concession_fixed_cap == Decimal("5000.00")

    # Tier 3: Tolerancia cero (0% de concesión)
    t3 = matrix.tier_policies["TIER_3_HIGH_RISK"]
    assert t3.max_concession_pct == 0.0
    assert t3.max_concession_fixed_cap == Decimal("0.00")


def test_safeguard_threshold_forces_human_gatekeeper():
    """
    Verifica que disputas con monto disputado >= $10,000 USD activan obligatoriamente
    la salvaguarda de Human Gatekeeper impidiendo el cierre autónomo sin visto bueno del CFO.
    """
    # case_009_mega_retailer_dispute tiene una disputa de $25,000 USD (> $10,000 USD)
    case_id = "case_009_mega_retailer_dispute"
    eval_res = DelegationMatrixEngine.evaluate_case_delegation(case_id, requested_mode="FULL_AUTONOMY")

    assert eval_res["total_disputed_amount"] >= Decimal("10000.00")
    assert eval_res["safeguard_triggered"] is True
    assert eval_res["enforced_mode"] == "HUMAN_GATEKEEPER"
    assert "Salvaguarda Financiera Activa" in eval_res["safeguard_reason"]

    # Iniciar careo en BilateralNegotiationEngine debe forzar HUMAN_GATEKEEPER
    session = BilateralNegotiationEngine.start_duel(case_id=case_id, governance_mode="FULL_AUTONOMY")
    assert session.governance_mode == "HUMAN_GATEKEEPER"

    # Intentar conmutar a FULL_AUTONOMY en caliente debe ser rechazado con ValueError
    with pytest.raises(ValueError) as excinfo:
        BilateralNegotiationEngine.set_governance_mode(case_id, "FULL_AUTONOMY")
    assert "Salvaguarda Financiera Activa" in str(excinfo.value)


def test_settlement_agreement_and_reciprocity():
    """
    Verifica que la generación del convenio mercantil incluye cláusulas de reciprocidad,
    sello ZKP SHA-256 e invarianza aritmética $0.00 MAE.
    """
    case_id = "case_005_amazon_shortage"
    session = BilateralNegotiationEngine.start_duel(case_id=case_id, governance_mode="HUMAN_GATEKEEPER")

    # Ejecutar rondas hasta acuerdo
    for _ in range(4):
        session = BilateralNegotiationEngine.advance_duel_step(case_id)

    # Aprobar formalmente
    session = BilateralNegotiationEngine.approve_settlement(case_id, operator_name="Lic. Roberto Morales (CFO)")
    assert session.status == "AGREEMENT_REACHED"
    assert session.settlement_minutes_hash is not None

    agreement = BilateralNegotiationEngine.get_settlement_agreement_details(case_id)
    assert agreement is not None
    assert agreement.case_id == case_id
    assert agreement.signed_by_operator == "Auditor B2B / SupplyMind AI" or "CFO" in agreement.signed_by_operator or "SupplyMind" in agreement.signed_by_operator
    assert len(agreement.zkp_seal_hash) == 64  # SHA-256

    # Invariante de conservación de montos ($0.00 MAE)
    total_reconciled = agreement.total_credit_memo + agreement.cash_recovery_amount
    assert total_reconciled == agreement.dispute_original_amount

    # Cláusulas de reciprocidad obligatoria
    assert len(agreement.reciprocal_commitments) >= 3
    assert any("Liquidación bancaria" in c for c in agreement.reciprocal_commitments)
    assert any("penalizaciones logísticas" in c for c in agreement.reciprocal_commitments)

    # Cláusulas de cosa juzgada mercantil
    assert any("Artículos 2944" in d for d in agreement.legal_doctrines)
    assert any("Artículo 1054 del Código de Comercio" in d for d in agreement.legal_doctrines)

    # Validar payload contable ERP de partida doble
    erp_payload = SettlementAgreementGenerator.build_erp_settlement_payload(agreement)
    assert erp_payload["erp_status"] == "READY_FOR_POSTING"
    total_debits = sum(e["debit"] for e in erp_payload["accounting_entries"])
    total_credits = sum(e["credit"] for e in erp_payload["accounting_entries"])
    assert round(total_debits, 2) == round(total_credits, 2)


def test_rest_api_delegation_matrix():
    """Valida los endpoints REST de consulta y actualización de la Matriz de Delegación."""
    # 1. GET /api/negotiation/delegation-matrix
    res = client.get("/api/negotiation/delegation-matrix")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "strict_approval_threshold" in data["matrix"]
    assert data["matrix"]["strict_approval_threshold"] == 10000.0

    # 2. POST /api/negotiation/delegation-matrix (Calibración)
    update_payload = {
        "cfo_approver": "Comité de Riesgos y Finanzas Corporativas B2B",
        "strict_approval_threshold": 12000.0
    }
    post_res = client.post("/api/negotiation/delegation-matrix", json=update_payload)
    assert post_res.status_code == 200
    updated_data = post_res.json()
    assert updated_data["matrix"]["strict_approval_threshold"] == 12000.0
    assert updated_data["matrix"]["cfo_approver"] == "Comité de Riesgos y Finanzas Corporativas B2B"

    # Restaurar umbral estándar de $10,000 USD
    client.post("/api/negotiation/delegation-matrix", json={"strict_approval_threshold": 10000.0})


def test_rest_api_governance_toggle_and_minutes():
    """Valida los endpoints REST de conmutación de modo de gobernanza y recuperación de convenio."""
    case_id = "case_005_amazon_shortage"

    # Iniciar careo
    start_res = client.post(f"/api/cases/{case_id}/negotiation/duel/start", json={"governance_mode": "HUMAN_GATEKEEPER"})
    assert start_res.status_code == 200

    # Conmutar gobernanza a FULL_AUTONOMY (permitido para caso < $10k)
    gov_res = client.post(
        f"/api/cases/{case_id}/negotiation/duel/governance",
        json={"governance_mode": "FULL_AUTONOMY"}
    )
    assert gov_res.status_code == 200
    assert gov_res.json()["governance_mode"] == "FULL_AUTONOMY"

    # Intentar conmutar a FULL_AUTONOMY en caso de alto valor (> $10k) -> debe dar 400
    high_case = "case_009_mega_retailer_dispute"
    client.post(f"/api/cases/{high_case}/negotiation/duel/start", json={"governance_mode": "HUMAN_GATEKEEPER"})
    bad_gov_res = client.post(
        f"/api/cases/{high_case}/negotiation/duel/governance",
        json={"governance_mode": "FULL_AUTONOMY"}
    )
    assert bad_gov_res.status_code == 400
    assert "Salvaguarda Financiera Activa" in bad_gov_res.json()["detail"]

    # Consultar convenio/minutas del caso 005
    min_res = client.get(f"/api/cases/{case_id}/negotiation/duel/minutes")
    assert min_res.status_code == 200
    min_data = min_res.json()
    assert min_data["status"] == "success"
    assert "markdown_content" in min_data
    assert "Cosa Juzgada" in min_data["markdown_content"]
