"""
Script para generar los expedientes de casos reales en formato PDF:
1. case_005_amazon_shortage: Disputa por faltante en muelle de recepción de Amazon (Fulfillment Center)
   con deducción injustificada de penalización ASN (Advance Shipping Notice).
2. case_006_walmart_otif_pricing: Disputa de retail masivo por discrepancia de precio unitario
   en factura vs Orden de Compra y deducción no autorizada de pronto pago.
"""

import sys
from pathlib import Path
from decimal import Decimal
import json

sys.path.append(str(Path(__file__).resolve().parent.parent))

from tools.document_reader.pdf_generator import (
    create_invoice_pdf,
    create_purchase_order_pdf,
    create_delivery_note_pdf,
    create_payment_receipt_pdf,
    create_contract_pdf
)

BASE_DIR = Path(__file__).resolve().parent.parent / "data" / "cases"

def generate_case_005_amazon():
    case_dir = BASE_DIR / "case_005_amazon_shortage"
    case_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Factura
    invoice_data = {
        "invoice_id": "INV-PAC-2026-4402",
        "vendor_id": "PACIFIC_TECH_CORP",
        "customer_id": "AMAZON_RETAIL_LLC",
        "po_reference": "PO-AMZ-2026-9041",
        "issue_date": "2026-03-10",
        "currency": "USD",
        "items": [
            {
                "item_id": "SKU-NVME-4TB",
                "description": "Enterprise PCIe Gen5 NVMe 4TB SSD",
                "quantity": 120,
                "unit_price": 250.00,
                "total_price": 30000.00
            },
            {
                "item_id": "SKU-SW-100G",
                "description": "100GbE Managed Data Center Switch",
                "quantity": 40,
                "unit_price": 450.00,
                "total_price": 18000.00
            }
        ],
        "subtotal": 48000.00,
        "tax": 0.00,
        "total_amount": 48000.00
    }
    create_invoice_pdf(invoice_data, case_dir / "invoice.pdf")
    
    # 2. Orden de Compra
    po_data = {
        "po_id": "PO-AMZ-2026-9041",
        "vendor_id": "PACIFIC_TECH_CORP",
        "customer_id": "AMAZON_RETAIL_LLC",
        "order_date": "2026-03-01",
        "currency": "USD",
        "items": [
            {
                "item_id": "SKU-NVME-4TB",
                "description": "Enterprise PCIe Gen5 NVMe 4TB SSD",
                "ordered_quantity": 120,
                "agreed_unit_price": 250.00,
                "total_price": 30000.00
            },
            {
                "item_id": "SKU-SW-100G",
                "description": "100GbE Managed Data Center Switch",
                "ordered_quantity": 40,
                "agreed_unit_price": 450.00,
                "total_price": 18000.00
            }
        ],
        "total_amount": 48000.00
    }
    create_purchase_order_pdf(po_data, case_dir / "purchase_order.pdf")
    
    # 3. Remisión / Bill of Lading
    delivery_data = {
        "delivery_id": "BOL-POD-77319",
        "po_reference": "PO-AMZ-2026-9041",
        "delivery_date": "2026-03-14",
        "received_by": "J_RAMIREZ_FC_SUPERVISOR",
        "warehouse_location": "AMAZON_ONT8_FULFILLMENT_CENTER",
        "signed": True,
        "discrepancy_reported": True,
        "items": [
            {
                "item_id": "SKU-NVME-4TB",
                "quantity_delivered": 120,
                "quantity_received": 100,
                "missing_quantity": 20,
                "damaged_quantity": 0,
                "notes": "Faltante físico en muelle. Tarima con cinta violada."
            },
            {
                "item_id": "SKU-SW-100G",
                "quantity_delivered": 40,
                "quantity_received": 40,
                "missing_quantity": 0,
                "damaged_quantity": 0,
                "notes": "Recibido completo y conforme."
            }
        ]
    }
    create_delivery_note_pdf(delivery_data, case_dir / "delivery.pdf")
    
    # 4. Comprobante de Pago
    payment_data = {
        "payment_id": "REM-AMZ-99120",
        "invoice_reference": "INV-PAC-2026-4402",
        "payment_date": "2026-03-25",
        "currency": "USD",
        "amount_paid": 40500.00,
        "deductions": [
            {
                "code": "DED-SHRT-20",
                "reason": "Dock Shortage - 20x SKU-NVME-4TB en muelle",
                "amount": 5000.00,
                "reference_doc": "BOL-POD-77319"
            },
            {
                "code": "DED-ASN-PENALTY",
                "reason": "Late Inbound EDI ASN Defect Fee (No autorizada)",
                "amount": 2500.00,
                "reference_doc": "CLAIM-ASN-990"
            }
        ]
    }
    create_payment_receipt_pdf(payment_data, case_dir / "payment.pdf")
    
    # 5. Contrato Marco
    contract_data = {
        "contract_id": "MSA-AMZ-PAC-2026",
        "vendor_id": "PACIFIC_TECH_CORP",
        "customer_id": "AMAZON_RETAIL_LLC",
        "valid_from": "2026-01-01",
        "valid_to": "2026-12-31",
        "clauses": [
            {
                "clause_id": "4.1",
                "title": "Ajuste por Faltantes Fisicos en Muelle",
                "text": "El Comprador podra deducir el valor de los bienes no entregados siempre que conste en remision de entrega sellada.",
                "policy": "DEDUCTION_ALLOWED_ON_SIGNED_DISCREPANCY",
                "tolerance_percentage": 0.00
            },
            {
                "clause_id": "5.3",
                "title": "Penalidades Operativas y Transmision ASN",
                "text": "Las penalizaciones operativas por discrepancias logisticas requieren notificacion formal previa y estan limitadas a maximo $250.00 USD por evento.",
                "policy": "LIMIT_PENALTY_OR_FORBIDDEN",
                "tolerance_percentage": 0.00
            }
        ]
    }
    create_contract_pdf(contract_data, case_dir / "contract.pdf")
    print(f"[OK] Expediente Real 1 generado en: {case_dir}")

