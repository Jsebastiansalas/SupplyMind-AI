"""
agent/core/harness_adapter.py
Adaptador Universal de Evaluación para el Harness Automatizado de Platica y Jurados (CLI + REST API).

Soporta de forma transparente:
1. Identificadores de casos del catálogo (`case_001`, `case_005_amazon_shortage`, `dataco_real_...`).
2. Directorios arbitrarios externos (`/ruta/a/carpeta_caso`) con normalización automática de nombres (ES/EN).
3. Archivos JSON individuales o payloads en memoria con los 5 documentos (`invoice`, `purchase_order`, `delivery`, `payment`, `contract`) o parámetros abreviados (`billed_amount`, `amount_paid`, `items`, `unauthorized_penalty`).
4. Salida JSON determinística 100% limpia en stdout (aislando logs decorativos en stderr) con invariante $0.00 MAE verificado.
"""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import re
import shutil
import sys
import time
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, Optional, Union

from config.settings import settings
from agent.core.skynet_runner import SkynetRunner


# Mapa de alias de nombres de archivos (Español / Inglés) para carpetas externas del Harness
FILENAME_ALIAS_MAP = {
    "factura.json": "invoice.json",
    "inv.json": "invoice.json",
    "orden_compra.json": "purchase_order.json",
    "orden_de_compra.json": "purchase_order.json",
    "po.json": "purchase_order.json",
    "remision.json": "delivery.json",
    "entrega.json": "delivery.json",
    "pod.json": "delivery.json",
    "pago.json": "payment.json",
    "comprobante_pago.json": "payment.json",
    "contrato.json": "contract.json",
}


