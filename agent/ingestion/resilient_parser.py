"""
agent/ingestion/resilient_parser.py
Pilar 1: Capa de Ingesta Autocurativa & Normalización Polimórfica de Esquemas (Fuzzy Schema).

Objetivo:
Garantizar que ningún archivo corrupto, JSON con comas de más, comillas simples,
claves sin comillas, alias no estándar, o documentos faltantes cause que el agente
alucine, crashee o pierda el contexto.
"""

import re
import json
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union

from data.models import (
    Invoice,
    InvoiceItem,
    PurchaseOrder,
    PurchaseOrderItem,
    DeliveryNote,
    DeliveryItem,
    PaymentReceipt,
    PaymentDeduction,
    CommercialContract,
    ContractClause,
    DocumentHealthAudit,
)


def repair_json_string(raw_text: str) -> Tuple[Dict[str, Any], List[str]]:
    """
    Auto-repara sintácticamente un string JSON corrupto o malformado.
    Maneja:
    - BOMs (\ufeff), caracteres nulos y caracteres de control.
    - Bloques markdown tipo ```json ... ```.
    - Comentarios de una línea (//) y multilínea (/* ... */).
    - Trailing commas en objetos {,} y arrays [,].
    - Comillas simples en claves o valores {'key': 'val'}.
    - Claves sin comillas {key: "val"}.
    - JSONs truncados (cierre automático de llaves y corchetes desbalanceados).
    - Extracción de JSON embebido dentro de texto libre.
    """
    repaired_warnings: List[str] = []
    text = raw_text.strip()

    # 1. Limpieza de caracteres invisibles y BOM
    if text.startswith("\ufeff"):
        text = text[1:].strip()
        repaired_warnings.append("Eliminado BOM (Byte Order Mark) UTF-8 del archivo")

    text = text.replace("\x00", "")

    # 2. Intento directo de parseo estándar
    try:
        return json.loads(text), repaired_warnings
    except json.JSONDecodeError:
        pass

    # 3. Quitar bloques markdown ```json ... ```
    md_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if md_match:
        text = md_match.group(1).strip()
        repaired_warnings.append("Extraído bloque JSON desde bloque de código Markdown")

    # 4. Quitar comentarios de estilo C / JavaScript
    text_clean = re.sub(r"/\*[\s\S]*?\*/", "", text)
    text_clean = re.sub(r"//.*$", "", text_clean, flags=re.MULTILINE)
    if text_clean != text:
        repaired_warnings.append("Eliminados comentarios de estilo C/JS no permitidos en JSON estándar")
        text = text_clean.strip()

    # 5. Reemplazar trailing commas en objetos y arrays
    # ej: {"a": 1,} -> {"a": 1} o [1, 2,] -> [1, 2]
    prev_len = len(text)
    text = re.sub(r",\s*([\]}])", r"\1", text)
    if len(text) != prev_len:
        repaired_warnings.append("Corregidas comas sobrantes (trailing commas) antes de cierre")

    # 6. Reemplazar comillas simples por comillas dobles en claves y cadenas simples
    # Claves: 'nombre': -> "nombre":
    text_quotes = re.sub(r"'([^'\\]*(?:\\.[^'\\]*)*)'(?=\s*:)", r'"\1"', text)
    # Valores de texto: : 'valor' -> : "valor"
    text_quotes = re.sub(r":\s*'([^'\\]*(?:\\.[^'\\]*)*)'", r': "\1"', text_quotes)
    if text_quotes != text:
        repaired_warnings.append("Convertidas comillas simples a dobles en claves y valores")
        text = text_quotes

    # 7. Claves no entrecomilladas: { id: "1" } -> { "id": "1" }
    text_unquoted = re.sub(r"([{,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:", r'\1"\2":', text)
    if text_unquoted != text:
        repaired_warnings.append("Entrecomilladas claves sintácticas desprovistas de comillas")
        text = text_unquoted

    # 8. Intento post-limpieza
    try:
        return json.loads(text), repaired_warnings
    except json.JSONDecodeError:
        pass

    # 9. Reparación de JSON truncado (desbalance de llaves y corchetes)
    open_curly = text.count("{") - text.count("}")
    open_square = text.count("[") - text.count("]")

    if open_curly > 0 or open_square > 0:
        # Cerrar cadenas abiertas si terminó a mitad de string
        if text.count('"') % 2 != 0:
            text += '"'
            repaired_warnings.append("Cerrada cadena de texto interrumpida a final de archivo")

        # Quitar coma colgante al final
        text = re.sub(r",\s*$", "", text.strip())

        # Anexar cierres faltantes
        closers = ("]" * max(0, open_square)) + ("}" * max(0, open_curly))
        text_healed = text + closers
        try:
            parsed = json.loads(text_healed)
            repaired_warnings.append(f"Auto-cerradas {open_curly} llaves y {open_square} corchetes desbalanceados")
            return parsed, repaired_warnings
        except json.JSONDecodeError:
            pass

    # 10. Búsqueda de la mayor subestructura JSON válida entre { ... }
    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace != -1 and last_brace > first_brace:
        sub = text[first_brace:last_brace + 1]
        try:
            parsed = json.loads(sub)
            repaired_warnings.append("Aislada y parseada subestructura JSON válida entre llaves principales")
            return parsed, repaired_warnings
        except json.JSONDecodeError:
            pass

    # Si todo falla, lanzar error con detalle estructurado
    raise ValueError(f"Imposible recuperar JSON corrupto: contenido estructuralmente irrecuperable.")


