from decimal import Decimal
from typing import List
from pydantic import BaseModel, ConfigDict
from data.models import (
    Invoice,
    PurchaseOrder,
    DeliveryNote,
    PaymentReceipt
)

class LineItemDiscrepancy(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    item_id: str
    description: str
    billed_quantity: int
    received_quantity: int
    missing_quantity: int
    damaged_quantity: int
    agreed_unit_price: Decimal
    invoiced_unit_price: Decimal
    price_difference: Decimal
    missing_amount: Decimal
    damaged_amount: Decimal
    total_impact: Decimal

class ReconciliationSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    billed_amount: Decimal
    received_amount: Decimal
    difference: Decimal  # received_amount - billed_amount (negativo si se pagó de menos)
    total_deductions_applied: Decimal
    
    # Desglose cuantitativo determinístico
    total_missing_amount: Decimal
    total_damaged_amount: Decimal
    total_price_discrepancy_amount: Decimal
    
    discrepancies: List[LineItemDiscrepancy]
    
    # Justificación matemática
    justified_deductions_amount: Decimal
    unjustified_deductions_amount: Decimal
    
    primary_discrepancy_type: str
    evidence_trail: List[str]

def reconcile_dispute_data(
    invoice: Invoice,
    purchase_order: PurchaseOrder,
    delivery: DeliveryNote,
    payment: PaymentReceipt
) -> ReconciliationSummary:
    """
    Motor determinístico de conciliación línea a línea para cadenas de suministro B2B.
    Realiza los cálculos con precisión exacta en Decimal para eliminar cualquier alucinación.
    """
    po_items_map = {item.item_id: item for item in purchase_order.items}
    delivery_items_map = {item.item_id: item for item in delivery.items}
    
    line_discrepancies: List[LineItemDiscrepancy] = []
    total_missing_amount = Decimal("0.00")
    total_damaged_amount = Decimal("0.00")
    total_price_discrepancy_amount = Decimal("0.00")
    evidence_trail: List[str] = []
    
    for inv_item in invoice.items:
        item_id = inv_item.item_id
        po_item = po_items_map.get(item_id)
        del_item = delivery_items_map.get(item_id)
        
        # 1. Cotejo de precios unitarios con la Orden de Compra
        agreed_price = po_item.agreed_unit_price if po_item else inv_item.unit_price
        price_diff = inv_item.unit_price - agreed_price
        if price_diff != Decimal("0.00"):
            price_impact = price_diff * Decimal(inv_item.quantity)
            total_price_discrepancy_amount += price_impact
            evidence_trail.append(
                f"Discrepancia de precio en {item_id}: facturado ${inv_item.unit_price} vs acordado ${agreed_price}"
            )
            
        # 2. Cotejo de cantidades físicas con la Remisión de Entrega
        rec_qty = del_item.quantity_received if del_item else inv_item.quantity
        deliv_qty = del_item.quantity_delivered if del_item else inv_item.quantity
        missing_qty = del_item.missing_quantity if del_item else max(0, inv_item.quantity - rec_qty)
        damaged_qty = del_item.damaged_quantity if del_item else 0
        
        item_missing_amount = Decimal(missing_qty) * inv_item.unit_price
        item_damaged_amount = Decimal(damaged_qty) * inv_item.unit_price
        total_missing_amount += item_missing_amount
        total_damaged_amount += item_damaged_amount
        
        total_line_impact = item_missing_amount + item_damaged_amount + (price_diff * Decimal(inv_item.quantity))
        
        if missing_qty > 0 or damaged_qty > 0 or price_diff != Decimal("0.00"):
            discrepancy_entry = LineItemDiscrepancy(
                item_id=item_id,
                description=inv_item.description,
                billed_quantity=inv_item.quantity,
                received_quantity=rec_qty,
                missing_quantity=missing_qty,
                damaged_quantity=damaged_qty,
                agreed_unit_price=agreed_price,
                invoiced_unit_price=inv_item.unit_price,
                price_difference=price_diff,
                missing_amount=item_missing_amount,
                damaged_amount=item_damaged_amount,
                total_impact=total_line_impact
            )
            line_discrepancies.append(discrepancy_entry)
            
            if missing_qty > 0:
                evidence_trail.append(
                    f"Faltante físico comprobado en {item_id} ({inv_item.description}): "
                    f"{missing_qty} unidades faltantes s/ remisión {delivery.delivery_id} "
                    f"valoradas en ${item_missing_amount:,.2f}"
                )
            if damaged_qty > 0:
                evidence_trail.append(
                    f"Mercancía averiada en {item_id}: {damaged_qty} unidades valoradas en ${item_damaged_amount:,.2f}"
                )

    # 3. Conciliación financiera global
    billed_amt = invoice.total_amount
    received_amt = payment.amount_paid
    diff = received_amt - billed_amt
    total_deductions = sum((d.amount for d in payment.deductions), Decimal("0.00"))
    
    # 4. Evaluación de deducciones justificadas vs injustificadas
    objective_discrepancy_total = total_missing_amount + total_damaged_amount + total_price_discrepancy_amount

    JUSTIFIED_INDICATORS = [
        "CONVENID", "ACORDAD", "JUSTIFICAD", "AMPARAD", "AUTORIZAD", "DICTAMEN",
        "CUARENTENA", "MANIOBRA", "DESESTIBA", "TARIMAS-CHEP", "DEMERITO",
        "MERMA-AVARIA", "COLGADO-SERVICIOS", "SEGURO-TRASLADO", "BONIFICACION-CATALOGO",
        "MISSING-PHYSICAL", "REBATE-ANUAL-CONVENIDO", "AJUSTE-COMERCIAL", "PRICE", "PRECIO",
        "PRC-VAR", "DAMAGE-BASE", "SHORTAGE", "RECALL-TEMP", "DED-MISSING"
    ]
    UNJUSTIFIED_INDICATORS = [
        "UNILATERAL", "EXTEMP", "NO PACTAD", "NO AUTORIZAD", "EXCESIV", "INDEBID",
        "IMPROCEDENTE", "FLETE-COMPARTIDO", "CROSSDOCK", "CADUCIDAD-CORTA", "EARLY-PAY",
        "ASN-LATE", "FOB-LOSS", "COOP-PUB", "UPC", "CALIBRACION", "ALLEGED-DAMAGE",
        "PARO-LINEA", "PALLET-DAMAGE", "GARANTIAS-DEFECT", "TICKETING", "DED-ASN",
        "UNAUTH", "ARBITRARY"
    ]

    justified_deductions = Decimal("0.00")
    unjustified_deductions = Decimal("0.00")

    if payment.deductions:
        rem_objective = objective_discrepancy_total
        for ded in payment.deductions:
            code_u = ded.code.upper()
            reason_u = ded.reason.upper()
            full_text = f"{code_u} {reason_u}"

            has_phys_link = any(k in full_text for k in ["DAMAGE", "AVERI", "SHRT", "SHORT", "FALT", "DOCK"])
            is_explicit_unjustified = any(sig in full_text for sig in UNJUSTIFIED_INDICATORS)
            is_explicit_justified = any(sig in full_text for sig in JUSTIFIED_INDICATORS)

            if is_explicit_unjustified:
                unjustified_deductions += ded.amount
            elif rem_objective > Decimal("0.00") and (is_explicit_justified or has_phys_link):
                match_amt = min(ded.amount, rem_objective)
                justified_deductions += match_amt
                unjustified_deductions += (ded.amount - match_amt)
                rem_objective -= match_amt
            elif is_explicit_justified:
                justified_deductions += ded.amount
                rem_objective = max(Decimal("0.00"), rem_objective - ded.amount)
            elif rem_objective > Decimal("0.00"):
                match_amt = min(ded.amount, rem_objective)
                justified_deductions += match_amt
                unjustified_deductions += (ded.amount - match_amt)
                rem_objective -= match_amt
            else:
                unjustified_deductions += ded.amount
    else:
        justified_deductions = min(total_deductions, objective_discrepancy_total)
        unjustified_deductions = max(Decimal("0.00"), total_deductions - justified_deductions)

    # Invariante contable estricta
    if (justified_deductions + unjustified_deductions) != total_deductions:
        unjustified_deductions = total_deductions - justified_deductions

    # Identificar causa principal
    if total_missing_amount > Decimal("0.00") and total_missing_amount >= total_damaged_amount:
        primary_type = "FALTANTE_DE_MERCANCIA"
    elif total_damaged_amount > Decimal("0.00"):
        primary_type = "MERCANCIA_AVERIADA"
    elif total_price_discrepancy_amount != Decimal("0.00"):
        primary_type = "DIFERENCIA_DE_PRECIO"
    elif unjustified_deductions > Decimal("0.00"):
        primary_type = "PENALIZACION_UNILATERAL_INDEBIDA"
    elif total_deductions > Decimal("0.00"):
        primary_type = "DEDUCCION_COMERCIAL_CONVENIDA"
    else:
        primary_type = "PAGO_EXACTO"
        
    for ded in payment.deductions:
        evidence_trail.append(
            f"Deducción aplicada en comprobante {payment.payment_id}: "
            f"código {ded.code}, motivo '{ded.reason}', monto ${ded.amount:,.2f}"
        )

    return ReconciliationSummary(
        billed_amount=billed_amt,
        received_amount=received_amt,
        difference=diff,
        total_deductions_applied=total_deductions,
        total_missing_amount=total_missing_amount,
        total_damaged_amount=total_damaged_amount,
        total_price_discrepancy_amount=total_price_discrepancy_amount,
        discrepancies=line_discrepancies,
        justified_deductions_amount=justified_deductions,
        unjustified_deductions_amount=unjustified_deductions,
        primary_discrepancy_type=primary_type,
        evidence_trail=evidence_trail
    )
