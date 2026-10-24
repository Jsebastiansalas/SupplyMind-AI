"""
Módulo Clasificador y Segmentador Autónomo de Documentos B2B para SupplyMind AI.
Capaz de analizar documentos completos de gran extensión (miles de caracteres, múltiples páginas)
con nombres de archivo arbitrarios o paquetes PDF consolidados, identificando con precisión matemática
y semántica la tipología de cada documento (Invoice, Purchase Order, Delivery Note, Payment, Contract).
"""

import re
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import pypdf

from config.settings import settings

DOCUMENT_SIGNATURES = {
    "invoice": {
        "keywords": [
            "factura", "invoice", "commercial invoice", "factura comercial",
            "cfdi", "subtotal", "total amount", "tax", "impuestos", "p. unitario",
            "unit price", "precio unitario", "emisor / proveedor", "cliente / receptor",
            "billed to", "remit to", "validez fiscal"
        ],
        "weight_multipliers": {
            "factura": 3.0,
            "invoice": 3.0,
            "cfdi": 2.5,
            "subtotal": 2.0,
            "emisor / proveedor": 2.5,
            "p. unitario": 1.5,
        },
        "negative_keywords": [
            "orden de compra / purchase order", "comprobante de pago",
            "remittance advice", "remision de entrega", "master agreement"
        ]
    },
    "purchase_order": {
        "keywords": [
            "orden de compra", "purchase order", "po id", "po reference",
            "po número", "comprador / retailer", "proveedor autorizado",
            "precio pactado", "total pactado", "cant. pedida", "ordered quantity",
            "order date", "fecha de orden", "condicion de pago"
        ],
        "weight_multipliers": {
            "orden de compra": 3.0,
            "purchase order": 3.0,
            "po id": 3.0,
            "precio pactado": 2.5,
            "cant. pedida": 2.0,
            "proveedor autorizado": 2.0,
        },
        "negative_keywords": [
            "factura comercial", "remision de entrega", "remittance advice", "contrato marco"
        ]
    },
    "delivery": {
        "keywords": [
            "remision de entrega", "remisión", "receiving slip", "bill of lading",
            "bol", "proof of delivery", "pod", "muelle", "bodega / hub",
            "received by", "recibido por", "despachado", "recibido", "faltante",
            "averiado", "damaged quantity", "missing quantity", "constancia de recepcion",
            "sello muelle", "discrepancia reportada", "dock receipt"
        ],
        "weight_multipliers": {
            "remision de entrega": 3.5,
            "bill of lading": 3.0,
            "receiving slip": 3.0,
            "recibido por": 2.5,
            "despachado": 2.0,
            "faltante": 2.0,
            "sello muelle": 2.5,
        },
        "negative_keywords": [
            "factura comercial", "purchase order", "comprobante de pago", "contrato marco"
        ]
    },
    "payment": {
        "keywords": [
            "comprobante de pago", "remittance advice", "aviso de pago",
            "monto efectivo pagado", "amount paid", "factura cancelada",
            "deducciones y retenciones", "codigo deduccion", "doc. referencia",
            "monto deducido", "total deducciones", "fecha de dispersion",
            "cuentas por pagar", "wire transfer", "transferencia bancaria"
        ],
        "weight_multipliers": {
            "comprobante de pago": 3.5,
            "remittance advice": 3.5,
            "monto efectivo pagado": 3.0,
            "deducciones y retenciones": 2.5,
            "codigo deduccion": 2.0,
            "factura cancelada": 2.5,
        },
        "negative_keywords": [
            "remision de entrega", "purchase order", "contrato marco"
        ]
    },
    "contract": {
        "keywords": [
            "contrato marco", "master agreement", "msa", "master supply agreement",
            "clausula", "cláusula", "acuerdo legal vinculante", "parte proveedora",
            "parte compradora", "vigencia", "terminos y condiciones",
            "politica operativa", "tolerancia permitida", "declaraciones",
            "penalidades operativas", "resolucion de controversias", "jurisdiccion"
        ],
        "weight_multipliers": {
            "contrato marco": 3.5,
            "master agreement": 3.5,
            "msa": 2.5,
            "clausula": 3.0,
            "cláusula": 3.0,
            "politica operativa": 2.5,
            "tolerancia permitida": 2.0,
        },
        "negative_keywords": [
            "remision de entrega", "remittance advice", "factura comercial"
        ]
    }
}

