"""
tests/test_phase9_cap_and_zkp.py
Pruebas exhaustivas para el Sprint 9.2:
- Conexión de ContractualCapEnforcer en reconcile_dispute_data y SanityGateEngine (Filtro 5).
- Auto-truncamiento con precisión Decimal ($0.00 MAE).
- Expansión Multi-Divisa (USD, MXN, EUR, €) en ZKPFinancialAuditor.
- Reconocimiento de Cifras Derivadas Legítimas (Intereses Art. 362 CCom, Topes, Impuestos y NPV).
"""

import pytest
from decimal import Decimal
from datetime import datetime, timezone

from data.models import (
    Invoice,
    InvoiceItem,
    PurchaseOrder,
    PurchaseOrderItem,
    DeliveryNote,
    DeliveryItem,
    PaymentReceipt,
    PaymentDeduction,
    CommercialContract,
    ContractClause,
    DisputeAnalysisReport,
    ZKPFinancialProof,
)
from tools.contract_analyzer.rules import ContractualCapEnforcer
from tools.reconciliation_engine.engine import reconcile_dispute_data
from agent.guardrails.sanity_gate import SanityGateEngine, SanityGateAuditResult
from agent.guardrails.arithmetic_verifier import (
    extract_monetary_figures,
    collect_valid_ground_truth_figures,
    ZKPFinancialAuditor,
)

Contract = CommercialContract


def test_contractual_cap_enforcer_multi_clause():
    """Valida que ContractualCapEnforcer.enforce_caps seleccione y aplique el tope contractual."""
    clauses = [
        ContractClause(
            clause_id="CL-6.1",
            title="Entrega",
            text="La entrega se realizará en el CEDIS pactado.",
            policy="LOGISTICA"
        ),
        ContractClause(
            clause_id="CL-7.4",
            title="Penalizaciones OTIF",
            text="En caso de demora, la penalización máxima no excederá el 3% del valor facturado.",
            policy="PENALIZACIONES"
        ),
    ]
    base_inv = Decimal("100000.00")
    deductions = [
        PaymentDeduction(code="OTIF", reason="Demora en entrega", amount=Decimal("7500.00"))
    ]

    allowed, excess, audits = ContractualCapEnforcer.enforce_caps(
        clauses=clauses,
        base_amount=base_inv,
        deductions_or_amount=deductions
    )

    assert allowed == Decimal("3000.00")
    assert excess == Decimal("4500.00")
    assert (allowed + excess) == Decimal("7500.00")
    assert len(audits) == 1
    assert audits[0].is_cap_exceeded is True
    assert audits[0].clause_id == "CL-7.4"


def test_reconcile_dispute_data_with_contract_cap_truncation():
    """Valida que reconcile_dispute_data trunque deducciones excesivas cuando se le pasa el contrato."""
    inv = Invoice(
        invoice_id="INV-CAP-001",
        vendor_id="VEND-01",
        customer_id="CUST-01",
        issue_date="2026-10-01",
        currency="USD",
        items=[
            InvoiceItem(item_id="SKU-1", description="Servidor Rack", quantity=10, unit_price=Decimal("10000.00"), total_price=Decimal("100000.00"))
        ],
        subtotal=Decimal("100000.00"),
        total_amount=Decimal("100000.00")
    )
    po = PurchaseOrder(
        po_id="PO-CAP-001",
        vendor_id="VEND-01",
        customer_id="CUST-01",
        order_date="2026-09-20",
        currency="USD",
        items=[
            PurchaseOrderItem(item_id="SKU-1", description="Servidor Rack", ordered_quantity=10, agreed_unit_price=Decimal("10000.00"), total_price=Decimal("100000.00"))
        ],
        total_amount=Decimal("100000.00")
    )
    deliv = DeliveryNote(
        delivery_id="REM-CAP-001",
        po_reference="PO-CAP-001",
        delivery_date="2026-10-03",
        received_by="Andén Central",
        warehouse_location="CEDIS Norte",
        signed=True,
        discrepancy_reported=False,
        items=[
            DeliveryItem(item_id="SKU-1", quantity_delivered=10, quantity_received=10, missing_quantity=0, damaged_quantity=0)
        ]
    )
    # Deducción comercial convenida de $8,000 en el comprobante
    pay = PaymentReceipt(
        payment_id="PAY-CAP-001",
        invoice_reference="INV-CAP-001",
        payment_date="2026-10-15",
        currency="USD",
        amount_paid=Decimal("92000.00"),
        deductions=[
            PaymentDeduction(code="AJUSTE-COMERCIAL", reason="Descuento comercial por volumen convenido", amount=Decimal("8000.00"))
        ]
    )
    # Contrato con tope del 5% sobre factura
    contract = CommercialContract(
        contract_id="CTR-CAP-001",
        vendor_id="VEND-01",
        customer_id="CUST-01",
        valid_from="2026-01-01",
        valid_to="2026-12-31",
        clauses=[
            ContractClause(
                clause_id="CL-CAP-5",
                title="Tope de Rebate Comercial",
                text="Cualquier cargo o ajuste comercial tendrá un tope máximo del 5% del valor total facturado.",
                policy="DESCUENTOS"
            )
        ]
    )

    summary = reconcile_dispute_data(
        invoice=inv,
        purchase_order=po,
        delivery=deliv,
        payment=pay,
        contract=contract
    )

    # Factura $100,000, 5% tope = $5,000 permitido.
    # Los $3,000 excedentes pasan de justificado a injustificado
    assert summary.justified_deductions_amount == Decimal("5000.00")
    assert summary.unjustified_deductions_amount == Decimal("3000.00")
    assert (summary.justified_deductions_amount + summary.unjustified_deductions_amount) == Decimal("8000.00")
    assert any("Tope contractual aplicado" in ev for ev in summary.evidence_trail)


