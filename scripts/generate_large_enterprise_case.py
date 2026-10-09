"""
Script para generar el expediente case_007_cisco_large_bundle:
Expediente de gran volumen y múltiples páginas para telecomunicaciones/infraestructura B2B.
Contiene documentos extensos (miles de caracteres, múltiples páginas y cláusulas detalladas)
guardados bajo nombres de archivo totalmente arbitrarios para validar la autonomía del clasificador.
"""

import sys
from pathlib import Path
from decimal import Decimal

sys.path.append(str(Path(__file__).resolve().parent.parent))

from tools.document_reader.pdf_generator import (
    create_invoice_pdf,
    create_purchase_order_pdf,
    create_delivery_note_pdf,
    create_payment_receipt_pdf,
    create_contract_pdf
)

BASE_DIR = Path(__file__).resolve().parent.parent / "data" / "cases"

def generate_case_007_large_bundle():
    case_dir = BASE_DIR / "case_007_cisco_large_bundle"
    case_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Factura Comercial Extensa (Nombre Arbitrario)
    invoice_data = {
        "invoice_id": "INV-CISCO-CORP-99214",
        "vendor_id": "CISCO_SYSTEMS_GLOBAL",
        "customer_id": "TELCO_ENTERPRISE_NETWORK",
        "po_reference": "PO-TELCO-2026-8810",
        "issue_date": "2026-03-05",
        "currency": "USD",
        "items": [
            {
                "item_id": "SKU-ROUTER-CORE",
                "description": "Carrier-Grade Core Router 400G Module",
                "quantity": 10,
                "unit_price": 5000.00,
                "total_price": 50000.00
            },
            {
                "item_id": "SKU-FIREWALL-NG",
                "description": "Next-Gen Enterprise Security Appliance 100G",
                "quantity": 5,
                "unit_price": 6000.00,
                "total_price": 30000.00
            },
            {
                "item_id": "SKU-FIBER-TRANS",
                "description": "100GbE QSFP28 Single-Mode Optical Transceiver",
                "quantity": 50,
                "unit_price": 400.00,
                "total_price": 20000.00
            },
            {
                "item_id": "SKU-SFP-MODULE",
                "description": "Multi-Mode Fiber Gigabit SFP+ Transceiver Pack",
                "quantity": 40,
                "unit_price": 300.00,
                "total_price": 12000.00
            },
            {
                "item_id": "SKU-POWER-RACK",
                "description": "Redundant High-Efficiency Server Rack Power Supply",
                "quantity": 20,
                "unit_price": 400.00,
                "total_price": 8000.00
            },
            {
                "item_id": "SKU-CABLING-CAT6",
                "description": "Industrial Shielded Cat6A High-Density Patch Bundle",
                "quantity": 50,
                "unit_price": 100.00,
                "total_price": 5000.00
            }
        ],
        "subtotal": 125000.00,
        "tax": 0.00,
        "total_amount": 125000.00
    }
    # Archivo con nombre corporativo arbitrario
    create_invoice_pdf(invoice_data, case_dir / "DOC_FISCAL_CFDI_SERIE_B_NO_99214.pdf")
    
    # 2. Orden de Compra Corporativa (Nombre Arbitrario, con precios negociados)
    po_data = {
        "po_id": "PO-TELCO-2026-8810",
        "vendor_id": "CISCO_SYSTEMS_GLOBAL",
        "customer_id": "TELCO_ENTERPRISE_NETWORK",
        "order_date": "2026-02-20",
        "currency": "USD",
        "items": [
            {
                "item_id": "SKU-ROUTER-CORE",
                "description": "Carrier-Grade Core Router 400G Module",
                "ordered_quantity": 10,
                "agreed_unit_price": 4500.00, # Pactado con descuento ($500 menos)
                "total_price": 45000.00
            },
            {
                "item_id": "SKU-FIREWALL-NG",
                "description": "Next-Gen Enterprise Security Appliance 100G",
                "ordered_quantity": 5,
                "agreed_unit_price": 5500.00, # Pactado con descuento ($500 menos)
                "total_price": 27500.00
            },
            {
                "item_id": "SKU-FIBER-TRANS",
                "description": "100GbE QSFP28 Single-Mode Optical Transceiver",
                "ordered_quantity": 50,
                "agreed_unit_price": 400.00,
                "total_price": 20000.00
            },
            {
                "item_id": "SKU-SFP-MODULE",
                "description": "Multi-Mode Fiber Gigabit SFP+ Transceiver Pack",
                "ordered_quantity": 40,
                "agreed_unit_price": 300.00,
                "total_price": 12000.00
            },
            {
                "item_id": "SKU-POWER-RACK",
                "description": "Redundant High-Efficiency Server Rack Power Supply",
                "ordered_quantity": 20,
                "agreed_unit_price": 400.00,
                "total_price": 8000.00
            },
            {
                "item_id": "SKU-CABLING-CAT6",
                "description": "Industrial Shielded Cat6A High-Density Patch Bundle",
                "ordered_quantity": 50,
                "agreed_unit_price": 100.00,
                "total_price": 5000.00
            }
        ],
        "total_amount": 117500.00 # Diferencia de precio unitario: $7,500.00 USD
    }
    create_purchase_order_pdf(po_data, case_dir / "ORDEN_COMPRA_CORPORATIVA_GLOBAL_PO8810.pdf")
    
    # 3. Remisión / Acta de Recepción en Almacén (Nombre Arbitrario, con faltante y avería)
    delivery_data = {
        "delivery_id": "ACTA-REC-DALLAS-4410",
        "po_reference": "PO-TELCO-2026-8810",
        "delivery_date": "2026-03-12",
        "received_by": "CHIEF_ING_CARLOS_MENDEZ",
        "warehouse_location": "TELCO_DALLAS_SUPER_HUB_TX",
        "signed": True,
        "discrepancy_reported": True,
        "items": [
            {
                "item_id": "SKU-ROUTER-CORE",
                "quantity_delivered": 10,
                "quantity_received": 10,
                "missing_quantity": 0,
                "damaged_quantity": 0,
                "notes": "Recibido completo en bastidor."
            },
            {
                "item_id": "SKU-FIREWALL-NG",
                "quantity_delivered": 5,
                "quantity_received": 5,
                "missing_quantity": 0,
                "damaged_quantity": 0,
                "notes": "Inspeccionado conforme con sello intacto."
            },
            {
                "item_id": "SKU-FIBER-TRANS",
                "quantity_delivered": 50,
                "quantity_received": 40,
                "missing_quantity": 10, # 10 faltantes x $400 = $4,000 USD
                "damaged_quantity": 0,
                "notes": "Faltante fisico en tarima 3. Caja abierta."
            },
            {
                "item_id": "SKU-SFP-MODULE",
                "quantity_delivered": 40,
                "quantity_received": 35,
                "missing_quantity": 0,
                "damaged_quantity": 5, # 5 averiados x $300 = $1,500 USD
                "notes": "Caja aplastada por montacargas."
            },
            {
                "item_id": "SKU-POWER-RACK",
                "quantity_delivered": 20,
                "quantity_received": 20,
                "missing_quantity": 0,
                "damaged_quantity": 0,
                "notes": "Recibido en orden."
            },
            {
                "item_id": "SKU-CABLING-CAT6",
                "quantity_delivered": 50,
                "quantity_received": 50,
                "missing_quantity": 0,
                "damaged_quantity": 0,
                "notes": "Recibido en orden."
            }
        ]
    }
    create_delivery_note_pdf(delivery_data, case_dir / "REMITO_RECEPCION_LOGISTICA_ALMACEN_DALLAS.pdf")
    
    # 4. Comprobante de Pago Bancario / Remittance Advice (Nombre Arbitrario)
    payment_data = {
        "payment_id": "WIRE-TELCO-2026-99014",
        "invoice_reference": "INV-CISCO-CORP-99214",
        "payment_date": "2026-03-26",
        "currency": "USD",
        "amount_paid": 98000.00,
        "deductions": [
            {
                "code": "DED-PRC-VAR",
                "reason": "Price variance correction to agreed Purchase Order rate",
                "amount": 7500.00,
                "reference_doc": "PO-TELCO-2026-8810"
            },
            {
                "code": "DED-SHORTAGE",
                "reason": "Physical dock shortage 10x SKU-FIBER-TRANS",
                "amount": 4000.00,
                "reference_doc": "ACTA-REC-DALLAS-4410"
            },
            {
                "code": "DED-DAMAGE",
                "reason": "Damaged goods 5x SKU-SFP-MODULE crushed",
                "amount": 1500.00,
                "reference_doc": "ACTA-REC-DALLAS-4410"
            },
            {
                "code": "DED-UNAUTH-PENALTY",
                "reason": "Arbitrary unannounced freight unloading penalty charge",
                "amount": 14000.00, # Deducción abusiva sin amparo contractual
                "reference_doc": "CLAIM-INT-881"
            }
        ]
    }
    create_payment_receipt_pdf(payment_data, case_dir / "AVISO_PAGO_Y_LIQUIDACION_BANCARIA_WIRE.pdf")
    
    # 5. Contrato Marco Extenso de Suministro Tecnológico (Nombre Arbitrario, 6 cláusulas)
    contract_data = {
        "contract_id": "MSA-GLOBAL-TELCO-CISCO-2026",
        "vendor_id": "CISCO_SYSTEMS_GLOBAL",
        "customer_id": "TELCO_ENTERPRISE_NETWORK",
        "valid_from": "2026-01-01",
        "valid_to": "2028-12-31",
        "clauses": [
            {
                "clause_id": "3.1",
                "title": "Alineacion Estricta a Precios de la Orden de Compra",
                "text": "Los precios aplicables a los pedidos se regiran con caracter vinculante por la Orden de Compra aprobada. Si el Proveedor factura a precios de lista superiores, el Comprador queda facultado para deducir de pleno derecho el sobreprecio.",
                "policy": "STRICT_MATCH",
                "tolerance_percentage": 0.00
            },
            {
                "clause_id": "4.2",
                "title": "Compensacion Automatica por Faltantes Fisicos Comprobados",
                "text": "Cualquier faltante verificado al momento de la descarga en muelle e incorporado en la remision de entrega firmada con sello sera deducible del pago final.",
                "policy": "DEDUCTION_ALLOWED_ON_SIGNED_DISCREPANCY",
                "tolerance_percentage": 0.00
            },
            {
                "clause_id": "5.1",
                "title": "Mercancia Averiada en Transporte o Descarga",
                "text": "Los bienes recibidos con dano visible en empaque o estructura seran descontados inmediatamente si se deja constancia expresa en el acta de muelle.",
                "policy": "DEDUCTION_ALLOWED_ON_SIGNED_DISCREPANCY",
                "tolerance_percentage": 0.00
            },
            {
                "clause_id": "6.1",
                "title": "Prohibicion de Penalidades Unilaterales de Muelle",
                "text": "Queda estrictamente prohibida la imposicion de multas operativas o cobros por maniobras de muelle sin aprobacion previa por escrito de ambas partes y proceso de conciliacion de 30 dias.",
                "policy": "LIMIT_PENALTY_OR_FORBIDDEN",
                "tolerance_percentage": 0.00
            },
            {
                "clause_id": "8.3",
                "title": "Auditoria de Cuentas por Cobrar y Resolucion Amigable",
                "text": "Las partes acuerdan someter las diferencias aritmeticas a verificacion documental deterministica antes de entablar litigio formal.",
                "policy": "DISPUTE_RESOLUTION_PROCEDURE",
                "tolerance_percentage": 0.00
            }
        ]
    }
    create_contract_pdf(contract_data, case_dir / "CONVENIO_MARCO_PROVEEDORES_MSA_GLOBAL_2026.pdf")
    print(f"[OK] Expediente de Gran Extensión (Case 007) generado en: {case_dir}")

if __name__ == "__main__":
    generate_case_007_large_bundle()
