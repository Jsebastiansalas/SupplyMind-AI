"""
scripts/create_mega_case.py
Genera el caso de estrés masivo case_009_mega_retailer_dispute:
- 40 SKUs industriales y de tecnología de alto valor
- Monto facturado: $385,000.00 USD
- Remisión multi-muelle con recepciones y faltantes físicos específicos
- Comprobante de pago con deducciones mixtas (faltante físico, pronto pago unilateral y multa ASN)
- Contrato marco comercial con cláusulas de jerarquía, penalidades y plazos
- Ground truth con precisión de centavo
"""

import json
from decimal import Decimal
from pathlib import Path

def create_mega_case():
    case_dir = Path("data/cases/case_009_mega_retailer_dispute")
    case_dir.mkdir(parents=True, exist_ok=True)

    base_items = [
        ("SKU-SRV-001", "Enterprise Rack Server Dual Xeon 64C", 10, 4500.00),     # 45,000
        ("SKU-SRV-002", "Storage Array 24-Bay SAS 12G 2U", 8, 3200.00),          # 25,600
        ("SKU-NET-003", "Core Switch 48-Port 100GbE QSFP28", 6, 5000.00),         # 30,000
        ("SKU-NET-004", "ToR Switch 48-Port 25GbE SFP28", 12, 1800.00),           # 21,600
        ("SKU-PWR-005", "Online UPS 10kVA Modular 3U", 10, 2200.00),              # 22,000
        ("SKU-SEC-006", "Next-Gen Firewall Appliance 40Gbps", 4, 6500.00),        # 26,000
        ("SKU-CAB-007", "Server Cabinet 42U 800x1200mm", 15, 800.00),             # 12,000
        ("SKU-PDU-008", "Managed PDU 32A 3-Phase Zero-U", 30, 450.00),            # 13,500
        ("SKU-OPT-009", "Transceiver 100G QSFP28 LR4 10km", 40, 350.00),         # 14,000
        ("SKU-IND-010", "Industrial Grade PCIe Gen5 4TB SSD", 60, 250.00),         # 15,000  (Faltante: 20 unids = $5,000)
        ("SKU-RAM-011", "DDR5 ECC Reg 64GB 5600MHz Module", 100, 180.00),         # 18,000
        ("SKU-CPU-012", "Server Processor 32-Core 2.8GHz", 15, 1200.00),          # 18,000
        ("SKU-KVM-013", "IP-KVM Switch 16-Port with DVI/USB", 8, 950.00),          # 7,600
        ("SKU-SFP-014", "Transceiver 25G SFP28 SR 100m", 80, 75.00),              # 6,000
        ("SKU-FBR-015", "MPO-12 Trunk Cable OM4 30m", 50, 90.00),                 # 4,500
        ("SKU-FBR-016", "LC-LC Duplex Patch Cord 5m", 120, 15.00),                # 1,800
        ("SKU-BAT-017", "Replacement Battery Pack for 10kVA UPS", 12, 600.00),     # 7,200
        ("SKU-FAN-018", "Hot-Swap Fan Module for Chassis", 40, 110.00),           # 4,400
        ("SKU-PSU-019", "Redundant Titanium PSU 1600W", 30, 280.00),              # 8,400
        ("SKU-NIC-020", "Dual-Port 25GbE PCIe Adapter", 35, 320.00),              # 11,200
        ("SKU-NIC-021", "Quad-Port 10GBASE-T Network Card", 25, 240.00),          # 6,000
        ("SKU-IND-022", "Industrial Touch Panel PC 21.5-inch", 30, 200.00),        # 6,000   (Faltante: 15 unids = $3,000)
        ("SKU-SEN-023", "Environmental Temp/Humidity Sensor", 50, 80.00),          # 4,000
        ("SKU-RMT-024", "Remote Power Control Gateway", 20, 310.00),               # 6,200
        ("SKU-BRK-025", "Mounting Bracket Rail Kit 2U", 40, 65.00),               # 2,600
        ("SKU-CBL-026", "Cat6A Shielded Patch Cable 2m 100-Pack", 25, 180.00),    # 4,500
        ("SKU-MGR-027", "Horizontal Cable Manager 1U", 50, 40.00),                # 2,000
        ("SKU-BLK-028", "Toolless Blanking Panel 1U 10-Pack", 30, 50.00),         # 1,500
        ("SKU-KEY-029", "Smart Rack Electronic Lock Handle", 20, 220.00),         # 4,400
        ("SKU-SMK-030", "Early Smoke Detection Aspiration Sensor", 10, 850.00),    # 8,500
        ("SKU-LED-031", "Rack Internal LED Lighting Bar", 40, 45.00),             # 1,800
        ("SKU-ANT-032", "External Dual-Band Antenna Omni", 60, 35.00),             # 2,100
        ("SKU-ROU-033", "Branch Office Edge SD-WAN Router", 12, 1100.00),         # 13,200
        ("SKU-MOD-034", "Cellular 5G Backup Module", 15, 450.00),                 # 6,750
        ("SKU-IND-035", "Heavy Duty Rugged Ethernet Switch", 25, 400.00),          # 10,000  (Faltante: 10 unids = $4,000)
        ("SKU-CON-036", "Serial Console Server 16-Port", 6, 1400.00),              # 8,400
        ("SKU-SFP-037", "Transceiver 10G SFP+ RJ45 30m", 60, 65.00),              # 3,900
        ("SKU-GEL-038", "Thermal Compound High-Density 20g", 50, 25.00),           # 1,250
        ("SKU-CLP-039", "Velcro Cable Tie Roll 25m", 80, 15.00),                  # 1,200
        ("SKU-CLN-040", "Fiber Optic Cleaning Click Pen Kit", 60, 40.00),          # 2,400
    ]

    total_invoice = sum(qty * price for _, _, qty, price in base_items)
    diff = 385000.00 - total_invoice
    base_items[0] = (base_items[0][0], base_items[0][1], base_items[0][2], base_items[0][3] + (diff / base_items[0][2]))

    invoice_items = []
    po_items = []
    delivery_items = []

    shortages = {
        "SKU-IND-010": 20,
        "SKU-IND-022": 15,
        "SKU-IND-035": 10,
    }

    for sku, desc, qty, price in base_items:
        tot_p = round(qty * price, 2)
        invoice_items.append({
            "item_id": sku,
            "description": desc,
            "quantity": qty,
            "unit_price": round(price, 2),
            "total_price": tot_p
        })
        po_items.append({
            "item_id": sku,
            "description": desc,
            "ordered_quantity": qty,
            "agreed_unit_price": round(price, 2),
            "total_price": tot_p
        })

        miss = shortages.get(sku, 0)
        rec = qty - miss
        notes = f"Faltante físico en muelle ({miss} u.) constatado en recepción" if miss > 0 else "Recepción completa conforme"
        delivery_items.append({
            "item_id": sku,
            "quantity_delivered": qty,
            "quantity_received": rec,
            "missing_quantity": miss,
            "damaged_quantity": 0,
            "notes": notes
        })

    # 1. invoice.json
    invoice_data = {
        "invoice_id": "INV-MEGA-2026-9001",
        "vendor_id": "TECH-ENTERPRISE-SUPPLY-MX",
        "customer_id": "RETAIL-GLOBAL-CORPORATION",
        "po_reference": "PO-GLOBAL-88001",
        "issue_date": "2026-03-01",
        "currency": "USD",
        "items": invoice_items,
        "subtotal": 385000.00,
        "tax": 0.00,
        "total_amount": 385000.00
    }
    with open(case_dir / "invoice.json", "w", encoding="utf-8") as f:
        json.dump(invoice_data, f, indent=2, ensure_ascii=False)

    # 2. purchase_order.json
    po_data = {
        "po_id": "PO-GLOBAL-88001",
        "vendor_id": "TECH-ENTERPRISE-SUPPLY-MX",
        "customer_id": "RETAIL-GLOBAL-CORPORATION",
        "order_date": "2026-02-25",
        "currency": "USD",
        "items": po_items,
        "total_amount": 385000.00
    }
    with open(case_dir / "purchase_order.json", "w", encoding="utf-8") as f:
        json.dump(po_data, f, indent=2, ensure_ascii=False)

    # 3. delivery.json
    delivery_data = {
        "delivery_id": "DEL-MULTI-DOCK-7701",
        "po_reference": "PO-GLOBAL-88001",
        "delivery_date": "2026-03-05",
        "warehouse_location": "CDI-MACRO-HUB-NORTE",
        "received_by": "CARLOS_MENDOZA_PATIO",
        "signed": True,
        "discrepancy_reported": True,
        "items": delivery_items
    }
    with open(case_dir / "delivery.json", "w", encoding="utf-8") as f:
        json.dump(delivery_data, f, indent=2, ensure_ascii=False)

    # 4. payment.json
    payment_data = {
        "payment_id": "PAY-SETTLE-88190",
        "invoice_reference": "INV-MEGA-2026-9001",
        "payment_date": "2026-03-20",
        "currency": "USD",
        "amount_paid": 360000.00,
        "deductions": [
            {
                "code": "DED-DOCK-SHORTAGE",
                "amount": 12000.00,
                "reason": "Dock Shortage: 20x SKU-IND-010, 15x SKU-IND-022, 10x SKU-IND-035"
            },
            {
                "code": "DED-EARLY-SETTLE",
                "amount": 8500.00,
                "reason": "Unauthorized Early Settlement Discount 3% (No pactado)"
            },
            {
                "code": "DED-ASN-PENALTY",
                "amount": 4500.00,
                "reason": "Unilateral EDI Inbound ASN Defect Fee (Sin adenda bilateral)"
            }
        ]
    }
    with open(case_dir / "payment.json", "w", encoding="utf-8") as f:
        json.dump(payment_data, f, indent=2, ensure_ascii=False)

    # 5. contract.json
    contract_data = {
        "contract_id": "CTR-MASTER-GLOBAL-2026",
        "vendor_id": "TECH-ENTERPRISE-SUPPLY-MX",
        "customer_id": "RETAIL-GLOBAL-CORPORATION",
        "valid_from": "2026-01-01",
        "valid_to": "2026-12-31",
        "clauses": [
            {
                "clause_id": "CLAUSE-3.1",
                "title": "Ajuste Estricto a Precios de Orden de Compra",
                "text": "Los precios unitarios acordados en la Orden de Compra formalmente aceptada regirán de manera irrevocable sobre cualquier catálogo previo.",
                "policy": "PRICE_VARIANCE",
                "tolerance_percentage": 0.0
            },
            {
                "clause_id": "CLAUSE-4.2",
                "title": "Deducción por Faltantes Físicos con Remisión Firmada",
                "text": "El comprador queda expresamente facultado para retener o deducir del pago el valor de las unidades faltantes, siempre y cuando consten debidamente anotadas y circunstanciadas en la remisión de entrega firmada y sellada por el transportista al momento de la descarga.",
                "policy": "SHORTAGE_TOLERANCE",
                "tolerance_percentage": 0.0
            },
            {
                "clause_id": "CLAUSE-5.1",
                "title": "Ventana de Notificación de Averías y Daños",
                "text": "Cualquier daño o avería no aparente deberá ser reportado por escrito con respaldo fotográfico fehaciente dentro de las 48 horas siguientes a la descarga en bodega.",
                "policy": "DAMAGED_GOODS",
                "tolerance_percentage": 0.0
            },
            {
                "clause_id": "CLAUSE-7.2",
                "title": "Condiciones de Descuento por Pronto Pago",
                "text": "Los descuentos financieros por pronto pago requerirán autorización expresa previa y por escrito de la tesorería del proveedor. Las deducciones unilaterales por pronto pago son improcedentes y nulas.",
                "policy": "EARLY_PAYMENT_TERMS",
                "tolerance_percentage": 0.0
            },
            {
                "clause_id": "CLAUSE-7.3",
                "title": "Prohibición de Penalizaciones Unilaterales Operativas",
                "text": "Queda estrictamente prohibida la imposición de multas, cargos por EDI, penalizaciones logísticas o cargos administrativos de forma unilateral sin un debido proceso de conciliación bilateral y acuerdo mutuo suscrito entre las partes.",
                "policy": "UNILATERAL_PENALTIES",
                "tolerance_percentage": 0.0
            },
            {
                "clause_id": "CLAUSE-8.2",
                "title": "Ventana de Reclamación y Caducidad Procesal (Notice Window)",
                "text": "Toda controversia o deducción deberá notificarse formalmente dentro de los 30 días naturales posteriores a la entrega. Transcurrido dicho plazo, precluye el derecho de reclamo.",
                "policy": "NOTICE_WINDOW",
                "tolerance_percentage": 0.0
            }
        ]
    }
    with open(case_dir / "contract.json", "w", encoding="utf-8") as f:
        json.dump(contract_data, f, indent=2, ensure_ascii=False)

    # 6. ground_truth.json
    gt_data = {
        "case_id": "case_009_mega_retailer_dispute",
        "category": "COMPOUND_MIXED",
        "billed_amount": "385000.00",
        "received_amount": "360000.00",
        "difference": "-25000.00",
        "expected_justified_amount": "12000.00",
        "expected_claimable_amount": "13000.00",
        "expected_confidence": 0.98,
        "justified_breakdown": {
            "SKU-IND-010": "5000.00",
            "SKU-IND-022": "3000.00",
            "SKU-IND-035": "4000.00"
        },
        "claimable_breakdown": {
            "DED-EARLY-SETTLE": "8500.00",
            "DED-ASN-PENALTY": "4500.00"
        },
        "required_clause_citations": ["CLAUSE-4.2", "CLAUSE-7.2", "CLAUSE-7.3"],
        "recommended_commercial_action": "EMIT_CREDIT_NOTE_AND_RECOVERY_LETTER"
    }
    with open(case_dir / "ground_truth.json", "w", encoding="utf-8") as f:
        json.dump(gt_data, f, indent=2, ensure_ascii=False)

    print(f"[OK] Expediente masivo generado en: {case_dir}")
    print(f"Total Facturado: $385,000.00 USD | Total Deducciones: $25,000.00 USD")
    print(f"Justificado: $12,000.00 USD | Reclamable: $13,000.00 USD")

if __name__ == "__main__":
    create_mega_case()
