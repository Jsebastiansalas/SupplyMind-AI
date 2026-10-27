"""
Tests Unitarios y de Integración para el Generador de Datos Reales B2B (Sprint 3.1).

Valida:
1. Integridad y completitud del catálogo de retailers y matriz de deducciones (US-302).
2. Síntesis paramétrica de expedientes comerciales y conservación de invariantes contables (US-301).
3. Conformidad Pydantic estricta de todos los documentos generados.
4. Compatibilidad con el lector resiliente de documentos (load_case_documents).
"""

from decimal import Decimal
from pathlib import Path
import pytest

from data.models import (
    Invoice, PurchaseOrder, DeliveryNote, PaymentReceipt, CommercialContract
)
from agent.training.factory.ground_truth import GroundTruth, DiscrepancyCategory
from tools.document_reader.reader import load_case_documents
from tools.real_data_generator.retailer_catalog import (
    RETAILER_CATALOG,
    get_retailer_profile,
    list_available_retailers,
    find_deduction_policy
)
from tools.real_data_generator.case_synthesizer import (
    EnterpriseCaseSynthesizer,
    CaseDossier
)


class TestRetailerCatalog:
    """Pruebas del Catálogo Maestro de Retailers y Matriz de Deducciones (US-302)."""

    def test_catalog_has_major_b2b_enterprises(self):
        """Verifica que el catálogo incluya al menos 15 grandes corporativos líderes."""
        retailers = list_available_retailers()
        assert len(retailers) >= 15

        essential_buyers = [
            "AMAZON_MX", "WALMART_MX", "MERCADOLIBRE_MX", "OXXO_FEMSA",
            "LIVERPOOL_MX", "CHEDRAUI_MX", "SORIANA_MX", "COSTCO_MX",
            "CISCO_MX", "SAMSUNG_MX", "LG_MX", "APPLE_MX",
            "TRUPER_MX", "BIOFARMA_MX", "INDITEX_MX", "SONY_MX"
        ]
        for buyer_id in essential_buyers:
            assert buyer_id in retailers, f"Falta el comprador esencial '{buyer_id}' en el catálogo"

    def test_retailer_fiscal_and_logistics_topology(self):
        """Valida RFCs con formato fiscal SAT y CEDIS reales."""
        for buyer_id, profile in RETAILER_CATALOG.items():
            # RFC debe tener 12 o 13 caracteres alfanuméricos
            assert len(profile.rfc) in [12, 13], f"RFC inválido para {buyer_id}: '{profile.rfc}'"
            assert profile.rfc.isalnum(), f"RFC contiene caracteres inválidos: '{profile.rfc}'"
            # Código postal debe tener 5 dígitos
            assert len(profile.postal_code) == 5, f"CP inválido para {buyer_id}: '{profile.postal_code}'"
            # Debe tener al menos un CEDIS y un supervisor
            assert len(profile.primary_cedis_list) >= 1, f"{buyer_id} no tiene CEDIS asignado"
            assert len(profile.warehouse_supervisors) >= 1, f"{buyer_id} no tiene supervisores"
            # Cláusulas contractuales mínimas
            assert len(profile.contract_clauses) >= 1, f"{buyer_id} no tiene cláusulas marco"

    def test_deduction_matrix_definitions(self):
        """Valida que las políticas de deducción cuenten con contra-estrategias de disputa."""
        amazon = get_retailer_profile("AMAZON_MX")
        assert amazon is not None
        asn_deduction = find_deduction_policy("AMAZON_MX", "ASN-LATE-EDI856")
        assert asn_deduction is not None
        assert asn_deduction.is_frequently_abusive is True
        assert "EDI 997" in asn_deduction.dispute_counter_strategy

        walmart = get_retailer_profile("WALMART_MX")
        assert walmart is not None
        early_pay = find_deduction_policy("WALMART_MX", "EARLY-PAY-2%")
        assert early_pay is not None
        assert early_pay.typical_penalty_pct == Decimal("2.00")
        assert "15 días" in early_pay.dispute_counter_strategy


