"""
tests/test_concession_engine.py
Suite de pruebas automatizadas para la Fase 1: Motor de Concesiones Comerciales
y Recálculo Dinámico Human-in-the-Loop.
"""

from decimal import Decimal
from pathlib import Path
import json
import pytest
from fastapi.testclient import TestClient

from api.main import app
from agent.core.concession_engine import (
    ConcessionEngine,
    ConcessionIntent,
    parse_concession_intent,
    format_concession_reply,
)
from data.models import DisputeAnalysisReport, CommercialConcession

client = TestClient(app)
ROOT_DIR = Path(__file__).resolve().parent.parent


# ============================================================================
# 1. PRUEBAS DE DETECCIÓN DE INTENCIÓN (parse_concession_intent)
# ============================================================================

def test_parse_concession_intent_percentages():
    """Valida la extracción precisa de intenciones basadas en porcentaje."""
    # 50% explícito
    intent = parse_concession_intent("Acepta el 50% de la penalidad ASN para conciliar")
    assert intent is not None
    assert intent.is_concession is True
    assert intent.is_reset is False
    assert intent.percentage == Decimal("50")
    assert intent.target_concept == "PENALIDAD_EDI_ASN"

    # La mitad (equivalente a 50%)
    intent_half = parse_concession_intent("Absorbe la mitad de la multa")
    assert intent_half is not None
    assert intent_half.percentage == Decimal("50.0")

    # 30% con punto decimal
    intent_pct = parse_concession_intent("Conceder 30.5% de la deducción por pronto pago")
    assert intent_pct is not None
    assert intent_pct.percentage == Decimal("30.5")
    assert intent_pct.target_concept == "DESCUENTO_PRONTO_PAGO"

    # 100% total
    intent_all = parse_concession_intent("Condonar toda la penalidad para cerrar la cuenta")
    assert intent_all is not None
    assert intent_all.percentage == Decimal("100.0")


def test_parse_concession_intent_fixed_amount():
    """Valida la extracción de importes monetarios fijos en USD."""
    # Importe con signo de dólar y comas
    intent = parse_concession_intent("Acepta $1,250 USD de la penalidad operativa")
    assert intent is not None
    assert intent.is_concession is True
    assert intent.is_reset is False
    assert intent.fixed_amount == Decimal("1250")

    # Importe simple
    intent_simple = parse_concession_intent("Cede 500 dolares de la multa")
    assert intent_simple is not None
    assert intent_simple.fixed_amount == Decimal("500")


def test_parse_concession_intent_reset():
    """Valida la detección de reversión o reinicio a la auditoría contractual pura."""
    for phrase in [
        "Restaurar términos originales",
        "Revertir concesión",
        "Revertir ajuste y volver a auditoría original",
        "Sin concesión, cobrar todo",
        "Reset auditoria"
    ]:
        intent = parse_concession_intent(phrase)
        assert intent is not None, f"Falló en frase: {phrase}"
        assert intent.is_concession is True
        assert intent.is_reset is True


def test_parse_concession_intent_ignored_queries():
    """Valida que consultas estándar NO se interpreten erróneamente como concesiones."""
    queries = [
        "¿Cuál es la causa raíz de la discrepancia?",
        "¿Cuánto es el monto reclamable?",
        "Explícame las cláusulas del contrato 4.2",
        "¿Quién recibió la mercancía en el muelle?",
        "Hola, buenos días agente",
        "Genera la carta de reclamación formal"
    ]
    for q in queries:
        assert parse_concession_intent(q) is None, f"Falso positivo en: {q}"


# ============================================================================
# 2. PRUEBAS DEL MOTOR MATEMÁTICO DETERMINÍSTICO (ConcessionEngine)
# ============================================================================

def test_concession_engine_apply_percentage_50():
    """Valida el recálculo matemático de 50% de concesión sobre saldo reclamable."""
    case_id = "case_005_amazon_shortage"
    base_report = ConcessionEngine.get_or_create_base_report(case_id)
    base_claimable = base_report.claimable_amount
    base_justified = base_report.justified_amount
    total_diff = abs(base_report.difference)

    # Invariante base
    assert base_justified + base_claimable == total_diff

    # Aplicar 50%
    intent = ConcessionIntent(
        is_concession=True,
        is_reset=False,
        percentage=Decimal("50.0"),
        target_concept="PENALIDAD_EDI_ASN",
        reason="Acuerdo comercial estratégico"
    )
    updated = ConcessionEngine.apply_concession(case_id, intent, operator_name="Operador Test")

    expected_concession = (base_claimable * Decimal("0.50")).quantize(Decimal("0.01"))
    expected_justified = base_justified + expected_concession
    expected_claimable = base_claimable - expected_concession

    assert updated.justified_amount == expected_justified
    assert updated.claimable_amount == expected_claimable
    # Invariante contable estricto al centavo en Decimal
    assert updated.justified_amount + updated.claimable_amount == total_diff

    # Trazabilidad auditable
    assert len(updated.concessions) == 1
    conc = updated.concessions[0]
    assert conc.concession_amount == expected_concession
    assert conc.operator == "Operador Test"
    assert conc.original_claimable == base_claimable
    assert conc.new_claimable == expected_claimable

    # Validar persistencia de archivos
    report_file = ROOT_DIR / "reports" / f"dispute_report_{case_id}.json"
    letter_file = ROOT_DIR / "reports" / f"carta_reclamacion_{case_id}.md"
    assert report_file.exists()
    assert letter_file.exists()

    with open(report_file, "r", encoding="utf-8") as f:
        saved_data = json.load(f)
    assert Decimal(str(saved_data["justified_amount"])) == expected_justified
    assert Decimal(str(saved_data["claimable_amount"])) == expected_claimable

    with open(letter_file, "r", encoding="utf-8") as lf:
        letter_txt = lf.read()
    assert "ACUERDO COMERCIAL Y CONCESIÓN MUTUA (HUMAN-IN-THE-LOOP)" in letter_txt
    assert str(conc.concession_id) in letter_txt


