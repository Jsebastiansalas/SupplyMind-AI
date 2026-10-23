"""
tests/test_negotiation_engine.py
Suite de pruebas automatizadas para la Fase 2: Motor de Negociación B2B Multitáctico,
Generación de Escenarios (Agresivo, Equilibrado, Conservador) y Minutas de Conciliación.
"""

from decimal import Decimal
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from api.main import app
from agent.core.negotiation_engine import (
    NegotiationEngine,
    parse_negotiation_query,
    format_negotiation_plan_reply,
)
from agent.core.concession_engine import ConcessionEngine
from data.models import NegotiationPlan, NegotiationScenario

client = TestClient(app)
ROOT_DIR = Path(__file__).resolve().parent.parent


# ============================================================================
# 1. PRUEBAS DE DETECCIÓN INTELIGENTE DE CONSULTAS DE NEGOCIACIÓN
# ============================================================================

def test_parse_negotiation_query_detection():
    """Valida la detección de intenciones de consulta y aplicación de escenarios."""
    # 1. Consulta general de escenarios
    for q in [
        "¿Qué escenarios de negociación sugieres?",
        "¿Cómo podemos negociar con Walmart?",
        "Muestrame la contrapropuesta comercial",
        "Estrategias de negociacion para este caso",
        "Genera la minuta de acuerdo bilateral"
    ]:
        res = parse_negotiation_query(q)
        assert res is not None, f"Falló en consulta: {q}"
        assert res["action"] == "show_scenarios"
        assert res["scenario_id"] is None

    # 2. Selección directa de escenario
    res_bal = parse_negotiation_query("Aplica el escenario equilibrado para cerrar acuerdo")
    assert res_bal is not None
    assert res_bal["action"] == "apply"
    assert res_bal["scenario_id"] == "BALANCED"

    res_agg = parse_negotiation_query("Aplica el escenario agresivo con requerimiento legal")
    assert res_agg is not None
    assert res_agg["action"] == "apply"
    assert res_agg["scenario_id"] == "AGGRESSIVE"

    res_cons = parse_negotiation_query("Aplica el escenario conservador para preservar la relación de cuenta")
    assert res_cons is not None
    assert res_cons["action"] == "apply"
    assert res_cons["scenario_id"] == "CONSERVATIVE"

    # 3. Consultas estándar no comerciales
    for non_q in [
        "¿Quién firmó la remisión de entrega?",
        "Descargar documento en PDF",
        "Hola buenos días agente",
        "¿Qué fecha tiene la factura?"
    ]:
        assert parse_negotiation_query(non_q) is None


# ============================================================================
# 2. PRUEBAS DEL MOTOR DE ESCENARIOS EN CASOS ÉLITE
# ============================================================================

@pytest.mark.parametrize("case_id", [
    "case_005_amazon_shortage",
    "case_006_walmart_otif_pricing",
    "case_007_cisco_large_bundle",
    "case_009_mega_retailer_dispute"
])
def test_negotiation_engine_build_plan_elite_cases(case_id: str):
    """Valida la construcción determinística y la cuadratura contable en los 4 casos élite."""
    plan: NegotiationPlan = NegotiationEngine.build_negotiation_plan(case_id)

    assert plan.case_id == case_id
    assert len(plan.scenarios) == 3
    assert plan.total_dispute_amount > Decimal("0.00")
    assert plan.recommended_scenario in ["BALANCED", "AGGRESSIVE"]

    scen_ids = [s.scenario_id for s in plan.scenarios]
    assert "AGGRESSIVE" in scen_ids
    assert "BALANCED" in scen_ids
    assert "CONSERVATIVE" in scen_ids

    # Verificar invariante contable estricto al centavo en TODOS los escenarios
    for sc in plan.scenarios:
        # Justified + Claimable == Total Dispute
        assert sc.justified_amount + sc.claimable_amount == plan.total_dispute_amount, (
            f"Violación de invariante en {case_id} [{sc.scenario_id}]: "
            f"{sc.justified_amount} + {sc.claimable_amount} != {plan.total_dispute_amount}"
        )
        assert sc.recovery_rate_pct >= 0.0 and sc.recovery_rate_pct <= 100.0
        assert sc.friction_risk in ["ALTO", "MEDIO", "BAJO"]
        assert len(sc.counterparty_concession_requested) > 10


