import json
from pathlib import Path
from typing import Dict, Any, List
from config.settings import settings
from data.models import (
    Invoice,
    PurchaseOrder,
    DeliveryNote,
    DeliveryItem,
    PaymentReceipt,
    CommercialContract
)

ROOT_DIR = Path(__file__).resolve().parent.parent.parent


def consolidate_partial_deliveries(deliveries: List[DeliveryNote]) -> DeliveryNote:
    """
    US-803: Consolida múltiples remisiones de entregas parciales (Split Shipments / Backorders)
    asociadas a una misma Orden de Compra en una sola entidad DeliveryNote agregada por SKU,
    evitando que entregas divididas en varios camiones se clasifiquen erróneamente como faltantes.
    """
    if not deliveries:
        raise ValueError("La lista de entregas parciales a consolidar está vacía.")
    if len(deliveries) == 1:
        return deliveries[0]

    base = deliveries[0]
    merged_items: Dict[str, Dict[str, Any]] = {}
    delivery_ids = []

    for d_note in deliveries:
        delivery_ids.append(d_note.delivery_id)
        for item in d_note.items:
            if item.item_id not in merged_items:
                merged_items[item.item_id] = {
                    "item_id": item.item_id,
                    "quantity_delivered": item.quantity_delivered,
                    "quantity_received": item.quantity_received,
                    "missing_quantity": item.missing_quantity,
                    "damaged_quantity": item.damaged_quantity,
                    "notes_list": [item.notes] if item.notes else [],
                }
            else:
                acc = merged_items[item.item_id]
                acc["quantity_delivered"] += item.quantity_delivered
                acc["quantity_received"] += item.quantity_received
                acc["missing_quantity"] += item.missing_quantity
                acc["damaged_quantity"] += item.damaged_quantity
                if item.notes:
                    acc["notes_list"].append(item.notes)

    consolidated_items = [
        DeliveryItem(
            item_id=k,
            quantity_delivered=v["quantity_delivered"],
            quantity_received=v["quantity_received"],
            missing_quantity=v["missing_quantity"],
            damaged_quantity=v["damaged_quantity"],
            notes=" | ".join(v["notes_list"]) if v["notes_list"] else f"Consolidado de {len(deliveries)} entregas parciales",
        )
        for k, v in merged_items.items()
    ]

    return DeliveryNote(
        delivery_id="+".join(delivery_ids),
        po_reference=base.po_reference,
        delivery_date=max(d.delivery_date for d in deliveries),
        received_by=", ".join(dict.fromkeys(d.received_by for d in deliveries if d.received_by)),
        warehouse_location=base.warehouse_location,
        signed=all(d.signed for d in deliveries),
        discrepancy_reported=any(d.discrepancy_reported for d in deliveries),
        items=consolidated_items,
    )

class DocumentReaderError(Exception):
    """Excepción para errores al localizar, leer o parsear documentos de un caso."""
    pass

