"""
tests/test_phase9_forensic_engines.py
Suite de verificación pericial forense para el Sprint 9.5:
- HU 9.5.1: Careo Judicial Específico por Evidencia en AdversarialCourtroomEngine.
- HU 9.5.2: Inspección Visual Sincronizada por Caso en PalletVisionAuditor.
- HU 9.5.3: Sincronización de Portales RPA con Casos Reales y PreDispatchLeakageRadar Conectado.
"""

from decimal import Decimal
import pytest

from agent.courtroom.models import AdversarialRole, AdversarialVerdict
from agent.courtroom.adversarial_engine import AdversarialCourtroomEngine
from agent.vision.pallet_vision_auditor import PalletVisionAuditor, CargoIntegrityCertificate
from agent.portal.retailer_portal_agent import RetailerPortalAgent, PortalSyncResult
from agent.predictive.leakage_radar import PreDispatchLeakageRadar, DviPredictionResult
from agent.core.concession_engine import ConcessionEngine
from tools.document_reader.reader import load_case_documents


def test_adversarial_courtroom_forensic_evidence_citation():
    """Valida que el careo judicial cite folios de factura, remisión, pago y cláusulas contractuales reales."""
    case_id = "case_005_amazon_shortage"
    report = ConcessionEngine.get_or_create_base_report(case_id)
    docs = load_case_documents(case_id)

    verdict = AdversarialCourtroomEngine.conduct_debate(report=report, docs=docs)

    assert isinstance(verdict, AdversarialVerdict)
    assert verdict.case_id == case_id
    assert verdict.disputed_amount > Decimal("0.00")

    # Verificar que el Fiscal cite la remisión real y la factura real
    all_pros_text = " ".join(a.argument_text for a in verdict.prosecutor_arguments)
    assert "BOL-POD-77319" in all_pros_text or "INV-PAC-2026-4402" in all_pros_text
    assert "AMAZON_ONT8_FULFILLMENT_CENTER" in all_pros_text or "muelle" in all_pros_text.lower()

    # Verificar que el Defensor invoque el contrato bilateral y fundamento legal
    all_def_text = " ".join(a.argument_text for a in verdict.advocate_counterarguments)
    all_def_grounds = " ".join(a.legal_or_contractual_ground for a in verdict.advocate_counterarguments)
    assert "MSA-AMZ-PAC-2026" in all_def_text or "bilateral" in all_def_text.lower()
    assert "Art. 88" in all_def_grounds or "Código de Comercio" in all_def_grounds or "1043" in all_def_grounds

    # Verificar que el Magistrado incluya folios y reloj SLA en su resumen
    assert "INV-PAC-2026-4402" in verdict.magistrate_summary_ruling
    assert "BOL-POD-77319" in verdict.magistrate_summary_ruling
    assert "SLA" in verdict.magistrate_summary_ruling or "Fuerza probatoria" in verdict.magistrate_summary_ruling
    assert verdict.probative_force_supplier_pct >= 80.0


def test_adversarial_courtroom_walmart_pricing_citation():
    """Valida el careo forense sobre case_006_walmart_otif_pricing con retenciones de precio y pronto pago."""
    case_id = "case_006_walmart_otif_pricing"
    report = ConcessionEngine.get_or_create_base_report(case_id)
    docs = load_case_documents(case_id)

    verdict = AdversarialCourtroomEngine.conduct_debate(report=report, docs=docs)

    assert verdict.case_id == case_id
    # Verificar que se desestimen retenciones unilaterales
    assert len(verdict.dismissed_objections) >= 1
    assert any("RECLAMABLE" in obj or "IMPROCEDENTE" in obj for obj in verdict.dismissed_objections)

    # Verificar mención a folios en el dictamen del magistrado
    assert "INV-NDP-88301" in verdict.magistrate_summary_ruling
    assert "REC-MMN-33019" in verdict.magistrate_summary_ruling


def test_pallet_vision_auditor_case_inspection():
    """Valida la inspección multimodal sincronizada con los documentos reales de case_005."""
    case_id = "case_005_amazon_shortage"

    # Inspección de tarima normal sin daño forzado
    cert = PalletVisionAuditor.inspect_pallet_for_case(case_id, simulate_damage=False)
    assert isinstance(cert, CargoIntegrityCertificate)
    assert cert.case_reference == case_id
    assert cert.dock_location == "AMAZON_ONT8_FULFILLMENT_CENTER"
    assert cert.pallet_audit.total_boxes_detected == 140  # 100 + 40 unidades recibidas
    assert cert.overall_verdict == "CARGO_PRISTINE_ACCEPTED"
    assert cert.seal_audit.is_seal_matched is True
    assert cert.pallet_audit.damaged_boxes_count == 0
    assert len(cert.forensic_sha256_hash) == 64

    # Inspección con simulación de daño
    cert_dmg = PalletVisionAuditor.inspect_pallet_for_case(case_id, simulate_damage=True)
    assert cert_dmg.overall_verdict == "IRREGULARITY_FLAGGED"
    assert cert_dmg.seal_audit.is_seal_matched is False
    assert cert_dmg.seal_audit.seal_status == "TAMPERED_BROKEN"
    assert cert_dmg.pallet_audit.damaged_boxes_count >= 2
    assert any(b.status == "ANOMALY_FLAGGED" for b in cert_dmg.bounding_boxes)


def test_retailer_portal_agent_dynamic_case_sync():
    """Valida la sincronización RPA que descubre casos reales en data/cases."""
    # Sincronización Walmart
    res_wm = RetailerPortalAgent.sync_retailer_portal("WALMART_RETAIL_LINK", max_items=5)
    assert isinstance(res_wm, PortalSyncResult)
    assert res_wm.total_deductions_found >= 2
    assert res_wm.currency == "MXN"
    # Debe haber al menos una partida real de Walmart sincronizada
    assert any("WAL" in d.deduction_id or "WM" in d.deduction_id for d in res_wm.deductions)
    assert any(d.dispute_deadline != "" for d in res_wm.deductions)

    # Sincronización Amazon
    res_amz = RetailerPortalAgent.sync_retailer_portal("AMAZON_VENDOR_CENTRAL", max_items=5)
    assert res_amz.currency == "USD"
    assert any("SHORTAGE" in d.deduction_code for d in res_amz.deductions)


def test_pre_dispatch_leakage_radar_rca_and_precedent_coupling():
    """Valida que el Radar Preventivo DVI integre Causa Raíz (RCA) y Precedentes Históricos."""
    res = PreDispatchLeakageRadar.evaluate_purchase_order(
        po_reference="PO-WM-PREVENT-01",
        retailer_id="WALMART_MEXICO",
        destination_dc="WALMART_DC_6014",
        total_amount=Decimal("120000.00"),
        estimated_transit_hours=4.0,
        appointment_window_hours=2.0,
        agreed_catalog_price_match=True,
        contract_has_unilateral_penalty=True
    )

    assert isinstance(res, DviPredictionResult)
    assert res.dvi_score >= 50.0

    # Debe contener el factor de riesgo RCA predictivo incorporado en HU 9.5.3
    factor_ids = [rf.factor_id for rf in res.risk_factors]
    assert "RF-RCA-PREDICTIVE" in factor_ids

    # Las salvaguardas deben incluir el protocolo correctivo
    safeguards_text = " ".join(res.pre_dispatch_safeguards)
    assert len(safeguards_text) > 50
    assert "EDI 856" in safeguards_text
