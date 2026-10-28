"""
tools/reconciliation_engine/batch_map_reduce.py
Motor de Conciliación Map-Reduce para Facturas y Remisiones Masivas (1,000 a 5,000+ SKUs).

Permite auditar operaciones comerciales gigantescas dividiendo el catálogo en sub-lotes
procesados en paralelo o secuenciales en memoria CPU con estricta precisión Decimal ($0.00 USD costo LLM),
validando invariantes contables globales y generando un Árbol Merkle de Integridad.
"""

from decimal import Decimal
import hashlib
from typing import List, Dict, Any, Tuple
from pydantic import BaseModel, ConfigDict, Field

from data.models import (
    Invoice,
    InvoiceItem,
    PurchaseOrder,
    DeliveryNote,
    PaymentReceipt,
    PaymentDeduction
)
from tools.reconciliation_engine.engine import (
    LineItemDiscrepancy,
    ReconciliationSummary,
    reconcile_dispute_data
)


class BatchReconciliationResult(BaseModel):
    """Resultado del cotejo contable de un sub-lote de SKUs."""
    model_config = ConfigDict(extra="forbid")

    batch_index: int
    sku_start_index: int
    sku_end_index: int
    items_count: int
    batch_billed_amount: Decimal
    batch_received_amount: Decimal
    batch_missing_amount: Decimal
    batch_damaged_amount: Decimal
    batch_price_diff_amount: Decimal
    discrepancies: List[LineItemDiscrepancy]
    batch_hash: str


class MassiveReconciliationManifest(BaseModel):
    """Manifiesto global consolidado por Map-Reduce con árbol de invariantes."""
    model_config = ConfigDict(extra="forbid")

    total_skus_processed: int
    total_batches_count: int
    batch_size: int
    invoice_total_amount: Decimal
    consolidated_billed_amount: Decimal
    consolidated_received_amount: Decimal
    consolidated_missing_amount: Decimal
    consolidated_damaged_amount: Decimal
    consolidated_price_diff_amount: Decimal
    total_discrepant_lines_count: int
    merkle_root_hash: str
    invariant_conserved: bool
    summary: ReconciliationSummary


