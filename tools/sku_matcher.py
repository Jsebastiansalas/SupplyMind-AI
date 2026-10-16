"""
tools/sku_matcher.py
Motor determinístico de conciliación y auditoría línea a línea por SKU (SKU-Level Matching)
y cálculo fiscal de impuestos (IVA 16% México / Retenciones).
"""

from decimal import Decimal
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, ConfigDict


class SKUItemAudit(BaseModel):
    model_config = ConfigDict(extra="ignore")

    item_id: str
    description: str
    quantity_billed: int
    quantity_received: int
    quantity_short: int
    quantity_damaged: int
    unit_price_invoiced: Decimal
    unit_price_agreed: Decimal
    price_variance: Decimal
    line_subtotal_billed: Decimal
    line_subtotal_received: Decimal
    line_missing_amount: Decimal
    line_damaged_amount: Decimal
    line_price_discrepancy: Decimal
    line_total_discrepancy: Decimal
    vat_impact_16: Decimal
    is_fully_reconciled: bool
    status_label: str


class SKUMatchingResult(BaseModel):
    model_config = ConfigDict(extra="ignore")

    total_skus_audited: int
    skus_with_discrepancies: int
    line_items: List[SKUItemAudit]
    total_short_amount: Decimal
    total_damaged_amount: Decimal
    total_price_variance_amount: Decimal
    net_line_discrepancy: Decimal
    total_vat_impact_16: Decimal
    credit_note_recommended_subtotal: Decimal
    credit_note_recommended_vat: Decimal
    credit_note_recommended_total: Decimal


def perform_sku_level_matching(
    invoice_data: Dict[str, Any],
    delivery_data: Optional[Dict[str, Any]] = None,
    po_data: Optional[Dict[str, Any]] = None,
) -> SKUMatchingResult:
    """
    Ejecuta el cotejo matemático determinístico de cada SKU individual entre la Factura,
    la Remisión de Entrega y la Orden de Compra.
    Calcula la base gravable y el impacto en IVA (16%) para la emisión precisa de Notas de Crédito.
    """
    inv_items = invoice_data.get("items", [])
    del_items_map = {}
    if delivery_data and "items" in delivery_data:
        del_items_map = {item.get("item_id") or item.get("sku"): item for item in delivery_data["items"]}

    po_items_map = {}
    if po_data and "items" in po_data:
        po_items_map = {item.get("item_id") or item.get("sku"): item for item in po_data["items"]}

    audited_lines: List[SKUItemAudit] = []
    total_short = Decimal("0.00")
    total_damaged = Decimal("0.00")
    total_price_var = Decimal("0.00")
    total_vat = Decimal("0.00")

    for item in inv_items:
        item_id = str(item.get("item_id") or item.get("sku") or "UNKNOWN")
        desc = str(item.get("description", item_id))
        qty_billed = int(item.get("quantity", 0))
        unit_price_inv = Decimal(str(item.get("unit_price", "0.00")))

        # Datos de Orden de Compra
        po_match = po_items_map.get(item_id, {})
        agreed_price_raw = po_match.get("agreed_unit_price") if "agreed_unit_price" in po_match else po_match.get("unit_price", unit_price_inv)
        unit_price_po = Decimal(str(agreed_price_raw))
        price_diff = unit_price_inv - unit_price_po

        # Datos de Remisión
        del_match = del_items_map.get(item_id, {})
        qty_received = int(del_match.get("quantity_received", qty_billed))
        qty_short = int(del_match.get("missing_quantity") if "missing_quantity" in del_match else del_match.get("quantity_missing", max(0, qty_billed - qty_received)))
        qty_damaged = int(del_match.get("damaged_quantity") if "damaged_quantity" in del_match else del_match.get("quantity_damaged", 0))

        # Cálculos monetarios por línea
        line_billed = unit_price_inv * Decimal(qty_billed)
        line_received = unit_price_po * Decimal(qty_received)
        missing_amt = unit_price_inv * Decimal(qty_short)
        damaged_amt = unit_price_inv * Decimal(qty_damaged)
        price_discrepancy = price_diff * Decimal(qty_billed)

        line_discrepancy = missing_amt + damaged_amt + price_discrepancy
        vat_impact = round(line_discrepancy * Decimal("0.16"), 2)

        is_reconciled = (line_discrepancy == Decimal("0.00"))

        if is_reconciled:
            label = "CONCILIADO 100%"
        elif qty_short > 0 and damaged_amt > Decimal("0.00"):
            label = "FALTANTE Y AVERÍA"
        elif qty_short > 0:
            label = f"FALTANTE ({qty_short} UDS)"
        elif damaged_amt > Decimal("0.00"):
            label = f"AVERÍA ({qty_damaged} UDS)"
        elif price_diff != Decimal("0.00"):
            label = "PRECIO DISCREPANTE"
        else:
            label = "OBSERVADO"

        audit_entry = SKUItemAudit(
            item_id=item_id,
            description=desc,
            quantity_billed=qty_billed,
            quantity_received=qty_received,
            quantity_short=qty_short,
            quantity_damaged=qty_damaged,
            unit_price_invoiced=unit_price_inv,
            unit_price_agreed=unit_price_po,
            price_variance=price_diff,
            line_subtotal_billed=line_billed,
            line_subtotal_received=line_received,
            line_missing_amount=missing_amt,
            line_damaged_amount=damaged_amt,
            line_price_discrepancy=price_discrepancy,
            line_total_discrepancy=line_discrepancy,
            vat_impact_16=vat_impact,
            is_fully_reconciled=is_reconciled,
            status_label=label,
        )

        audited_lines.append(audit_entry)
        total_short += missing_amt
        total_damaged += damaged_amt
        total_price_var += price_discrepancy
        total_vat += vat_impact

    net_disc = total_short + total_damaged + total_price_var
    skus_with_disc = sum(1 for line in audited_lines if not line.is_fully_reconciled)

    # Nota de Crédito comercial sugerida (subtotal + IVA 16%)
    nc_subtotal = net_disc
    nc_vat = round(nc_subtotal * Decimal("0.16"), 2)
    nc_total = nc_subtotal + nc_vat

    return SKUMatchingResult(
        total_skus_audited=len(audited_lines),
        skus_with_discrepancies=skus_with_disc,
        line_items=audited_lines,
        total_short_amount=total_short,
        total_damaged_amount=total_damaged,
        total_price_variance_amount=total_price_var,
        net_line_discrepancy=net_disc,
        total_vat_impact_16=total_vat,
        credit_note_recommended_subtotal=nc_subtotal,
        credit_note_recommended_vat=nc_vat,
        credit_note_recommended_total=nc_total,
    )
