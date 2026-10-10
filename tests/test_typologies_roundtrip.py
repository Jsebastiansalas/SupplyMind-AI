import json
import shutil
import tempfile
from decimal import Decimal
from pathlib import Path
import pytest

from agent.training.factory.case_synthesizer import AdversarialCaseSynthesizer
from agent.training.factory.ground_truth import GroundTruth
from tools.document_reader.reader import load_case_documents, DocumentReaderError
from tools.reconciliation_engine.engine import reconcile_dispute_data, ReconciliationSummary


ALL_TYPOLOGIES = [
    "unsigned_pod",
    "extemporaneous_damage",
    "administrative_penalties",
    "compound_mixed",
    "tolerance_window",
    "price_precedence",
]


class TestTypologiesAndDiskPersistenceRoundtrip:
    """
    Adversarial verification suite for the 6 dispute typologies and disk persistence:
    1. In-memory synthesis
    2. Export to disk via export_case_to_disk
    3. Ingestion via load_case_documents
    4. Deterministic reconciliation verification
    """

    @pytest.mark.parametrize("typology", ALL_TYPOLOGIES)
    def test_typology_roundtrip_reconciliation_exact_amounts(self, typology: str):
        """
        Verify that for each of the 6 typologies:
        - In-memory generation produces valid documents and GroundTruth.
        - export_case_to_disk exports all 6 JSON files.
        - load_case_documents correctly ingests them.
        - reconcile_dispute_data produces identical mathematical amounts between in-memory and disk reloaded.
        """
        case_id = f"TEST_ROUNDTRIP_{typology.upper()}_01"
        synthesizer = AdversarialCaseSynthesizer()

        # 1. In-memory generation
        docs_mem, gt_mem = synthesizer.generate_case(case_id=case_id, typology=typology)
        summary_mem = reconcile_dispute_data(
            invoice=docs_mem["invoice"],
            purchase_order=docs_mem["purchase_order"],
            delivery=docs_mem["delivery"],
            payment=docs_mem["payment"],
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            # 2. Export to disk
            case_dir = synthesizer.export_case_to_disk(
                case_id=case_id,
                target_dir=Path(tmpdir) / case_id,
                typology=typology,
            )

            # Check all 6 files exist
            assert (case_dir / "invoice.json").is_file(), f"invoice.json missing for {typology}"
            assert (case_dir / "purchase_order.json").is_file(), f"purchase_order.json missing for {typology}"
            assert (case_dir / "delivery.json").is_file(), f"delivery.json missing for {typology}"
            assert (case_dir / "payment.json").is_file(), f"payment.json missing for {typology}"
            assert (case_dir / "contract.json").is_file(), f"contract.json missing for {typology}"
            assert (case_dir / "ground_truth.json").is_file(), f"ground_truth.json missing for {typology}"

            # Verify ground_truth.json round-trip fidelity
            with open(case_dir / "ground_truth.json", "r", encoding="utf-8") as f:
                gt_loaded = GroundTruth.model_validate_json(f.read())
            assert gt_loaded.case_id == gt_mem.case_id
            assert gt_loaded.billed_amount == gt_mem.billed_amount
            assert gt_loaded.received_amount == gt_mem.received_amount
            assert gt_loaded.difference == gt_mem.difference
            assert gt_loaded.expected_justified_amount == gt_mem.expected_justified_amount
            assert gt_loaded.expected_claimable_amount == gt_mem.expected_claimable_amount
            assert len(gt_loaded.line_items) == len(gt_mem.line_items)
            assert len(gt_loaded.deductions) == len(gt_mem.deductions)

            # 3. Ingest from disk via load_case_documents
            docs_disk = load_case_documents(str(case_dir))

            assert "invoice" in docs_disk
            assert "purchase_order" in docs_disk
            assert "delivery" in docs_disk
            assert "payment" in docs_disk
            assert "contract" in docs_disk

            # 4. Reconciliation on reloaded models
            summary_disk = reconcile_dispute_data(
                invoice=docs_disk["invoice"],
                purchase_order=docs_disk["purchase_order"],
                delivery=docs_disk["delivery"],
                payment=docs_disk["payment"],
            )

            # 5. Exact match verification (all amounts in Decimal)
            assert isinstance(summary_disk.billed_amount, Decimal)
            assert isinstance(summary_disk.received_amount, Decimal)
            assert isinstance(summary_disk.difference, Decimal)
            assert isinstance(summary_disk.total_deductions_applied, Decimal)
            assert isinstance(summary_disk.total_missing_amount, Decimal)
            assert isinstance(summary_disk.total_damaged_amount, Decimal)
            assert isinstance(summary_disk.total_price_discrepancy_amount, Decimal)
            assert isinstance(summary_disk.justified_deductions_amount, Decimal)
            assert isinstance(summary_disk.unjustified_deductions_amount, Decimal)

            assert summary_disk.billed_amount == summary_mem.billed_amount
            assert summary_disk.received_amount == summary_mem.received_amount
            assert summary_disk.difference == summary_mem.difference
            assert summary_disk.total_deductions_applied == summary_mem.total_deductions_applied
            assert summary_disk.total_missing_amount == summary_mem.total_missing_amount
            assert summary_disk.total_damaged_amount == summary_mem.total_damaged_amount
            assert summary_disk.total_price_discrepancy_amount == summary_mem.total_price_discrepancy_amount
            assert summary_disk.justified_deductions_amount == summary_mem.justified_deductions_amount
            assert summary_disk.unjustified_deductions_amount == summary_mem.unjustified_deductions_amount
            assert summary_disk.primary_discrepancy_type == summary_mem.primary_discrepancy_type
            assert len(summary_disk.discrepancies) == len(summary_mem.discrepancies)

            # Item by item discrepancy check
            for disc_disk, disc_mem in zip(summary_disk.discrepancies, summary_mem.discrepancies):
                assert disc_disk.item_id == disc_mem.item_id
                assert disc_disk.billed_quantity == disc_mem.billed_quantity
                assert disc_disk.received_quantity == disc_mem.received_quantity
                assert disc_disk.missing_quantity == disc_mem.missing_quantity
                assert disc_disk.damaged_quantity == disc_mem.damaged_quantity
                assert disc_disk.agreed_unit_price == disc_mem.agreed_unit_price
                assert disc_disk.invoiced_unit_price == disc_mem.invoiced_unit_price
                assert disc_disk.price_difference == disc_mem.price_difference
                assert disc_disk.missing_amount == disc_mem.missing_amount
                assert disc_disk.damaged_amount == disc_mem.damaged_amount
                assert disc_disk.total_impact == disc_mem.total_impact

            # Check arithmetic invariants
            assert summary_disk.difference == summary_disk.received_amount - summary_disk.billed_amount
            assert (
                summary_disk.justified_deductions_amount + summary_disk.unjustified_deductions_amount
                == summary_disk.total_deductions_applied
            )

    @pytest.mark.parametrize("typology", ALL_TYPOLOGIES)
    def test_typology_across_all_difficulty_levels(self, typology: str):
        """Verify round-trip across difficulty levels 1 through 5."""
        synthesizer = AdversarialCaseSynthesizer()
        with tempfile.TemporaryDirectory() as tmpdir:
            for level in range(1, 6):
                case_id = f"CASE_LVL_{level}_{typology}"
                case_dir = synthesizer.export_case_to_disk(
                    case_id=case_id,
                    target_dir=Path(tmpdir) / case_id,
                    typology=typology,
                    difficulty_level=level,
                )
                docs = load_case_documents(str(case_dir))
                summary = reconcile_dispute_data(
                    invoice=docs["invoice"],
                    purchase_order=docs["purchase_order"],
                    delivery=docs["delivery"],
                    payment=docs["payment"],
                )
                assert summary.billed_amount > Decimal("0.00")
                assert summary.received_amount > Decimal("0.00")
                assert summary.difference < Decimal("0.00")

    def test_path_with_spaces_and_nested_folders(self):
        """Stress-test export and load when path has spaces or unusual characters."""
        synthesizer = AdversarialCaseSynthesizer()
        with tempfile.TemporaryDirectory() as tmpdir:
            spaced_dir = Path(tmpdir) / "Special Case Directory With Spaces [2026]"
            case_id = "CASE SPACES 001"
            case_dir = synthesizer.export_case_to_disk(
                case_id=case_id,
                target_dir=spaced_dir / case_id,
                typology="compound_mixed",
            )
            assert case_dir.exists()
            docs = load_case_documents(str(case_dir))
            summary = reconcile_dispute_data(
                invoice=docs["invoice"],
                purchase_order=docs["purchase_order"],
                delivery=docs["delivery"],
                payment=docs["payment"],
            )
            assert summary.billed_amount == Decimal("15000.00")
            assert summary.received_amount == Decimal("14100.00")
            assert summary.difference == Decimal("-900.00")

    def test_overwriting_existing_case_directory(self):
        """Verify export_case_to_disk can overwrite/update an existing case folder cleanly."""
        synthesizer = AdversarialCaseSynthesizer()
        with tempfile.TemporaryDirectory() as tmpdir:
            case_id = "CASE_OVERWRITE_001"
            target = Path(tmpdir) / case_id
            # First export: unsigned_pod
            synthesizer.export_case_to_disk(case_id=case_id, target_dir=target, typology="unsigned_pod")
            docs1 = load_case_documents(str(target))
            assert docs1["invoice"].total_amount == Decimal("10000.00")

            # Second export into same target: tolerance_window
            synthesizer.export_case_to_disk(case_id=case_id, target_dir=target, typology="tolerance_window")
            docs2 = load_case_documents(str(target))
            assert docs2["invoice"].total_amount == Decimal("20000.00")

    def test_missing_files_error_handling(self):
        """Verify load_case_documents raises DocumentReaderError when required files are missing."""
        synthesizer = AdversarialCaseSynthesizer()
        with tempfile.TemporaryDirectory() as tmpdir:
            case_id = "CASE_MISSING_DELIVERY"
            target = Path(tmpdir) / case_id
            synthesizer.export_case_to_disk(case_id=case_id, target_dir=target, typology="unsigned_pod")
            
            # Delete delivery.json
            (target / "delivery.json").unlink()
            
            # Deleting a required document must raise DocumentReaderError (either due to missing doc or schema mismatch)
            with pytest.raises(DocumentReaderError):
                load_case_documents(str(target))