def parse_resilient_decimal(val: Any, default: Decimal = Decimal("0.00")) -> Decimal:
    """
    Convierte cualquier valor a Decimal de forma tolerante a errores:
    - Limpia signos monetarios ('$', 'USD', 'MXN', comas y espacios).
    - Tolera notación europea ('1.250,50' -> '1250.50').
    - Maneja números flotantes convirtiendo a str para evitar imprecisión binaria.
    """
    if val is None:
        return default
    if isinstance(val, Decimal):
        return val
    if isinstance(val, (int, float)):
        return Decimal(str(val))

    s_raw = str(val).strip()
    if not s_raw:
        return default

    # Detección de número negativo (incluye contabilidad entre paréntesis como (350.25))
    is_negative = ("-" in s_raw) or (s_raw.startswith("(") and s_raw.endswith(")"))

    # Limpieza de caracteres de moneda y letras
    s_clean = re.sub(r"[^\d,\.]", "", s_raw)
    if not s_clean:
        return default

    # Manejo de separadores:
    # Caso 1: Formato estándar 1,250.50
    if "," in s_clean and "." in s_clean:
        if s_clean.rfind(".") > s_clean.rfind(","):
            s_clean = s_clean.replace(",", "")
        else:
            # Caso 2: Formato europeo 1.250,50
            s_clean = s_clean.replace(".", "").replace(",", ".")
    elif "," in s_clean:
        # E.g. "1250,50" -> "1250.50" o "1,250"
        parts = s_clean.split(",")
        if len(parts) == 2 and len(parts[1]) in [1, 2]:
            s_clean = s_clean.replace(",", ".")
        else:
            s_clean = s_clean.replace(",", "")

    if is_negative and not s_clean.startswith("-"):
        s_clean = f"-{s_clean}"

    try:
        return Decimal(s_clean)
    except InvalidOperation:
        return default


