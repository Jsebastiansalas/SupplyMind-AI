import json
import pytest
from decimal import Decimal
from pathlib import Path
import tempfile
import shutil

from agent.ingestion.resilient_parser import (
    repair_json_string,
    parse_resilient_decimal,
    normalize_schema_dict,
    impute_missing_document,
    ResilientDocumentLoader
)
from tools.document_reader.reader import load_case_documents_with_health, load_case_documents
from agent.core.skynet_runner import SkynetRunner


def test_repair_json_syntax_dirty_formats():
    """Valida la auto-reparación de JSONs con sintaxis no estándar (comas flotantes, comillas simples, comentarios)."""
    # 1. Comillas simples y trailing commas
    dirty_single_quotes = "{'invoice_id': 'INV-999', 'total_amount': '1500.00', 'items': [{'sku': 'A1', 'qty': 5,},],}"
    parsed, warnings = repair_json_string(dirty_single_quotes)
    assert parsed["invoice_id"] == "INV-999"
    assert len(parsed["items"]) == 1
    assert parsed["items"][0]["qty"] == 5
    assert len(warnings) > 0

    # 2. Comentarios estilo JS / C++
    dirty_comments = """
    {
        // Identificador oficial
        "po_id": "PO-1234",
        /* Monto acordado */
        "total_amount": 2500.00,
    }
    """
    parsed2, _ = repair_json_string(dirty_comments)
    assert parsed2["po_id"] == "PO-1234"
    assert parsed2["total_amount"] == 2500.00

    # 3. Llaves sin comillas (unquoted keys)
    dirty_unquoted = "{delivery_id: 'DEL-888', recipient: 'Amazon FC', signed: true}"
    parsed3, _ = repair_json_string(dirty_unquoted)
    assert parsed3["delivery_id"] == "DEL-888"
    assert parsed3["signed"] is True

    # 4. Truncamiento de llaves / corchetes
    dirty_truncated = '{"vendor_id": "VEN-01", "items": [{"id": "1"}, {"id": "2"}'
    parsed4, _ = repair_json_string(dirty_truncated)
    assert parsed4["vendor_id"] == "VEN-01"
    assert len(parsed4["items"]) == 2


def test_parse_resilient_decimal():
    """Valida extracción precisa de Decimals desde cadenas comerciales con monedas o formatos internacionales."""
    assert parse_resilient_decimal("$ 1,250.75 USD") == Decimal("1250.75")
    assert parse_resilient_decimal("1.500,50 €") == Decimal("1500.50")
    assert parse_resilient_decimal("- $ 450.00") == Decimal("-450.00")
    assert parse_resilient_decimal("(350.25)") == Decimal("-350.25")
    assert parse_resilient_decimal("1000") == Decimal("1000.00")
    assert parse_resilient_decimal(250.5) == Decimal("250.50")
    assert parse_resilient_decimal(None, default=Decimal("0.00")) == Decimal("0.00")
    assert parse_resilient_decimal("N/A", default=Decimal("99.99")) == Decimal("99.99")


def test_normalize_schema_dict_aliases():
    """Valida mapeo de alias no estándar a los modelos estrictos Pydantic."""
    # Factura en español con alias
    raw_invoice = {
        "folio": "F-2026-001",
        "emisor": "Distribuidora del Norte",
        "receptor": "Retail Corp",
        "orden_compra": "OC-5501",
        "divisa": "USD",
        "partidas": [
            {
                "codigo": "SKU-99",
                "descripcion": "Leche Entera UHT",
                "cant": "100",
                "precio": "$ 2.50"
            }
        ]
    }
    norm_inv, warnings = normalize_schema_dict(raw_invoice, "invoice")
    assert norm_inv["invoice_id"] == "F-2026-001"
    assert norm_inv["vendor_id"] == "Distribuidora del Norte"
    assert norm_inv["po_reference"] == "OC-5501"
    assert len(norm_inv["items"]) == 1
    assert norm_inv["items"][0]["quantity"] == 100
    assert norm_inv["items"][0]["unit_price"] == Decimal("2.50")
    assert norm_inv["total_amount"] == Decimal("250.00")

    # Remisión con alias
    raw_delivery = {
        "remision_id": "REM-441",
        "transportista": "Transportes Rápidos",
        "articulos": [
            {
                "sku": "SKU-99",
                "recibido": 90,
                "danado": 2,
                "faltante": 10
            }
        ],
        "firmado": True
    }
    norm_del, _ = normalize_schema_dict(raw_delivery, "delivery")
    assert norm_del["delivery_id"] == "REM-441"
    assert norm_del["items"][0]["quantity_received"] == 90
    assert norm_del["items"][0]["missing_quantity"] == 10
    assert norm_del["items"][0]["damaged_quantity"] == 2
    assert norm_del["signed"] is True


