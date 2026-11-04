"""
tests/test_phase8_superagent.py
Suite de pruebas unitarias e integrales para la Fase 8 (Superagente B2B Autónomo):
- Sprint 8.1: Unificación de 15 Súper-Herramientas en el Bucle ReAct (TOOL_DEFINITIONS & ToolExecutor)
- Sprint 8.2: Conciliación Multi-Entrega (Split Shipments N:M), Conversor UoM (CA <-> EA) y Cross-SKU
- Sprint 8.3: Auditor de Topes Porcentuales y Franquicias Contractuales (ContractualCapEnforcer)
- Sprint 8.4: Auto-Corrección Algebraica de OCR y PDFs Escaneados (OpticalMathHealer)
- Sprint 8.5: Memoria Episódica Auto-Evolutiva en SQLite (Closed-Loop Precedent Learning)
- Sprint 8.6: Careo Adversarial Contextual Anclado a Cláusulas y Modo RHI
"""

from decimal import Decimal
from agent.core.state import DisputeState
from agent.memory.audit_logger import AuditLogger
from agent.tools.registry import TOOL_DEFINITIONS, ToolExecutor
from tools.document_reader.reader import consolidate_partial_deliveries
from tools.reconciliation_engine.engine import reconcile_dispute_data
from tools.contract_analyzer.rules import ContractualCapEnforcer
from tools.document_reader.pdf_parser import OpticalMathHealer
from agent.memory.precedent_graph import DisputeMemoryNetwork
from agent.core.skynet_runner import SkynetRunner
from agent.core.bilateral_negotiation_engine import BilateralNegotiationEngine
from data.models import (
    Invoice,
    InvoiceItem,
    PurchaseOrder,
    PurchaseOrderItem,
    DeliveryNote,
    DeliveryItem,
    PaymentReceipt,
    PaymentDeduction,
)


def test_sprint_8_1_unified_15_react_super_tools():
    """Valida que TOOL_DEFINITIONS exponga las 15 herramientas y ToolExecutor las ejecute sin errores."""
    # Fase 9 amplió el arsenal a 18; las 15 de Fase 8 deben seguir presentes.
    assert len(TOOL_DEFINITIONS) >= 15
    tool_names = {t["function"]["name"] for t in TOOL_DEFINITIONS}
    expected_new_tools = {
        "audit_cross_border_fx_and_incoterms",
        "audit_edi_856_asn_compliance",
        "evaluate_dispute_sla_and_interrupt_prescription",
        "reconcile_edi820_bank_remittance",
        "evaluate_relational_health_rhi",
        "generate_preventive_capa_ticket",
        "run_bilateral_negotiation_duel",
        "dispatch_dossier_to_retailer_portal",
        "generate_erp_accounting_and_cfdi_payload",
    }
    assert expected_new_tools.issubset(tool_names)

    case_id = "case_005_amazon_shortage"
    state = DisputeState(case_id=case_id, objective="Auditar integralmente")
    logger = AuditLogger(case_id=case_id)
    executor = ToolExecutor(state=state, audit_logger=logger)

    res_sla = executor.execute_tool(
        "evaluate_dispute_sla_and_interrupt_prescription",
        {"case_id": case_id, "issue_interruption_notice": True}
    )
    assert res_sla["status"] == "success"
    assert res_sla["sla_status"]["is_prescription_interrupted"] is True

    res_820 = executor.execute_tool("reconcile_edi820_bank_remittance", {"case_id": case_id})
    assert res_820["status"] == "success"
    assert res_820["three_way_match"]["is_perfect_match"] is True

    res_rhi = executor.execute_tool("evaluate_relational_health_rhi", {"case_id": case_id})
    assert res_rhi["status"] == "success"
    assert res_rhi["relational_health"]["rhi_score"] > 0

    res_capa = executor.execute_tool("generate_preventive_capa_ticket", {"case_id": case_id})
    assert res_capa["status"] == "success"
    assert res_capa["capa_ticket"]["ticket_id"].startswith("CAPA-2026-")