def normalize_schema_dict(raw_data: Dict[str, Any], doc_type: str) -> Tuple[Dict[str, Any], List[str]]:
    """
    Normaliza de forma polimórfica (Fuzzy Schema) un diccionario de datos brutos
    mapeando alias semánticos a los nombres canónicos requeridos por los modelos Pydantic.
    """
    d = dict(raw_data)
    warnings: List[str] = []
    dtype = doc_type.lower().strip()

    def _get_first(keys: List[str], default: Any = None) -> Any:
        for k in keys:
            if k in d and d[k] is not None:
                return d[k]
        return default

    # --------------------------------------------------------------------------
    # 1. Factura Comercial (Invoice)
    # --------------------------------------------------------------------------
    if dtype in ["invoice", "factura"]:
        inv_id = _get_first(["invoice_id", "id", "folio", "folio_factura", "invoice_num", "number", "inv_id"], "INV-AUTO-001")
        vendor_id = _get_first(["vendor_id", "vendor", "proveedor", "seller_id", "emisor", "supplier_id"], "VEN-DEFAULT")
        customer_id = _get_first(["customer_id", "customer", "cliente", "buyer_id", "receptor"], "CUST-DEFAULT")
        po_ref = _get_first(["po_reference", "po_id", "po_number", "orden_compra", "po", "order_reference"], None)
        issue_date = _get_first(["issue_date", "date", "fecha", "fecha_emision", "created_at"], "2026-01-01")
        currency = str(_get_first(["currency", "moneda", "divisa"], "USD")).upper()

        raw_items = _get_first(["items", "line_items", "lineas", "partidas", "productos", "articulos"], [])
        norm_items = []
        calc_subtotal = Decimal("0.00")

        for idx, it in enumerate(raw_items, 1):
            if not isinstance(it, dict):
                continue
            item_id = str(it.get("item_id") or it.get("sku") or it.get("code") or it.get("codigo") or it.get("id") or f"PROD-{idx}")
            desc = str(it.get("description") or it.get("desc") or it.get("descripcion") or it.get("name") or it.get("producto") or f"Producto {item_id}")
            qty_raw = it.get("quantity") or it.get("qty") or it.get("cantidad") or it.get("cant") or 1
            try:
                qty = max(0, int(qty_raw))
            except Exception:
                qty = 1

            unit_price = parse_resilient_decimal(it.get("unit_price") or it.get("price") or it.get("precio") or it.get("precio_unitario"), Decimal("0.00"))
            total_price = parse_resilient_decimal(it.get("total_price") or it.get("total") or it.get("monto") or it.get("importe"), unit_price * Decimal(qty))

            calc_subtotal += total_price
            norm_items.append({
                "item_id": item_id,
                "description": desc,
                "quantity": qty,
                "unit_price": unit_price,
                "total_price": total_price
            })

        # Si no hay ítems válidos, generar un ítem base a partir del subtotal o total solo si hay un monto válido
        if not norm_items:
            declared_tot = parse_resilient_decimal(_get_first(["total_amount", "total", "monto_total", "importe_total", "subtotal"]), Decimal("0.00"))
            if declared_tot <= Decimal("0.00"):
                raise ValueError("Factura sin partidas comerciales y sin monto numérico válido.")
            norm_items.append({
                "item_id": "PROD-GENERIC-01",
                "description": "Partida Comercial Consolidada",
                "quantity": 1,
                "unit_price": declared_tot,
                "total_price": declared_tot
            })
            calc_subtotal = declared_tot
            warnings.append("Factura sin partidas explícitas: sintetizada partida genérica a partir del total")

        subtotal = parse_resilient_decimal(_get_first(["subtotal", "sub_total", "net_amount"]), calc_subtotal)
        tax = parse_resilient_decimal(_get_first(["tax", "iva", "impuesto", "taxes"]), Decimal("0.00"))
        total_amount = parse_resilient_decimal(_get_first(["total_amount", "total", "monto_total", "grand_total"]), subtotal + tax)

        return {
            "invoice_id": str(inv_id),
            "vendor_id": str(vendor_id),
            "customer_id": str(customer_id),
            "po_reference": str(po_ref) if po_ref else None,
            "issue_date": str(issue_date),
            "currency": currency,
            "items": norm_items,
            "subtotal": subtotal,
            "tax": tax,
            "total_amount": total_amount
        }, warnings

    # --------------------------------------------------------------------------
    # 2. Orden de Compra (Purchase Order)
    # --------------------------------------------------------------------------
    if dtype in ["purchase_order", "po", "orden_compra"]:
        po_id = _get_first(["po_id", "id", "folio", "po_number", "orden_compra", "po"], "PO-AUTO-001")
        vendor_id = _get_first(["vendor_id", "vendor", "proveedor", "seller_id"], "VEN-DEFAULT")
        customer_id = _get_first(["customer_id", "customer", "cliente", "buyer_id"], "CUST-DEFAULT")
        order_date = _get_first(["order_date", "date", "fecha", "order_date"], "2026-01-01")
        currency = str(_get_first(["currency", "moneda", "divisa"], "USD")).upper()

        raw_items = _get_first(["items", "line_items", "lineas", "partidas", "productos"], [])
        norm_items = []
        calc_total = Decimal("0.00")

        for idx, it in enumerate(raw_items, 1):
            if not isinstance(it, dict):
                continue
            item_id = str(it.get("item_id") or it.get("sku") or it.get("code") or it.get("id") or f"PROD-{idx}")
            desc = str(it.get("description") or it.get("desc") or it.get("name") or f"Producto {item_id}")
            qty_raw = it.get("ordered_quantity") or it.get("quantity") or it.get("qty") or it.get("cantidad") or 1
            try:
                ordered_qty = max(0, int(qty_raw))
            except Exception:
                ordered_qty = 1

            agreed_price = parse_resilient_decimal(it.get("agreed_unit_price") or it.get("unit_price") or it.get("price") or it.get("precio"), Decimal("0.00"))
            total_price = parse_resilient_decimal(it.get("total_price") or it.get("total") or it.get("monto"), agreed_price * Decimal(ordered_qty))
            calc_total += total_price

            norm_items.append({
                "item_id": item_id,
                "description": desc,
                "ordered_quantity": ordered_qty,
                "agreed_unit_price": agreed_price,
                "total_price": total_price
            })

        if not norm_items:
            norm_items.append({
                "item_id": "PROD-GENERIC-01",
                "description": "Partida Ordenada Genérica",
                "ordered_quantity": 1,
                "agreed_unit_price": Decimal("100.00"),
                "total_price": Decimal("100.00")
            })
            calc_total = Decimal("100.00")

        total_amount = parse_resilient_decimal(_get_first(["total_amount", "total", "monto_total"]), calc_total)

        return {
            "po_id": str(po_id),
            "vendor_id": str(vendor_id),
            "customer_id": str(customer_id),
            "order_date": str(order_date),
            "currency": currency,
            "items": norm_items,
            "total_amount": total_amount
        }, warnings

    # --------------------------------------------------------------------------
    # 3. Remisión de Entrega (Delivery Note)
    # --------------------------------------------------------------------------
    if dtype in ["delivery", "delivery_note", "remision"]:
        del_id = _get_first(["delivery_id", "id", "remision_id", "folio", "delivery_num", "guia"], "DEL-AUTO-001")
        po_ref = _get_first(["po_reference", "po_id", "po", "orden_compra"], "PO-AUTO-001")
        del_date = _get_first(["delivery_date", "date", "fecha", "fecha_entrega"], "2026-01-05")
        received_by = _get_first(["received_by", "receptor", "recibido_por", "firma"], "Personal de Muelle / Patio")
        wh_loc = _get_first(["warehouse_location", "warehouse", "bodega", "cedis", "muelle"], "CEDIS Muelle Central")
        signed = bool(_get_first(["signed", "firmado", "firmada", "signed_by_recipient"], True))
        discrepancy = bool(_get_first(["discrepancy_reported", "discrepancia", "faltante_reportado"], False))

        raw_items = _get_first(["items", "line_items", "partidas", "productos", "articulos", "lineas"], [])
        norm_items = []

        for idx, it in enumerate(raw_items, 1):
            if not isinstance(it, dict):
                continue
            item_id = str(it.get("item_id") or it.get("sku") or it.get("code") or it.get("codigo") or it.get("id") or f"PROD-{idx}")
            q_del_raw = it.get("quantity_delivered") or it.get("delivered_qty") or it.get("cantidad_entregada") or it.get("despachado") or it.get("quantity") or 0
            q_rec_raw = it.get("quantity_received") or it.get("received_qty") or it.get("cantidad_recibida") or it.get("recibido") or it.get("received") or q_del_raw

            try:
                q_del = max(0, int(q_del_raw))
            except Exception:
                q_del = 0
            try:
                q_rec = max(0, int(q_rec_raw))
            except Exception:
                q_rec = q_del

            # Deducir faltante si no viene explícito
            missing_def = max(0, q_del - q_rec)
            missing = int(it.get("missing_quantity") or it.get("missing_qty") or it.get("faltante") or it.get("missing") or missing_def)
            damaged = int(it.get("damaged_quantity") or it.get("damaged_qty") or it.get("dañado") or it.get("danado") or it.get("damaged") or 0)
            notes = it.get("notes") or it.get("notas") or None

            norm_items.append({
                "item_id": item_id,
                "quantity_delivered": q_del,
                "quantity_received": q_rec,
                "missing_quantity": missing,
                "damaged_quantity": damaged,
                "notes": notes
            })

        if not norm_items:
            norm_items.append({
                "item_id": "PROD-GENERIC-01",
                "quantity_delivered": 1,
                "quantity_received": 1,
                "missing_quantity": 0,
                "damaged_quantity": 0,
                "notes": "Recepción genérica completa s/ salvedades"
            })

        return {
            "delivery_id": str(del_id),
            "po_reference": str(po_ref),
            "delivery_date": str(del_date),
            "received_by": str(received_by),
            "warehouse_location": str(wh_loc),
            "signed": signed,
            "discrepancy_reported": discrepancy or any(it["missing_quantity"] > 0 for it in norm_items),
            "items": norm_items
        }, warnings

    # --------------------------------------------------------------------------
    # 4. Comprobante de Pago (Payment Receipt)
    # --------------------------------------------------------------------------
    if dtype in ["payment", "payment_receipt", "pago"]:
        pay_id = _get_first(["payment_id", "id", "folio", "comprobante_id", "spei_id", "transaction_id"], "PAY-AUTO-001")
        inv_ref = _get_first(["invoice_reference", "invoice_id", "factura", "ref_factura"], "INV-AUTO-001")
        pay_date = _get_first(["payment_date", "date", "fecha", "fecha_pago"], "2026-01-20")
        currency = str(_get_first(["currency", "moneda", "divisa"], "USD")).upper()
        amount_paid = parse_resilient_decimal(_get_first(["amount_paid", "paid_amount", "monto_pagado", "importe_pagado", "total_paid"]), Decimal("0.00"))

        raw_deductions = _get_first(["deductions", "deducciones", "retenciones", "descuentos"], [])
        norm_deductions = []

        for idx, ded in enumerate(raw_deductions, 1):
            if not isinstance(ded, dict):
                continue
            code = str(ded.get("code") or ded.get("codigo") or f"DED-AUTO-{idx:03d}")
            reason = str(ded.get("reason") or ded.get("motivo") or ded.get("concepto") or "Retención comercial no especificada")
            amt = parse_resilient_decimal(ded.get("amount") or ded.get("monto") or ded.get("importe"), Decimal("0.00"))
            ref_doc = ded.get("reference_doc") or ded.get("doc_ref") or None

            norm_deductions.append({
                "code": code,
                "reason": reason,
                "amount": amt,
                "reference_doc": ref_doc
            })

        return {
            "payment_id": str(pay_id),
            "invoice_reference": str(inv_ref),
            "payment_date": str(pay_date),
            "currency": currency,
            "amount_paid": amount_paid,
            "deductions": norm_deductions
        }, warnings

    # --------------------------------------------------------------------------
    # 5. Contrato Comercial (Commercial Contract)
    # --------------------------------------------------------------------------
    if dtype in ["contract", "commercial_contract", "contrato"]:
        con_id = _get_first(["contract_id", "id", "folio", "contrato_id"], "CON-AUTO-001")
        vendor_id = _get_first(["vendor_id", "vendor", "proveedor"], "VEN-DEFAULT")
        customer_id = _get_first(["customer_id", "customer", "cliente"], "CUST-DEFAULT")
        valid_from = _get_first(["valid_from", "desde", "fecha_inicio"], "2026-01-01")
        valid_to = _get_first(["valid_to", "hasta", "fecha_fin"], "2026-12-31")

        raw_clauses = _get_first(["clauses", "clausulas", "condiciones"], [])
        norm_clauses = []

        for idx, cl in enumerate(raw_clauses, 1):
            if isinstance(cl, dict):
                cid = str(cl.get("clause_id") or cl.get("id") or f"CLAUSE-{idx}")
                title = str(cl.get("title") or cl.get("titulo") or f"Cláusula {cid}")
                text = str(cl.get("text") or cl.get("texto") or cl.get("descripcion") or title)
                policy = str(cl.get("policy") or cl.get("politica") or "STANDARD_COMMERCIAL_TERMS")
                tolerance = parse_resilient_decimal(cl.get("tolerance_percentage") or cl.get("tolerancia"), Decimal("0.00"))
            elif isinstance(cl, str):
                cid = f"CLAUSE-{idx}"
                title = f"Término Contractual {idx}"
                text = cl
                policy = "STANDARD_COMMERCIAL_TERMS"
                tolerance = Decimal("0.00")
            else:
                continue

            norm_clauses.append({
                "clause_id": cid,
                "title": title,
                "text": text,
                "policy": policy,
                "tolerance_percentage": tolerance
            })

        if not norm_clauses:
            norm_clauses.append({
                "clause_id": "CLAUSE-STD-01",
                "title": "Condición General de Recepción y Pago",
                "text": "Las entregas deberán corresponder a las órdenes de compra emitidas. Cualquier discrepancia u objeción comercial deberá notificarse dentro de los 30 días posteriores al descargue.",
                "policy": "NOTICE_WINDOW_30_DAYS",
                "tolerance_percentage": Decimal("0.00")
            })

        return {
            "contract_id": str(con_id),
            "vendor_id": str(vendor_id),
            "customer_id": str(customer_id),
            "valid_from": str(valid_from),
            "valid_to": str(valid_to),
            "clauses": norm_clauses
        }, warnings

    return d, warnings