def test_negotiation_engine_apply_scenario_balanced():
    """Valida la aplicación del escenario Equilibrado y la generación de la Minuta Formal."""
    case_id = "case_005_amazon_shortage"
    base_report = ConcessionEngine.get_or_create_base_report(case_id)
    total_diff = abs(base_report.difference)

    updated_report = NegotiationEngine.apply_scenario(
        case_id=case_id,
        scenario_id="BALANCED",
        operator_name="Director Comercial Test"
    )

    assert updated_report.active_scenario == "BALANCED"
    assert updated_report.justified_amount + updated_report.claimable_amount == total_diff

    # En case_005: base_claimable era $2,500.00; con BALANCED se concede el 50% ($1,250.00)
    assert updated_report.claimable_amount == Decimal("1250.00")
    assert updated_report.justified_amount == Decimal("6250.00")

    # Validar archivo de Minuta Formal
    minutes_file = ROOT_DIR / "reports" / f"minuta_acuerdo_{case_id}.md"
    assert minutes_file.exists()

    with open(minutes_file, "r", encoding="utf-8") as mf:
        content = mf.read()

    assert "MINUTA DE CONCILIACIÓN Y CONVENIO DE TRANSACCIÓN COMERCIAL" in content
    assert "Amazon Fulfillment Services LLC" in content
    assert "Director Comercial Test" in content
    assert "Cláusula 1 (Emisión de Nota de Crédito)" in content
    assert "Cláusula 4 (Finiquito y No Repetición)" in content
    assert "$1,250.00 USD" in content


def test_negotiation_engine_apply_aggressive_and_conservative():
    """Valida los extremos: Cobro Íntegro vs Conservación Total de Relación."""
    case_id = "case_005_amazon_shortage"
    base_report = ConcessionEngine.get_or_create_base_report(case_id)
    total_diff = abs(base_report.difference)

    # 1. Conservador: Nota de crédito 100%
    rep_cons = NegotiationEngine.apply_scenario(case_id, "CONSERVATIVE")
    assert rep_cons.active_scenario == "CONSERVATIVE"
    assert rep_cons.claimable_amount == Decimal("0.00")
    assert rep_cons.justified_amount == total_diff

    # 2. Agresivo: Restablece cobro del 100% reclamable original
    rep_agg = NegotiationEngine.apply_scenario(case_id, "AGGRESSIVE")
    assert rep_agg.active_scenario == "AGGRESSIVE"
    assert rep_agg.claimable_amount == base_report.claimable_amount
    assert rep_agg.justified_amount == base_report.justified_amount


# ============================================================================
# 3. PRUEBAS DE INTEGRACIÓN API REST (Fase 2)
# ============================================================================

def test_api_get_negotiation_plan():
    """Valida el endpoint GET /api/cases/{case_id}/negotiation."""
    case_id = "case_006_walmart_otif_pricing"
    response = client.get(f"/api/cases/{case_id}/negotiation")
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "success"
    assert data["case_id"] == case_id
    plan = data["plan"]
    assert plan["account_name"] == "Walmart Inc. Retail Operations"
    assert len(plan["scenarios"]) == 3
    assert "### 🤝 Propuesta Multi-Táctica de Negociación B2B" in data["summary_markdown"]


def test_api_select_negotiation_scenario():
    """Valida el endpoint POST /api/cases/{case_id}/negotiation/select."""
    case_id = "case_006_walmart_otif_pricing"
    payload = {
        "scenario_id": "BALANCED",
        "operator_name": "Lic. Roberto González (VP Finanzas)"
    }
    response = client.post(f"/api/cases/{case_id}/negotiation/select", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "success"
    assert data["selected_scenario"] == "BALANCED"
    assert "report" in data
    assert "MINUTA DE CONCILIACIÓN" in data["settlement_minutes"]
    assert "Lic. Roberto González" in data["settlement_minutes"]

    # Validación de escenario no válido
    bad_resp = client.post(f"/api/cases/{case_id}/negotiation/select", json={"scenario_id": "INVALIDO"})
    assert bad_resp.status_code == 400


def test_api_chat_negotiation_interaction():
    """Valida la conversación natural sobre escenarios y la aplicación vía chat."""
    case_id = "case_005_amazon_shortage"

    # 1. Pregunta sobre escenarios disponibles
    ask_payload = {
        "message": "¿Qué escenarios de contrapropuesta y negociación B2B sugieres para este caso?",
        "role": "commercial_negotiator"
    }
    resp1 = client.post(f"/api/cases/{case_id}/chat", json=ask_payload)
    assert resp1.status_code == 200
    data1 = resp1.json()
    assert data1["mode"] == "negotiation_options"
    assert "Propuesta Multi-Táctica de Negociación B2B" in data1["reply"]
    assert "negotiation_plan" in data1

    # 2. Orden de aplicación de escenario vía chat
    apply_payload = {
        "message": "Aplica el escenario equilibrado: concesión del 50% con reciprocidad comercial",
        "role": "commercial_negotiator"
    }
    resp2 = client.post(f"/api/cases/{case_id}/chat", json=apply_payload)
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["mode"] == "negotiation_scenario"
    assert data2["scenario_applied"] == "BALANCED"
    assert "recalculated_report" in data2
    assert data2["recalculated_report"]["claimable_amount"] == 1250.0
