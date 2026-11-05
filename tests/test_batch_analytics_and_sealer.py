"""
tests/test_batch_analytics_and_sealer.py
Pruebas unitarias e integrales para:
- Eje 1: Generador de Evidencia Visual y Analítica (`BatchAnalyticsVisualizer`)
- Eje 2: Certificación Criptográfica SHA-256 + Merkle Root (`BatchAuditSealer`)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import pytest

from tools.batch_processor.batch_analytics_visualizer import BatchAnalyticsVisualizer
from tools.batch_processor.batch_audit_sealer import BatchAuditSealer, GENESIS_HASH
from tools.batch_processor.unattended_batch_orchestrator import UnattendedBatchOrchestrator


def _build_sample_records(count: int = 8) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    for i in range(1, count + 1):
        billed = round(1000.0 * i, 2)
        disputed = round(150.0 * i, 2)
        received = round(billed - disputed, 2)
        recovered = round(disputed * 0.85, 2)
        justified = round(disputed - recovered, 2)
        records.append({
            "unit_index": i,
            "task_id": f"work_unit_{i:04d}",
            "case_id": f"CASE-TEST-{i:04d}",
            "source_origin": "REAL_RETAIL_DOC",
            "retailer_id": "WALMART_MX" if i % 2 == 0 else "AMAZON_MX",
            "retailer_name": "Walmart de México y Centroamérica" if i % 2 == 0 else "Amazon México FC",
            "category": "FILL_RATE_PENALTY" if i % 2 == 0 else "SHORTAGE_CLAIM",
            "timestamp_start": "2026-11-05T00:00:00+00:00",
            "timestamp_end": "2026-11-05T00:00:42+00:00",
            "duration_seconds": 41.5 + (i * 0.2),
            "status": "RECOVERED_QUARANTINE" if i == count else "SUCCESS",
            "billed_amount": billed,
            "received_amount": received,
            "disputed_amount": disputed,
            "recovered_amount": recovered,
            "justified_amount": justified,
            "financial_delta": 0.0,
            "tokens_prompt": 400 + i * 10,
            "tokens_completion": 220 + i * 5,
            "tokens_total": 620 + i * 15,
            "cost_usd": round(0.00051 + (i * 0.00002), 6),
            "model_used": "grok-4.7",
            "input_summary": f"Auditar caso {i}",
            "result_summary": f"Dictamen {i} completado",
            "error_encountered": "NONE",
            "recovery_action": "NOT_REQUIRED",
            "legal_basis": "Código de Comercio Art. 383",
            "erp_action": "BAPI_ACC_DOCUMENT_POST",
        })
    return records


def test_sealer_deterministic_hashes_and_merkle_root(tmp_path: Path) -> None:
    """Verifica que el cálculo de hashes SHA-256 y la raíz de Merkle sean deterministas."""
    records = _build_sample_records(6)
    sealer = BatchAuditSealer(reports_dir=tmp_path)

    h1 = sealer.compute_record_hash(records[0])
    h2 = sealer.compute_record_hash(records[0])
    assert h1 == h2
    assert len(h1) == 64

    seal_res = sealer.seal_records(records)
    assert seal_res["total_units_sealed"] == 6
    assert len(seal_res["merkle_root"]) == 64
    assert seal_res["merkle_root"] != GENESIS_HASH
    assert Path(seal_res["manifest_json"]).exists()
    assert Path(seal_res["manifest_sha256"]).exists()

    verification = sealer.verify_batch_integrity(records=records)
    assert verification.is_valid is True
    assert verification.mae_zero_invariant_passed is True
    assert verification.total_records_verified == 6
    assert len(verification.tampered_tasks) == 0


def test_sealer_detects_financial_tampering(tmp_path: Path) -> None:
    """Verifica que cualquier alteración a un monto o campo rompa la cadena SHA-256 y la raíz de Merkle."""
    records = _build_sample_records(5)
    sealer = BatchAuditSealer(reports_dir=tmp_path)
    sealer.seal_records(records)

    # Alterar maliciosamente el monto recuperado de la tarea #3
    tampered_records = [dict(r) for r in records]
    tampered_records[2]["recovered_amount"] = tampered_records[2]["recovered_amount"] + 500.00

    verification = sealer.verify_batch_integrity(records=tampered_records)
    assert verification.is_valid is False
    assert verification.mae_zero_invariant_passed is False
    assert any("work_unit_0003" in t for t in verification.tampered_tasks)


def test_visualizer_computes_summary_and_exports_html(tmp_path: Path) -> None:
    """Verifica que el visualizador genere el JSON analítico y el tablero HTML/SVG autocontenido."""
    records = _build_sample_records(10)
    sealer = BatchAuditSealer(reports_dir=tmp_path)
    seal_info = sealer.seal_records(records)

    visualizer = BatchAnalyticsVisualizer(reports_dir=tmp_path)
    paths = visualizer.export_visual_dashboard(records=records, seal_info=seal_info)

    json_path = Path(paths["analytics_json"])
    html_path = Path(paths["analytics_html"])
    assert json_path.exists()
    assert html_path.exists()

    summary = json.loads(json_path.read_text(encoding="utf-8"))
    assert summary["total_units"] == 10
    assert summary["status_breakdown"]["SUCCESS"] == 9
    assert summary["status_breakdown"]["RECOVERED_QUARANTINE"] == 1
    assert summary["success_rate_pct"] == 100.0
    assert summary["financials"]["mae_zero_verified"] is True
    assert len(summary["retailer_breakdown"]) == 2
    assert len(summary["cumulative_series"]) > 0

    html_content = html_path.read_text(encoding="utf-8")
    assert "<svg" in html_content
    assert "SELLO CRIPTOGRÁFICO SHA-256 ACTIVO" in html_content
    assert seal_info["merkle_root"][:24] in html_content
    assert "Walmart de México" in html_content


def test_orchestrator_automatically_seals_and_generates_dashboard(tmp_path: Path) -> None:
    """Verifica que el orquestador ejecute automáticamente el sellado SHA-256 y el tablero visual al exportar."""
    orchestrator = UnattendedBatchOrchestrator(
        output_dir=tmp_path,
        total_units=4,
        target_duration_hours=0.0,
        dry_run=True,
        resume=False,
    )
    res = orchestrator.run_unattended_batch()
    export_paths = res["export_paths"]

    assert Path(export_paths["audit_manifest_json"]).exists()
    assert Path(export_paths["audit_manifest_sha256"]).exists()
    assert Path(export_paths["analytics_json"]).exists()
    assert Path(export_paths["analytics_html"]).exists()
    assert len(export_paths["merkle_root"]) == 64

    # Auditar el lote recién exportado desde disco
    sealer = BatchAuditSealer(reports_dir=tmp_path)
    ver = sealer.verify_batch_integrity()
    assert ver.is_valid is True
    assert ver.files_digest_passed is True
    assert ver.mae_zero_invariant_passed is True
