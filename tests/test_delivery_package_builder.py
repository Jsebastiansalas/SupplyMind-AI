"""
tests/test_delivery_package_builder.py
Suite de pruebas para el Generador y Validador del Paquete Oficial de Entrega.

Valida:
1. Auditoría técnica de cumplimiento de los 3 requisitos de Platica.
2. Generación íntegra de la plantilla para la plataforma de entrega.
"""

from pathlib import Path
import pytest

from tools.batch_processor.delivery_package_builder import (
    DeliveryPackageBuilder,
    DeliveryComplianceAudit,
)


def test_delivery_package_builder_audit(tmp_path):
    """Valida la auditoría de cumplimiento técnico de entrega."""
    builder = DeliveryPackageBuilder(reports_dir=tmp_path)
    audit = builder.audit_delivery_readiness()

    assert isinstance(audit, DeliveryComplianceAudit)
    assert audit.gateway_key_verified is True
    assert "Auditoría Platica:" in audit.summary_text


def test_delivery_package_builder_submission_text(tmp_path):
    """Valida la generación del texto de entrega para Platica."""
    builder = DeliveryPackageBuilder(reports_dir=tmp_path)
    text = builder.generate_platform_submission_text(
        repo_url="https://github.com/Jsebastiansalas/platica",
        video_url="https://youtu.be/DEMO123",
    )

    assert "# Entrega Oficial - Semana de Carga" in text
    assert "SupplyMind AI" in text
    assert "1,024" in text
    assert "https://github.com/Jsebastiansalas/platica/blob/develop/reports/unattended_batch_execution_log.csv" in text
    assert "https://youtu.be/DEMO123" in text
