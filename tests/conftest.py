"""
tests/conftest.py
Configuración global de pytest para SupplyMind AI:
1. Aísla llamadas HTTP en vivo a la pasarela durante pruebas unitarias por defecto (acelerando la suite de 570 tests a <20s y evitando gasto de cuota en CI/Harness), permitiendo activar llamadas reales con `pytest --live-api`.
2. Limpia automáticamente artefactos residuales de casos sintéticos de prueba en `reports/` al finalizar la sesión.
"""

from pathlib import Path
import shutil
import subprocess
import pytest

from config.settings import settings


def pytest_addoption(parser):
    parser.addoption(
        "--live-api",
        action="store_true",
        default=False,
        help="Ejecutar pruebas haciendo llamadas HTTP en vivo contra la pasarela de Platica.",
    )


@pytest.fixture(autouse=True)
def isolate_live_api_by_default(request, monkeypatch):
    """Evita llamadas de red bloqueantes en pruebas unitarias salvo que se indique --live-api."""
    if not request.config.getoption("--live-api"):
        monkeypatch.setattr(settings, "RETO_KEY", "")
        monkeypatch.delenv("RETO_KEY", raising=False)
        monkeypatch.delenv("PLATICA_API_KEY", raising=False)
        monkeypatch.delenv("XAI_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)


def pytest_sessionfinish(session, exitstatus):
    """Limpia archivos temporales creados por pruebas de casos negativos o sintéticos."""
    reports_dir = Path("reports")
    if not reports_dir.exists():
        return

    temp_patterns = [
        "*non_existent_case_99999*",
        "*test_bad_schema*",
        "*test_corrupt_json*",
        "*test_dynamic_case*",
        "*case_test_guided_case_999*",
        "*case_auto_learning_test*",
    ]
    for pattern in temp_patterns:
        for p in reports_dir.rglob(pattern):
            try:
                if p.is_dir():
                    shutil.rmtree(p, ignore_errors=True)
                elif p.is_file():
                    p.unlink(missing_ok=True)
            except Exception:
                pass