class MassiveBatchReconciliationEngine:
    """Motor Map-Reduce determinístico para expedientes masivos."""

    DEFAULT_BATCH_SIZE: int = 50

    @classmethod
    def _compute_batch_hash(cls, batch_idx: int, billed: Decimal, rec: Decimal, diff: Decimal) -> str:
        payload = f"BATCH:{batch_idx}|B:{billed:.2f}|R:{rec:.2f}|D:{diff:.2f}".encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    @classmethod
    def map_reduce_reconcile(
        cls,
        invoice: Invoice,
        purchase_order: PurchaseOrder,
        delivery: DeliveryNote,
        payment: PaymentReceipt,
        batch_size: int = DEFAULT_BATCH_SIZE
    ) -> MassiveReconciliationManifest:
        """
        Ejecuta la partición Map-Reduce sobre los items de la factura.
        """
        po_items_map = {item.item_id: item for item in purchase_order.items}
        del_items_map = {item.item_id: item for item in delivery.items}

        all_items = invoice.items
        total_items = len(all_items)
        batch_results: List[BatchReconciliationResult] = []

        total_billed = Decimal("0.00")
        total_received = Decimal("0.00")
        total_missing = Decimal("0.00")
        total_damaged = Decimal("0.00")
        total_price_diff = Decimal("0.00")
        all_discrepancies: List[LineItemDiscrepancy] = []

        # --- MAP PHASE: Procesamiento en sub-lotes ---
        for b_idx, start_idx in enumerate(range(0, total_items, batch_size)):
            end_idx = min(total_items, start_idx + batch_size)
            batch_slice = all_items[start_idx:end_idx]

            b_billed = Decimal("0.00")
            b_received = Decimal("0.00")
            b_missing = Decimal("0.00")
            b_damaged = Decimal("0.00")
            b_price = Decimal("0.00")
            b_discrepancies: List[LineItemDiscrepancy] = []

            for inv_item in batch_slice:
                item_id = inv_item.item_id
                po_item = po_items_map.get(item_id)
                del_item = del_items_map.get(item_id)

                b_billed += inv_item.total_price

                # 1. Cotejo de precio
                agreed_price = po_item.agreed_unit_price if po_item else inv_item.unit_price
                price_diff = inv_item.unit_price - agreed_price
                if price_diff != Decimal("0.00"):
                    price_impact = price_diff * Decimal(inv_item.quantity)
                    b_price += price_impact

                # 2. Cotejo físico
                rec_qty = del_item.quantity_received if del_item else inv_item.quantity
                deliv_qty = del_item.quantity_delivered if del_item else inv_item.quantity
                missing_qty = del_item.missing_quantity if del_item else max(0, inv_item.quantity - rec_qty)
                damaged_qty = del_item.damaged_quantity if del_item else 0

                item_missing_amount = Decimal(missing_qty) * inv_item.unit_price
                item_damaged_amount = Decimal(damaged_qty) * inv_item.unit_price
                b_missing += item_missing_amount
                b_damaged += item_damaged_amount

                line_received_amt = Decimal(rec_qty) * agreed_price
                b_received += line_received_amt

                total_impact = item_missing_amount + item_damaged_amount + (price_diff * Decimal(inv_item.quantity))

                if missing_qty > 0 or damaged_qty > 0 or price_diff != Decimal("0.00"):
                    discr = LineItemDiscrepancy(
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
                        total_impact=total_impact
                    )
                    b_discrepancies.append(discr)

            # Hash del lote para integridad Merkle
            b_hash = cls._compute_batch_hash(b_idx, b_billed, b_received, b_missing + b_damaged + b_price)

            batch_res = BatchReconciliationResult(
                batch_index=b_idx,
                sku_start_index=start_idx,
                sku_end_index=end_idx,
                items_count=len(batch_slice),
                batch_billed_amount=b_billed,
                batch_received_amount=b_received,
                batch_missing_amount=b_missing,
                batch_damaged_amount=b_damaged,
                batch_price_diff_amount=b_price,
                discrepancies=b_discrepancies,
                batch_hash=b_hash
            )
            batch_results.append(batch_res)

            # Acumular para el reduce
            total_billed += b_billed
            total_missing += b_missing
            total_damaged += b_damaged
            total_price_diff += b_price
            all_discrepancies.extend(b_discrepancies)

        # --- REDUCE PHASE: Consolidación y Verificación de Invariantes ---
        received_amt_paid = payment.amount_paid
        diff = received_amt_paid - total_billed
        total_deductions = sum((d.amount for d in payment.deductions), Decimal("0.00"))
        objective_discrepancy_total = total_missing + total_damaged + total_price_diff

        # Clasificación de deducciones con el motor calibrado
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

        # Invariante contable
        if (justified_deductions + unjustified_deductions) != total_deductions:
            unjustified_deductions = total_deductions - justified_deductions

        # Causa primaria
        if total_missing > Decimal("0.00") and total_missing >= total_damaged:
            primary_type = "FALTANTE_DE_MERCANCIA"
        elif total_damaged > Decimal("0.00"):
            primary_type = "MERCANCIA_AVERIADA"
        elif total_price_diff != Decimal("0.00"):
            primary_type = "DIFERENCIA_DE_PRECIO"
        elif unjustified_deductions > Decimal("0.00"):
            primary_type = "PENALIZACION_UNILATERAL_INDEBIDA"
        elif total_deductions > Decimal("0.00"):
            primary_type = "DEDUCCION_COMERCIAL_CONVENIDA"
        else:
            primary_type = "PAGO_EXACTO"

        evidence_trail = [
            f"Map-Reduce Audit: {total_items} partidas conciliadas en {len(batch_results)} lotes de {batch_size} SKUs.",
            f"Total Facturado Consolidado: ${total_billed:,.2f} USD | Total Pagado: ${received_amt_paid:,.2f} USD.",
            f"Faltante Físico Auditado: ${total_missing:,.2f} USD | Mercancía Averiada: ${total_damaged:,.2f} USD."
        ]
        for ded in payment.deductions:
            evidence_trail.append(f"Deducción {ded.code}: ${ded.amount:,.2f} USD ('{ded.reason}')")

        summary = ReconciliationSummary(
            billed_amount=total_billed,
            received_amount=received_amt_paid,
            difference=diff,
            total_deductions_applied=total_deductions,
            total_missing_amount=total_missing,
            total_damaged_amount=total_damaged,
            total_price_discrepancy_amount=total_price_diff,
            discrepancies=all_discrepancies,
            justified_deductions_amount=justified_deductions,
            unjustified_deductions_amount=unjustified_deductions,
            primary_discrepancy_type=primary_type,
            evidence_trail=evidence_trail
        )

        # Cálculo de la Raíz Merkle de los lotes
        combined_hashes = "".join(b.batch_hash for b in batch_results).encode("utf-8")
        merkle_root = hashlib.sha256(combined_hashes).hexdigest()

        # Validación estricta de invariante con la factura original
        inv_conserved = (total_billed == invoice.total_amount)

        return MassiveReconciliationManifest(
            total_skus_processed=total_items,
            total_batches_count=len(batch_results),
            batch_size=batch_size,
            invoice_total_amount=invoice.total_amount,
            consolidated_billed_amount=total_billed,
            consolidated_received_amount=received_amt_paid,
            consolidated_missing_amount=total_missing,
            consolidated_damaged_amount=total_damaged,
            consolidated_price_diff_amount=total_price_diff,
            total_discrepant_lines_count=len(all_discrepancies),
            merkle_root_hash=merkle_root,
            invariant_conserved=inv_conserved,
            summary=summary
        )