def impute_missing_document(doc_type: str, existing_docs: Dict[str, Any], case_id: str) -> Tuple[Any, str]:
    """
    Sintetiza un documento comercial faltante de forma consistente y auditable,
    garantizando que la falta de un archivo secundario no detenga el análisis ni cause alucinaciones.
    """
    dtype = doc_type.lower().strip()

    # 1. Imputación de Orden de Compra a partir de Factura
    if dtype in ["purchase_order", "po"]:
        inv: Optional[Invoice] = existing_docs.get("invoice")
        if inv:
            po_items = [
                PurchaseOrderItem(
                    item_id=it.item_id,
                    description=it.description,
                    ordered_quantity=it.quantity,
                    agreed_unit_price=it.unit_price,
                    total_price=it.total_price
                )
                for it in inv.items
            ]
            po = PurchaseOrder(
                po_id=inv.po_reference or f"PO-IMPUTED-{case_id}",
                vendor_id=inv.vendor_id,
                customer_id=inv.customer_id,
                order_date=inv.issue_date,
                currency=inv.currency,
                items=po_items,
                total_amount=inv.subtotal
            )
            return po, "Orden de compra (PO) no suministrada; imputada automáticamente con las partidas y precios de la factura."
        else:
            po = PurchaseOrder(
                po_id=f"PO-SYNTH-{case_id}",
                vendor_id="VEN-DEFAULT",
                customer_id="CUST-DEFAULT",
                order_date="2026-01-01",
                currency="USD",
                items=[PurchaseOrderItem(item_id="SKU-GEN-01", description="Partida Imputada", ordered_quantity=1, agreed_unit_price=Decimal("100.00"), total_price=Decimal("100.00"))],
                total_amount=Decimal("100.00")
            )
            return po, "Orden de compra sintetizada con valores mínimos por carencia documental."

    # 2. Imputación de Contrato Marco Estándar
    if dtype in ["contract", "commercial_contract"]:
        inv: Optional[Invoice] = existing_docs.get("invoice")
        con = CommercialContract(
            contract_id=f"CON-IMPUTED-{case_id}",
            vendor_id=inv.vendor_id if inv else "VEN-DEFAULT",
            customer_id=inv.customer_id if inv else "CUST-DEFAULT",
            valid_from="2026-01-01",
            valid_to="2026-12-31",
            clauses=[
                ContractClause(
                    clause_id="CLAUSE-STD-TIMELY-NOTICE",
                    title="Plazo Contractual de Objeción de Facturas",
                    text="El comprador dispondrá de 30 días naturales posteriores al arribo de mercancía para formular objeciones o deducciones; transcurrido dicho plazo, la factura se considerará irrevocablemente aceptada.",
                    policy="NOTICE_WINDOW_30_DAYS",
                    tolerance_percentage=Decimal("0.00")
                ),
                ContractClause(
                    clause_id="CLAUSE-STD-DELIVERY-RISK",
                    title="Transferencia de Riesgo y Custodia en Muelle",
                    text="La constancia firmada y sellada en la remisión de entrega por el transportista o personal de patio constituye prueba plena del estado físico de las mercancías recibidas.",
                    policy="STANDARD_DELIVERY_PROOF",
                    tolerance_percentage=Decimal("0.00")
                )
            ]
        )
        return con, "Contrato marco MSA no aportado; adoptadas cláusulas mercantiles estándar de buena fe (Aviso a 30 días)."

    # 3. Imputación de Remisión (Delivery)
    if dtype in ["delivery", "delivery_note"]:
        inv: Optional[Invoice] = existing_docs.get("invoice")
        po: Optional[PurchaseOrder] = existing_docs.get("purchase_order")
        items_source = inv.items if inv else (po.items if po else [])

        del_items = [
            DeliveryItem(
                item_id=it.item_id,
                quantity_delivered=it.quantity if hasattr(it, "quantity") else it.ordered_quantity,
                quantity_received=it.quantity if hasattr(it, "quantity") else it.ordered_quantity,
                missing_quantity=0,
                damaged_quantity=0,
                notes="Entrega asumida conforme s/ remisión física"
            )
            for it in items_source
        ]
        if not del_items:
            del_items = [DeliveryItem(item_id="SKU-GEN-01", quantity_delivered=1, quantity_received=1, missing_quantity=0, damaged_quantity=0, notes="")]

        deliv = DeliveryNote(
            delivery_id=f"DEL-IMPUTED-{case_id}",
            po_reference=inv.po_reference if inv and inv.po_reference else (po.po_id if po else f"PO-{case_id}"),
            delivery_date=inv.issue_date if inv else "2026-01-05",
            received_by="Receptor en Muelle (Conforme)",
            warehouse_location="CEDIS Principal",
            signed=True,
            discrepancy_reported=False,
            items=del_items
        )
        return deliv, "Remisión física no localizada en expediente; asumida entrega física completa conforme a factura sin faltantes declarados."

    # 4. Imputación de Pago (Payment)
    if dtype in ["payment", "payment_receipt"]:
        inv: Optional[Invoice] = existing_docs.get("invoice")
        pay = PaymentReceipt(
            payment_id=f"PAY-IMPUTED-{case_id}",
            invoice_reference=inv.invoice_id if inv else f"INV-{case_id}",
            payment_date=inv.issue_date if inv else "2026-01-20",
            currency=inv.currency if inv else "USD",
            amount_paid=Decimal("0.00"),
            deductions=[PaymentDeduction(code="DED-FULL-HOLD", reason="Retención total por falta de comprobante de pago bancario", amount=inv.total_amount if inv else Decimal("0.00"))]
        )
        return pay, "Comprobante de pago bancario no localizado; considerado impago total temporal para análisis de recuperación."

    raise ValueError(f"Tipo documental desconocido para imputación: {doc_type}")


