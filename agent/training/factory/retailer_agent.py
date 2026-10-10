"""
Retailer Buyer Agent (Comprador Retailer).

Agente adversarial con el incentivo económico de maximizar el margen de caja del
comprador mediante deducciones unilaterales, cargos por cumplimiento no pactados,
descuentos por pronto pago no devengados y ajustes de precio.
"""

from decimal import Decimal
from typing import List, Tuple, Optional
from data.models import PaymentReceipt, PaymentDeduction
from agent.training.factory.ground_truth import GroundTruthDeductionAssessment


class RetailerBuyerAgent:
    """
    Genera comprobantes de pago (PaymentReceipt) con deducciones arbitrarias,
    ocultas o legítimas, enfrentando al conciliador con tácticas agresivas de tesorería.
    """

    def __init__(self, retailer_name: str = "RetailCorp S.A. de C.V."):
        self.retailer_name = retailer_name

    def create_shortage_deduction(
        self,
        amount: Decimal,
        reference_doc: str,
        is_pod_signed: bool = True,
        units_missing: int = 10,
        sku: str = "PROD-001"
    ) -> Tuple[PaymentDeduction, GroundTruthDeductionAssessment]:
        """
        Deducción por faltante físico en recepción de mercancía.
        Si el POD está firmado por el transportista, la deducción es JUSTIFICADA (Cláusula 4.2).
        Si el POD NO está firmado o no tiene sello, la deducción carece de sustento probatorio y es RECLAMABLE.
        """
        code = "DED-SHORTAGE"
        reason = f"Deducción por faltante físico de {units_missing} unidades {sku} s/ remisión {reference_doc}"
        deduction = PaymentDeduction(
            code=code,
            reason=reason,
            amount=amount,
            reference_doc=reference_doc
        )
        assessment = GroundTruthDeductionAssessment(
            code=code,
            amount=amount,
            reason=reason,
            is_justified=is_pod_signed,
            governing_clause_id="CLAUSE-4.2",
            factual_basis=(
                f"Faltante físico reportado en remisión {reference_doc} con firma válida."
                if is_pod_signed else
                f"Remisión {reference_doc} carece de firma de recibido o sello de discrepancia; prueba plena inválida."
            ),
            remedy_action="ACCEPT_AND_CREDIT" if is_pod_signed else "REJECT_AND_CLAIM"
        )
        return deduction, assessment

    def create_extemporaneous_damage_deduction(
        self,
        amount: Decimal,
        reference_doc: str,
        days_after_delivery: int = 30,
        sku: str = "PROD-002"
    ) -> Tuple[PaymentDeduction, GroundTruthDeductionAssessment]:
        """
        Deducción extemporánea por mercancía averiada reportada semanas después de la entrega
        violando el plazo contractual de 48 horas y la obligación de aportar evidencia fotográfica.
        """
        code = "DED-EXTEMP-DAMAGE"
        reason = (
            f"Cargo extemporáneo por cajas rotas {sku} detectadas en reacomodo de bodega "
            f"({days_after_delivery} días post-entrega s/ {reference_doc})"
        )
        deduction = PaymentDeduction(
            code=code,
            reason=reason,
            amount=amount,
            reference_doc=reference_doc
        )
        assessment = GroundTruthDeductionAssessment(
            code=code,
            amount=amount,
            reason=reason,
            is_justified=False,
            governing_clause_id="CLAUSE-5.1",
            factual_basis=(
                f"Reporte de avería extemporáneo a los {days_after_delivery} días sin acta fotográfica "
                f"inmediata en muelle, infringiendo el plazo perentorio de 48h de la Cláusula 5.1."
            ),
            remedy_action="REJECT_AND_CLAIM"
        )
        return deduction, assessment

    def create_administrative_fee_deduction(
        self,
        code: str,
        amount: Decimal,
        reason: str
    ) -> Tuple[PaymentDeduction, GroundTruthDeductionAssessment]:
        """
        Penalización administrativa unilateral (ASN tardío, retraso en cita de muelle, error de código de barras).
        Injustificada contractualmente según la Cláusula 7.3 que prohíbe penalizaciones sin adenda expresa.
        """
        deduction = PaymentDeduction(
            code=code,
            reason=reason,
            amount=amount,
            reference_doc=None
        )
        assessment = GroundTruthDeductionAssessment(
            code=code,
            amount=amount,
            reason=reason,
            is_justified=False,
            governing_clause_id="CLAUSE-7.3",
            factual_basis=(
                f"Penalización unilateral {code} aplicada sin adenda bilateral ni soporte contractual vinculante."
            ),
            remedy_action="REJECT_AND_CLAIM"
        )
        return deduction, assessment

    def create_unilateral_penalty_deduction(
        self,
        amount: Decimal,
        penalty_type: str = "DED-ASN-LATE",
        reason: Optional[str] = None
    ) -> Tuple[PaymentDeduction, GroundTruthDeductionAssessment]:
        """
        Alias / método de conveniencia para generar deducciones por penalizaciones unilaterales.
        """
        desc = reason or f"Penalización unilateral por {penalty_type}"
        return self.create_administrative_fee_deduction(
            code=penalty_type,
            amount=amount,
            reason=desc
        )

    def create_tolerance_exempt_deduction(
        self,
        amount: Decimal,
        reference_doc: str,
        percentage_shortage: Decimal,
        allowed_tolerance: Decimal
    ) -> Tuple[PaymentDeduction, GroundTruthDeductionAssessment]:
        """
        Deducción aplicada sobre faltante que se encuentra dentro del rango de tolerancia contractual
        pactado para mercancías a granel o merma natural de embarque (ej. 1.2% < 2.0%).
        """
        code = "DED-TOLERANCE-SHORTAGE"
        reason = f"Deducción por faltante en volumen ({percentage_shortage:.2f}%) s/ remisión {reference_doc}"
        deduction = PaymentDeduction(
            code=code,
            reason=reason,
            amount=amount,
            reference_doc=reference_doc
        )
        assessment = GroundTruthDeductionAssessment(
            code=code,
            amount=amount,
            reason=reason,
            is_justified=False,
            governing_clause_id="CLAUSE-6.1",
            factual_basis=(
                f"Faltante de volumen ({percentage_shortage:.2f}%) está amparado bajo la franquicia "
                f"de tolerancia contractual de {allowed_tolerance:.2f}% de la Cláusula 6.1."
            ),
            remedy_action="REJECT_AND_CLAIM"
        )
        return deduction, assessment

    def create_price_variance_deduction(
        self,
        amount: Decimal,
        po_reference: str,
        sku: str
    ) -> Tuple[PaymentDeduction, GroundTruthDeductionAssessment]:
        """
        Ajuste por diferencia de precio entre el precio facturado y el precio pactado en la OC.
        Es 100% JUSTIFICADA si la Cláusula 3.1 otorga prelación jurídica a la Orden de Compra.
        """
        code = "DED-PRICE-VARIANCE"
        reason = f"Ajuste por sobrefacturación en {sku} respecto a precio pactado en {po_reference}"
        deduction = PaymentDeduction(
            code=code,
            reason=reason,
            amount=amount,
            reference_doc=po_reference
        )
        assessment = GroundTruthDeductionAssessment(
            code=code,
            amount=amount,
            reason=reason,
            is_justified=True,
            governing_clause_id="CLAUSE-3.1",
            factual_basis=(
                f"Precio en factura excedió el precio pactado en {po_reference}; "
                f"la Cláusula 3.1 confiere prelación contractual estricta a la Orden de Compra."
            ),
            remedy_action="ACCEPT_AND_CREDIT"
        )
        return deduction, assessment

    def build_payment_receipt(
        self,
        payment_id: str,
        invoice_reference: str,
        invoice_total: Decimal,
        deductions: List[PaymentDeduction],
        payment_date: str = "2026-09-30",
        currency: str = "USD"
    ) -> PaymentReceipt:
        """Construye el comprobante de pago liquidando el remanente neto."""
        total_deductions = sum((d.amount for d in deductions), Decimal("0.00"))
        amount_paid = max(Decimal("0.00"), invoice_total - total_deductions)
        return PaymentReceipt(
            payment_id=payment_id,
            invoice_reference=invoice_reference,
            payment_date=payment_date,
            currency=currency,
            amount_paid=amount_paid,
            deductions=deductions
        )
