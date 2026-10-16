"""
Tests for SKU Matcher and Notice Window Auditor tools.
Ensures deterministic calculation of Mexican VAT 16%, SKU variances, and notice window statute of limitations.
"""

from decimal import Decimal
from tools.sku_matcher import perform_sku_level_matching
from tools.notice_window_auditor import audit_notice_window

def test_sku_matching_price_and_quantity_variance():
    invoice_data = {
        "items": [
            {"sku": "SKU-PRO-01", "description": "Televisor 55 OLED", "quantity": 10, "unit_price": 500.0, "total": 5000.0},
            {"sku": "SKU-PRO-02", "description": "Barra de Sonido", "quantity": 5, "unit_price": 100.0, "total": 500.0}
        ]
    }
    delivery_data = {
        "items": [
            {"sku": "SKU-PRO-01", "quantity_received": 8, "quantity_damaged": 1},
            {"sku": "SKU-PRO-02", "quantity_received": 5, "quantity_damaged": 0}
        ]
    }
    po_data = {
        "items": [
            {"sku": "SKU-PRO-01", "unit_price": 450.0},  # Invoiced at 500, agreed at 450 -> price variance!
            {"sku": "SKU-PRO-02", "unit_price": 100.0}
        ]
    }

    result = perform_sku_level_matching(invoice_data, delivery_data, po_data)
    
    assert result.net_line_discrepancy > Decimal("0.00")
    assert result.total_vat_impact_16 == (result.net_line_discrepancy * Decimal("0.16")).quantize(Decimal("0.01"))
    assert result.credit_note_recommended_total > Decimal("0.00")
    
    # Check item details
    sku1 = next(item for item in result.line_items if item.item_id == "SKU-PRO-01")
    assert sku1.quantity_short == 2
    assert sku1.quantity_damaged == 1
    assert sku1.price_variance == Decimal("50.00")

def test_notice_window_on_time():
    # Delivery 2026-03-01, Deduction 2026-03-15 (14 days <= 30 days)
    audit = audit_notice_window(
        delivery_data={"delivery_date": "2026-03-01"},
        payment_data={"payment_date": "2026-03-15"},
        default_limit_days=30
    )
    assert audit.is_timely is True
    assert audit.statute_of_limitations_applied is False
    assert audit.days_elapsed == 14
    assert "PLAZO" in audit.status_label

def test_notice_window_expired():
    # Delivery 2026-01-01, Deduction 2026-02-15 (45 days > 30 days)
    audit = audit_notice_window(
        delivery_data={"delivery_date": "2026-01-01"},
        payment_data={"payment_date": "2026-02-15"},
        default_limit_days=30
    )
    assert audit.is_timely is False
    assert audit.statute_of_limitations_applied is True
    assert audit.days_elapsed == 45
    assert "EXTEMPORÁNEO" in audit.status_label