def test_concession_engine_apply_100_percent_full_forgiveness():
    """Valida la condonación total (100%) cerrando el litigio sin saldo reclamable."""
    case_id = "case_005_amazon_shortage"
    base_report = ConcessionEngine.get_or_create_base_report(case_id)
    total_diff = abs(base_report.difference)

    intent = ConcessionIntent(
        is_concession=True,
        is_reset=False,
        percentage=Decimal("100.0"),
        target_concept="PENALIDAD_COMPLETA",
        reason="Condonación comercial total"
    )
    updated = ConcessionEngine.apply_concession(case_id, intent)

    assert updated.claimable_amount == Decimal("0.00")
    assert updated.justified_amount == total_diff
    assert updated.justified_amount + updated.claimable_amount == total_diff
    assert "Acuerdo Pleno" in updated.recommended_action


def test_concession_engine_reset_restoration():
    """Valida que la reversión restaure íntegramente la auditoría contractual pura."""
    case_id = "case_005_amazon_shortage"
    base_report = ConcessionEngine.get_or_create_base_report(case_id)

    # Primero aplicar concesión
    intent_apply = ConcessionIntent(is_concession=True, is_reset=False, percentage=Decimal("50.0"))
    ConcessionEngine.apply_concession(case_id, intent_apply)

    # Luego revertir
    intent_reset = ConcessionIntent(is_concession=True, is_reset=True)
    restored = ConcessionEngine.apply_concession(case_id, intent_reset)

    assert restored.justified_amount == base_report.justified_amount
    assert restored.claimable_amount == base_report.claimable_amount
    assert len(restored.concessions) == 0


def test_format_concession_reply():
    """Valida la generación de respuestas en Markdown con tablas ejecutivas."""
    case_id = "case_002"
    intent = ConcessionIntent(is_concession=True, percentage=Decimal("50.0"))
    report = ConcessionEngine.apply_concession(case_id, intent)
    reply = format_concession_reply(report, intent)

    assert "### ⚡ Concesión Comercial Human-in-the-Loop Aplicada con Éxito" in reply
    assert "Deducción Justificada (Nota de Crédito)" in reply
    assert "Saldo Reclamable (Cobranza)" in reply
    assert "case_002" in reply

    # Reset reply
    reset_intent = ConcessionIntent(is_concession=True, is_reset=True)
    reset_report = ConcessionEngine.apply_concession(case_id, reset_intent)
    reset_reply = format_concession_reply(reset_report, reset_intent)
    assert "### 🔄 Auditoría Contractual Restaurada a Términos Originales" in reset_reply


# ============================================================================
# 3. PRUEBAS DE INTEGRACIÓN DE ENDPOINTS API REST
# ============================================================================

def test_api_chat_concession_natural_language_interception():
    """Valida que el endpoint de chat intercepte y recalcule en vivo vía lenguaje natural."""
    case_id = "case_005_amazon_shortage"
    payload = {
        "message": "Acepta el 50% de la penalidad ASN de $2,500 y concilia el resto",
        "role": "commercial_negotiator"
    }
    response = client.post(f"/api/cases/{case_id}/chat", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["mode"] == "human_in_the_loop"
    assert data["concession_applied"] is True
    assert "recalculated_report" in data
    rep = data["recalculated_report"]
    assert rep["claimable_amount"] == 1250.0  # 2500 - 50%
    assert rep["justified_amount"] == 6250.0  # 5000 + 1250
    assert "Concesión Comercial Human-in-the-Loop" in data["reply"]


def test_api_concession_parametric_endpoint_and_history():
    """Valida los endpoints dedicados POST /concession y GET /concessions."""
    case_id = "case_006_walmart_otif_pricing"

    # 1. Aplicar concesión paramétrica
    concess_payload = {
        "percentage": 50.0,
        "concept": "PENALIDAD_OTIF_LOGISTICA",
        "reason": "Acuerdo de nivel de servicio trimestral con Walmart"
    }
    resp = client.post(f"/api/cases/{case_id}/concession", json=concess_payload)
    assert resp.status_code == 200
    res_data = resp.json()
    assert res_data["status"] == "success"
    assert len(res_data["concessions"]) >= 1

    # 2. Consultar historial de concesiones activas
    hist_resp = client.get(f"/api/cases/{case_id}/concessions")
    assert hist_resp.status_code == 200
    hist_data = hist_resp.json()
    assert hist_data["case_id"] == case_id
    assert len(hist_data["concessions"]) >= 1
    assert hist_data["concessions"][0]["target"] == "PENALIDAD_OTIF_LOGISTICA"

    # 3. Revertir mediante endpoint paramétrico
    reset_payload = {"is_reset": True}
    reset_resp = client.post(f"/api/cases/{case_id}/concession", json=reset_payload)
    assert reset_resp.status_code == 200
    assert len(reset_resp.json()["concessions"]) == 0
