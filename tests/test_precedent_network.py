"""
tests/test_precedent_network.py
Suite de pruebas periciales para la Fase 2: Red de Memoria & Historial de Precedentes B2B.
Valida el grafo de precedentes por retailer, persistencia relacional SQLite/JSON,
el motor de emparejamiento semántico multidimensional, la auto-inyección en cartas
de reclamación y el bucle de auto-aprendizaje al resolver controversias.
"""

from decimal import Decimal
import json
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from agent.memory.precedent_graph import (
    DisputeMemoryNetwork,
    DisputePrecedentRecord,
    RetailerPrecedentProfile
)
from agent.memory.precedent_matcher import PrecedentMatcher, MatchedPrecedent
from data.models import DisputeAnalysisReport
from tools.report_exporter.exporter import generate_reclamation_letter, export_dispute_artifacts
from agent.core.state import DisputeState
from api.main import app

client = TestClient(app)


@pytest.fixture
def temp_memory_network(tmp_path):
    """Fixture que proporciona una instancia limpia y aislada de DisputeMemoryNetwork."""
    net = DisputeMemoryNetwork(data_dir=tmp_path / "precedents_test")
    return net


def test_precedent_registration_and_sqlite_persistence(temp_memory_network):
    """Valida el registro atómico y la recuperación íntegra de precedentes en SQLite y JSON."""
    net = temp_memory_network

    record = DisputePrecedentRecord(
        precedent_id="PREC-TEST-001",
        case_id="case_test_walmart",
        date_resolved="2026-10-20",
        retailer_id="WALMART_MEXICO",
        retailer_name="Walmart México",
        dispute_type="Penalización por retraso ASN en muelle de Cuautitlán",
        deduction_code="DED-ASN-PENALTY",
        governing_clause="CLAUSE-14.2",
        billed_amount=Decimal("45000.00"),
        disputed_amount=Decimal("3500.00"),
        justified_amount=Decimal("0.00"),
        recovered_amount=Decimal("3500.00"),
        outcome="WON",
        success_rate_ratio=1.0,
        key_evidence_cited=["Log de citas RetailLink", "Convenio Marco 2026"],
        binding_argument="Walmart aceptó reembolsar la penalidad al acreditarse saturación de muelle imputable al comprador.",
        precedent_summary="Reintegro del 100% por $3,500.00 USD."
    )

    net.register_precedent(record)

    # 1. Recuperación directa
    all_precedents = net.get_all_precedents()
    assert len(all_precedents) == 1
    p = all_precedents[0]
    assert p.precedent_id == "PREC-TEST-001"
    assert p.retailer_id == "WALMART_MEXICO"
    assert p.recovered_amount == Decimal("3500.00")
    assert p.outcome == "WON"

    # 2. Persistencia en SQLite
    sqlite_precedents = net.get_precedents_by_retailer("WALMART_MEXICO")
    assert len(sqlite_precedents) == 1
    assert sqlite_precedents[0].case_id == "case_test_walmart"

    # 3. Persistencia en JSON legible
    assert net.json_file.exists()
    with open(net.json_file, "r", encoding="utf-8") as f:
        json_data = json.load(f)
    assert len(json_data) == 1
    assert json_data[0]["deduction_code"] == "DED-ASN-PENALTY"


