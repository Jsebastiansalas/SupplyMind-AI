"""
scripts/generate_massive_1000_sku_case.py
Generador pericial del caso de estrés masivo case_036_massive_1000_skus:
- 1,000 SKUs comerciales auditados con precisión de centavo ($0.00 MAE)
- Contrato extenso multi-capítulo de ~80 páginas equivalentes
- Conciliación de remisión multi-estiba y deducciones mixtas (faltante físico + penalización ASN unilateral)
- Ground truth con estricta integridad Decimal
"""

import json
from decimal import Decimal
from pathlib import Path

def generate_massive_case(num_skus: int = 1000):
    case_dir = Path("data/cases/case_036_massive_1000_skus")
    case_dir.mkdir(parents=True, exist_ok=True)

    invoice_items = []
    po_items = []
    deliv_items = []

    total_invoice = Decimal("0.00")
    total_missing_amount = Decimal("0.00")

    # SKUs específicos con discrepancias controladas
    shortage_configs = {
        10: 5,    # SKU-0010: faltan 5 unids
        50: 8,    # SKU-0050: faltan 8 unids
        200: 10,  # SKU-0200: faltan 10 unids
        500: 4,   # SKU-0500: faltan 4 unids
        950: 6    # SKU-0950: faltan 6 unids
    }

    justified_breakdown = {}

    for i in range(1, num_skus + 1):
        item_id = f"SKU-IND-{i:04d}"
        desc = f"Componente Industrial Automatizado Grado Enterprise Modelo X-{i:04d}"
        qty = 20 + (i % 15)
        unit_price = Decimal("25.00") + Decimal(str(i % 40)) * Decimal("3.50")
        line_total = Decimal(str(qty)) * unit_price
        total_invoice += line_total

        inv_item = {
            "item_id": item_id,
            "description": desc,
            "quantity": qty,
            "unit_price": float(unit_price),
            "total_price": float(line_total)
        }
        invoice_items.append(inv_item)

        po_item = {
            "item_id": item_id,
            "description": desc,
            "quantity": qty,
            "unit_price": float(unit_price),
            "total_price": float(line_total)
        }
        po_items.append(po_item)

        # Determinar recepción y faltante
        missing_qty = shortage_configs.get(i, 0)
        received_qty = qty - missing_qty
        
        if missing_qty > 0:
            impact = Decimal(str(missing_qty)) * unit_price
            total_missing_amount += impact
            justified_breakdown[item_id] = f"{impact:.2f}"
            note = f"Faltante físico verificado en muelle: se recibieron {received_qty} de {qty} unidades. Sello de discrepancia."
        else:
            note = "Recibido completo y conforme en muelle."

        del_item = {
            "item_id": item_id,
            "quantity_delivered": qty,
            "quantity_received": received_qty,
            "missing_quantity": missing_qty,
            "damaged_quantity": 0,
            "notes": note
        }
        deliv_items.append(del_item)

    # 1. Factura
    invoice_doc = {
        "invoice_id": "INV-MASSIVE-1000-01",
        "vendor_id": "VEN-GLOBAL-IND-99",
        "customer_id": "CUST-MEGA-RETAIL-CORP",
        "po_reference": "PO-MASSIVE-2026-9901",
        "issue_date": "2026-09-01",
        "currency": "USD",
        "items": invoice_items,
        "subtotal": float(total_invoice),
        "tax": 0.00,
        "total_amount": float(total_invoice)
    }

    # 2. Orden de Compra
    po_doc = {
        "po_id": "PO-MASSIVE-2026-9901",
        "vendor_id": "VEN-GLOBAL-IND-99",
        "customer_id": "CUST-MEGA-RETAIL-CORP",
        "issue_date": "2026-08-25",
        "currency": "USD",
        "items": po_items,
        "subtotal": float(total_invoice),
        "tax": 0.00,
        "total_amount": float(total_invoice)
    }

    # 3. Remisión de Entrega
    deliv_doc = {
        "delivery_id": "DEL-MASSIVE-LOG-8812",
        "po_reference": "PO-MASSIVE-2026-9901",
        "delivery_date": "2026-09-05",
        "received_by": "Jefe de Muelle Logístico Central (Ing. Roberto Valenzuela)",
        "warehouse_location": "Centro de Distribución Nacional - Muelles 1 al 12",
        "signed": True,
        "discrepancy_reported": True,
        "items": deliv_items
    }

    # 4. Comprobante de Pago y Deducciones
    unilateral_penalty = Decimal("5000.00")
    total_deductions = total_missing_amount + unilateral_penalty
    amount_paid = total_invoice - total_deductions

    payment_doc = {
        "payment_id": "PAY-MASSIVE-FIN-7710",
        "invoice_reference": "INV-MASSIVE-1000-01",
        "payment_date": "2026-10-02",
        "currency": "USD",
        "amount_paid": float(amount_paid),
        "deductions": [
            {
                "code": "DED-SHORTAGE-SIGNED",
                "reason": "Deducción de unidades faltantes acreditadas en remisión DEL-MASSIVE-LOG-8812 (5 SKUs)",
                "amount": float(total_missing_amount),
                "reference_doc": "DEL-MASSIVE-LOG-8812"
            },
            {
                "code": "DED-ASN-UNILATERAL-PENALTY",
                "reason": "Penalización por supuesta omisión en transmisión EDI ASN previa",
                "amount": float(unilateral_penalty),
                "reference_doc": "SLA-INTERNAL-MEMO-2026"
            }
        ]
    }

    # 5. Contrato Marco Extenso (Multi-Capítulo ~80 Páginas Equivalentes)
    contract_clauses = [
        {
            "clause_id": "CLAUSE-1.1",
            "title": "Objeto y Alcance del Suministro Industrial",
            "text": "El presente contrato marco regula el suministro de 1,000 referencias de componentes industriales y equipamiento automatizado entre las partes.",
            "policy": "SUPPLY_FRAMEWORK",
            "tolerance_percentage": 0.00
        },
        {
            "clause_id": "CLAUSE-2.3",
            "title": "Catálogo de Precios y Procedimiento de Órdenes de Compra",
            "text": "Todos los precios pactados en la Orden de Compra son fijos e inmutables durante la vigencia del contrato. Toda discrepancia de precio superior a la PO se considerará no autorizada.",
            "policy": "STRICT_MATCH",
            "tolerance_percentage": 0.00
        },
        {
            "clause_id": "CLAUSE-4.2",
            "title": "Faltantes Físicos y Remisión de Muelle",
            "text": "En caso de faltantes físicos comprobados mediante remisión firmada con sello y rúbrica del personal de muelle receptor, el comprador podrá deducir el valor exacto de las unidades no entregadas de la factura correspondiente.",
            "policy": "DEDUCTION_ALLOWED_ON_SIGNED_DISCREPANCY",
            "tolerance_percentage": 0.00
        },
        {
            "clause_id": "CLAUSE-6.1",
            "title": "Plazos de Reclamo y Ventana de Notificación",
            "text": "El comprador dispone de una ventana de notificación perentoria de 30 días naturales posteriores a la entrega para presentar cualquier objeción o reclamación comercial.",
            "policy": "NOTICE_WINDOW_30_DAYS",
            "tolerance_percentage": 0.00
        },
        {
            "clause_id": "CLAUSE-9.3",
            "title": "Invalidez de Penalidades Logísticas Unilaterales",
            "text": "Queda estrictamente prohibida la imposición unilateral de multas o deducciones por conceptos EDI, avisos anticipados de embarque (ASN) o retrasos en muelle sin la firma previa de un convenio bilateral suscrito por los representantes legales de ambas empresas. Toda deducción no pactada expresamente se considerará nula y de cobro inmediato.",
            "policy": "UNILATERAL_PENALTY_PROHIBITED",
            "tolerance_percentage": 0.00
        },
        {
            "clause_id": "CLAUSE-12.4",
            "title": "Jurisdicción, Ley Aplicable y Solución de Controversias",
            "text": "Las controversias se dirimirán preferentemente por acuerdo mutuo conciliatorio de cuentas comerciales previo a cualquier recurso jurisdiccional.",
            "policy": "COMMERCIAL_CONCILIATION_FIRST",
            "tolerance_percentage": 0.00
        }
    ]

    # Generamos un texto extenso simulando 80 páginas de contrato marco formal con capítulos y secciones
    extended_contract_text_parts = [
        "# CONTRATO MARCO MAESTRO DE SUMINISTRO INDUSTRIAL Y LOGÍSTICA B2B",
        "## CAPÍTULO I: DECLARACIONES Y CAPACIDAD LEGAL",
        "Las partes celebran el presente instrumento con plena capacidad jurídica...",
        "## CAPÍTULO II: ESPECIFICACIONES TÉCNICAS Y CATÁLOGO DE 1,000 SKUS",
        "El proveedor pondrá a disposición del cliente el catálogo completo detallado en los Anexos I a X...",
        "## CAPÍTULO III: CONDICIONES DE PEDIDO Y PRECIOS (CLÁUSULA 2.3)",
        "Todos los precios pactados en la Orden de Compra son fijos e inmutables...",
        "## CAPÍTULO IV: RECEPCIÓN FÍSICA Y FALTANTES EN MUELLE (CLÁUSULA 4.2)",
        "En caso de faltantes físicos comprobados mediante remisión firmada con sello y rúbrica del personal de muelle receptor, el comprador podrá deducir el valor exacto de las unidades no entregadas...",
        "## CAPÍTULO V: CALIDAD, EMBALAJE Y DEVOLUCIONES",
        "El embalaje industrial cumplirá con la norma ISO-9001...",
        "## CAPÍTULO VI: PLAZOS DE RECLAMO Y VENTANA DE NOTIFICACIÓN (CLÁUSULA 6.1)",
        "El comprador dispone de una ventana de notificación perentoria de 30 días naturales posteriores a la entrega...",
        "## CAPÍTULO VII: FACTURACIÓN ELECTRÓNICA Y CONDICIONES FISCALES",
        "Las facturas se emitirán cumpliendo con todas las regulaciones tributarias e IVA al 16%...",
        "## CAPÍTULO VIII: POLÍTICAS DE PAGO Y CONCILIACIÓN BANCARIA",
        "El pago se efectuará vía transferencia bancaria electrónica a 30 días fecha factura...",
        "## CAPÍTULO IX: PROHIBICIÓN EXPRESA DE PENALIDADES UNILATERALES (CLÁUSULA 9.3)",
        "Queda estrictamente prohibida la imposición unilateral de multas o deducciones por conceptos EDI, avisos anticipados de embarque (ASN) o retrasos en muelle sin la firma previa de un convenio bilateral suscrito por ambas empresas. Toda deducción no pactada expresamente se considerará nula y de cobro inmediato.",
        "## CAPÍTULO X: FUERZA MAYOR Y CASO FORTUITO",
        "Ninguna de las partes será responsable por demoras derivadas de desastres naturales...",
        "## CAPÍTULO XI: CONFIDENCIALIDAD Y PROTECCIÓN DE DATOS",
        "Las partes mantendrán estricta confidencialidad sobre precios y especificaciones técnicas...",
        "## CAPÍTULO XII: RESOLUCIÓN Y RESCISIÓN (CLÁUSULA 12.4)",
        "Las controversias se dirimirán preferentemente por acuerdo mutuo conciliatorio...",
        "## ANEXO I: LISTA DE 1,000 REFERENCIAS HOMOLOGADAS",
        "Detalle técnico de los componentes SKU-IND-0001 al SKU-IND-1000..."
    ]
    # Replicamos secciones narrativas de anexos para simular el volumen documental de 80 páginas
    for page_idx in range(1, 40):
        extended_contract_text_parts.append(
            f"### APÉNDICE TÉCNICO COMPLEMENTARIO {page_idx}: HOJA DE RUTA LOGÍSTICA\n"
            f"Especificaciones operativas de estiba, cubicaje de tarimas y protocolos de recepción "
            f"para el lote de componentes industriales en centros de distribución regionales (Pág {page_idx*2})."
        )

    full_contract_text = "\n\n".join(extended_contract_text_parts)

    contract_doc = {
        "contract_id": "CTR-MASSIVE-2026-X1",
        "vendor_id": "VEN-GLOBAL-IND-99",
        "customer_id": "CUST-MEGA-RETAIL-CORP",
        "valid_from": "2026-01-01",
        "valid_to": "2026-12-31",
        "clauses": contract_clauses,
        "raw_content": full_contract_text
    }

    # 6. Ground Truth Pericial
    ground_truth_doc = {
        "case_id": "case_036_massive_1000_skus",
        "category": "MASSIVE_MULTI_SKU_DISPUTE",
        "buyer_id": "MEGA_RETAIL_CORP",
        "buyer_name": "Mega Retail Corporation Logistics",
        "industry": "Componentes Industriales y Automatización",
        "currency": "USD",
        "total_skus": num_skus,
        "billed_amount": f"{total_invoice:.2f}",
        "received_amount": f"{amount_paid:.2f}",
        "difference": f"{-total_deductions:.2f}",
        "expected_justified_amount": f"{total_missing_amount:.2f}",
        "expected_claimable_amount": f"{unilateral_penalty:.2f}",
        "expected_confidence": 0.99,
        "justified_breakdown": justified_breakdown,
        "claimable_breakdown": {
            "DED-ASN-UNILATERAL-PENALTY": f"{unilateral_penalty:.2f}"
        },
        "required_clause_citations": [
            "CLAUSE-4.2",
            "CLAUSE-9.3"
        ],
        "recommended_commercial_action": "PARTIAL_CREDIT_AND_DISPUTE_UNILATERAL"
    }

    # Guardar todos los archivos JSON en el expediente
    (case_dir / "invoice.json").write_text(json.dumps(invoice_doc, indent=2, ensure_ascii=False), encoding="utf-8")
    (case_dir / "purchase_order.json").write_text(json.dumps(po_doc, indent=2, ensure_ascii=False), encoding="utf-8")
    (case_dir / "delivery.json").write_text(json.dumps(deliv_doc, indent=2, ensure_ascii=False), encoding="utf-8")
    (case_dir / "payment.json").write_text(json.dumps(payment_doc, indent=2, ensure_ascii=False), encoding="utf-8")
    (case_dir / "contract.json").write_text(json.dumps(contract_doc, indent=2, ensure_ascii=False), encoding="utf-8")
    (case_dir / "ground_truth.json").write_text(json.dumps(ground_truth_doc, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"[OK] Expediente masivo generado en: {case_dir}")
    print(f"     Total SKUs: {num_skus}")
    print(f"     Facturado: ${total_invoice:,.2f} USD")
    print(f"     Pagado: ${amount_paid:,.2f} USD")
    print(f"     Deducción Faltante (Justificado): ${total_missing_amount:,.2f} USD")
    print(f"     Deducción ASN (Reclamable): ${unilateral_penalty:,.2f} USD")

    return {
        "case_dir": str(case_dir),
        "total_invoice": total_invoice,
        "amount_paid": amount_paid,
        "total_missing_amount": total_missing_amount,
        "unilateral_penalty": unilateral_penalty
    }

if __name__ == "__main__":
    generate_massive_case(1000)
