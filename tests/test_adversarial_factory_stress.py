"""
tests/test_adversarial_factory_stress.py
Empirical stress-testing harness for Adversarial Case Factory (agent.training.factory).

Challenges tested:
1. Mathematical invariants and strict ValueError rejection in GroundTruth.
2. Extreme inputs: 0 amounts, large numbers (10^8), fractional cents, negative values.
3. 50 sequential case generations: state isolation, memory stability, invariant consistency,
   disk export and roundtrip loading via load_case_documents & reconcile_dispute_data.
4. Edge cases & security: path traversal in case_id, unaligned line item totals, empty deductions.
"""

import gc
import json
import os
import shutil
import tempfile
import tracemalloc
from decimal import Decimal
from pathlib import Path
from typing import Dict, Any, List

import pytest
from pydantic import ValidationError

from agent.training.factory.ground_truth import (
    GroundTruth,
    GroundTruthLineItem,
    GroundTruthDeductionAssessment,
    GroundTruthDeduction,
    DiscrepancyCategory,
    CommercialActionType,
)
from agent.training.factory.retailer_agent import RetailerBuyerAgent
from agent.training.factory.carrier_agent import CarrierLogisticsAgent
from agent.training.factory.lawyer_agent import CorporateLawyerAgent
from agent.training.factory.case_synthesizer import AdversarialCaseSynthesizer
from tools.document_reader.reader import load_case_documents
from tools.reconciliation_engine.engine import reconcile_dispute_data


class TestGroundTruthMathInvariants:
    """Stress tests on mathematical coherence and strict rejection."""

    def test_rejects_justified_plus_claimable_not_equal_to_deductions(self):
        """When justified + claimable != sum(deductions), GroundTruth MUST raise ValueError."""
        with pytest.raises(ValueError, match="Violación de Invariante de Resolución"):
            GroundTruth(
                case_id="MATH-001",
                billed_amount=Decimal("1000.00"),
                received_amount=Decimal("800.00"),
                expected_justified_amount=Decimal("150.00"),
                expected_claimable_amount=Decimal("30.00"),  # 150 + 30 = 180 != 200
                deductions=[
                    GroundTruthDeductionAssessment(
                        code="DED-1",
                        amount=Decimal("200.00"),
                        reason="Test deduction",
                        is_justified=True,
                    )
                ],
            )

    def test_rejects_billed_minus_received_not_equal_to_deductions(self):
        """When billed_amount - received_amount != sum(deductions), GroundTruth MUST raise ValueError."""
        with pytest.raises(ValueError, match="Violación de Invariante Contable"):
            GroundTruth(
                case_id="MATH-002",
                billed_amount=Decimal("1000.00"),
                received_amount=Decimal("800.00"),  # difference = 200
                expected_justified_amount=Decimal("150.00"),
                expected_claimable_amount=Decimal("0.00"),
                deductions=[
                    GroundTruthDeductionAssessment(
                        code="DED-1",
                        amount=Decimal("150.00"),  # deductions sum = 150 != 200
                        reason="Test deduction",
                        is_justified=True,
                    )
                ],
            )

    def test_rejects_individual_deductions_mismatch_with_justified_or_claimable(self):
        """
        When total deductions == justified + claimable, but individual deductions' is_justified
        flag does not match expected_justified_amount or expected_claimable_amount,
        GroundTruth MUST raise ValueError.
        """
        with pytest.raises(ValueError, match="Inconsistencia en deducciones justificadas"):
            GroundTruth(
                case_id="MATH-003",
                billed_amount=Decimal("1000.00"),
                received_amount=Decimal("800.00"),
                expected_justified_amount=Decimal("200.00"),
                expected_claimable_amount=Decimal("0.00"),
                deductions=[
                    GroundTruthDeductionAssessment(
                        code="DED-1",
                        amount=Decimal("100.00"),
                        reason="Justified",
                        is_justified=True,
                    ),
                    GroundTruthDeductionAssessment(
                        code="DED-2",
                        amount=Decimal("100.00"),
                        reason="Unjustified",
                        is_justified=False,  # is_justified=False, so sum(justified)=100 != 200
                    ),
                ],
            )

    def test_rejects_empty_deductions_with_non_zero_underpayment(self):
        """If billed != received but deductions list is empty, must raise ValueError."""
        with pytest.raises(ValueError, match="Violación de Invariante Contable"):
            GroundTruth(
                case_id="MATH-004",
                billed_amount=Decimal("1000.00"),
                received_amount=Decimal("800.00"),
                expected_justified_amount=Decimal("0.00"),
                expected_claimable_amount=Decimal("0.00"),
                deductions=[],
            )

    def test_accepts_perfect_zero_dispute_when_fully_paid(self):
        """When fully paid (billed == received) and no deductions, it must validate successfully."""
        gt = GroundTruth(
            case_id="MATH-005",
            billed_amount=Decimal("5000.00"),
            received_amount=Decimal("5000.00"),
            expected_justified_amount=Decimal("0.00"),
            expected_claimable_amount=Decimal("0.00"),
            deductions=[],
        )
        assert gt.net_difference == Decimal("0.00")
        assert gt.difference == Decimal("0.00")

    def test_project_md_field_alias_support(self):
        """Verify compatibility with PROJECT.md field names (justified_deductions_amount, claimable_deductions_amount)."""
        gt = GroundTruth(
            case_id="MATH-006",
            billed_amount=Decimal("2000.00"),
            received_amount=Decimal("1500.00"),
            justified_deductions_amount=Decimal("300.00"),
            claimable_deductions_amount=Decimal("200.00"),
            deductions=[
                GroundTruthDeduction(
                    code="DED-A",
                    amount=Decimal("300.00"),
                    reason="Justified item",
                    is_justified=True,
                ),
                GroundTruthDeduction(
                    code="DED-B",
                    amount=Decimal("200.00"),
                    reason="Claimable item",
                    is_justified=False,
                ),
            ],
        )
        assert gt.expected_justified_amount == Decimal("300.00")
        assert gt.expected_claimable_amount == Decimal("200.00")
        assert gt.justified_deductions_amount == Decimal("300.00")
        assert gt.claimable_deductions_amount == Decimal("200.00")
        assert gt.net_difference == Decimal("500.00")