def load_case_documents(case_id: str) -> Dict[str, Any]:
    """
    Carga y valida rigurosamente los 5 documentos comerciales de un caso.
    
    Retorna un diccionario con las instancias tipadas de Pydantic:
    - 'invoice': Invoice
    - 'purchase_order': PurchaseOrder
    - 'delivery': DeliveryNote
    - 'payment': PaymentReceipt
    - 'contract': CommercialContract
    """
    provided_path = Path(case_id)
    if provided_path.is_absolute() or provided_path.exists():
        case_path = provided_path
    elif (settings.DATA_DIR / case_id).exists():
        case_path = settings.DATA_DIR / case_id
    elif (Path("data/holdout_cases") / case_id).exists():
        case_path = Path("data/holdout_cases") / case_id
    elif (ROOT_DIR / "data" / "holdout_cases" / case_id).exists():
        case_path = ROOT_DIR / "data" / "holdout_cases" / case_id
    elif (Path("data/real_supply_chain_cases") / case_id).exists():
        case_path = Path("data/real_supply_chain_cases") / case_id
    elif (ROOT_DIR / "data" / "real_supply_chain_cases" / case_id).exists():
        case_path = ROOT_DIR / "data" / "real_supply_chain_cases" / case_id
    else:
        case_path = settings.DATA_DIR / case_id

    if not case_path.exists() or not case_path.is_dir():
        raise DocumentReaderError(f"El expediente del caso '{case_id}' no existe (ruta evaluada: {case_path})")
        
    from tools.document_reader.classifier import DocumentClassifier
    from tools.document_reader.pdf_parser import PDFCaseParser
    from tools.document_reader.multiformat_parser import MultiFormatParser

    mapped = DocumentClassifier.classify_and_map_case_directory(case_path)
    documents = {}
    
    # 1. Factura (Invoice)
    if "invoice" in mapped:
        inv_file = mapped["invoice"]
        try:
            inv_ext = inv_file.suffix.lower()
            if inv_ext == ".json":
                with open(inv_file, "r", encoding="utf-8", errors="replace") as f:
                    raw_content = f.read()
                try:
                    documents["invoice"] = Invoice.model_validate(json.load(inv_file.open("r", encoding="utf-8")))
                except Exception:
                    # Activación de autocuración sintáctica y de esquema
                    from agent.ingestion.resilient_parser import repair_json_string, normalize_schema_dict
                    raw_dict, _ = repair_json_string(raw_content)
                    norm_dict, _ = normalize_schema_dict(raw_dict, "invoice")
                    documents["invoice"] = Invoice.model_validate(norm_dict)
            elif inv_ext == ".pdf":
                documents["invoice"] = PDFCaseParser.parse_invoice(inv_file)
            elif inv_ext in (".csv", ".xlsx"):
                documents["invoice"] = MultiFormatParser.parse_tabular_document(inv_file, "invoice")
            elif inv_ext in (".txt", ".eml"):
                documents["invoice"] = MultiFormatParser.parse_text_document(inv_file, "invoice")
            elif inv_ext in (".png", ".jpg", ".jpeg", ".webp"):
                from tools.ocr_engine.vision import OCREngine
                ocr = OCREngine()
                documents["invoice"] = ocr.extract_invoice(inv_file)
        except Exception as e:
            raise DocumentReaderError(f"Error al procesar factura '{inv_file.name}' en '{case_id}': {str(e)}")
    else:
        raise DocumentReaderError(f"Falta el documento requerido de Factura (invoice) en el expediente '{case_id}'")

    # 2. Orden de Compra (Purchase Order)
    if "purchase_order" in mapped:
        po_file = mapped["purchase_order"]
        try:
            po_ext = po_file.suffix.lower()
            if po_ext == ".json":
                with open(po_file, "r", encoding="utf-8", errors="replace") as f:
                    raw_content = f.read()
                try:
                    documents["purchase_order"] = PurchaseOrder.model_validate(json.load(po_file.open("r", encoding="utf-8")))
                except Exception:
                    from agent.ingestion.resilient_parser import repair_json_string, normalize_schema_dict
                    raw_dict, _ = repair_json_string(raw_content)
                    norm_dict, _ = normalize_schema_dict(raw_dict, "purchase_order")
                    documents["purchase_order"] = PurchaseOrder.model_validate(norm_dict)
            elif po_ext == ".pdf":
                documents["purchase_order"] = PDFCaseParser.parse_purchase_order(po_file)
            elif po_ext in (".csv", ".xlsx"):
                documents["purchase_order"] = MultiFormatParser.parse_tabular_document(po_file, "purchase_order")
            elif po_ext in (".txt", ".eml"):
                documents["purchase_order"] = MultiFormatParser.parse_text_document(po_file, "purchase_order")
            elif po_ext in (".png", ".jpg", ".jpeg", ".webp"):
                from tools.ocr_engine.vision import OCREngine
                ocr = OCREngine()
                documents["purchase_order"] = ocr.extract_purchase_order(po_file)
        except Exception as e:
            raise DocumentReaderError(f"Error al procesar orden de compra '{po_file.name}' en '{case_id}': {str(e)}")
    else:
        raise DocumentReaderError(f"Falta el documento requerido de Orden de Compra (purchase_order) en el expediente '{case_id}'")

    # 3. Comprobante de Pago (Payment Receipt)
    if "payment" in mapped:
        pay_file = mapped["payment"]
        try:
            pay_ext = pay_file.suffix.lower()
            if pay_ext == ".json":
                with open(pay_file, "r", encoding="utf-8", errors="replace") as f:
                    raw_content = f.read()
                try:
                    documents["payment"] = PaymentReceipt.model_validate(json.load(pay_file.open("r", encoding="utf-8")))
                except Exception:
                    from agent.ingestion.resilient_parser import repair_json_string, normalize_schema_dict
                    raw_dict, _ = repair_json_string(raw_content)
                    norm_dict, _ = normalize_schema_dict(raw_dict, "payment")
                    documents["payment"] = PaymentReceipt.model_validate(norm_dict)
            elif pay_ext == ".pdf":
                documents["payment"] = PDFCaseParser.parse_payment_receipt(pay_file)
            elif pay_ext in (".csv", ".xlsx"):
                documents["payment"] = MultiFormatParser.parse_tabular_document(pay_file, "payment")
            elif pay_ext in (".txt", ".eml"):
                documents["payment"] = MultiFormatParser.parse_text_document(pay_file, "payment")
            elif pay_ext in (".png", ".jpg", ".jpeg", ".webp"):
                from tools.ocr_engine.vision import OCREngine
                ocr = OCREngine()
                documents["payment"] = ocr.extract_payment_receipt(pay_file)
        except Exception as e:
            raise DocumentReaderError(f"Error al procesar comprobante de pago '{pay_file.name}' en '{case_id}': {str(e)}")
    else:
        raise DocumentReaderError(f"Falta el documento requerido de Comprobante de Pago (payment) en el expediente '{case_id}'")

    # 4. Contrato Comercial (Commercial Contract)
    if "contract" in mapped:
        con_file = mapped["contract"]
        try:
            con_ext = con_file.suffix.lower()
            if con_ext == ".json":
                with open(con_file, "r", encoding="utf-8", errors="replace") as f:
                    raw_content = f.read()
                try:
                    documents["contract"] = CommercialContract.model_validate(json.load(con_file.open("r", encoding="utf-8")))
                except Exception:
                    from agent.ingestion.resilient_parser import repair_json_string, normalize_schema_dict
                    raw_dict, _ = repair_json_string(raw_content)
                    norm_dict, _ = normalize_schema_dict(raw_dict, "contract")
                    documents["contract"] = CommercialContract.model_validate(norm_dict)
            elif con_ext == ".pdf":
                documents["contract"] = PDFCaseParser.parse_contract(con_file)
            elif con_ext == ".md":
                from tools.contract_analyzer.rag import ContractRAG
                rag = ContractRAG()
                documents["contract"] = rag.ingest_contract_markdown(str(case_id), con_file)
            elif con_ext in (".csv", ".xlsx"):
                documents["contract"] = MultiFormatParser.parse_tabular_document(con_file, "contract")
            elif con_ext in (".txt", ".eml"):
                documents["contract"] = MultiFormatParser.parse_text_document(con_file, "contract")
        except Exception as e:
            raise DocumentReaderError(f"Error al procesar contrato '{con_file.name}' en '{case_id}': {str(e)}")
    else:
        raise DocumentReaderError(f"Falta el documento requerido de Contrato (contract) en el expediente '{case_id}'")

    # 5. Remisión de Entrega (Delivery Note)
    if "delivery" in mapped:
        del_file = mapped["delivery"]
        try:
            del_ext = del_file.suffix.lower()
            if del_ext == ".json":
                with open(del_file, "r", encoding="utf-8", errors="replace") as f:
                    raw_content = f.read()
                try:
                    documents["delivery"] = DeliveryNote.model_validate(json.load(del_file.open("r", encoding="utf-8")))
                except Exception:
                    from agent.ingestion.resilient_parser import repair_json_string, normalize_schema_dict
                    raw_dict, _ = repair_json_string(raw_content)
                    norm_dict, _ = normalize_schema_dict(raw_dict, "delivery")
                    documents["delivery"] = DeliveryNote.model_validate(norm_dict)
            elif del_ext == ".pdf":
                documents["delivery"] = PDFCaseParser.parse_delivery_note(del_file)
            elif del_ext in (".csv", ".xlsx"):
                documents["delivery"] = MultiFormatParser.parse_tabular_document(del_file, "delivery")
            elif del_ext in (".txt", ".eml"):
                documents["delivery"] = MultiFormatParser.parse_text_document(del_file, "delivery")
            elif del_ext in [".png", ".jpg", ".jpeg", ".webp"]:
                from tools.ocr_engine.vision import OCREngine
                ocr = OCREngine()
                documents["delivery"] = ocr.extract_delivery_note(del_file)

            # Verificar si existen remisiones parciales adicionales (Split Shipments: delivery_02.json, etc.)
            extra_deliv_files = sorted(
                [
                    p for p in case_path.glob("*delivery*.json")
                    if p.resolve() != del_file.resolve()
                ]
            )
            if extra_deliv_files and "delivery" in documents:
                partial_notes = [documents["delivery"]]
                for ep in extra_deliv_files:
                    try:
                        partial_notes.append(DeliveryNote.model_validate(json.loads(ep.read_text(encoding="utf-8"))))
                    except Exception:
                        pass
                if len(partial_notes) > 1:
                    documents["delivery"] = consolidate_partial_deliveries(partial_notes)
        except Exception as e:
            raise DocumentReaderError(f"Error al procesar remisión de entrega '{del_file.name}' en '{case_id}': {str(e)}")
    else:
        raise DocumentReaderError(f"Falta el documento requerido de Remisión (delivery) en el expediente '{case_id}'")

    return documents