class TestEnterpriseCaseSynthesizer:
    """Pruebas del Sintetizador Paramétrico de Casos (US-301)."""

    def test_synthesize_case_mathematical_conservation(self):
        """
        Garantiza la conservación contable absoluta:
        Facturado - Recibido = Suma Deducciones = Justificado + Reclamable
        """
        dossier = EnterpriseCaseSynthesizer.synthesize_custom_case(
            case_id="test_case_synthesis_math",
            buyer_id="WALMART_MX",
            category=DiscrepancyCategory.COMPOUND_MIXED if hasattr(DiscrepancyCategory, "COMPOUND_MIXED") else DiscrepancyCategory.MIXED,
            items_spec=[
                {
                    "sku": "SKU-WHEY-2KG",
                    "description": "Proteína Whey Isolate 2kg",
                    "ordered_qty": 100,
                    "invoiced_qty": 100,
                    "delivered_qty": 100,
                    "received_qty": 80,
                    "missing_qty": 20,
                    "agreed_price": Decimal("45.00")
                }
            ],
            deductions_spec=[
                {
                    "code": "SHORTAGE-DOCK",
                    "reason": "Deducción por 20 bultos faltantes s/ remisión con sello",
                    "amount": Decimal("900.00"),
                    "is_justified": True,
                    "clause_ref": "CLAUSE-4.2"
                },
                {
                    "code": "EARLY-PAY-2%",
                    "reason": "Descuento por pronto pago extemporáneo a los 45 días",
                    "amount": Decimal("100.00"),
                    "is_justified": False,
                    "clause_ref": "CLAUSE-7.2"
                }
            ]
        )

        # 1. Total facturado
        expected_billed = Decimal("4500.00")
        assert dossier.invoice.total_amount == expected_billed

        # 2. Total pagado y deducciones
        expected_deductions = Decimal("1000.00")
        assert dossier.payment.amount_paid == Decimal("3500.00")
        assert sum(d.amount for d in dossier.payment.deductions) == expected_deductions

        # 3. Ground truth invariante
        gt = dossier.ground_truth
        assert gt.billed_amount == expected_billed
        assert gt.received_amount == Decimal("3500.00")
        assert gt.expected_justified_amount == Decimal("900.00")
        assert gt.expected_claimable_amount == Decimal("100.00")
        assert gt.expected_justified_amount + gt.expected_claimable_amount == expected_deductions

    def test_synthesized_documents_pydantic_validation(self, tmp_path):
        """Verifica que los documentos generados se guarden y carguen con load_case_documents."""
        case_dir = tmp_path / "case_test_roundtrip"
        dossier = EnterpriseCaseSynthesizer.synthesize_custom_case(
            case_id="case_test_roundtrip",
            buyer_id="MERCADOLIBRE_MX",
            category=DiscrepancyCategory.UNILATERAL_PENALTY,
            items_spec=[
                {
                    "sku": "SKU-HEADSET-BT",
                    "ordered_qty": 50,
                    "invoiced_qty": 50,
                    "delivered_qty": 50,
                    "received_qty": 50,
                    "agreed_price": Decimal("45.00")
                }
            ],
            deductions_spec=[
                {
                    "code": "CROSSDOCK-MISROUTING",
                    "reason": "Cargo por extravío en cross-docking",
                    "amount": Decimal("225.00"),
                    "is_justified": False,
                    "clause_ref": "CLAUSE-5.1"
                }
            ]
        )

        files = dossier.save_to_directory(case_dir)
        assert len(files) == 6
        assert (case_dir / "invoice.json").exists()
        assert (case_dir / "purchase_order.json").exists()
        assert (case_dir / "delivery.json").exists()
        assert (case_dir / "payment.json").exists()
        assert (case_dir / "contract.json").exists()
        assert (case_dir / "ground_truth.json").exists()

        # Cargar con el cargador oficial del sistema
        docs = load_case_documents(str(case_dir))
        assert isinstance(docs["invoice"], Invoice)
        assert isinstance(docs["purchase_order"], PurchaseOrder)
        assert isinstance(docs["delivery"], DeliveryNote)
        assert isinstance(docs["payment"], PaymentReceipt)
        assert isinstance(docs["contract"], CommercialContract)

    def test_synthesizer_rejects_deductions_exceeding_invoice(self):
        """El sintetizador debe rechazar deducciones superiores al total facturado."""
        with pytest.raises(ValueError, match="exceden total facturado"):
            EnterpriseCaseSynthesizer.synthesize_custom_case(
                case_id="case_invalid_over_deducted",
                buyer_id="AMAZON_MX",
                category=DiscrepancyCategory.UNILATERAL_PENALTY,
                items_spec=[
                    {
                        "sku": "SKU-NVME-4TB",
                        "ordered_qty": 1,
                        "agreed_price": Decimal("100.00")
                    }
                ],
                deductions_spec=[
                    {
                        "code": "EXCESS-DED",
                        "reason": "Deducción absurda superior al total",
                        "amount": Decimal("500.00"),
                        "is_justified": False
                    }
                ]
            )