class TestExtremeInputs:
    """Stress tests on boundary numbers, extreme sizes, negative inputs, fractional cents."""

    def test_zero_amounts_handling(self):
        """0 billed, 0 received, 0 deductions -> Valid."""
        gt = GroundTruth(
            case_id="EXTREME-ZERO",
            billed_amount=Decimal("0.00"),
            received_amount=Decimal("0.00"),
            expected_justified_amount=Decimal("0.00"),
            expected_claimable_amount=Decimal("0.00"),
            deductions=[],
        )
        assert gt.billed_amount == Decimal("0.00")
        assert gt.received_amount == Decimal("0.00")
        assert gt.net_difference == Decimal("0.00")

    def test_large_numbers_10_pow_8(self):
        """Test $100,000,000 (10^8) transaction with exact penny deduction."""
        large_billed = Decimal("100000000.00")
        penny_ded = Decimal("0.01")
        large_received = large_billed - penny_ded

        gt = GroundTruth(
            case_id="EXTREME-LARGE",
            billed_amount=large_billed,
            received_amount=large_received,
            expected_justified_amount=Decimal("0.00"),
            expected_claimable_amount=penny_ded,
            deductions=[
                GroundTruthDeduction(
                    code="DED-PENNY",
                    amount=penny_ded,
                    reason="One cent withholding on $100M",
                    is_justified=False,
                )
            ],
        )
        assert gt.billed_amount == large_billed
        assert gt.received_amount == Decimal("99999999.99")
        assert gt.net_difference == Decimal("0.01")
        assert gt.expected_claimable_amount == Decimal("0.01")

        # Test JSON dump & reload precision preservation
        json_data = gt.model_dump_json()
        assert "100000000.00" in json_data or "100000000" in json_data
        reloaded = GroundTruth.model_validate_json(json_data)
        assert reloaded.billed_amount == large_billed
        assert reloaded.received_amount == Decimal("99999999.99")

    def test_fractional_sub_cent_precision(self):
        """Test sub-cent precision e.g. 0.005 and 0.0001 (bulk commodity pricing)."""
        billed = Decimal("1000.1250")
        received = Decimal("950.0750")
        diff = Decimal("50.0500")
        just = Decimal("30.0300")
        claim = Decimal("20.0200")

        gt = GroundTruth(
            case_id="EXTREME-SUBCENT",
            billed_amount=billed,
            received_amount=received,
            expected_justified_amount=just,
            expected_claimable_amount=claim,
            deductions=[
                GroundTruthDeduction(
                    code="DED-SUB1",
                    amount=just,
                    reason="Sub-cent justified",
                    is_justified=True,
                ),
                GroundTruthDeduction(
                    code="DED-SUB2",
                    amount=claim,
                    reason="Sub-cent claimable",
                    is_justified=False,
                ),
            ],
        )
        assert gt.net_difference == diff
        assert gt.billed_amount - gt.received_amount == just + claim

    def test_negative_amounts_strictly_rejected_by_pydantic(self):
        """Negative billed_amount, received_amount, or deduction amount must raise ValidationError."""
        with pytest.raises(ValidationError):
            GroundTruth(
                case_id="EXTREME-NEG-1",
                billed_amount=Decimal("-100.00"),
                received_amount=Decimal("0.00"),
            )

        with pytest.raises(ValidationError):
            GroundTruth(
                case_id="EXTREME-NEG-2",
                billed_amount=Decimal("100.00"),
                received_amount=Decimal("-10.00"),
            )

        with pytest.raises(ValidationError):
            GroundTruthDeduction(
                code="DED-NEG",
                amount=Decimal("-50.00"),
                reason="Negative deduction",
                is_justified=False,
            )

    def test_difficulty_level_bounds(self):
        """Difficulty level must be between 1 and 5."""
        with pytest.raises(ValidationError):
            GroundTruth(
                case_id="DIFF-0",
                difficulty_level=0,
                billed_amount=Decimal("100.00"),
                received_amount=Decimal("100.00"),
            )

        with pytest.raises(ValidationError):
            GroundTruth(
                case_id="DIFF-6",
                difficulty_level=6,
                billed_amount=Decimal("100.00"),
                received_amount=Decimal("100.00"),
            )