def test_retailer_profile_aggregation_metrics(temp_memory_network):
    """Valida el cálculo automatizado de tasas de éxito, montos recuperados y patrones."""
    net = temp_memory_network

    p1 = DisputePrecedentRecord(
        precedent_id="PREC-W1",
        case_id="case_w1",
        date_resolved="2026-09-01",
        retailer_id="WALMART_MEXICO",
        retailer_name="Walmart México",
        dispute_type="Penalidad ASN",
        deduction_code="DED-ASN",
        governing_clause="CLAUSE-14.2",
        billed_amount=Decimal("10000.00"),
        disputed_amount=Decimal("2000.00"),
        justified_amount=Decimal("0.00"),
        recovered_amount=Decimal("2000.00"),
        outcome="WON",
        success_rate_ratio=1.0,
        binding_argument="Arg 1",
        precedent_summary="Summary 1"
    )

    p2 = DisputePrecedentRecord(
        precedent_id="PREC-W2",
        case_id="case_w2",
        date_resolved="2026-09-15",
        retailer_id="WALMART_MEXICO",
        retailer_name="Walmart México",
        dispute_type="Penalidad ASN",
        deduction_code="DED-ASN",
        governing_clause="CLAUSE-14.2",
        billed_amount=Decimal("20000.00"),
        disputed_amount=Decimal("4000.00"),
        justified_amount=Decimal("1000.00"),
        recovered_amount=Decimal("3000.00"),
        outcome="PARTIAL_CONCESSION",
        success_rate_ratio=0.75,
        binding_argument="Arg 2",
        precedent_summary="Summary 2"
    )

    net.register_precedent(p1)
    net.register_precedent(p2)

    profile = net.get_retailer_profile("WALMART_MEXICO")
    assert profile is not None
    assert profile.total_cases_analyzed == 2
    assert profile.cases_won == 1
    assert profile.cases_partial == 1
    assert profile.cases_lost == 0
    assert profile.overall_success_rate_pct == 100.0  # (1 + 1) / 2 = 100%
    assert profile.total_disputed_usd == Decimal("6000.00")
    assert profile.total_recovered_usd == Decimal("5000.00")
    assert profile.average_recovery_rate_pct == 83.33  # 5000 / 6000 = 83.33%
    assert len(profile.common_dispute_patterns) >= 1


def test_precedent_matcher_multidimensional_scoring(temp_memory_network):
    """Valida la recuperación y ponderación semántica de precedentes análogos."""
    net = temp_memory_network

    # Insertar precedente ancla
    net.register_precedent(DisputePrecedentRecord(
        precedent_id="PREC-AMAZON-001",
        case_id="case_005_amazon_shortage",
        date_resolved="2026-09-10",
        retailer_id="AMAZON_MEXICO",
        retailer_name="Amazon México",
        dispute_type="Faltante físico en recibo no acreditado en remisión",
        deduction_code="DED-SHORTAGE-ASN",
        governing_clause="CLAUSE-4.2",
        billed_amount=Decimal("24500.00"),
        disputed_amount=Decimal("3500.00"),
        justified_amount=Decimal("1700.00"),
        recovered_amount=Decimal("1800.00"),
        outcome="PARTIAL_CONCESSION",
        success_rate_ratio=0.514,
        binding_argument="Se acreditó que el faltante fue demora interna de desembalaje.",
        precedent_summary="Recuperación de $1,800 USD."
    ))

    matcher = PrecedentMatcher(memory_network=net)

    # Consulta con alta afinidad (mismo retailer y causa afín)
    matches = matcher.find_relevant_precedents(
        retailer_id="AMAZON_MEXICO",
        dispute_type="Faltante de mercancía en entrega",
        deduction_code="DED-SHORTAGE-ASN",
        top_k=2
    )

    assert len(matches) == 1
    m = matches[0]
    assert m.precedent.case_id == "case_005_amazon_shortage"
    assert m.similarity_score >= 0.50
    assert "Mismo cliente corporativo (Amazon México)" in m.match_reasons
    assert "DED-SHORTAGE-ASN" in m.formal_citation_text

    # Generación de bloque para carta
    block = PrecedentMatcher.format_precedents_block_for_letter(matches)
    assert "Antecedentes y Precedentes Comerciales Vinculantes" in block
    assert "case_005_amazon_shortage" in block
    assert "$1,800.00 USD" in block


