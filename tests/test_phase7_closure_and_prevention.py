"""
tests/test_phase7_closure_and_prevention.py
Suite de pruebas unitarias e integrales para la Fase 7:
Superinteligencia Operativa, Prevención Causa Raíz y Cierre Financiero (Sprints 7.1 a 7.5).
Valida US-701 a US-710 con precisión estricta Decimal ($0.00 MAE).
"""

from decimal import Decimal
from pathlib import Path
from fastapi.testclient import TestClient

from api.main import app
from agent.core.dispute_sla_watchdog import DisputeSlaWatchdog
from agent.core.bank_remittance_reconciler import BankRemittanceReconciler
from agent.core.relational_health_engine import RelationalHealthEngine
from agent.core.bilateral_negotiation_engine import BilateralNegotiationEngine
from agent.core.root_cause_analyzer import RootCauseAnalyzer
from agent.core.capa_ticket_generator import CapaTicketGenerator

client = TestClient(app)


def test_sprint_7_1_sla_watchdog_and_art_1041_interruption():
    """
    Valida US-701 y US-702:
    - Ventanas de caducidad SLA por Retailer (Amazon 30d, Walmart 90d, Soriana 60d, General 120d).
    - Clasificación del semáforo de urgencia (CRITICAL_EXPIRED, HIGH_IMMINENT, MEDIUM_ATTENTION, LOW_HEALTHY).
    - Emisión de Notificación Formal de Interrupción de Prescripción (Art. 1041 CCom) con hash SHA-256.
    """
    # 1. Evaluar Amazon Shortage (ventana 30d) con distintos días transcurridos
    st_healthy = DisputeSlaWatchdog.evaluate_case_sla("case_001", simulated_elapsed_days=40)
    assert st_healthy.contractual_sla_days == 120
    assert st_healthy.days_to_expiration == 80
    assert st_healthy.urgency_level == "LOW_HEALTHY"

    st_medium = DisputeSlaWatchdog.evaluate_case_sla("case_006_walmart_otif_pricing", simulated_elapsed_days=70)
    assert st_medium.contractual_sla_days == 90
    assert st_medium.days_to_expiration == 20
    assert st_medium.urgency_level == "MEDIUM_ATTENTION"

    st_imminent = DisputeSlaWatchdog.evaluate_case_sla("case_005_amazon_shortage", simulated_elapsed_days=23)
    assert st_imminent.contractual_sla_days == 30
    assert st_imminent.days_to_expiration == 7
    assert st_imminent.urgency_level == "HIGH_IMMINENT"

    st_expired = DisputeSlaWatchdog.evaluate_case_sla("case_009_mega_retailer_dispute", simulated_elapsed_days=65)
    assert st_expired.contractual_sla_days == 60
    assert st_expired.days_to_expiration == -5
    assert st_expired.urgency_level == "CRITICAL_EXPIRED"

    # 2. Emitir Aviso de Interrupción de Prescripción Art. 1041 CCom (US-702)
    notice = DisputeSlaWatchdog.issue_prescription_interruption_notice(
        case_id="case_005_amazon_shortage",
        operator_name="Lic. Roberto Villarreal (Director Jurídico)",
        simulated_elapsed_days=23
    )
    assert notice.notice_id.startswith("INT-1041-")
    assert len(notice.forensic_hash_sha256) == 64
    assert "Artículo 1041 del Código de Comercio" in notice.notice_markdown
    assert Path(notice.file_path).exists()

    # Verificar que el estado del caso ahora reporta prescripción interrumpida/congelada
    st_after = DisputeSlaWatchdog.evaluate_case_sla("case_005_amazon_shortage", simulated_elapsed_days=23)
    assert st_after.is_prescription_interrupted is True
    assert st_after.interruption_folio == notice.notice_id