def test_sprint_8_2_multi_delivery_split_shipments_and_uom_cross_sku():
    """
    Valida US-803 y US-804:
    1. Consolidación de entregas parciales (3 camiones) sin generar falsos faltantes.
    2. Conversión automática de Unidades de Medida (Cajas Master x12 vs Piezas EA) y Cross-SKU
       (SKU-NVME-500 vs WM-NVME-500) con precisión Decimal ($0.00 MAE).
    """
    # 1. Consolidar 2 entregas parciales de una orden de 100 unidades (60 en camión 1 + 40 en camión 2)
    deliv_1 = DeliveryNote(
        delivery_id="DEL-PART-01",
        po_reference="PO-SPLIT-100",
        delivery_date="2026-04-01",
        received_by="Muelle Norte T1",
        warehouse_location="CEDIS_MTY",
        signed=True,
        discrepancy_reported=False,
        items=[
            DeliveryItem(
                item_id="WM-PRO-900",
                quantity_delivered=60,
                quantity_received=60,
                missing_quantity=0,
                damaged_quantity=0,
                notes="Camión 1 de 2 (Piezas EA)",
            )
        ],
    )
    deliv_2 = DeliveryNote(
        delivery_id="DEL-PART-02",
        po_reference="PO-SPLIT-100",
        delivery_date="2026-04-02",
        received_by="Muelle Norte T2",
        warehouse_location="CEDIS_MTY",
        signed=True,
        discrepancy_reported=False,
        items=[
            DeliveryItem(
                item_id="WM-PRO-900",
                quantity_delivered=60,
                quantity_received=60,
                missing_quantity=0,
                damaged_quantity=0,
                notes="Camión 2 de 2 (Piezas EA)",
            )
        ],
    )
    consolidated_deliv = consolidate_partial_deliveries([deliv_1, deliv_2])
    assert consolidated_deliv.delivery_id == "DEL-PART-01+DEL-PART-02"
    assert consolidated_deliv.items[0].quantity_received == 120  # 120 piezas individuales recibidas

    # 2. Factura emitida en 10 Cajas Master x12 piezas ($120.00 por caja = $1,200.00) con código SKU-PRO-900
    inv = Invoice(
        invoice_id="INV-UOM-01",
        vendor_id="VENDOR-01",
        customer_id="WALMART",
        po_reference="PO-SPLIT-100",
        issue_date="2026-04-01",
        currency="USD",
        items=[
            InvoiceItem(
                item_id="SKU-PRO-900",
                description=" Disco Estado Sólido Industrial — Caja Master x12 piezas",
                quantity=10,
                unit_price=Decimal("120.00"),
                total_price=Decimal("1200.00"),
            )
        ],
        subtotal=Decimal("1200.00"),
        tax=Decimal("0.00"),
        total_amount=Decimal("1200.00"),
    )
    po = PurchaseOrder(
        po_id="PO-SPLIT-100",
        vendor_id="VENDOR-01",
        customer_id="WALMART",
        order_date="2026-03-25",
        currency="USD",
        items=[
            PurchaseOrderItem(
                item_id="WM-PRO-900",
                description="Disco Estado Sólido Industrial — Caja Master x12 piezas",
                ordered_quantity=10,
                agreed_unit_price=Decimal("120.00"),
                total_price=Decimal("1200.00"),
            )
        ],
        total_amount=Decimal("1200.00"),
    )
    pay = PaymentReceipt(
        payment_id="PAY-UOM-01",
        invoice_reference="INV-UOM-01",
        payment_date="2026-04-15",
        amount_paid=Decimal("1000.00"),
        currency="USD",
        deductions=[
            PaymentDeduction(
                code="DED-UNILATERAL",
                reason="Retención administrativa unilateral por supuesto faltante",
                amount=Decimal("200.00"),
            )
        ],
    )

    rec_summary = reconcile_dispute_data(inv, po, consolidated_deliv, pay)
    # 10 cajas x 12 piezas == 120 piezas recibidas -> 0 faltante físico
    assert rec_summary.total_missing_amount == Decimal("0.00")
    assert rec_summary.justified_deductions_amount == Decimal("0.00")
    assert rec_summary.unjustified_deductions_amount == Decimal("200.00")
    assert any("Conversión UoM aplicada" in ev for ev in rec_summary.evidence_trail)


