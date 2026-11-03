"""
tests/test_multiformat_real_cases.py
Fase 10 - Sprint 10.6: Suite de Pruebas de Ingesta Multiformato (.csv, .xlsx, .txt, .json)
y Casos Reales Abiertos de Cadena de Suministro (DataCo Global Smart Supply Chain Dataset).
"""

import json
from decimal import Decimal
from pathlib import Path

from tools.document_reader.multiformat_parser import MultiFormatParser
from tools.document_reader.reader import load_case_documents
from agent.core.skynet_runner import SkynetRunner

ROOT_DIR = Path(__file__).resolve().parent.parent
REAL_CASES_DIR = ROOT_DIR / "data" / "real_supply_chain_cases"


def test_openxml_xlsx_native_roundtrip(tmp_path: Path):
    """
    Verifica que el motor nativo OpenXML (.xlsx) escriba y lea hojas de cálculo
    con metadatos y filas tabulares sin pérdida de precisión.
    """
    xlsx_file = tmp_path / "test_invoice.xlsx"
    MultiFormatParser.write_xlsx_workbook(
        xlsx_file,
        headers=["item_id", "description", "quantity", "unit_price", "total_price"],
        rows=[
            ["DC-1360", "Pelican Sunstream 100 Kayak", 10, "199.99", "1999.90"],
            ["DC-1073", "O'Brien Men's Neoprene Life Vest", 20, "49.98", "999.60"],
        ],
        metadata={
            "invoice_id": "INV-TEST-XLSX",
            "vendor_id": "DATACO-HUB",
            "customer_id": "BUYER-01",
            "subtotal": "2999.50",
            "total_amount": "2999.50",
        },
    )

    assert xlsx_file.exists()
    meta, rows, full_text = MultiFormatParser.read_xlsx_grid(xlsx_file)
    assert meta["invoice_id"] == "INV-TEST-XLSX"
    assert len(rows) == 2
    assert rows[0]["item_id"] == "DC-1360"
    assert rows[1]["total_price"] == "999.60"
    assert "Pelican Sunstream 100 Kayak" in full_text

    inv_model = MultiFormatParser.parse_tabular_document(xlsx_file, "invoice")
    assert inv_model.invoice_id == "INV-TEST-XLSX"
    assert inv_model.total_amount == Decimal("2999.50")
    assert len(inv_model.items) == 2


def test_dataco_open_supply_chain_source_csv_exists():
    """
    Verifica que el extracto verificable del dataset público DataCo Global Smart Supply Chain
    (DOI: 10.17632/8gx2fvg2k6.5) esté presente y contenga los registros fuente.
    """
    src_csv = REAL_CASES_DIR / "dataco_open_supply_chain_source_records.csv"
    assert src_csv.exists(), "Falta el archivo fuente dataco_open_supply_chain_source_records.csv"
    _, rows, text = MultiFormatParser.read_csv_grid(src_csv)
    assert len(rows) >= 5
    assert "10.17632/8gx2fvg2k6.5" in text
    skus = {r["product_card_id"] for r in rows}
    assert {"DC-1360", "DC-957", "DC-1004", "DC-191", "DC-365"}.issubset(skus)


def test_all_5_dataco_real_multiformat_cases_zero_tolerance():
    """
    Verifica que los 5 expedientes multiformato de DataCo (.csv, .xlsx, .txt, .json)
    sean cargados por load_case_documents y resueltos por SkynetRunner con $0.00 MAE.
    """
    expected_cases = [
        "dataco_real_001_caguas_pelican_kayak",
        "dataco_real_002_cleveland_diamondback_cycling",
        "dataco_real_003_los_angeles_field_stream_hunting",
        "dataco_real_004_chicago_nike_footwear_overcharge",
        "dataco_real_005_miami_perfect_fitness_multiformat",
    ]

    observed_extensions = set()

    for cid in expected_cases:
        case_dir = REAL_CASES_DIR / cid
        assert case_dir.exists()

        # Registrar extensiones de archivo presentes en el expediente
        for f in case_dir.iterdir():
            if f.is_file() and f.name != "ground_truth.json":
                observed_extensions.add(f.suffix.lower())

        # 1. Verificar carga de los 5 documentos tipados Pydantic
        docs = load_case_documents(cid)
        assert set(docs.keys()) == {"invoice", "purchase_order", "delivery", "payment", "contract"}

        # 2. Verificar resolución con Cero Tolerancia ($0.00 MAE) contra ground_truth.json
        gt = json.loads((case_dir / "ground_truth.json").read_text(encoding="utf-8"))
        gt_just = Decimal(str(gt["expected_justified_amount"]))
        gt_claim = Decimal(str(gt["expected_claimable_amount"]))

        runner = SkynetRunner(case_id=cid, fast_path=True, use_cache=False)
        report = runner.run()

        assert report is not None
        assert report.justified_amount == gt_just, (
            f"Fallo en {cid}: justificado predicho {report.justified_amount} != esperado {gt_just}"
        )
        assert report.claimable_amount == gt_claim, (
            f"Fallo en {cid}: reclamable predicho {report.claimable_amount} != esperado {gt_claim}"
        )
        assert (report.justified_amount + report.claimable_amount) == abs(report.difference)

    # Confirmar que la batería multiformato cubre .xlsx, .csv, .txt y .json
    assert {".xlsx", ".csv", ".txt", ".json"}.issubset(observed_extensions)