def load_case_documents_with_health(case_id: str, allow_imputation: bool = True):
    """
    Carga resiliente integral que retorna los 5 documentos comerciales tipados
    junto con la auditoría de salud e integridad documental (DocumentHealthAudit).
    """
    from agent.ingestion.resilient_parser import ResilientDocumentLoader
    return ResilientDocumentLoader.load_case_resilient(case_id, allow_imputation=allow_imputation)


def load_massive_case_hierarchical(case_id: str) -> Dict[str, Any]:
    """
    Cargador pericial jerárquico para expedientes masivos y extensos (Fase 1).
    Detecta automáticamente contratos de más de 50 páginas y facturas de cientos de SKUs,
    generando la jerarquía estructural, el cotejo Map-Reduce y la firma sintética compacta.
    """
    from tools.document_reader.hierarchical_segmenter import HierarchicalDocumentSegmenter
    from tools.reconciliation_engine.batch_map_reduce import MassiveBatchReconciliationEngine
    from tools.document_reader.synthetic_fingerprint import SyntheticFingerprintGenerator

    # 1. Cargar documentos tipados
    docs = load_case_documents(case_id)
    inv: Invoice = docs["invoice"]
    po: PurchaseOrder = docs["purchase_order"]
    deliv: DeliveryNote = docs["delivery"]
    pay: PaymentReceipt = docs["payment"]
    contract = docs.get("contract")

    # 2. Segmentación Jerárquica del Contrato si existe texto
    hierarchy = None
    contract_text = ""
    if contract:
        if hasattr(contract, "clauses") and contract.clauses:
            contract_text = "\n\n".join([f"CLÁUSULA {c.clause_id}: {c.text}" for c in contract.clauses])
        elif hasattr(contract, "raw_content") and contract.raw_content:
            contract_text = contract.raw_content
        elif isinstance(contract, str):
            contract_text = contract

        if contract_text:
            hierarchy = HierarchicalDocumentSegmenter.segment_text(
                raw_text=contract_text,
                document_name=f"contrato_{case_id}",
                total_pages=max(1, len(contract_text.split()) // 350)
            )

    # 3. Conciliación Map-Reduce en Sub-Lotes
    manifest = MassiveBatchReconciliationEngine.map_reduce_reconcile(
        invoice=inv,
        purchase_order=po,
        delivery=deliv,
        payment=pay,
        batch_size=50
    )

    # 4. Generación de la Firma Sintética de Alta Densidad
    fingerprint = SyntheticFingerprintGenerator.generate(
        case_id=case_id,
        invoice=inv,
        payment=pay,
        rec_summary=manifest.summary,
        hierarchy=hierarchy,
        manifest=manifest
    )

    is_massive = len(inv.items) >= 50 or (hierarchy and hierarchy.total_pages >= 20)

    return {
        "documents": docs,
        "hierarchy": hierarchy,
        "manifest": manifest,
        "fingerprint": fingerprint,
        "is_massive_scale": is_massive,
        "summary": manifest.summary
    }