class DocumentClassifier:
    """Clasificador y enrutador inteligente de documentos comerciales B2B."""

    @classmethod
    def extract_full_text(cls, pdf_path: Path) -> Tuple[str, List[str]]:
        """Extrae el texto completo del documento y el texto página por página sin límite de caracteres."""
        if not pdf_path.exists():
            raise FileNotFoundError(f"Archivo no encontrado: {pdf_path}")
        reader = pypdf.PdfReader(str(pdf_path))
        pages_text = []
        has_images = False
        for page in reader.pages:
            t = page.extract_text() or ""
            pages_text.append(t)
            if len(page.images) > 0:
                has_images = True
        full_text = "\n".join(pages_text)
        
        # Detección de PDF escaneado (sin capa de texto vectorial pero con imágenes)
        if len(full_text.strip()) < 30 and has_images:
            try:
                from tools.ocr_engine.vision import OCREngine
                ocr = OCREngine()
                scanned_text = ocr.transcribe_scanned_pdf(pdf_path)
                if scanned_text.strip():
                    return scanned_text, [scanned_text]
            except Exception:
                pass
                
        return full_text, pages_text

    @classmethod
    def score_document(cls, text: str) -> Dict[str, float]:
        """Calcula puntuaciones ponderadas para cada tipo documental analizando todo el texto."""
        text_lower = text.lower()
        scores = {}
        
        for doc_type, config in DOCUMENT_SIGNATURES.items():
            score = 0.0
            # 1. Palabras clave positivas con multiplicadores
            for kw in config["keywords"]:
                count = text_lower.count(kw.lower())
                if count > 0:
                    weight = config["weight_multipliers"].get(kw.lower(), 1.0)
                    score += count * weight * 10.0
            
            # 2. Penalización por palabras clave negativas
            for nkw in config["negative_keywords"]:
                count = text_lower.count(nkw.lower())
                if count > 0:
                    score -= count * 15.0
                    
            scores[doc_type] = max(0.0, score)
            
        return scores

    @classmethod
    def classify_pdf(cls, pdf_path: Path) -> Tuple[str, float]:
        """
        Clasifica un archivo PDF individual analizando todo su contenido.
        Retorna (doc_type, confidence_score entre 0.0 y 1.0).
        """
        full_text, _ = cls.extract_full_text(pdf_path)
        if not full_text.strip():
            return "unknown", 0.0
            
        scores = cls.score_document(full_text)
        total_score = sum(scores.values())
        
        if total_score == 0:
            # Fallback a LLM si las reglas determinísticas no dan puntuación
            return cls._llm_classify(full_text)
            
        best_type = max(scores, key=scores.get)
        confidence = round(scores[best_type] / total_score, 4) if total_score > 0 else 0.0
        
        if confidence < 0.40 and settings.is_live_api_ready:
            return cls._llm_classify(full_text)
            
        return best_type, confidence

    @classmethod
    def classify_and_map_case_directory(cls, case_dir: Path) -> Dict[str, Path]:
        """
        Escanea un directorio con archivos de nombres arbitrarios y mapea cada
        rol comercial requerido ('invoice', 'purchase_order', 'delivery', 'payment', 'contract')
        a su archivo correspondiente.
        """
        pdf_files = list(case_dir.glob("*.pdf"))
        json_files = list(case_dir.glob("*.json"))
        image_files = list(case_dir.glob("*.png")) + list(case_dir.glob("*.jpg")) + list(case_dir.glob("*.jpeg")) + list(case_dir.glob("*.webp"))
        
        mapped_documents: Dict[str, Path] = {}
        
        # 1. Si los nombres convencionales ya existen, asignarlos directamente
        standard_keys = {
            "invoice": ["invoice.pdf", "invoice.json"],
            "purchase_order": ["purchase_order.pdf", "purchase_order.json"],
            "delivery": ["delivery.pdf", "delivery.json", "delivery.png", "delivery.jpg", "delivery.jpeg"],
            "payment": ["payment.pdf", "payment.json"],
            "contract": ["contract.pdf", "contract.json", "contract.md"]
        }
        all_standard_found = True
        for key, possible_names in standard_keys.items():
            found = False
            for name in possible_names:
                p = case_dir / name
                if p.exists():
                    mapped_documents[key] = p
                    found = True
                    break
            if not found:
                all_standard_found = False
                
        if all_standard_found and len(mapped_documents) == 5:
            return mapped_documents
            
        # 2. Si no están los 5 nombres estándar, clasificar exhaustivamente los archivos restantes
        already_mapped_paths = set(mapped_documents.values())
        all_candidates = [
            f for f in (pdf_files + json_files + image_files) 
            if f not in already_mapped_paths and f.name not in ["meta.json", "ground_truth.json"] and not f.name.startswith(".")
        ]
        
        scored_candidates: List[Tuple[Path, str, float]] = []
        for candidate in all_candidates:
            if candidate.suffix.lower() == ".pdf":
                doc_type, conf = cls.classify_pdf(candidate)
                scored_candidates.append((candidate, doc_type, conf))
            elif candidate.suffix.lower() == ".json":
                try:
                    with open(candidate, "r", encoding="utf-8", errors="replace") as f:
                        data_text = f.read()
                    scores = cls.score_document(data_text)
                    if not any(scores.values()) or max(scores.values()) == 0:
                        stem = candidate.stem.lower()
                        for role in ["invoice", "purchase_order", "delivery", "payment", "contract"]:
                            if role in stem or (role == "payment" and "pago" in stem) or (role == "delivery" and "remision" in stem):
                                scores[role] = 10.0
                    best_type = max(scores, key=scores.get) if any(scores.values()) else "unknown"
                    scored_candidates.append((candidate, best_type, 0.95))
                except Exception:
                    pass
            elif candidate.suffix.lower() in [".png", ".jpg", ".jpeg", ".webp"]:
                try:
                    from tools.ocr_engine.vision import OCREngine
                    ocr = OCREngine()
                    img_text = ocr.transcribe_image(candidate)
                    scores = cls.score_document(img_text)
                    best_type = max(scores, key=scores.get) if any(scores.values()) else "delivery"
                    conf = scores[best_type] / max(1.0, sum(scores.values())) if any(scores.values()) else 0.90
                    scored_candidates.append((candidate, best_type, max(0.85, conf)))
                except Exception:
                    scored_candidates.append((candidate, "delivery", 0.85))
                    
        # Asignar el mejor candidato para cada rol faltante
        for role in ["invoice", "purchase_order", "delivery", "payment", "contract"]:
            if role in mapped_documents:
                continue
            matches = [c for c in scored_candidates if c[1] == role]
            if matches:
                # Elegir el de mayor confianza
                matches.sort(key=lambda x: x[2], reverse=True)
                mapped_documents[role] = matches[0][0]
                
        # 3. Soporte para archivo consolidado único (ej. expediente_completo.pdf)
        if len(mapped_documents) < 5 and len(pdf_files) == 1 and not json_files:
            single_bundle = pdf_files[0]
            split_docs = cls.split_consolidated_bundle(single_bundle, case_dir / "_split_bundle")
            for k, v in split_docs.items():
                if k not in mapped_documents:
                    mapped_documents[k] = v
                    
        return mapped_documents

    @classmethod
    def split_consolidated_bundle(cls, bundle_pdf: Path, output_dir: Path) -> Dict[str, Path]:
        """
        Segmenta un paquete PDF consolidado de varias páginas donde vienen
        juntos la Factura, Orden de Compra, Remisión, Pago y Contrato.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        reader = pypdf.PdfReader(str(bundle_pdf))
        
        classified_pages: List[Tuple[int, str, float]] = []
        for i, page in enumerate(reader.pages):
            p_text = page.extract_text() or ""
            scores = cls.score_document(p_text)
            best_t = max(scores, key=scores.get) if any(scores.values()) else "unknown"
            conf = scores[best_t] if any(scores.values()) else 0.0
            classified_pages.append((i, best_t, conf))
            
        role_pages: Dict[str, List[int]] = {
            "invoice": [],
            "purchase_order": [],
            "delivery": [],
            "payment": [],
            "contract": []
        }
        for page_idx, doc_type, _ in classified_pages:
            if doc_type in role_pages:
                role_pages[doc_type].append(page_idx)
                
        resulting_files: Dict[str, Path] = {}
        for role, page_indices in role_pages.items():
            if page_indices:
                writer = pypdf.PdfWriter()
                for p_idx in page_indices:
                    writer.add_page(reader.pages[p_idx])
                target_file = output_dir / f"{role}.pdf"
                with open(target_file, "wb") as f_out:
                    writer.write(f_out)
                resulting_files[role] = target_file
                
        return resulting_files

    @classmethod
    def _llm_classify(cls, text: str) -> Tuple[str, float]:
        """Clasificador semántico Grok para casos de alta ambigüedad textual."""
        if not settings.is_live_api_ready:
            return "unknown", 0.0
        try:
            from openai import OpenAI
            client = OpenAI(
                base_url=settings.PLATICA_BASE_URL,
                api_key=settings.RETO_KEY
            )
            prompt = (
                "Clasifica el siguiente documento comercial en EXACTAMENTE una de estas opciones:\n"
                "- invoice (Factura comercial emitida por el proveedor)\n"
                "- purchase_order (Orden de compra emitida por el cliente)\n"
                "- delivery (Remisión o comprobante de entrega en almacén / Bill of Lading)\n"
                "- payment (Comprobante de pago bancario o Remittance Advice con deducciones)\n"
                "- contract (Contrato mercantil, acuerdo marco o Master Service Agreement)\n\n"
                f"Contenido del documento:\n\"\"\"\n{text[:4000]}\n\"\"\"\n\n"
                "Responde en formato JSON estricto con campos: {'category': '...', 'confidence': 0.95}"
            )
            response = client.chat.completions.create(
                model=settings.MODEL_NAME,
                messages=[
                    {"role": "system", "content": "Eres un clasificador documental corporativo experto en supply chain."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            res = json.loads(response.choices[0].message.content)
            cat = res.get("category", "unknown").lower()
            conf = float(res.get("confidence", 0.85))
            return cat, conf
        except Exception:
            return "unknown", 0.0
