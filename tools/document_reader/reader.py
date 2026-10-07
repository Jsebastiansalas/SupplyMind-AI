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
    case_path = settings.DATA_DIR / case_id
    if not case_path.exists() or not case_path.is_dir():
        raise DocumentReaderError(f"El expediente del caso '{case_id}' no existe en {settings.DATA_DIR}")
        
    required_files = {
        "invoice": ("invoice.json", Invoice),
        "purchase_order": ("purchase_order.json", PurchaseOrder),
        "delivery": ("delivery.json", DeliveryNote),
        "payment": ("payment.json", PaymentReceipt),
        "contract": ("contract.json", CommercialContract),
    }
    
    documents = {}
    for doc_key, (file_name, model_cls) in required_files.items():
        file_path = case_path / file_name
        if not file_path.exists():
            raise DocumentReaderError(f"Falta el documento requerido '{file_name}' en el expediente '{case_id}'")
            
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            documents[doc_key] = model_cls.model_validate(data)
        except Exception as e:
            raise DocumentReaderError(f"Error al validar '{file_name}' en '{case_id}': {str(e)}")
            
    return documents
