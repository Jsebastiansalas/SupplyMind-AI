"""
tests/test_batch_resilience_and_technical_report.py
Pruebas unitarias para:
- Eje 3: Validador de Resiliencia y Caos Controlado (`BatchResilienceVerifier`)
- Eje 4: Generador de Reporte Técnico Oficial ("Qué lograste, qué falló, costo por tarea")
"""

from __future__ import annotations

from pathlib import Path

from tools.batch_processor.batch_resilience_verifier import BatchResilienceVerifier
from tools.batch_processor.delivery_package_builder import DeliveryPackageBuilder


def test_resilience_anomaly_quarantine_scenario(tmp_path: Path) -> None:
    """Verifica que las tipologías de fallos documentales sean aisladas en RECOVERED_QUARANTINE con $0.00 MAE."""
    verifier = BatchResilienceVerifier(reports_dir=tmp_path)
    res = verifier.test_anomaly_quarantine_recovery()
    assert res.passed is True
    assert res.units_tested == 4
    assert res.units_recovered == 4
    assert res.mae_zero_preserved is True


def test_resilience_gateway_transient_fault_backoff(tmp_path: Path) -> None:
    """Verifica que el orquestador se recupere de un HTTP 429 transitorio mediante Exponential Backoff."""
    verifier = BatchResilienceVerifier(reports_dir=tmp_path)
    res = verifier.test_gateway_transient_fault_backoff()
    assert res.passed is True
    assert res.units_recovered == 1


def test_resilience_crash_and_idempotent_resume(tmp_path: Path) -> None:
    """Verifica que tras un corte abrupto el lote retome exactamente donde quedó sin duplicar registros."""
    verifier = BatchResilienceVerifier(reports_dir=tmp_path)
    res = verifier.test_crash_and_idempotent_resume()
    assert res.passed is True
    assert res.units_tested == 6
    assert res.units_recovered == 6


def test_full_resilience_audit_exports_reports(tmp_path: Path) -> None:
    """Verifica que la auditoría completa exporte el JSON y MD de resiliencia y perfil de anomalías."""
    verifier = BatchResilienceVerifier(reports_dir=tmp_path)
    report = verifier.run_full_resilience_audit()
    assert report["all_resilience_scenarios_passed"] is True
    assert report["queue_fault_profile"]["total_queue_units"] == 1024
    assert report["queue_fault_profile"]["injected_anomaly_units"] > 0
    assert verifier.audit_json_path.exists()
    assert verifier.audit_md_path.exists()


def test_delivery_package_builder_technical_report(tmp_path: Path) -> None:
    """Verifica que el reporte técnico incluya Qué se logró, Qué falló, Cómo se recuperó y Costo por tarea."""
    builder = DeliveryPackageBuilder(reports_dir=tmp_path)
    report_md = builder.generate_technical_report()

    assert "¿Qué logramos?" in report_md
    assert "¿Qué falló y cómo se recuperó el agente?" in report_md
    assert "Costo Total, Costo por Tarea" in report_md
    assert "AUTO_QUARANTINE_AND_FORENSIC_ISOLATION" in report_md
    assert "$0.00 MAE" in report_md