def test_sprint_7_2_edi820_parser_and_three_way_settlement_matcher():
    """
    Valida US-703 y US-704:
    - Generación y parseo de estado de remesa bancaria EDI 820 y CSV bancario.
    - Ecuación exacta del 3-Way Settlement Matcher con precisión Decimal ($0.00 MAE):
      Factura Original - Deducción Retailer + Monto Recuperado Convenio = Depósito Neto Bancario.
    - Emisión del Certificado de Cierre y Liquidación de Cartera ($0.00 saldo insoluto).
    """
    case_id = "case_005_amazon_shortage"
    raw_edi820 = BankRemittanceReconciler.generate_case_edi820_payload(case_id)
    assert "ST*820" in raw_edi820
    assert "BPR*I*" in raw_edi820
    assert "RMR*IV*" in raw_edi820

    remittance, match_res, certificate = BankRemittanceReconciler.execute_three_way_settlement_match(
        case_id=case_id,
        raw_remittance_content=raw_edi820
    )

    assert isinstance(match_res.original_invoice_amount, Decimal)
    assert isinstance(match_res.total_disputed_deduction, Decimal)
    assert isinstance(match_res.agreed_settlement_recovery, Decimal)
    assert isinstance(match_res.actual_bank_remittance_cash, Decimal)

    # Verificar invariante US-704:
    # Factura Original - Deducción Retailer + Monto Recuperado Convenio = Depósito Neto Bancario
    calculated_net = (
        match_res.original_invoice_amount
        - match_res.total_disputed_deduction
        + match_res.agreed_settlement_recovery
    )
    assert calculated_net == match_res.actual_bank_remittance_cash
    assert match_res.residual_balance_variance == Decimal("0.00")
    assert match_res.mae_precision == Decimal("0.00")
    assert match_res.is_perfect_match is True
    assert match_res.match_status == "CLOSED_ZERO_BALANCE"

    # Verificar Certificado de Cierre y Liquidación de Cartera
    assert certificate.final_open_balance == Decimal("0.00")
    assert certificate.status == "LIQUIDATED_CLOSED"
    assert len(certificate.zkp_clearance_hash_sha256) == 64
    assert Path(certificate.file_path).exists()

    # Verificar soporte de CSV bancario
    csv_payload = (
        "invoice_id,gross_amount,deduction_amount,recovered_amount,credit_memo,net_deposit,trn_reference\n"
        "INV-CSV-901,50000.00,10000.00,8000.00,2000.00,48000.00,SPEI-CSV-202699\n"
    )
    csv_remit = BankRemittanceReconciler.parse_remittance_payload(csv_payload, case_id="case_001")
    assert csv_remit.raw_format == "BANK_CSV"
    assert csv_remit.total_gross_amount == Decimal("50000.00")
    assert csv_remit.net_bank_deposit == Decimal("48000.00")


def test_sprint_7_3_relational_health_index_and_negotiation_modulation():
    """
    Valida US-705 y US-706:
    - Cálculo del Relationship Health Index (RHI 0-100 pts) con LTV, Share of Wallet, Margen y Reciprocidad.
    - Modulación dinámica:
      * DIPLOMATIC_PRESERVATION (RHI > 80)
      * FIRM_COMMERCIAL (RHI 50-80)
      * ASSERTIVE_LITIGIOUS (RHI < 50)
    - Acoplamiento directo con BilateralNegotiationEngine.
    """
    # 1. RHI > 80 -> DIPLOMATIC_PRESERVATION (ej. Walmart / Amazon Tier-1)
    rhi_high = RelationalHealthEngine.evaluate_relational_health("case_006_walmart_otif_pricing")
    assert rhi_high.rhi_score > 80.0
    assert rhi_high.modulation_mode == "DIPLOMATIC_PRESERVATION"
    assert rhi_high.churn_risk_level == "LOW_STRATEGIC"

    # 2. RHI 50-80 -> FIRM_COMMERCIAL (ej. Home Depot / Soriana Tier-2)
    rhi_mid = RelationalHealthEngine.evaluate_relational_health("case_008_homedepot_damaged_scanned")
    assert 50.0 <= rhi_mid.rhi_score <= 80.0
    assert rhi_mid.modulation_mode == "FIRM_COMMERCIAL"

    # 3. RHI < 50 -> ASSERTIVE_LITIGIOUS (ej. Distribuidor de bajo margen o override < 50)
    rhi_low = RelationalHealthEngine.evaluate_relational_health("case_004", override_rhi_score=32.0)
    assert rhi_low.rhi_score == 32.0
    assert rhi_low.modulation_mode == "ASSERTIVE_LITIGIOUS"
    assert rhi_low.recommended_max_concession_pct == 0.0

    # 4. Verificar que BilateralNegotiationEngine inyecta el RHI y bloquea concesiones en ASSERTIVE_LITIGIOUS
    duel_litigious = BilateralNegotiationEngine.start_duel(
        case_id="case_004",
        governance_mode="HUMAN_GATEKEEPER",
        override_rhi_score=30.0
    )
    assert duel_litigious.rhi_score == 30.0
    assert duel_litigious.modulation_mode == "ASSERTIVE_LITIGIOUS"
    assert duel_litigious.delegation_limit_pct == 0.0
    assert duel_litigious.delegation_limit_amount == Decimal("0.00")