def test_claim_letter_precedent_injection():
    """Valida la inyección autónoma de precedentes en la Carta Formal de Reclamación."""
    report = DisputeAnalysisReport(
        case_id="case_006_walmart_otif_pricing",
        currency="USD",
        billed_amount=Decimal("32000.00"),
        received_amount=Decimal("29600.00"),
        difference=Decimal("-2400.00"),
        root_cause="Penalización OTIF y cargos EDI ASN sin adenda bilateral previa.",
        evidence=["Log de citas RetailLink", "Convenio Marco 2026"],
        justified_amount=Decimal("0.00"),
        claimable_amount=Decimal("2400.00"),
        confidence=0.99,
        recommended_action="Reclamar la totalidad del cargo unilateral."
    )

    state = DisputeState(
        case_id="case_006_walmart_otif_pricing",
        objective="Reclamar retención indebida a Walmart",
        loaded_documents={
            "invoice": type("Obj", (), {"invoice_id": "INV-WAL-99", "vendor_id": "PROV-NACIONAL", "customer_id": "WALMART_MEXICO"})(),
            "payment": type("Obj", (), {"payment_id": "PAY-WAL-11", "deductions": [type("Ded", (), {"code": "DED-ASN-PENALTY"})()]})(),
            "delivery": type("Obj", (), {"delivery_id": "DEL-WAL-44"})(),
            "contract": type("Obj", (), {"contract_id": "CTR-WAL-2026"})()
        }
    )

    letter = generate_reclamation_letter(report=report, state=state)

    # Debe contener la sección formal de precedentes vinculantes
    assert "Antecedentes y Precedentes Comerciales Vinculantes" in letter
    assert "Walmart" in letter
    assert "MONTO TOTAL A REINTEGRAR: $2,400.00 USD" in letter


def test_auto_learning_loop_on_case_export(tmp_path):
    """Valida que tras exportar los artefactos de un caso resuelto, este se aprenda en la memoria."""
    report = DisputeAnalysisReport(
        case_id="case_auto_learning_test",
        currency="USD",
        billed_amount=Decimal("15000.00"),
        received_amount=Decimal("11000.00"),
        difference=Decimal("-4000.00"),
        root_cause="Descuento comercial no pactado en orden de compra.",
        evidence=["PO acordada con precio fijo"],
        justified_amount=Decimal("0.00"),
        claimable_amount=Decimal("4000.00"),
        confidence=0.98,
        recommended_action="Exigir reintegro inmediato."
    )

    state = DisputeState(
        case_id="case_auto_learning_test",
        objective="Auditar caso auto learning",
        loaded_documents={
            "invoice": type("Obj", (), {"invoice_id": "INV-AL-01", "vendor_id": "CORP-A", "customer_id": "COSTCO_WHOLESALE"})(),
            "payment": type("Obj", (), {"payment_id": "PAY-AL-01", "deductions": []})(),
            "contract": type("Obj", (), {"contract_id": "CTR-COSTCO", "clauses": [type("Cl", (), {"clause_id": "CLAUSE-3.2"})()]})()
        }
    )

    # Exportar artefactos (activa el auto-aprendizaje)
    files = export_dispute_artifacts(report=report, state=state)
    assert "markdown_report" in files

    # Verificar que el nuevo precedente fue registrado en la red persistente
    net = DisputeMemoryNetwork()
    costco_precedents = net.get_precedents_by_retailer("COSTCO_WHOLESALE")
    learned_case_ids = [p.case_id for p in costco_precedents]
    assert "case_auto_learning_test" in learned_case_ids


def test_api_precedents_endpoints():
    """Valida los endpoints REST /api/precedents/profiles, /match y /all."""
    # 1. Perfiles de Retailer
    res_prof = client.get("/api/precedents/profiles")
    assert res_prof.status_code == 200
    data_prof = res_prof.json()
    assert data_prof["status"] == "success"
    assert data_prof["total_retailers"] >= 1
    assert any("WALMART" in p["retailer_id"] for p in data_prof["profiles"])

    # 2. Matching de Precedentes
    res_match = client.get("/api/precedents/match", params={
        "retailer_id": "WALMART_MEXICO",
        "dispute_type": "penalizacion ASN en muelle",
        "deduction_code": "DED-ASN-PENALTY"
    })
    assert res_match.status_code == 200
    data_match = res_match.json()
    assert data_match["status"] == "success"
    assert data_match["matches_count"] >= 1
    assert "Antecedentes y Precedentes" in data_match["formatted_letter_block"]

    # 3. Lista completa de precedentes
    res_all = client.get("/api/precedents/all")
    assert res_all.status_code == 200
    data_all = res_all.json()
    assert data_all["total_precedents"] >= 5