def generate_case_006_walmart():
    case_dir = BASE_DIR / "case_006_walmart_otif_pricing"
    case_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Factura (Con error de sobreprecio: $35 en vez de $32 pactados)
    invoice_data = {
        "invoice_id": "INV-NDP-88301",
        "vendor_id": "NORDIC_DAIRY_LTD",
        "customer_id": "MEGAMART_STORES_INC",
        "po_reference": "PO-MMN-77102",
        "issue_date": "2026-03-12",
        "currency": "USD",
        "items": [
            {
                "item_id": "SKU-WHEY-2KG",
                "description": "Whey Isolate Protein 2kg Container",
                "quantity": 1500,
                "unit_price": 35.00,  # Erróneo: pactado en $32.00
                "total_price": 52500.00
            },
            {
                "item_id": "SKU-BAR-PLANT",
                "description": "Plant Protein Nutrition Bar 12-Pack",
                "quantity": 800,
                "unit_price": 15.00,
                "total_price": 12000.00
            }
        ],
        "subtotal": 64500.00,
        "tax": 0.00,
        "total_amount": 64500.00
    }
    create_invoice_pdf(invoice_data, case_dir / "invoice.pdf")
    
    # 2. Orden de Compra (Precio pactado $32.00 para SKU-WHEY-2KG)
    po_data = {
        "po_id": "PO-MMN-77102",
        "vendor_id": "NORDIC_DAIRY_LTD",
        "customer_id": "MEGAMART_STORES_INC",
        "order_date": "2026-03-02",
        "currency": "USD",
        "items": [
            {
                "item_id": "SKU-WHEY-2KG",
                "description": "Whey Isolate Protein 2kg Container",
                "ordered_quantity": 1500,
                "agreed_unit_price": 32.00,
                "total_price": 48000.00
            },
            {
                "item_id": "SKU-BAR-PLANT",
                "description": "Plant Protein Nutrition Bar 12-Pack",
                "ordered_quantity": 800,
                "agreed_unit_price": 15.00,
                "total_price": 12000.00
            }
        ],
        "total_amount": 60000.00
    }
    create_purchase_order_pdf(po_data, case_dir / "purchase_order.pdf")
    
    # 3. Remisión (Entregado 100% completo y sin daño)
    delivery_data = {
        "delivery_id": "REC-MMN-33019",
        "po_reference": "PO-MMN-77102",
        "delivery_date": "2026-03-15",
        "received_by": "M_RODRIGUEZ_RECEIVING_MGR",
        "warehouse_location": "MEGAMART_DC_12_CHICAGO",
        "signed": True,
        "discrepancy_reported": False,
        "items": [
            {
                "item_id": "SKU-WHEY-2KG",
                "quantity_delivered": 1500,
                "quantity_received": 1500,
                "missing_quantity": 0,
                "damaged_quantity": 0,
                "notes": "Recepcion completa y conforme en pallets sellados."
            },
            {
                "item_id": "SKU-BAR-PLANT",
                "quantity_delivered": 800,
                "quantity_received": 800,
                "missing_quantity": 0,
                "damaged_quantity": 0,
                "notes": "Recepcion conforme."
            }
        ]
    }
    create_delivery_note_pdf(delivery_data, case_dir / "delivery.pdf")
    
    # 4. Comprobante de Pago
    payment_data = {
        "payment_id": "REM-MMN-10294",
        "invoice_reference": "INV-NDP-88301",
        "payment_date": "2026-03-28",
        "currency": "USD",
        "amount_paid": 56500.00,
        "deductions": [
            {
                "code": "DED-PRICE-CORR",
                "reason": "Price Variance Adjustment SKU-WHEY-2KG to PO rate",
                "amount": 4500.00,
                "reference_doc": "PO-MMN-77102"
            },
            {
                "code": "DED-EARLY-PAY",
                "reason": "Unauthorized Early Settlement Discount 5%",
                "amount": 3500.00,
                "reference_doc": "FIN-DISC-002"
            }
        ]
    }
    create_payment_receipt_pdf(payment_data, case_dir / "payment.pdf")
    
    # 5. Contrato Marco
    contract_data = {
        "contract_id": "MSA-MMN-NDP-2026",
        "vendor_id": "NORDIC_DAIRY_LTD",
        "customer_id": "MEGAMART_STORES_INC",
        "valid_from": "2026-01-01",
        "valid_to": "2026-12-31",
        "clauses": [
            {
                "clause_id": "3.1",
                "title": "Ajuste Estricto a Precios de Orden de Compra",
                "text": "Los precios facturados por el Proveedor deben corresponder exactamente a los precios fijados en la Orden de Compra. Cualquier exceso podra ser deducido unilateralmente.",
                "policy": "STRICT_MATCH",
                "tolerance_percentage": 0.00
            },
            {
                "clause_id": "7.2",
                "title": "Condiciones de Descuento por Pronto Pago",
                "text": "Todo descuento por pronto pago requiere pago dentro de los primeros 10 dias naturales. Pagos posteriores al dia 10 perderan derecho a deduccion por este concepto.",
                "policy": "DISCOUNT_WINDOW_STRICT",
                "tolerance_percentage": 0.00
            }
        ]
    }
    create_contract_pdf(contract_data, case_dir / "contract.pdf")
    print(f"[OK] Expediente Real 2 generado en: {case_dir}")

if __name__ == "__main__":
    generate_case_005_amazon()
    generate_case_006_walmart()
    print("\n[ÉXITO] Todos los expedientes en PDF fueron generados con éxito.")