class ResilientDocumentLoader:
    """
    Cargador integral y autocurativo de expedientes comerciales B2B.
    Garantiza que cualquier caso con datos sucios, JSONs rotos o documentos faltantes
    pueda ser analizado con máxima resiliencia sin alucinar.
    """

    @classmethod
    def load_case_resilient(
        cls,
        case_id: str,
        allow_imputation: bool = True
    ) -> Tuple[Dict[str, Any], DocumentHealthAudit]:
        """
        Carga y auto-repara los documentos comerciales de un caso.
        Retorna (documentos_pydantic, auditoria_de_salud).
        """
        from config.settings import settings
        from tools.document_reader.classifier import DocumentClassifier
        from tools.document_reader.pdf_parser import PDFCaseParser

        provided_path = Path(case_id)
        if provided_path.is_absolute() or provided_path.exists():
            case_path = provided_path
        else:
            case_path = settings.DATA_DIR / case_id

        if not case_path.exists() or not case_path.is_dir():
            raise FileNotFoundError(f"Expediente '{case_id}' no encontrado en {case_path}")

        mapped = DocumentClassifier.classify_and_map_case_directory(case_path)
        documents: Dict[str, Any] = {}
        repaired_issues: List[str] = []
        imputed_documents: List[str] = []
        schema_warnings: List[str] = []
        docs_present: List[str] = list(mapped.keys())
        docs_missing: List[str] = []

        health_score = 100.0

        # Helper interno para cargar archivo JSON o PDF de forma tolerante
        def _load_doc_file(doc_key: str, model_cls: Any) -> Optional[Any]:
            nonlocal health_score
            if doc_key not in mapped:
                return None
            f_path = mapped[doc_key]
            suffix = f_path.suffix.lower()

            try:
                if suffix == ".json":
                    with open(f_path, "r", encoding="utf-8", errors="replace") as f:
                        raw_content = f.read()

                    # Auto-reparar JSON si fuera necesario
                    raw_dict, fix_msgs = repair_json_string(raw_content)
                    if fix_msgs:
                        health_score -= min(10.0, len(fix_msgs) * 2.5)
                        repaired_issues.extend([f"[{f_path.name}] {m}" for m in fix_msgs])

                    # Normalización polimórfica de esquemas y alias
                    norm_dict, warn_msgs = normalize_schema_dict(raw_dict, doc_key)
                    if warn_msgs:
                        schema_warnings.extend([f"[{f_path.name}] {w}" for w in warn_msgs])

                    return model_cls.model_validate(norm_dict)

                elif suffix == ".pdf":
                    # Parseo tolerante de PDF
                    if doc_key == "invoice":
                        return PDFCaseParser.parse_invoice(f_path)
                    elif doc_key == "purchase_order":
                        return PDFCaseParser.parse_purchase_order(f_path)
                    elif doc_key == "delivery":
                        return PDFCaseParser.parse_delivery_note(f_path)
                    elif doc_key == "payment":
                        return PDFCaseParser.parse_payment_receipt(f_path)
                    elif doc_key == "contract":
                        return PDFCaseParser.parse_contract(f_path)

                elif suffix in [".png", ".jpg", ".jpeg", ".webp"] and doc_key == "delivery":
                    from tools.ocr_engine.vision import OCREngine
                    return OCREngine().extract_delivery_note(f_path)

                elif suffix == ".md" and doc_key == "contract":
                    from tools.contract_analyzer.rag import ContractRAG
                    return ContractRAG().ingest_contract_markdown(str(case_id), f_path)

            except Exception as e:
                # Si falló la validación directa, intentar normalización forzada
                repaired_issues.append(f"[{f_path.name}] Error de lectura primaria: {str(e)[:150]}. Activando autocuración profunda.")
                health_score -= 15.0
                try:
                    # Intento de rescate con dict mínimo
                    rescue_dict, _ = normalize_schema_dict({"id": f_path.stem}, doc_key)
                    return model_cls.model_validate(rescue_dict)
                except Exception:
                    return None
            return None

        # 1. Factura (Invoice)
        doc_inv = _load_doc_file("invoice", Invoice)
        if doc_inv:
            documents["invoice"] = doc_inv
        else:
            docs_missing.append("invoice")

        # 2. Orden de Compra (Purchase Order)
        doc_po = _load_doc_file("purchase_order", PurchaseOrder)
        if doc_po:
            documents["purchase_order"] = doc_po
        else:
            docs_missing.append("purchase_order")

        # 3. Comprobante de Pago (Payment Receipt)
        doc_pay = _load_doc_file("payment", PaymentReceipt)
        if doc_pay:
            documents["payment"] = doc_pay
        else:
            docs_missing.append("payment")

        # 4. Contrato Comercial (Commercial Contract)
        doc_con = _load_doc_file("contract", CommercialContract)
        if doc_con:
            documents["contract"] = doc_con
        else:
            docs_missing.append("contract")

        # 5. Remisión de Entrega (Delivery Note)
        doc_del = _load_doc_file("delivery", DeliveryNote)
        if doc_del:
            documents["delivery"] = doc_del
        else:
            docs_missing.append("delivery")

        # Imputación de documentos faltantes si está permitido
        # No se permite imputación si hay 1 o menos documentos presentes (carencia fáctica absoluta)
        if len(docs_present) <= 1:
            allow_imputation = False
            health_score = 0.0

        if allow_imputation and docs_missing:
            for m_doc in list(docs_missing):
                # No podemos imputar si ni siquiera hay factura ni remisión
                if m_doc == "invoice" and not documents.get("purchase_order") and not documents.get("delivery"):
                    continue

                try:
                    imputed_instance, rationale = impute_missing_document(m_doc, documents, case_id)
                    documents[m_doc] = imputed_instance
                    imputed_documents.append(f"{m_doc}: {rationale}")
                    docs_missing.remove(m_doc)
                    health_score -= 10.0
                except Exception as imp_err:
                    repaired_issues.append(f"Fallo al imputar {m_doc}: {str(imp_err)}")

        # Clasificación del estado de salud
        health_score = max(0.0, min(100.0, round(health_score, 1)))
        if health_score >= 98.0 and not imputed_documents and not repaired_issues:
            status = "PRISTINE"
            safety = "SAFE_FOR_AUTONOMOUS_SETTLEMENT"
        elif health_score >= 80.0:
            status = "AUTO_REPAIRED"
            safety = "SAFE_WITH_TRACEABILITY"
        elif health_score >= 50.0:
            status = "DEGRADED"
            safety = "REQUIRES_OPERATOR_OVERSIGHT"
        else:
            status = "QUARANTINE"
            safety = "HOLD_SETTLEMENT_DOCUMENT_AUDIT_REQUIRED"

        audit = DocumentHealthAudit(
            case_id=case_id,
            health_score=health_score,
            status=status,
            is_healthy=(health_score >= 50.0),
            repaired_issues=repaired_issues,
            imputed_documents=imputed_documents,
            documents_present=docs_present,
            documents_missing=docs_missing,
            schema_warnings=schema_warnings,
            execution_safety_level=safety,
            generated_at=datetime.now(timezone.utc).isoformat()
        )

        return documents, audit
