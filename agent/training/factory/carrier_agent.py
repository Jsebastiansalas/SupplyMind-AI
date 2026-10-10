"""
Carrier Logistics Agent (Transportista).

Agente adversarial encargado de la documentación física de entrega en muelle.
Introduce o refuta discrepancias físicas de entrega (faltantes, averías en tránsito),
evaluando la solidez de la prueba de entrega (POD firmado con sello de muelle vs POD ambiguo o sin firmar).
"""

from typing import List, Optional
from data.models import DeliveryNote, DeliveryItem, PurchaseOrderItem


class CarrierLogisticsAgent:
    """
    Simula la actuación de empresas de transporte y operadores de muelle,
    generando comprobantes de entrega (DeliveryNote) con diferentes grados de validez probatoria.
    """

    def __init__(self, carrier_name: str = "Logística y Carga del Norte S.A."):
        self.carrier_name = carrier_name

    def build_clean_delivery_note(
        self,
        delivery_id: str,
        po_reference: str,
        po_items: List[PurchaseOrderItem],
        delivery_date: str = "2026-09-03",
        warehouse_location: str = "Bodega Central RetailCorp - Muelle 4",
        receiver_name: str = "Carlos Mendoza (Jefe de Almacén Central)"
    ) -> DeliveryNote:
        """Genera una remisión de entrega limpia, 100% recibida y debidamente firmada."""
        items = [
            DeliveryItem(
                item_id=item.item_id,
                quantity_delivered=item.ordered_quantity,
                quantity_received=item.ordered_quantity,
                missing_quantity=0,
                damaged_quantity=0,
                notes="Recibido completo y en perfecto estado a entera satisfacción."
            )
            for item in po_items
        ]
        return DeliveryNote(
            delivery_id=delivery_id,
            po_reference=po_reference,
            delivery_date=delivery_date,
            received_by=receiver_name,
            warehouse_location=warehouse_location,
            signed=True,
            discrepancy_reported=False,
            items=items
        )

    def build_discrepant_delivery_note(
        self,
        delivery_id: str,
        po_reference: str,
        po_items: List[PurchaseOrderItem],
        shortages: Optional[dict] = None,   # item_id -> missing_qty
        damages: Optional[dict] = None,     # item_id -> damaged_qty
        signed: bool = True,
        discrepancy_reported: bool = True,
        delivery_date: str = "2026-09-03",
        warehouse_location: str = "Bodega Central RetailCorp - Muelle 4",
        receiver_name: str = "Carlos Mendoza (Jefe de Almacén Central)"
    ) -> DeliveryNote:
        """
        Genera una remisión con faltantes o averías documentadas.
        Permite variar la validez probatoria (signed=False o discrepancy_reported=False)
        para desafiar el criterio de jerarquía de evidencia del agente de conciliación.
        """
        shortages = shortages or {}
        damages = damages or {}

        items: List[DeliveryItem] = []
        for item in po_items:
            m_qty = shortages.get(item.item_id, 0)
            d_qty = damages.get(item.item_id, 0)
            delivered_qty = item.ordered_quantity
            received_qty = max(0, delivered_qty - m_qty)

            if m_qty > 0 and signed and discrepancy_reported:
                note = f"Faltante físico en estiba: {m_qty} cajas no recibidas. Anotado con sello de discrepancia y firma del transportista."
            elif m_qty > 0 and not signed:
                note = f"Anotación informal en rampa de {m_qty} piezas faltantes; el chofer no firmó la remisión y se retiró del muelle sin recabar sello oficial."
            elif d_qty > 0:
                note = f"Avería detectada al abrir estiba: {d_qty} unidades rotas."
            else:
                note = "Recibido de conformidad."

            items.append(
                DeliveryItem(
                    item_id=item.item_id,
                    quantity_delivered=delivered_qty,
                    quantity_received=received_qty,
                    missing_quantity=m_qty,
                    damaged_quantity=d_qty,
                    notes=note
                )
            )

        received_by_str = receiver_name if signed else "Sin firma del receptor (Recepción no formalizada)"

        return DeliveryNote(
            delivery_id=delivery_id,
            po_reference=po_reference,
            delivery_date=delivery_date,
            received_by=received_by_str,
            warehouse_location=warehouse_location,
            signed=signed,
            discrepancy_reported=discrepancy_reported,
            items=items
        )