def test_sprint_8_3_contractual_cap_enforcer():
    """
    Valida US-805 y US-806:
    Extracción de tope porcentual contractual ('tope máximo del 3%') y partición exacta en Decimal
    entre el cargo permitido y el excedente abusivo reclamable.
    """
    clause_text = (
        "Cláusula 7.4 Penalidades Logísticas OTIF: En caso de retraso en cita de entrega, "
        "el comprador podrá aplicar un cargo administrativo con un tope máximo del 3% sobre "
        "el valor de la factura. Cualquier retención superior será improcedente."
    )
    audit = ContractualCapEnforcer.enforce_deduction_cap(
        clause_id="CL-7.4",
        clause_text=clause_text,
        base_amount=Decimal("100000.00"),
        deduction_applied=Decimal("7500.00"),
    )
    assert audit.is_cap_exceeded is True
    assert audit.cap_percentage == Decimal("3.00")
    assert audit.contractually_allowed_amount == Decimal("3000.00")
    assert audit.unjustified_excess_amount == Decimal("4500.00")
    assert (audit.contractually_allowed_amount + audit.unjustified_excess_amount) == Decimal("7500.00")


def test_sprint_8_4_self_healing_optical_math():
    """
    Valida US-807 y US-808:
    Reconstrucción algebraica determinística cuando el OCR lee erróneamente un dígito
    (ej. cantidad '12' en lugar de '120' con precio $250.00 e importe de línea $30,000.00).
    """
    corrupted_inv = Invoice(
        invoice_id="INV-OCR-99",
        vendor_id="VEND-1",
        customer_id="CUST-1",
        issue_date="2026-05-01",
        currency="USD",
        items=[
            InvoiceItem(
                item_id="SKU-NVME-4TB",
                description="Enterprise SSD",
                quantity=12,  # Dígito '0' perdido por sello en el escaneo (debería ser 120)
                unit_price=Decimal("250.00"),
                total_price=Decimal("30000.00"),
            )
        ],
        subtotal=Decimal("3000.00"),
        tax=Decimal("0.00"),
        total_amount=Decimal("3000.00"),
    )

    healed_inv = OpticalMathHealer.heal_invoice(corrupted_inv)
    assert healed_inv.items[0].quantity == 120
    assert healed_inv.subtotal == Decimal("30000.00")
    assert healed_inv.total_amount == Decimal("30000.00")

    corrupted_deliv = DeliveryNote(
        delivery_id="DEL-OCR-99",
        po_reference="PO-99",
        delivery_date="2026-05-03",
        received_by="Inspector",
        warehouse_location="HUB_1",
        signed=True,
        discrepancy_reported=True,
        items=[
            DeliveryItem(
                item_id="SKU-NVME-4TB",
                quantity_delivered=120,
                quantity_received=100,
                missing_quantity=0,  # OCR omitió el 20 en la columna de faltantes
                damaged_quantity=0,
            )
        ],
    )
    healed_deliv = OpticalMathHealer.heal_delivery_note(corrupted_deliv)
    assert healed_deliv.items[0].missing_quantity == 20


def test_sprint_8_5_and_8_6_closed_loop_memory_and_contextual_duel():
    """
    Valida US-809 y US-810:
    - Al ejecutar SkynetRunner o cerrar un careo bilateral, el precedente se persiste
      automáticamente en la base SQLite de DisputeMemoryNetwork.
    - El careo bilateral inyecta evidencias reales del caso y la directriz RHI.
    """
    runner = SkynetRunner(case_id="case_001", fast_path=True, use_cache=False)
    report = runner.run()
    assert report.billed_amount > Decimal("0.00")

    mem_net = DisputeMemoryNetwork()
    all_precs = mem_net.get_all_precedents()
    assert any(p.case_id == "case_001" for p in all_precs)

    # Verificar inyección de evidencias reales y sufijo RHI en Careo Bilateral
    session = BilateralNegotiationEngine.start_duel(
        case_id="case_006_walmart_otif_pricing",
        governance_mode="HUMAN_GATEKEEPER",
        override_rhi_score=88.0,
    )
    session = BilateralNegotiationEngine.advance_duel_step("case_006_walmart_otif_pricing")
    r2 = session.rounds[-1]
    assert "compromiso recíproco de volumen" in r2.supplier_message