def test_sprint_7_4_longitudinal_rca_and_capa_tickets():
    """
    Valida US-707 y US-708:
    - Análisis longitudinal de Causa Raíz (RCA) sobre los 50 casos de benchmark hacia los 4 departamentos:
      WAREHOUSE_CEDIS, TRANSPORT_LOGISTICS, SYSTEMS_EDI, SALES_COMMERCIAL.
    - Generación y persistencia de Tickets CAPA en reports/capa/ con responsable y checklist pre-despacho.
    """
    rca_report = RootCauseAnalyzer.analyze_fleet_root_causes(target_benchmark_size=50)
    assert rca_report.total_cases_analyzed >= 50
    assert rca_report.total_fleet_disputed_usd > Decimal("0.00")
    assert rca_report.total_preventable_leakage_usd > Decimal("0.00")
    assert len(rca_report.department_attributions) == 4

    dept_codes = {d.department_code for d in rca_report.department_attributions}
    assert dept_codes == {"WAREHOUSE_CEDIS", "TRANSPORT_LOGISTICS", "SYSTEMS_EDI", "SALES_COMMERCIAL"}

    # Suma exacta de fugas por departamento == fuga prevenible total de la flota
    sum_dept_leakage = sum((d.total_financial_leakage_usd for d in rca_report.department_attributions), Decimal("0.00"))
    assert sum_dept_leakage == rca_report.total_preventable_leakage_usd

    # Generar Ticket CAPA para un caso real (US-708)
    capa = CapaTicketGenerator.generate_capa_ticket("case_005_amazon_shortage")
    assert capa.ticket_id.startswith("CAPA-2026-")
    assert capa.department_code in dept_codes
    assert len(capa.corrective_actions) >= 3
    assert len(capa.pre_dispatch_checklist) >= 3
    assert Path(capa.file_path).exists()


def test_sprint_7_5_fastapi_remittance_and_capa_endpoints():
    """Valida todos los endpoints REST de la Fase 7 en /api/remittance/*."""
    case_id = "case_005_amazon_shortage"

    # 1. SLA Status
    res_sla = client.get(f"/api/remittance/sla/{case_id}")
    assert res_sla.status_code == 200
    assert res_sla.json()["sla_status"]["case_id"] == case_id

    # 2. Emitir Interrupción Art. 1041 CCom
    res_int = client.post(
        f"/api/remittance/sla/{case_id}/interrupt",
        json={"operator_name": "Auditor Fiscal B2B"}
    )
    assert res_int.status_code == 200
    assert res_int.json()["sla_status"]["is_prescription_interrupted"] is True

    # 3. Conciliación 3-Way EDI 820
    res_rec = client.post(f"/api/remittance/reconcile/{case_id}", json={})
    assert res_rec.status_code == 200
    rec_json = res_rec.json()
    assert rec_json["three_way_match"]["is_perfect_match"] is True
    assert rec_json["three_way_match"]["mae_precision"] == 0.0
    assert rec_json["clearance_certificate"]["final_open_balance"] == 0.0

    # 4. Salud Relacional RHI
    res_rhi = client.get(f"/api/remittance/relational-health/{case_id}")
    assert res_rhi.status_code == 200
    assert res_rhi.json()["relational_health"]["rhi_score"] > 0

    # 5. RCA Longitudinal y Ticket CAPA
    res_rca = client.get("/api/remittance/rca-fleet?target_benchmark_size=50")
    assert res_rca.status_code == 200
    assert res_rca.json()["rca_report"]["total_cases_analyzed"] >= 50

    res_capa = client.post(f"/api/remittance/capa/{case_id}", json={})
    assert res_capa.status_code == 200
    assert res_capa.json()["capa_ticket"]["ticket_id"].startswith("CAPA-2026-")