def test_sanity_gate_filtro_5_contractual_cap():
    """Valida la ejecución del Filtro 5 en SanityGateEngine reforzando el reporte."""
    report = DisputeAnalysisReport(
        case_id="case_test_cap_gate",
        currency="USD",
        billed_amount=Decimal("200000.00"),
        received_amount=Decimal("170000.00"),
        difference=Decimal("-30000.00"),  # $30,000 retenidos
        root_cause="Penalización por merma operativa.",
        evidence=["Recibo de pago"],
        justified_amount=Decimal("30000.00"),  # Inicialmente justificado $30,000
        claimable_amount=Decimal("0.00"),
        confidence=0.95,
        recommended_action="Conciliar."
    )
    # Contrato con tope de tolerancia de merma del 4% ($8,000 USD sobre $200,000)
    contract = CommercialContract(
        contract_id="CTR-MERMA-001",
        vendor_id="VEND-01",
        customer_id="CUST-01",
        valid_from="2026-01-01",
        valid_to="2026-12-31",
        clauses=[
            ContractClause(
                clause_id="CL-4.2",
                title="Tolerancia de Merma",
                text="El cliente aceptará una tolerancia de merma de hasta un 4% sobre la facturación bruta.",
                policy="OPERACION"
            )
        ]
    )
    docs = {"contract": contract}

    result: SanityGateAuditResult = SanityGateEngine.audit_and_reinforce_case(report, docs=docs)

    assert result.contractual_cap_enforced is True
    # Tope 4% de $200,000 = $8,000 USD permitido.
    # Excedente = $30,000 - $8,000 = $22,000 USD reclamables
    assert result.contractual_cap_excess_claimed == Decimal("22000.00")
    assert report.justified_amount == Decimal("8000.00")
    assert report.claimable_amount == Decimal("22000.00")
    # Invariante contable estricta
    assert (report.justified_amount + report.claimable_amount) == abs(report.difference)
    assert any("Filtro 5 (Tope Contractual" in n for n in result.audit_notes)


def test_zkp_multi_currency_extraction():
    """Valida la extracción exacta de montos en USD, MXN, EUR y símbolos € / $."""
    sample = (
        "Se aplicó retención de $12,500.00 USD, equivalente a 225000.00 pesos en moneda local "
        "y un sobrecargo logístico de €1,450.50 euros por maniobra transfronteriza de 850 MXN."
    )
    extracted = extract_monetary_figures(sample)
    vals = [val for _, val in extracted]

    assert Decimal("12500.00") in vals
    assert Decimal("225000.00") in vals
    assert Decimal("1450.50") in vals
    assert Decimal("850.00") in vals


def test_zkp_legitimate_derived_figures_acceptance():
    """Valida que ZKPFinancialAuditor reconozca como legítimas las cifras derivadas (Art. 362 CCom, Caps, IVA, NPV)."""
    claimable = Decimal("10000.00")
    # 9% de interés anual Art. 362 CCom = $900.00
    # Prorrateo 30 días Art. 362 = $10,000 * 0.09 * 30 / 360 = $75.00
    # Subtotal sin IVA 16% = $10,000 / 1.16 = $8,620.69
    # IVA 16% = $1,379.31
    report = DisputeAnalysisReport(
        case_id="case_zkp_derived",
        currency="USD",
        billed_amount=Decimal("50000.00"),
        received_amount=Decimal("40000.00"),
        difference=Decimal("-10000.00"),
        root_cause=(
            "Retención unilateral de $10,000.00 USD. "
            "El interés moratorio anual según el Art. 362 CCom es de $900.00 USD (o $75.00 USD a 30 días), "
            "con un subtotal base de $8,620.69 USD y un IVA 16% de $1,379.31 USD."
        ),
        evidence=["Factura SAT"],
        justified_amount=Decimal("0.00"),
        claimable_amount=claimable,
        confidence=0.98,
        recommended_action="Exigir pago inmediato de $10,000.00 USD más intereses estatutarios de $900.00 USD."
    )

    proof: ZKPFinancialProof = ZKPFinancialAuditor.audit_report(report)

    # No debe considerarse alucinación, ya que son cifras matemáticas derivadas válidas
    assert proof.text_hallucination_detected is False
    assert proof.audit_status == "MATHEMATICALLY_PROVEN"
    assert proof.confidence_penalty == 0.0


def test_zkp_still_rejects_genuine_hallucinations():
    """Valida que ZKPFinancialAuditor siga interceptando números totalmente inventados."""
    report = DisputeAnalysisReport(
        case_id="case_zkp_hallucination",
        currency="USD",
        billed_amount=Decimal("50000.00"),
        received_amount=Decimal("40000.00"),
        difference=Decimal("-10000.00"),
        root_cause="Retención de $10,000.00 USD, pero el comprador exige indemnización absurda de $88,777.00 USD.",
        evidence=[],
        justified_amount=Decimal("0.00"),
        claimable_amount=Decimal("10000.00"),
        confidence=0.98,
        recommended_action="Cobrar saldo."
    )

    proof: ZKPFinancialProof = ZKPFinancialAuditor.audit_report(report)

    assert proof.text_hallucination_detected is True
    assert proof.audit_status == "HALLUCINATION_INTERCEPTED"
    assert any("88777" in fig for fig in proof.detected_hallucinated_figures)
    assert proof.confidence_penalty > 0.0