def test_impute_missing_document():
    """Valida imputación automática determinística cuando falta un documento secundario (OC o Contrato)."""
    raw_invoice = {
        "folio": "INV-TEST-01",
        "emisor": "VEN-TEST",
        "receptor": "CUST-TEST",
        "partidas": [{"codigo": "IT-1", "cant": 10, "precio": "100.00"}]
    }
    norm_inv, _ = normalize_schema_dict(raw_invoice, "invoice")
    from data.models import Invoice
    inv_model = Invoice.model_validate(norm_inv)

    docs = {"invoice": inv_model}
    imputed_po, rationale = impute_missing_document("purchase_order", docs, "case_test_impute")
    assert imputed_po.po_id.startswith("PO-IMPUTED-")
    assert imputed_po.total_amount == Decimal("1000.00")
    assert "factura" in rationale.lower()

    # Imputar contrato faltante
    imputed_ctr, c_rationale = impute_missing_document("contract", docs, "case_test_impute")
    assert imputed_ctr.contract_id.startswith(("CON-IMPUTED-", "CTR-IMPUTED-"))
    assert len(imputed_ctr.clauses) > 0
    assert "términos comerciales estándar" in c_rationale.lower() or "contrato marco" in c_rationale.lower()


def test_resilient_loader_on_pristine_cases():
    """Valida que los casos existentes de la suite se cargan con estado PRISTINE (100% de salud)."""
    docs, audit = load_case_documents_with_health("case_001")
    assert len(docs) == 5
    assert audit.health_score == 100.0
    assert audit.status == "PRISTINE"
    assert audit.is_healthy is True
    assert audit.execution_safety_level == "SAFE_FOR_AUTONOMOUS_SETTLEMENT"
    assert len(audit.repaired_issues) == 0


def test_resilient_loader_on_dirty_synthesized_case(tmp_path):
    """Crea un caso sintético con JSONs con errores de sintaxis y verifica auto-reparación e imputación sin caerse."""
    case_dir = tmp_path / "case_dirty_healed"
    case_dir.mkdir()

    # Factura con comillas simples, comentarios y comas flotantes
    invoice_content = """
    {
        // Factura con errores comunes de extracción
        'folio': 'INV-HEAL-100',
        'proveedor': 'Proveedor Sucio S.A.',
        'receptor': 'Retailer Exigente',
        'divisa': 'USD',
        'lineas': [
            {'sku': 'SKU-DIRTY-1', 'descripcion': 'Teclado Gamer', 'qty': '20', 'precio': '$ 50.00 USD',},
        ],
    }
    """
    (case_dir / "invoice.json").write_text(invoice_content, encoding="utf-8")

    # Remisión con unquoted keys y trailing commas
    delivery_content = """
    {
        delivery_id: "DEL-HEAL-200",
        items: [
            {item_id: "SKU-DIRTY-1", received: 18, missing: 2, damaged: 0,},
        ],
        signed: true,
    }
    """
    (case_dir / "delivery.json").write_text(delivery_content, encoding="utf-8")

    # Comprobante de pago con deducción no autorizada
    payment_content = """
    {
        'payment_id': 'PAY-HEAL-300',
        'amount_paid': '900.00',
        'deductions': [
            {'code': 'SHORTAGE', 'amount': '$100.00', 'reason': '2 teclados faltantes'},
        ],
    }
    """
    (case_dir / "payment.json").write_text(payment_content, encoding="utf-8")

    # Nótese: NO guardamos purchase_order.json ni contract.json intencionalmente para forzar imputación autocurativa

    docs, audit = ResilientDocumentLoader.load_case_resilient(str(case_dir), allow_imputation=True)
    assert len(docs) == 5
    assert "invoice" in docs
    assert "delivery" in docs
    assert "payment" in docs
    assert "purchase_order" in docs  # Imputada con éxito
    assert "contract" in docs        # Imputado con éxito

    assert audit.health_score < 100.0
    assert audit.status in ["AUTO_REPAIRED", "DEGRADED"]
    assert audit.is_healthy is True
    assert len(audit.imputed_documents) == 2
    assert any("invoice" in issue.lower() or "del" in issue.lower() for issue in audit.repaired_issues)


def test_skynet_runner_integration_with_health_audit():
    """Valida que SkynetRunner ejecuta el ciclo completo incorporando el DocumentHealthAudit en el reporte final."""
    runner = SkynetRunner(case_id="case_001", fast_path=True, use_cache=False)
    report = runner.run()

    assert report is not None
    assert report.health_audit is not None
    assert getattr(report.health_audit, "health_score", None) == 100.0 or report.health_audit.get("health_score") == 100.0
    assert getattr(report.health_audit, "status", None) == "PRISTINE" or report.health_audit.get("status") == "PRISTINE"
    assert getattr(report.health_audit, "is_healthy", None) is True or report.health_audit.get("is_healthy") is True