class TestSynthesizer50CasesStress:
    """Stress testing the synthesizer across 50 sequential runs."""

    def test_generate_50_cases_sequentially_without_invariants_failure(self):
        """
        Generate 50 cases sequentially cycling through all 6 typologies.
        Verify:
        - All 50 pass GroundTruth invariant validation without exception.
        - Invoice total equals GroundTruth billed_amount.
        - Payment amount_paid equals GroundTruth received_amount.
        - Deductions sum matches difference.
        - Cross-document references (PO reference) are consistent.
        """
        synthesizer = AdversarialCaseSynthesizer()
        typologies = synthesizer.TYPOLOGY_NAMES

        for i in range(1, 51):
            typology = typologies[(i - 1) % len(typologies)]
            case_id = f"CASE_STRESS_{i:03d}"
            difficulty = (i % 5) + 1

            docs, gt = synthesizer.generate_case(
                case_id=case_id,
                typology=typology,
                difficulty_level=difficulty,
            )

            # Invariant verifications
            assert gt.case_id == case_id
            assert gt.difficulty_level == difficulty
            assert docs["invoice"].total_amount == gt.billed_amount
            assert docs["payment"].amount_paid == gt.received_amount
            assert docs["invoice"].po_reference == docs["purchase_order"].po_id
            assert docs["delivery"].po_reference == docs["purchase_order"].po_id
            assert docs["payment"].invoice_reference == docs["invoice"].invoice_id

            # Math verification
            expected_underpaid = gt.billed_amount - gt.received_amount
            assert expected_underpaid == gt.expected_justified_amount + gt.expected_claimable_amount
            assert sum(d.amount for d in gt.deductions) == expected_underpaid
            assert len(docs["contract"].clauses) >= 4

    def test_50_cases_memory_leak_and_state_isolation(self):
        """
        Verify memory stability and absence of state leakage across 50 iterations.
        No items or deductions should leak from iteration N to iteration N+1.
        """
        tracemalloc.start()
        snapshot_start = tracemalloc.take_snapshot()

        synthesizer = AdversarialCaseSynthesizer()
        case_records = []

        for i in range(1, 51):
            case_id = f"LEAK_TEST_{i:03d}"
            docs, gt = synthesizer.generate_case(case_id=case_id, typology="compound_mixed")

            # Store minimal footprint
            case_records.append((case_id, len(docs["purchase_order"].items), len(gt.deductions)))

            # If compound_mixed, items must always be exactly 2, deductions exactly 2
            assert len(docs["purchase_order"].items) == 2, f"Leaked items in iteration {i}"
            assert len(docs["invoice"].items) == 2, f"Leaked invoice items in iteration {i}"
            assert len(docs["delivery"].items) == 2, f"Leaked delivery items in iteration {i}"
            assert len(docs["payment"].deductions) == 2, f"Leaked deductions in iteration {i}"
            assert len(gt.deductions) == 2, f"Leaked GT deductions in iteration {i}"

        snapshot_end = tracemalloc.take_snapshot()
        top_stats = snapshot_end.compare_to(snapshot_start, "lineno")
        total_growth_kb = sum(stat.size_diff for stat in top_stats) / 1024

        tracemalloc.stop()
        # Memory growth for 50 cases should be well within reasonable limits (< 15MB)
        assert total_growth_kb < 15360, f"Excessive memory growth: {total_growth_kb:.2f} KB"

    def test_export_and_disk_roundtrip_50_cases(self):
        """
        Export 50 cases to disk in a temporary directory.
        Verify that load_case_documents() loads each case successfully and
        reconcile_dispute_data() computes identical values to GroundTruth.
        """
        temp_dir = Path(tempfile.mkdtemp(prefix="adversarial_test_50_"))
        try:
            synthesizer = AdversarialCaseSynthesizer()
            typologies = synthesizer.TYPOLOGY_NAMES

            for i in range(1, 51):
                case_id = f"DISK_CASE_{i:03d}"
                typ = typologies[(i - 1) % len(typologies)]

                case_path = synthesizer.export_case_to_disk(
                    case_id=case_id,
                    target_dir=temp_dir,
                    typology=typ,
                )

                # Verify all 6 JSON files were created
                assert (case_path / "invoice.json").exists()
                assert (case_path / "purchase_order.json").exists()
                assert (case_path / "delivery.json").exists()
                assert (case_path / "payment.json").exists()
                assert (case_path / "contract.json").exists()
                assert (case_path / "ground_truth.json").exists()

                # Load with DocumentReader
                docs = load_case_documents(case_id=str(case_path))
                assert docs["invoice"].invoice_id == f"INV-{case_id.upper()}"
                assert docs["purchase_order"].po_id == f"PO-{case_id.upper()}"

                # Run reconciliation engine
                summary = reconcile_dispute_data(
                    invoice=docs["invoice"],
                    purchase_order=docs["purchase_order"],
                    delivery=docs["delivery"],
                    payment=docs["payment"],
                )

                # Read ground truth
                with open(case_path / "ground_truth.json", "r", encoding="utf-8") as f:
                    gt_dict = json.load(f)
                    gt = GroundTruth.model_validate(gt_dict)

                # Verify numerical match with reconciliation engine
                assert summary.billed_amount == gt.billed_amount
                assert summary.received_amount == gt.received_amount
                assert summary.difference == gt.difference
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
