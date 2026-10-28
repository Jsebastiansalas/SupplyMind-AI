import json
from pathlib import Path
from typing import Dict, Any
from config.settings import settings
from data.models import (
    Invoice,
    PurchaseOrder,
    DeliveryNote,
    PaymentReceipt,
    CommercialContract
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
    else:
        case_path = settings.DATA_DIR / case_id

    if not case_path.exists() or not case_path.is_dir():
        raise DocumentReaderError(f"El expediente del caso '{case_id}' no existe (ruta evaluada: {case_path})")
        
    from tools.document_reader.classifier import DocumentClassifier
    from tools.document_reader.pdf_parser import PDFCaseParser

    mapped = DocumentClassifier.classify_and_map_case_directory(case_path)
    documents = {}
    
    # 1. Factura (Invoice)
    if "invoice" in mapped:
        inv_file = mapped["invoice"]
        try:
            if inv_file.suffix.lower() == ".json":
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
            elif inv_file.suffix.lower() == ".pdf":
                documents["invoice"] = PDFCaseParser.parse_invoice(inv_file)
        except Exception as e:
            raise DocumentReaderError(f"Error al procesar factura '{inv_file.name}' en '{case_id}': {str(e)}")
    else:
        raise DocumentReaderError(f"Falta el documento requerido de Factura (invoice) en el expediente '{case_id}'")

    # 2. Orden de Compra (Purchase Order)
    if "purchase_order" in mapped:
        po_file = mapped["purchase_order"]
        try:
            if po_file.suffix.lower() == ".json":
                with open(po_file, "r", encoding="utf-8", errors="replace") as f:
                    raw_content = f.read()
                try:
                    documents["purchase_order"] = PurchaseOrder.model_validate(json.load(po_file.open("r", encoding="utf-8")))
                except Exception:
                    from agent.ingestion.resilient_parser import repair_json_string, normalize_schema_dict
                    raw_dict, _ = repair_json_string(raw_content)
                    norm_dict, _ = normalize_schema_dict(raw_dict, "purchase_order")
                    documents["purchase_order"] = PurchaseOrder.model_validate(norm_dict)
            elif po_file.suffix.lower() == ".pdf":
                documents["purchase_order"] = PDFCaseParser.parse_purchase_order(po_file)
        except Exception as e:
            raise DocumentReaderError(f"Error al procesar orden de compra '{po_file.name}' en '{case_id}': {str(e)}")
    else:
        raise DocumentReaderError(f"Falta el documento requerido de Orden de Compra (purchase_order) en el expediente '{case_id}'")

    # 3. Comprobante de Pago (Payment Receipt)
    if "payment" in mapped:
        pay_file = mapped["payment"]
        try:
            if pay_file.suffix.lower() == ".json":
                with open(pay_file, "r", encoding="utf-8", errors="replace") as f:
                    raw_content = f.read()
                try:
                    documents["payment"] = PaymentReceipt.model_validate(json.load(pay_file.open("r", encoding="utf-8")))
                except Exception:
                    from agent.ingestion.resilient_parser import repair_json_string, normalize_schema_dict
                    raw_dict, _ = repair_json_string(raw_content)
                    norm_dict, _ = normalize_schema_dict(raw_dict, "payment")
                    documents["payment"] = PaymentReceipt.model_validate(norm_dict)
            elif pay_file.suffix.lower() == ".pdf":
                documents["payment"] = PDFCaseParser.parse_payment_receipt(pay_file)
        except Exception as e:
            raise DocumentReaderError(f"Error al procesar comprobante de pago '{pay_file.name}' en '{case_id}': {str(e)}")
    else:
        raise DocumentReaderError(f"Falta el documento requerido de Comprobante de Pago (payment) en el expediente '{case_id}'")

    # 4. Contrato Comercial (Commercial Contract)
    if "contract" in mapped:
        con_file = mapped["contract"]
        try:
            if con_file.suffix.lower() == ".json":
                with open(con_file, "r", encoding="utf-8", errors="replace") as f:
                    raw_content = f.read()
                try:
                    documents["contract"] = CommercialContract.model_validate(json.load(con_file.open("r", encoding="utf-8")))
                except Exception:
                    from agent.ingestion.resilient_parser import repair_json_string, normalize_schema_dict
                    raw_dict, _ = repair_json_string(raw_content)
                    norm_dict, _ = normalize_schema_dict(raw_dict, "contract")
                    documents["contract"] = CommercialContract.model_validate(norm_dict)
            elif con_file.suffix.lower() == ".pdf":
                documents["contract"] = PDFCaseParser.parse_contract(con_file)
            elif con_file.suffix.lower() == ".md":
                from tools.contract_analyzer.rag import ContractRAG
                rag = ContractRAG()
                documents["contract"] = rag.ingest_contract_markdown(str(case_id), con_file)
        except Exception as e:
            raise DocumentReaderError(f"Error al procesar contrato '{con_file.name}' en '{case_id}': {str(e)}")
    else:
        raise DocumentReaderError(f"Falta el documento requerido de Contrato (contract) en el expediente '{case_id}'")

    # 5. Remisión de Entrega (Delivery Note)
    if "delivery" in mapped:
        del_file = mapped["delivery"]
        try:
            if del_file.suffix.lower() == ".json":
                with open(del_file, "r", encoding="utf-8", errors="replace") as f:
                    raw_content = f.read()
                try:
                    documents["delivery"] = DeliveryNote.model_validate(json.load(del_file.open("r", encoding="utf-8")))
                except Exception:
                    from agent.ingestion.resilient_parser import repair_json_string, normalize_schema_dict
                    raw_dict, _ = repair_json_string(raw_content)
                    norm_dict, _ = normalize_schema_dict(raw_dict, "delivery")
                    documents["delivery"] = DeliveryNote.model_validate(norm_dict)
            elif del_file.suffix.lower() == ".pdf":
                documents["delivery"] = PDFCaseParser.parse_delivery_note(del_file)
            elif del_file.suffix.lower() in [".png", ".jpg", ".jpeg", ".webp"]:
                from tools.ocr_engine.vision import OCREngine
                ocr = OCREngine()
                documents["delivery"] = ocr.extract_delivery_note(del_file)
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