class HarnessAdapter:
    """Adaptador estandarizado para evaluaciones automatizadas del Harness de Platica."""

    @staticmethod
    def _sanitize_case_id(raw_id: str) -> str:
        clean = re.sub(r"[^a-zA-Z0-9_\-]", "_", raw_id.strip()).lower()
        if not clean:
            clean = "case_harness_eval"
        if not (clean.startswith("case_") or clean.startswith("dataco_") or clean.startswith("holdout_")):
            clean = f"case_{clean}"
        return clean

    @classmethod
    def materialize_from_dict(cls, payload: Dict[str, Any], default_id: Optional[str] = None) -> str:
        """
        Materializa un expediente de 5 documentos en `data/cases/<case_id>` a partir de un diccionario JSON.
        Soporta tanto payloads con documentos anidados (`invoice`, `purchase_order`, etc.)
        como payloads parametrizados (`billed_amount`, `amount_paid`, `items`, etc.).
        """
        raw_id = str(payload.get("case_id") or default_id or f"harness_{int(time.time())}")
        case_id = cls._sanitize_case_id(raw_id)
        target_dir = settings.DATA_DIR / case_id
        target_dir.mkdir(parents=True, exist_ok=True)

        # Caso A: El payload ya trae documentos explícitos (en inglés o español)
        doc_keys = {
            "invoice": ["invoice", "factura"],
            "purchase_order": ["purchase_order", "po", "orden_compra"],
            "delivery": ["delivery", "pod", "remision", "entrega"],
            "payment": ["payment", "pago"],
            "contract": ["contract", "contrato"],
        }
        found_explicit_docs = False
        for canonical_name, aliases in doc_keys.items():
            for alias in aliases:
                if alias in payload and isinstance(payload[alias], dict):
                    found_explicit_docs = True
                    with open(target_dir / f"{canonical_name}.json", "w", encoding="utf-8") as f:
                        json.dump(payload[alias], f, indent=2, ensure_ascii=False)
                    break

        if found_explicit_docs:
            # Asegurar que si algún documento opcional no vino en el payload, se cree una estructura base válida
            cls._ensure_minimum_five_docs(target_dir, case_id, payload)
            return case_id

        # Caso B: El payload es parametrizado o guiado
        from api.routes.cases import GuidedCaseRequest, GuidedCaseItem, create_guided_case

        billed = float(payload.get("billed_amount", payload.get("total_amount", 10000.0)))
        paid = payload.get("amount_paid", payload.get("received_amount", None))
        paid_float = float(paid) if paid is not None else None
        unauth = float(payload.get("unauthorized_penalty", 0.0))
        missing_val = float(payload.get("missing_amount", 0.0))

        raw_items = payload.get("items")
        guided_items = []
        if isinstance(raw_items, list) and len(raw_items) > 0:
            for idx, it in enumerate(raw_items):
                if isinstance(it, dict):
                    guided_items.append(
                        GuidedCaseItem(
                            item_id=str(it.get("item_id", f"SKU-{idx+1:03d}")),
                            description=str(it.get("description", f"Producto B2B {idx+1}")),
                            ordered_quantity=int(it.get("ordered_quantity", it.get("quantity", 100))),
                            delivered_quantity=int(it.get("delivered_quantity", it.get("quantity_received", 100))),
                            missing_quantity=int(it.get("missing_quantity", 0)),
                            damaged_quantity=int(it.get("damaged_quantity", 0)),
                            agreed_unit_price=float(it.get("agreed_unit_price", it.get("unit_price", 100.0))),
                            invoiced_unit_price=(
                                float(it["invoiced_unit_price"])
                                if it.get("invoiced_unit_price") is not None
                                else None
                            ),
                        )
                    )
        if not guided_items:
            unit_price = round(billed / 100.0, 2) if billed > 0 else 100.0
            missing_qty = int(round(missing_val / unit_price)) if (missing_val > 0 and unit_price > 0) else 0
            guided_items.append(
                GuidedCaseItem(
                    item_id="PROD-HARNESS-01",
                    description="Mercancía Comercial B2B",
                    ordered_quantity=100,
                    delivered_quantity=max(0, 100 - missing_qty),
                    missing_quantity=missing_qty,
                    damaged_quantity=0,
                    agreed_unit_price=unit_price,
                )
            )

        req = GuidedCaseRequest(
            case_id=case_id,
            display_name=str(payload.get("display_name", f"Harness Case {case_id}")),
            category=str(payload.get("category", "Harness Evaluation")),
            description=str(payload.get("description", "Expediente inyectado por el Harness de Evaluación")),
            vendor_id=str(payload.get("vendor_id", "VEN-HARNESS-01")),
            customer_id=str(payload.get("customer_id", payload.get("retailer_name", "CUST-RETAIL-01"))),
            currency=str(payload.get("currency", "USD")),
            items=guided_items,
            amount_paid=paid_float,
            unauthorized_penalty=unauth,
            unauthorized_penalty_reason=str(
                payload.get("unauthorized_penalty_reason", "Deducción unilateral sin sustento contractual")
            ),
        )
        create_guided_case(req)
        return case_id

    @classmethod
    def _ensure_minimum_five_docs(cls, target_dir: Path, case_id: str, payload: Dict[str, Any]) -> None:
        """Completa cualquier documento faltante con valores por defecto consistentes."""
        short_code = case_id.replace("case_", "")[:6].upper() or "HRN"
        inv_path = target_dir / "invoice.json"
        if inv_path.exists():
            try:
                inv_data = json.loads(inv_path.read_text(encoding="utf-8"))
            except Exception:
                inv_data = {}
        else:
            inv_data = {
                "invoice_id": f"INV-{short_code}",
                "vendor_id": "VEN-01",
                "customer_id": "CUST-01",
                "po_reference": f"PO-{short_code}",
                "issue_date": "2026-09-01",
                "currency": "USD",
                "items": [{"item_id": "SKU-001", "description": "Item", "quantity": 10, "unit_price": 100.0, "total_price": 1000.0}],
                "subtotal": 1000.0,
                "tax": 0.0,
                "total_amount": 1000.0,
            }
            inv_path.write_text(json.dumps(inv_data, indent=2, ensure_ascii=False), encoding="utf-8")

        total_amt = float(inv_data.get("total_amount", 1000.0))
        po_path = target_dir / "purchase_order.json"
        if not po_path.exists():
            po_items = []
            for it in inv_data.get("items", []):
                po_items.append({
                    "item_id": it.get("item_id", "SKU-001"),
                    "description": it.get("description", "Item"),
                    "ordered_quantity": it.get("quantity", it.get("ordered_quantity", 10)),
                    "agreed_unit_price": it.get("unit_price", it.get("agreed_unit_price", 100.0)),
                    "total_price": it.get("total_price", total_amt),
                })
            po_doc = {
                "po_id": inv_data.get("po_reference", f"PO-{short_code}"),
                "vendor_id": inv_data.get("vendor_id", "VEN-01"),
                "customer_id": inv_data.get("customer_id", "CUST-01"),
                "order_date": "2026-08-25",
                "currency": inv_data.get("currency", "USD"),
                "items": po_items,
                "total_amount": total_amt,
            }
            po_path.write_text(json.dumps(po_doc, indent=2, ensure_ascii=False), encoding="utf-8")

        del_path = target_dir / "delivery.json"
        if not del_path.exists():
            del_items = []
            for it in inv_data.get("items", []):
                qty = it.get("quantity", it.get("ordered_quantity", 10))
                del_items.append({
                    "item_id": it.get("item_id", "SKU-001"),
                    "quantity_delivered": qty,
                    "quantity_received": qty,
                    "missing_quantity": 0,
                    "damaged_quantity": 0,
                    "notes": "Entrega conforme en muelle",
                })
            del_doc = {
                "delivery_id": f"DEL-{short_code}",
                "po_reference": inv_data.get("po_reference", f"PO-{short_code}"),
                "delivery_date": "2026-09-03",
                "received_by": "Almacén Central",
                "warehouse_location": "CEDIS Principal",
                "signed": True,
                "discrepancy_reported": False,
                "items": del_items,
            }
            del_path.write_text(json.dumps(del_doc, indent=2, ensure_ascii=False), encoding="utf-8")

        pay_path = target_dir / "payment.json"
        if not pay_path.exists():
            pay_doc = {
                "payment_id": f"PAY-{short_code}",
                "invoice_reference": inv_data.get("invoice_id", f"INV-{short_code}"),
                "payment_date": "2026-09-25",
                "currency": inv_data.get("currency", "USD"),
                "amount_paid": float(payload.get("amount_paid", total_amt)),
                "deductions": payload.get("deductions", []),
            }
            pay_path.write_text(json.dumps(pay_doc, indent=2, ensure_ascii=False), encoding="utf-8")

        ctr_path = target_dir / "contract.json"
        if not ctr_path.exists():
            ctr_doc = {
                "contract_id": f"CTR-{short_code}",
                "vendor_id": inv_data.get("vendor_id", "VEN-01"),
                "customer_id": inv_data.get("customer_id", "CUST-01"),
                "valid_from": "2026-01-01",
                "valid_to": "2026-12-31",
                "clauses": [
                    {
                        "clause_id": "CLAUSE-3.1",
                        "title": "Inalterabilidad de Precios y Recepción",
                        "text": "Toda deducción requiere evidencia firmada en muelle de descarga.",
                        "policy": "STRICT_MATCH",
                        "tolerance_percentage": 0.0,
                    }
                ],
            }
            ctr_path.write_text(json.dumps(ctr_doc, indent=2, ensure_ascii=False), encoding="utf-8")

    @classmethod
    def resolve_input_target(cls, target: Union[str, Path, Dict[str, Any]]) -> str:
        """
        Resuelve cualquier entrada (ID de caso, ruta a directorio, ruta a archivo JSON o dict)
        y retorna un identificador/ruta lista para `SkynetRunner`.
        """
        if isinstance(target, dict):
            return cls.materialize_from_dict(target)

        target_str = str(target).strip()
        p = Path(target_str)

        # 1. Si es un archivo JSON existente en disco
        if p.exists() and p.is_file() and p.suffix.lower() == ".json":
            data = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return cls.materialize_from_dict(data, default_id=p.stem)

        # 2. Si es un directorio existente en disco
        if p.exists() and p.is_dir():
            # Verificar si tiene archivos con alias en español y normalizarlos si hace falta
            has_canonical = (p / "invoice.json").exists() or any(p.glob("*.xlsx")) or any(p.glob("*.pdf"))
            if not has_canonical:
                case_id = cls._sanitize_case_id(p.name)
                dest_dir = settings.DATA_DIR / case_id
                dest_dir.mkdir(parents=True, exist_ok=True)
                for item in p.iterdir():
                    if item.is_file():
                        mapped_name = FILENAME_ALIAS_MAP.get(item.name.lower(), item.name)
                        shutil.copy2(item, dest_dir / mapped_name)
                cls._ensure_minimum_five_docs(dest_dir, case_id, {})
                return case_id
            return str(p.resolve())

        # 3. Si es un case_id conocido en data/cases, data/real_supply_chain_cases o data/holdout_cases
        return target_str

    @classmethod
    def evaluate(
        cls,
        target: Union[str, Path, Dict[str, Any]],
        fast_path: bool = False,
        question: Optional[str] = None,
        silent_stdout: bool = True,
    ) -> Dict[str, Any]:
        """
        Ejecuta la evaluación completa del caso y retorna un diccionario JSON estandarizado
        con verificación matemática $0.00 MAE y telemetría de consumo.
        """
        t0 = time.perf_counter()
        capture_buf = io.StringIO()

        with (contextlib.redirect_stdout(capture_buf) if silent_stdout else contextlib.nullcontext()):
            resolved_case = cls.resolve_input_target(target)
            runner = SkynetRunner(
                case_id=resolved_case,
                fast_path=fast_path,
                auto_route=not fast_path,
            )
            report = runner.run()
            answer = runner.ask(question) if question else None

        elapsed = round(time.perf_counter() - t0, 4)

        billed = Decimal(str(report.billed_amount or 0))
        received = Decimal(str(report.received_amount or 0))
        diff = abs(Decimal(str(report.difference if report.difference is not None else (billed - received))))
        justified = abs(Decimal(str(report.justified_amount or 0)))
        claimable = abs(Decimal(str(report.claimable_amount or 0)))
        delta_mae = abs(diff - (justified + claimable))

        tokens_in = int(getattr(runner.state, "tokens_in", 0) or 0)
        tokens_out = int(getattr(runner.state, "tokens_out", 0) or 0)
        cost_usd = float(getattr(runner.state, "estimated_cost_usd", 0.0) or 0.0)
        tools_used = [t.tool_name for t in getattr(runner.state, "tool_traces", [])]

        result: Dict[str, Any] = {
            "status": "SUCCESS",
            "case_id": report.case_id,
            "currency": getattr(report, "currency", "USD"),
            "billed_amount": float(billed),
            "received_amount": float(received),
            "difference": float(diff),
            "justified_amount": float(justified),
            "claimable_amount": float(claimable),
            "mae_invariant_verified": bool(delta_mae == Decimal("0.00")),
            "financial_delta_mae": float(delta_mae),
            "root_cause": report.root_cause,
            "evidence": list(report.evidence or []),
            "recommended_action": report.recommended_action,
            "confidence": float(report.confidence),
            "telemetry": {
                "model": settings.MODEL_NAME,
                "gateway_url": settings.PLATICA_BASE_URL,
                "live_api_configured": settings.is_live_api_ready,
                "tokens_in": tokens_in,
                "tokens_out": tokens_out,
                "tokens_total": tokens_in + tokens_out,
                "cost_usd": round(cost_usd, 6),
                "gateway_unit_cost_usd": 0.011340,
                "execution_time_seconds": elapsed,
                "tools_invoked": tools_used,
            },
        }
        if answer is not None:
            result["question"] = question
            result["agent_answer"] = answer

        return result
