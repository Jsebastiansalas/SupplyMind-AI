"""
Adversarial Case Synthesizer (Sintetizador Adversarial de Disputas B2B).

Coordina a los tres agentes adversariales (Comprador Retailer, Transportista y Abogado)
para generar expedientes completos de disputa comercial con las 5 estructuras tipadas
de Pydantic (Invoice, PurchaseOrder, DeliveryNote, PaymentReceipt, CommercialContract)
y un Ground Truth inmutable con invariantes matemáticos verificados al centavo.
"""

import json
from decimal import Decimal
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, Union, List

from config.settings import settings
from data.models import (
    Invoice,
    InvoiceItem,
    PurchaseOrder,
    PurchaseOrderItem,
    DeliveryNote,
    PaymentReceipt,
    CommercialContract,
)
from agent.training.factory.ground_truth import (
    GroundTruth,
    GroundTruthLineItem,
    GroundTruthDeductionAssessment,
    DiscrepancyCategory,
    CommercialActionType,
)
from agent.training.factory.retailer_agent import RetailerBuyerAgent
from agent.training.factory.carrier_agent import CarrierLogisticsAgent
from agent.training.factory.lawyer_agent import CorporateLawyerAgent


class AdversarialCaseSynthesizer:
    """
    Sintetizador de casos de frontera para entrenamiento y evaluación colegiada.
    Implementa 6 tipologías de disputa representativas de la cadena de suministro B2B.
    """

    TYPOLOGY_NAMES = [
        "unsigned_pod",
        "extemporaneous_damage",
        "administrative_penalties",
        "compound_mixed",
        "tolerance_window",
        "price_precedence",
        "enterprise_mega_bundle",
    ]

    def __init__(
        self,
        retailer_agent: Optional[RetailerBuyerAgent] = None,
        carrier_agent: Optional[CarrierLogisticsAgent] = None,
        lawyer_agent: Optional[CorporateLawyerAgent] = None,
    ):
        self.retailer = retailer_agent or RetailerBuyerAgent()
        self.carrier = carrier_agent or CarrierLogisticsAgent()
        self.lawyer = lawyer_agent or CorporateLawyerAgent()

    def normalize_typology(self, typology: Optional[str], case_id: str) -> str:
        """Determina la tipología normalizada a partir del parámetro o del case_id."""
        if typology:
            t_lower = str(typology).lower().strip()
            if t_lower in ["1", "unsigned_pod", "ambiguous_pod", "pod"]:
                return "unsigned_pod"
            if t_lower in ["2", "extemporaneous_damage", "damage_window", "extemp"]:
                return "extemporaneous_damage"
            if t_lower in ["3", "administrative_penalties", "hidden_penalties", "asn_fee"]:
                return "administrative_penalties"
            if t_lower in ["4", "compound_mixed", "multi_sku", "mixed"]:
                return "compound_mixed"
            if t_lower in ["5", "tolerance_window", "volume_tolerance", "tolerance"]:
                return "tolerance_window"
            if t_lower in ["6", "price_precedence", "expired_quote", "price_variance", "quote_vs_po"]:
                return "price_precedence"
            if t_lower in ["7", "enterprise_mega_bundle", "mega", "enterprise", "extensive", "multi_sku_extensive"]:
                return "enterprise_mega_bundle"
            for known in self.TYPOLOGY_NAMES:
                if known in t_lower:
                    return known

        # Si no se especificó tipología, derivar determinísticamente del case_id
        c_lower = case_id.lower()
        if "mega" in c_lower or "extensive" in c_lower or "t6" in c_lower or "enterprise" in c_lower:
            return "enterprise_mega_bundle"
        if "unsigned" in c_lower or "pod" in c_lower:
            return "unsigned_pod"
        if "damage" in c_lower or "extemp" in c_lower:
            return "extemporaneous_damage"
        if "admin" in c_lower or "fee" in c_lower or "penalty" in c_lower:
            return "administrative_penalties"
        if "mixed" in c_lower or "compound" in c_lower or "multi" in c_lower:
            return "compound_mixed"
        if "tolerance" in c_lower or "bulk" in c_lower:
            return "tolerance_window"
        if "price" in c_lower or "quote" in c_lower or "variance" in c_lower:
            return "price_precedence"

        # Asignación pseudo-cíclica por hash
        idx = abs(hash(case_id)) % len(self.TYPOLOGY_NAMES)
        return self.TYPOLOGY_NAMES[idx]

    def generate_case(
        self,
        case_id: str,
        typology: Optional[str] = None,
        difficulty_level: int = 1,
    ) -> Tuple[Dict[str, Any], GroundTruth]:
        """
        Sintetiza un caso de prueba completo en memoria con los 5 modelos de datos
        y su correspondiente GroundTruth matemáticamente conciliado.
        """
        resolved_typology = self.normalize_typology(typology, case_id)

        dispatch_map = {
            "unsigned_pod": self._generate_unsigned_pod_case,
            "extemporaneous_damage": self._generate_extemporaneous_damage_case,
            "administrative_penalties": self._generate_administrative_penalties_case,
            "compound_mixed": self._generate_compound_mixed_case,
            "tolerance_window": self._generate_tolerance_window_case,
            "price_precedence": self._generate_price_precedence_case,
            "enterprise_mega_bundle": self._generate_enterprise_extensive_case,
        }

        generator_fn = dispatch_map.get(resolved_typology, self._generate_unsigned_pod_case)
        return generator_fn(case_id, difficulty_level)

    def _generate_unsigned_pod_case(
        self, case_id: str, difficulty_level: int
    ) -> Tuple[Dict[str, Any], GroundTruth]:
        """
        Tipología 1: POD Ambiguo / Sin Firma (The Ambiguous/Unsigned POD).
        El transportista anota faltante, pero la remisión carece de firma de recepción
        y sello oficial. Contractualmente (Cláusula 4.2), carece de valor probatorio
        de Nivel 1. La deducción debe ser rechazada y reclamada al 100%.
        """
        sku = "PROD-001"
        invoiced_qty = 100
        delivered_qty = 100
        missing_qty = 10
        received_qty = 90
        unit_price = Decimal("100.00")
        billed_amount = Decimal("10000.00")
        shortage_amount = Decimal("1000.00")
        amount_paid = Decimal("9000.00")

        po_ref = f"PO-{case_id.upper()}"
        inv_ref = f"INV-{case_id.upper()}"
        del_ref = f"DEL-{case_id.upper()}"
        pay_ref = f"PAY-{case_id.upper()}"
        ctr_ref = "CTR-RETAIL-2026"

        po = PurchaseOrder(
            po_id=po_ref,
            vendor_id="VEN-001",
            customer_id="CUST-RETAIL-101",
            order_date="2026-08-20",
            currency="USD",
            items=[
                PurchaseOrderItem(
                    item_id=sku,
                    description="Caja Aceite Industrial Extra 12x1L",
                    ordered_quantity=invoiced_qty,
                    agreed_unit_price=unit_price,
                    total_price=billed_amount,
                )
            ],
            total_amount=billed_amount,
        )

        invoice = Invoice(
            invoice_id=inv_ref,
            vendor_id="VEN-001",
            customer_id="CUST-RETAIL-101",
            po_reference=po_ref,
            issue_date="2026-08-25",
            currency="USD",
            items=[
                InvoiceItem(
                    item_id=sku,
                    description="Caja Aceite Industrial Extra 12x1L",
                    quantity=invoiced_qty,
                    unit_price=unit_price,
                    total_price=billed_amount,
                )
            ],
            subtotal=billed_amount,
            tax=Decimal("0.00"),
            total_amount=billed_amount,
        )

        # Carrier genera remisión SIN FIRMA y SIN SELLO (prueba plena inválida)
        delivery = self.carrier.build_discrepant_delivery_note(
            delivery_id=del_ref,
            po_reference=po_ref,
            po_items=po.items,
            shortages={sku: missing_qty},
            signed=False,
            discrepancy_reported=False,
        )

        # Buyer aplica deducción por faltante
        deduction, deduction_gt = self.retailer.create_shortage_deduction(
            amount=shortage_amount,
            reference_doc=del_ref,
            is_pod_signed=False,
            units_missing=missing_qty,
            sku=sku,
        )

        payment = self.retailer.build_payment_receipt(
            payment_id=pay_ref,
            invoice_reference=inv_ref,
            invoice_total=billed_amount,
            deductions=[deduction],
        )

        contract = self.lawyer.generate_standard_contract(contract_id=ctr_ref)

        gt_line = GroundTruthLineItem(
            item_id=sku,
            description="Caja Aceite Industrial Extra 12x1L",
            invoiced_qty=invoiced_qty,
            received_qty=received_qty,
            missing_qty=missing_qty,
            damaged_qty=0,
            invoiced_price=unit_price,
            agreed_price=unit_price,
        )

        gt = GroundTruth(
            case_id=case_id,
            difficulty_level=difficulty_level,
            category=DiscrepancyCategory.PHYSICAL_SHORTAGE,
            expected_action_type=CommercialActionType.COLLECTION_LETTER,
            billed_amount=billed_amount,
            received_amount=amount_paid,
            difference=amount_paid - billed_amount,
            expected_justified_amount=Decimal("0.00"),
            expected_claimable_amount=shortage_amount,
            line_items=[gt_line],
            deductions=[deduction_gt],
            required_evidence_citations=[inv_ref, del_ref, pay_ref, ctr_ref],
            required_clause_citations=["CLAUSE-4.2", "CLAUSE-8.2"],
            evidence_hierarchy_rule_applied=(
                "Remisión de entrega sin firma ni sello carece de valor probatorio de Nivel 1 "
                "(Cláusula 4.2 y 8.2); deducción por faltante improcedente."
            ),
            scenario_tags=["unsigned_pod", "evidence_hierarchy", "shortage_rejected"],
        )

        documents = {
            "invoice": invoice,
            "purchase_order": po,
            "delivery": delivery,
            "payment": payment,
            "contract": contract,
        }
        return documents, gt

    def _generate_extemporaneous_damage_case(
        self, case_id: str, difficulty_level: int
    ) -> Tuple[Dict[str, Any], GroundTruth]:
        """
        Tipología 2: Notificación Extemporánea de Avería (Extemporaneous Damage Notice).
        La remisión fue firmada limpia de conformidad. El comprador retiene pago 30 días
        después por mercancía dañada, infringiendo el plazo de 48h con fotos (Cláusula 5.1).
        """
        sku = "PROD-002"
        invoiced_qty = 50
        unit_price = Decimal("150.00")
        billed_amount = Decimal("7500.00")
        damage_amount = Decimal("750.00")  # 5 unidades x $150
        amount_paid = Decimal("6750.00")

        po_ref = f"PO-{case_id.upper()}"
        inv_ref = f"INV-{case_id.upper()}"
        del_ref = f"DEL-{case_id.upper()}"
        pay_ref = f"PAY-{case_id.upper()}"
        ctr_ref = "CTR-RETAIL-2026"

        po = PurchaseOrder(
            po_id=po_ref,
            vendor_id="VEN-001",
            customer_id="CUST-RETAIL-101",
            order_date="2026-08-10",
            currency="USD",
            items=[
                PurchaseOrderItem(
                    item_id=sku,
                    description="Lote Componentes Electrónicos Industriales",
                    ordered_quantity=invoiced_qty,
                    agreed_unit_price=unit_price,
                    total_price=billed_amount,
                )
            ],
            total_amount=billed_amount,
        )

        invoice = Invoice(
            invoice_id=inv_ref,
            vendor_id="VEN-001",
            customer_id="CUST-RETAIL-101",
            po_reference=po_ref,
            issue_date="2026-08-15",
            currency="USD",
            items=[
                InvoiceItem(
                    item_id=sku,
                    description="Lote Componentes Electrónicos Industriales",
                    quantity=invoiced_qty,
                    unit_price=unit_price,
                    total_price=billed_amount,
                )
            ],
            subtotal=billed_amount,
            tax=Decimal("0.00"),
            total_amount=billed_amount,
        )

        # Entrega limpia y firmada de conformidad
        delivery = self.carrier.build_clean_delivery_note(
            delivery_id=del_ref,
            po_reference=po_ref,
            po_items=po.items,
        )

        # Buyer aplica deducción extemporánea a los 30 días
        deduction, deduction_gt = self.retailer.create_extemporaneous_damage_deduction(
            amount=damage_amount,
            reference_doc=del_ref,
            days_after_delivery=30,
            sku=sku,
        )

        payment = self.retailer.build_payment_receipt(
            payment_id=pay_ref,
            invoice_reference=inv_ref,
            invoice_total=billed_amount,
            deductions=[deduction],
        )

        contract = self.lawyer.generate_standard_contract(contract_id=ctr_ref)

        gt_line = GroundTruthLineItem(
            item_id=sku,
            description="Lote Componentes Electrónicos Industriales",
            invoiced_qty=invoiced_qty,
            received_qty=invoiced_qty,
            missing_qty=0,
            damaged_qty=0,  # Legalmente no admitida
            invoiced_price=unit_price,
            agreed_price=unit_price,
        )

        gt = GroundTruth(
            case_id=case_id,
            difficulty_level=difficulty_level,
            category=DiscrepancyCategory.EXTEMPORANEOUS_CLAIM,
            expected_action_type=CommercialActionType.COLLECTION_LETTER,
            billed_amount=billed_amount,
            received_amount=amount_paid,
            difference=amount_paid - billed_amount,
            expected_justified_amount=Decimal("0.00"),
            expected_claimable_amount=damage_amount,
            line_items=[gt_line],
            deductions=[deduction_gt],
            required_evidence_citations=[inv_ref, del_ref, pay_ref, ctr_ref],
            required_clause_citations=["CLAUSE-5.1"],
            evidence_hierarchy_rule_applied=(
                "Notificación extemporánea de avería a los 30 días sin reporte fotográfico "
                "infringe la ventana perentoria de 48 horas de la Cláusula 5.1."
            ),
            scenario_tags=["extemporaneous_claim", "notice_window_48h", "clean_delivery"],
        )

        documents = {
            "invoice": invoice,
            "purchase_order": po,
            "delivery": delivery,
            "payment": payment,
            "contract": contract,
        }
        return documents, gt

    def _generate_administrative_penalties_case(
        self, case_id: str, difficulty_level: int
    ) -> Tuple[Dict[str, Any], GroundTruth]:
        """
        Tipología 3: Penalizaciones Administrativas Ocultas (Hidden Administrative Penalties).
        El comprador aplica unilateralmente cargos por ASN tardío ($500.00) y cita de muelle ($300.00).
        La entrega fue 100% conforme. La Cláusula 7.3 prohíbe penalizaciones sin adenda bilateral.
        """
        sku = "PROD-003"
        invoiced_qty = 100
        unit_price = Decimal("120.00")
        billed_amount = Decimal("12000.00")
        fee_asn = Decimal("500.00")
        fee_slot = Decimal("300.00")
        total_deductions = fee_asn + fee_slot  # $800.00
        amount_paid = Decimal("11200.00")

        po_ref = f"PO-{case_id.upper()}"
        inv_ref = f"INV-{case_id.upper()}"
        del_ref = f"DEL-{case_id.upper()}"
        pay_ref = f"PAY-{case_id.upper()}"
        ctr_ref = "CTR-RETAIL-2026"

        po = PurchaseOrder(
            po_id=po_ref,
            vendor_id="VEN-001",
            customer_id="CUST-RETAIL-101",
            order_date="2026-08-01",
            currency="USD",
            items=[
                PurchaseOrderItem(
                    item_id=sku,
                    description="Caja Café de Especialidad 24x500g",
                    ordered_quantity=invoiced_qty,
                    agreed_unit_price=unit_price,
                    total_price=billed_amount,
                )
            ],
            total_amount=billed_amount,
        )

        invoice = Invoice(
            invoice_id=inv_ref,
            vendor_id="VEN-001",
            customer_id="CUST-RETAIL-101",
            po_reference=po_ref,
            issue_date="2026-08-05",
            currency="USD",
            items=[
                InvoiceItem(
                    item_id=sku,
                    description="Caja Café de Especialidad 24x500g",
                    quantity=invoiced_qty,
                    unit_price=unit_price,
                    total_price=billed_amount,
                )
            ],
            subtotal=billed_amount,
            tax=Decimal("0.00"),
            total_amount=billed_amount,
        )

        delivery = self.carrier.build_clean_delivery_note(
            delivery_id=del_ref,
            po_reference=po_ref,
            po_items=po.items,
        )

        # Buyer aplica penalizaciones administrativas unilaterales
        ded1, ded1_gt = self.retailer.create_administrative_fee_deduction(
            code="DED-ASN-FEE",
            amount=fee_asn,
            reason="Cargo unilateral por transmisión extemporánea de archivo ASN",
        )
        ded2, ded2_gt = self.retailer.create_administrative_fee_deduction(
            code="DED-LATE-SLOT",
            amount=fee_slot,
            reason="Penalización operativa por arribo fuera de ventana de cita en rampa",
        )

        payment = self.retailer.build_payment_receipt(
            payment_id=pay_ref,
            invoice_reference=inv_ref,
            invoice_total=billed_amount,
            deductions=[ded1, ded2],
        )

        contract = self.lawyer.generate_standard_contract(contract_id=ctr_ref)

        gt_line = GroundTruthLineItem(
            item_id=sku,
            description="Caja Café de Especialidad 24x500g",
            invoiced_qty=invoiced_qty,
            received_qty=invoiced_qty,
            missing_qty=0,
            damaged_qty=0,
            invoiced_price=unit_price,
            agreed_price=unit_price,
        )

        gt = GroundTruth(
            case_id=case_id,
            difficulty_level=difficulty_level,
            category=DiscrepancyCategory.UNILATERAL_PENALTY,
            expected_action_type=CommercialActionType.COLLECTION_LETTER,
            billed_amount=billed_amount,
            received_amount=amount_paid,
            difference=amount_paid - billed_amount,
            expected_justified_amount=Decimal("0.00"),
            expected_claimable_amount=total_deductions,
            line_items=[gt_line],
            deductions=[ded1_gt, ded2_gt],
            required_evidence_citations=[inv_ref, del_ref, pay_ref, ctr_ref],
            required_clause_citations=["CLAUSE-7.3"],
            evidence_hierarchy_rule_applied=(
                "Prohibición contractual expresa de retenciones unilaterales por penalidades "
                "o cargos de cumplimiento sin adenda bilateral (Cláusula 7.3)."
            ),
            scenario_tags=["unilateral_penalty", "asn_fee", "slot_fee_rejected"],
        )

        documents = {
            "invoice": invoice,
            "purchase_order": po,
            "delivery": delivery,
            "payment": payment,
            "contract": contract,
        }
        return documents, gt

    def _generate_compound_mixed_case(
        self, case_id: str, difficulty_level: int
    ) -> Tuple[Dict[str, Any], GroundTruth]:
        """
        Tipología 4: Caso Mixto Multi-SKU (Compound / Multi-SKU Mixed Case).
        SKU 1 tiene un faltante genuino documentado en remisión firmada con sello ($500.00 -> Justificado).
        El comprador además descuenta un cobro arbitrario de cumplimiento ($400.00 -> Reclamable).
        Requiere resolución bifurcada: Nota de Crédito por $500 y Carta de Cobranza por $400.
        """
        sku1 = "PROD-001"
        sku2 = "PROD-002"
        p1 = Decimal("50.00")
        p2 = Decimal("100.00")
        q1 = 100
        q2 = 100
        missing_sku1 = 10

        billed_amount = (Decimal(q1) * p1) + (Decimal(q2) * p2)  # $5,000 + $10,000 = $15,000.00
        justified_shortage = Decimal("500.00")  # 10 x $50
        unilateral_charge = Decimal("400.00")
        total_deductions = justified_shortage + unilateral_charge  # $900.00
        amount_paid = billed_amount - total_deductions  # $14,100.00

        po_ref = f"PO-{case_id.upper()}"
        inv_ref = f"INV-{case_id.upper()}"
        del_ref = f"DEL-{case_id.upper()}"
        pay_ref = f"PAY-{case_id.upper()}"
        ctr_ref = "CTR-RETAIL-2026"

        po = PurchaseOrder(
            po_id=po_ref,
            vendor_id="VEN-001",
            customer_id="CUST-RETAIL-101",
            order_date="2026-08-01",
            currency="USD",
            items=[
                PurchaseOrderItem(
                    item_id=sku1,
                    description="Caja Aceite Vegetal 12x1L",
                    ordered_quantity=q1,
                    agreed_unit_price=p1,
                    total_price=Decimal("5000.00"),
                ),
                PurchaseOrderItem(
                    item_id=sku2,
                    description="Caja Café Gourmet Tostado 24x500g",
                    ordered_quantity=q2,
                    agreed_unit_price=p2,
                    total_price=Decimal("10000.00"),
                ),
            ],
            total_amount=billed_amount,
        )

        invoice = Invoice(
            invoice_id=inv_ref,
            vendor_id="VEN-001",
            customer_id="CUST-RETAIL-101",
            po_reference=po_ref,
            issue_date="2026-08-05",
            currency="USD",
            items=[
                InvoiceItem(
                    item_id=sku1,
                    description="Caja Aceite Vegetal 12x1L",
                    quantity=q1,
                    unit_price=p1,
                    total_price=Decimal("5000.00"),
                ),
                InvoiceItem(
                    item_id=sku2,
                    description="Caja Café Gourmet Tostado 24x500g",
                    quantity=q2,
                    unit_price=p2,
                    total_price=Decimal("10000.00"),
                ),
            ],
            subtotal=billed_amount,
            tax=Decimal("0.00"),
            total_amount=billed_amount,
        )

        # Carrier genera remisión con faltante FIRMADO y con SELLO para SKU1
        delivery = self.carrier.build_discrepant_delivery_note(
            delivery_id=del_ref,
            po_reference=po_ref,
            po_items=po.items,
            shortages={sku1: missing_sku1},
            signed=True,
            discrepancy_reported=True,
        )

        # Deducción 1: Faltante legítimo firmado
        ded1, ded1_gt = self.retailer.create_shortage_deduction(
            amount=justified_shortage,
            reference_doc=del_ref,
            is_pod_signed=True,
            units_missing=missing_sku1,
            sku=sku1,
        )

        # Deducción 2: Cargo unilateral arbitrario
        ded2, ded2_gt = self.retailer.create_administrative_fee_deduction(
            code="DED-COMPLIANCE",
            amount=unilateral_charge,
            reason="Retención unilateral por presunta discrepancia de etiquetado de tarimas",
        )

        payment = self.retailer.build_payment_receipt(
            payment_id=pay_ref,
            invoice_reference=inv_ref,
            invoice_total=billed_amount,
            deductions=[ded1, ded2],
        )

        contract = self.lawyer.generate_standard_contract(contract_id=ctr_ref)

        gt_lines = [
            GroundTruthLineItem(
                item_id=sku1,
                description="Caja Aceite Vegetal 12x1L",
                invoiced_qty=q1,
                received_qty=q1 - missing_sku1,
                missing_qty=missing_sku1,
                damaged_qty=0,
                invoiced_price=p1,
                agreed_price=p1,
            ),
            GroundTruthLineItem(
                item_id=sku2,
                description="Caja Café Gourmet Tostado 24x500g",
                invoiced_qty=q2,
                received_qty=q2,
                missing_qty=0,
                damaged_qty=0,
                invoiced_price=p2,
                agreed_price=p2,
            ),
        ]

        gt = GroundTruth(
            case_id=case_id,
            difficulty_level=difficulty_level,
            category=DiscrepancyCategory.MIXED,
            expected_action_type=CommercialActionType.MIXED_RESOLUTION,
            billed_amount=billed_amount,
            received_amount=amount_paid,
            difference=amount_paid - billed_amount,
            expected_justified_amount=justified_shortage,
            expected_claimable_amount=unilateral_charge,
            line_items=gt_lines,
            deductions=[ded1_gt, ded2_gt],
            required_evidence_citations=[inv_ref, del_ref, pay_ref, ctr_ref],
            required_clause_citations=["CLAUSE-4.2", "CLAUSE-7.3"],
            evidence_hierarchy_rule_applied=(
                "Resolución mixta obligatoria: emisión de Nota de Crédito ($500.00) por faltante acreditado "
                "en remisión firmada (Cláusula 4.2) y Carta de Cobranza ($400.00) por cargo unilateral improcedente (Cláusula 7.3)."
            ),
            scenario_tags=["multi_sku", "compound_case", "mixed_resolution"],
        )

        documents = {
            "invoice": invoice,
            "purchase_order": po,
            "delivery": delivery,
            "payment": payment,
            "contract": contract,
        }
        return documents, gt

    def _generate_tolerance_window_case(
        self, case_id: str, difficulty_level: int
    ) -> Tuple[Dict[str, Any], GroundTruth]:
        """
        Tipología 5: Ventana de Tolerancia Contractual (Contractual Tolerance Window).
        Orden de 1,000 unidades a granel ($20,000). Faltante de 12 unidades (1.2% < 2.0% franquicia).
        El comprador deduce $240. La Cláusula 6.1 prohíbe retenciones dentro del margen de tolerancia.
        La deducción es indebida y debe reclamarse al 100%.
        """
        sku = "PROD-BULK-01"
        invoiced_qty = 1000
        delivered_qty = 1000
        missing_qty = 12
        received_qty = 988
        unit_price = Decimal("20.00")
        billed_amount = Decimal("20000.00")
        tolerance_shortage_amount = Decimal("240.00")  # 12 x $20
        amount_paid = Decimal("19760.00")

        po_ref = f"PO-{case_id.upper()}"
        inv_ref = f"INV-{case_id.upper()}"
        del_ref = f"DEL-{case_id.upper()}"
        pay_ref = f"PAY-{case_id.upper()}"
        ctr_ref = "CTR-RETAIL-2026"

        po = PurchaseOrder(
            po_id=po_ref,
            vendor_id="VEN-001",
            customer_id="CUST-RETAIL-101",
            order_date="2026-08-10",
            currency="USD",
            items=[
                PurchaseOrderItem(
                    item_id=sku,
                    description="Saco Granel Azúcar Refinada 50kg",
                    ordered_quantity=invoiced_qty,
                    agreed_unit_price=unit_price,
                    total_price=billed_amount,
                )
            ],
            total_amount=billed_amount,
        )

        invoice = Invoice(
            invoice_id=inv_ref,
            vendor_id="VEN-001",
            customer_id="CUST-RETAIL-101",
            po_reference=po_ref,
            issue_date="2026-08-15",
            currency="USD",
            items=[
                InvoiceItem(
                    item_id=sku,
                    description="Saco Granel Azúcar Refinada 50kg",
                    quantity=invoiced_qty,
                    unit_price=unit_price,
                    total_price=billed_amount,
                )
            ],
            subtotal=billed_amount,
            tax=Decimal("0.00"),
            total_amount=billed_amount,
        )

        delivery = self.carrier.build_discrepant_delivery_note(
            delivery_id=del_ref,
            po_reference=po_ref,
            po_items=po.items,
            shortages={sku: missing_qty},
            signed=True,
            discrepancy_reported=True,
        )

        deduction, deduction_gt = self.retailer.create_tolerance_exempt_deduction(
            amount=tolerance_shortage_amount,
            reference_doc=del_ref,
            percentage_shortage=Decimal("1.20"),
            allowed_tolerance=Decimal("2.00"),
        )

        payment = self.retailer.build_payment_receipt(
            payment_id=pay_ref,
            invoice_reference=inv_ref,
            invoice_total=billed_amount,
            deductions=[deduction],
        )

        contract = self.lawyer.generate_standard_contract(contract_id=ctr_ref)

        gt_line = GroundTruthLineItem(
            item_id=sku,
            description="Saco Granel Azúcar Refinada 50kg",
            invoiced_qty=invoiced_qty,
            received_qty=received_qty,
            missing_qty=missing_qty,
            damaged_qty=0,
            invoiced_price=unit_price,
            agreed_price=unit_price,
        )

        gt = GroundTruth(
            case_id=case_id,
            difficulty_level=difficulty_level,
            category=DiscrepancyCategory.TOLERANCE_EXEMPT,
            expected_action_type=CommercialActionType.COLLECTION_LETTER,
            billed_amount=billed_amount,
            received_amount=amount_paid,
            difference=amount_paid - billed_amount,
            expected_justified_amount=Decimal("0.00"),
            expected_claimable_amount=tolerance_shortage_amount,
            line_items=[gt_line],
            deductions=[deduction_gt],
            required_evidence_citations=[inv_ref, del_ref, pay_ref, ctr_ref],
            required_clause_citations=["CLAUSE-6.1"],
            evidence_hierarchy_rule_applied=(
                "Faltante en volumen del 1.20% protegido por la franquicia de tolerancia "
                "del 2.00% estipulada en la Cláusula 6.1; retención económica indebida."
            ),
            scenario_tags=["volume_tolerance", "bulk_order", "retention_barred"],
        )

        documents = {
            "invoice": invoice,
            "purchase_order": po,
            "delivery": delivery,
            "payment": payment,
            "contract": contract,
        }
        return documents, gt

    def _generate_price_precedence_case(
        self, case_id: str, difficulty_level: int
    ) -> Tuple[Dict[str, Any], GroundTruth]:
        """
        Tipología 6: Cotización Expirada vs Prelación de OC (Expired Quote vs PO Precedence).
        El proveedor facturó a precio de lista ($100.00 x 100 = $10,000), pero la OC pactó
        precio promocional ($85.00 x 100 = $8,500). El comprador deduce $1,500.00.
        La Cláusula 3.1 otorga prevalencia jurídica a la OC; la deducción es 100% justificada.
        Acción requerida: emisión de Nota de Crédito por $1,500.00.
        """
        sku = "PROD-004"
        qty = 100
        invoiced_price = Decimal("100.00")
        agreed_price = Decimal("85.00")
        billed_amount = Decimal("10000.00")
        po_total = Decimal("8500.00")
        variance_amount = Decimal("1500.00")
        amount_paid = po_total

        po_ref = f"PO-{case_id.upper()}"
        inv_ref = f"INV-{case_id.upper()}"
        del_ref = f"DEL-{case_id.upper()}"
        pay_ref = f"PAY-{case_id.upper()}"
        ctr_ref = "CTR-RETAIL-2026"

        po = PurchaseOrder(
            po_id=po_ref,
            vendor_id="VEN-001",
            customer_id="CUST-RETAIL-101",
            order_date="2026-08-01",
            currency="USD",
            items=[
                PurchaseOrderItem(
                    item_id=sku,
                    description="Caja Licores Importados 12x750ml",
                    ordered_quantity=qty,
                    agreed_unit_price=agreed_price,
                    total_price=po_total,
                )
            ],
            total_amount=po_total,
        )

        invoice = Invoice(
            invoice_id=inv_ref,
            vendor_id="VEN-001",
            customer_id="CUST-RETAIL-101",
            po_reference=po_ref,
            issue_date="2026-08-05",
            currency="USD",
            items=[
                InvoiceItem(
                    item_id=sku,
                    description="Caja Licores Importados 12x750ml",
                    quantity=qty,
                    unit_price=invoiced_price,
                    total_price=billed_amount,
                )
            ],
            subtotal=billed_amount,
            tax=Decimal("0.00"),
            total_amount=billed_amount,
        )

        delivery = self.carrier.build_clean_delivery_note(
            delivery_id=del_ref,
            po_reference=po_ref,
            po_items=po.items,
        )

        deduction, deduction_gt = self.retailer.create_price_variance_deduction(
            amount=variance_amount,
            po_reference=po_ref,
            sku=sku,
        )

        payment = self.retailer.build_payment_receipt(
            payment_id=pay_ref,
            invoice_reference=inv_ref,
            invoice_total=billed_amount,
            deductions=[deduction],
        )

        contract = self.lawyer.generate_standard_contract(contract_id=ctr_ref)

        gt_line = GroundTruthLineItem(
            item_id=sku,
            description="Caja Licores Importados 12x750ml",
            invoiced_qty=qty,
            received_qty=qty,
            missing_qty=0,
            damaged_qty=0,
            invoiced_price=invoiced_price,
            agreed_price=agreed_price,
        )

        gt = GroundTruth(
            case_id=case_id,
            difficulty_level=difficulty_level,
            category=DiscrepancyCategory.PRICE_MISMATCH,
            expected_action_type=CommercialActionType.CREDIT_NOTE,
            billed_amount=billed_amount,
            received_amount=amount_paid,
            difference=amount_paid - billed_amount,
            expected_justified_amount=variance_amount,
            expected_claimable_amount=Decimal("0.00"),
            line_items=[gt_line],
            deductions=[deduction_gt],
            required_evidence_citations=[inv_ref, po_ref, pay_ref, ctr_ref],
            required_clause_citations=["CLAUSE-3.1"],
            evidence_hierarchy_rule_applied=(
                "Prevalencia estricta del precio pactado en la Orden de Compra sobre la Factura "
                "(Cláusula 3.1); deducción válidamente aplicada que amerita Nota de Crédito."
            ),
            scenario_tags=["price_variance", "po_precedence", "credit_note_issued"],
        )

        documents = {
            "invoice": invoice,
            "purchase_order": po,
            "delivery": delivery,
            "payment": payment,
            "contract": contract,
        }
        return documents, gt

    def _generate_enterprise_extensive_case(
        self, case_id: str, difficulty_level: int = 5
    ) -> Tuple[Dict[str, Any], GroundTruth]:
        """
        Tipología 7 / Tier 6: Expediente Masivo Multi-SKU de Alta Cuantía (Enterprise Extensive Docket).
        Sintetiza un expediente corporativo complejo con 12 SKUs industriales y tecnológicos,
        facturación de $185,400.00 USD, con múltiples faltantes físicos amparados por remisión
        firmada con sello ($5,100.00), cargos unilaterales por transmisión extemporánea de ASN ($1,200.00)
        y descuento financiero de pronto pago no pactado ($3,700.00). Retención total: $10,000.00 USD.
        Requiere resolución bifurcada: Nota de Crédito por $5,100.00 USD (con desglose de IVA)
        y Carta de Cobranza por $4,900.00 USD.
        Invariantes matemáticos de centavo:
          expected_justified_amount ($5,100.00) + expected_claimable_amount ($4,900.00) == total_deductions ($10,000.00) == billed_amount ($185,400.00) - received_amount ($175,400.00).
        """
        raw_items = [
            ("SKU-SRV-001", "Servidor Rack 2U Enterprise Dual Xeon 64C", 10, Decimal("4500.00")),     # 45,000
            ("SKU-NET-002", "Switch Top-of-Rack 48x25G + 6x100G", 8, Decimal("2800.00")),             # 22,400
            ("SKU-STR-003", "Cabina Almacenamiento All-Flash 24-Bay NVMe", 4, Decimal("6500.00")),     # 26,000
            ("SKU-PWR-004", "Modulo UPS Online Modular 10kVA", 6, Decimal("1900.00")),                 # 11,400
            ("SKU-CAB-005", "Gabinete Servidor 42U Blindado", 12, Decimal("750.00")),                  # 9,000
            ("SKU-SSD-006", "Disco NVMe Enterprise PCIe 7.68TB", 40, Decimal("350.00")),               # 14,000 (Faltante 10 uds = $3,500.00)
            ("SKU-RAM-007", "Modulo RAM DDR5 64GB 5600MHz ECC", 80, Decimal("180.00")),               # 14,400
            ("SKU-OPT-008", "Transceptor Optico 100G QSFP28 LR4", 30, Decimal("320.00")),              # 9,600  (Faltante 5 uds = $1,600.00)
            ("SKU-SEC-009", "Firewall Perimetral NGFW 40Gbps", 2, Decimal("8200.00")),                 # 16,400
            ("SKU-PDU-010", "PDU Monitoreable Trifasica 32A Zero-U", 20, Decimal("450.00")),           # 9,000
            ("SKU-KVM-011", "Conmutador Digital IP-KVM 16 Puertos", 5, Decimal("1100.00")),           # 5,500
            ("SKU-CBL-012", "Troncal Fibra Optica MPO-12 OM4 50m", 30, Decimal("90.00")),             # 2,700
        ]

        shortages = {
            "SKU-SSD-006": 10,  # 10 x $350.00 = $3,500.00
            "SKU-OPT-008": 5,   # 5 x $320.00 = $1,600.00
        }

        po_ref = f"PO-{case_id.upper()}"
        inv_ref = f"INV-{case_id.upper()}"
        del_ref = f"DEL-{case_id.upper()}"
        pay_ref = f"PAY-{case_id.upper()}"
        ctr_ref = "CTR-GLOBAL-ENTERPRISE-2026"

        po_items = []
        inv_items = []
        gt_lines = []
        billed_amount = Decimal("0.00")

        for sku, desc, qty, price in raw_items:
            line_total = Decimal(qty) * price
            billed_amount += line_total
            po_items.append(PurchaseOrderItem(
                item_id=sku,
                description=desc,
                ordered_quantity=qty,
                agreed_unit_price=price,
                total_price=line_total,
            ))
            inv_items.append(InvoiceItem(
                item_id=sku,
                description=desc,
                quantity=qty,
                unit_price=price,
                total_price=line_total,
            ))
            miss = shortages.get(sku, 0)
            gt_lines.append(GroundTruthLineItem(
                item_id=sku,
                description=desc,
                invoiced_qty=qty,
                received_qty=qty - miss,
                missing_qty=miss,
                damaged_qty=0,
                invoiced_price=price,
                agreed_price=price,
            ))

        justified_shortage = Decimal("5100.00")  # $3,500 + $1,600
        fee_asn = Decimal("1200.00")
        fee_early_discount = Decimal("3700.00")
        unilateral_charges = fee_asn + fee_early_discount  # $4,900.00
        total_deductions = justified_shortage + unilateral_charges  # $10,000.00
        amount_paid = billed_amount - total_deductions  # $175,400.00

        po = PurchaseOrder(
            po_id=po_ref,
            vendor_id="VEN-ENTERPRISE-GLOBAL",
            customer_id="CUST-MEGA-RETAIL",
            order_date="2026-08-01",
            currency="USD",
            items=po_items,
            total_amount=billed_amount,
        )

        invoice = Invoice(
            invoice_id=inv_ref,
            vendor_id="VEN-ENTERPRISE-GLOBAL",
            customer_id="CUST-MEGA-RETAIL",
            po_reference=po_ref,
            issue_date="2026-08-05",
            currency="USD",
            items=inv_items,
            subtotal=billed_amount,
            tax=Decimal("0.00"),
            total_amount=billed_amount,
        )

        delivery = self.carrier.build_discrepant_delivery_note(
            delivery_id=del_ref,
            po_reference=po_ref,
            po_items=po.items,
            shortages=shortages,
            signed=True,
            discrepancy_reported=True,
        )

        ded1, ded1_gt = self.retailer.create_shortage_deduction(
            amount=justified_shortage,
            reference_doc=del_ref,
            is_pod_signed=True,
            units_missing=15,
            sku="SKU-SSD-006, SKU-OPT-008",
        )
        ded2, ded2_gt = self.retailer.create_administrative_fee_deduction(
            code="DED-LATE-ASN",
            amount=fee_asn,
            reason="Penalización administrativa unilateral por transmisión extemporánea de archivo EDI ASN",
        )
        ded3, ded3_gt = self.retailer.create_administrative_fee_deduction(
            code="DED-UNILATERAL-DISCOUNT",
            amount=fee_early_discount,
            reason="Descuento financiero de pronto pago aplicado unilateralmente sin autorización de tesorería",
        )

        payment = self.retailer.build_payment_receipt(
            payment_id=pay_ref,
            invoice_reference=inv_ref,
            invoice_total=billed_amount,
            deductions=[ded1, ded2, ded3],
        )

        contract = self.lawyer.generate_standard_contract(contract_id=ctr_ref)

        gt = GroundTruth(
            case_id=case_id,
            difficulty_level=min(5, max(1, difficulty_level)),
            category=DiscrepancyCategory.MIXED,
            expected_action_type=CommercialActionType.MIXED_RESOLUTION,
            billed_amount=billed_amount,
            received_amount=amount_paid,
            difference=amount_paid - billed_amount,
            expected_justified_amount=justified_shortage,
            expected_claimable_amount=unilateral_charges,
            line_items=gt_lines,
            deductions=[ded1_gt, ded2_gt, ded3_gt],
            required_evidence_citations=[inv_ref, del_ref, pay_ref, ctr_ref],
            required_clause_citations=["CLAUSE-4.2", "CLAUSE-7.3"],
            evidence_hierarchy_rule_applied=(
                "Resolución bifurcada obligatoria en expediente masivo multi-SKU: aceptación de deducción justificada ($5,100.00 USD) "
                "por faltante en remisión firmada con sello (Cláusula 4.2) emitiendo Nota de Crédito, y reclamación formal íntegra ($4,900.00 USD) "
                "por penalidad EDI y descuento financiero unilateral indebido (Cláusula 7.3)."
            ),
            scenario_tags=["enterprise_mega", "multi_sku_extensive", "compound_mixed", "split_resolution"],
        )

        documents = {
            "invoice": invoice,
            "purchase_order": po,
            "delivery": delivery,
            "payment": payment,
            "contract": contract,
        }
        return documents, gt

    def export_case_to_disk(
        self,
        case_id: str,
        target_dir: Optional[Union[str, Path]] = None,
        typology: Optional[str] = None,
        difficulty_level: int = 1,
    ) -> Path:
        """
        Genera y exporta en disco el expediente completo en formato JSON compatible con DocumentReader:
        - invoice.json
        - purchase_order.json
        - delivery.json
        - payment.json
        - contract.json
        - ground_truth.json (archivo confidencial de auditoría)
        """
        documents, ground_truth = self.generate_case(
            case_id=case_id,
            typology=typology,
            difficulty_level=difficulty_level,
        )

        if target_dir is not None:
            base_path = Path(target_dir)
            # Si target_dir termina con el nombre del caso, no anidar doble
            if base_path.name == case_id:
                case_dir = base_path
            else:
                case_dir = base_path / case_id
        else:
            case_dir = settings.DATA_DIR / "cases" / case_id

        case_dir.mkdir(parents=True, exist_ok=True)

        # 1. invoice.json
        with open(case_dir / "invoice.json", "w", encoding="utf-8") as f:
            f.write(documents["invoice"].model_dump_json(indent=2))

        # 2. purchase_order.json
        with open(case_dir / "purchase_order.json", "w", encoding="utf-8") as f:
            f.write(documents["purchase_order"].model_dump_json(indent=2))

        # 3. delivery.json
        with open(case_dir / "delivery.json", "w", encoding="utf-8") as f:
            f.write(documents["delivery"].model_dump_json(indent=2))

        # 4. payment.json
        with open(case_dir / "payment.json", "w", encoding="utf-8") as f:
            f.write(documents["payment"].model_dump_json(indent=2))

        # 5. contract.json
        with open(case_dir / "contract.json", "w", encoding="utf-8") as f:
            f.write(documents["contract"].model_dump_json(indent=2))

        # 6. ground_truth.json
        with open(case_dir / "ground_truth.json", "w", encoding="utf-8") as f:
            f.write(ground_truth.model_dump_json(indent=2))

        return case_dir
