import os
import re
from pathlib import Path
from decimal import Decimal
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

try:
    import chromadb
except ImportError:
    chromadb = None

from data.models import CommercialContract, ContractClause

class VectorContract(BaseModel):
    contract_id: str
    is_vectorized: bool = True
    collection_name: str
    clauses_count: int = 0

class ScoredClause(BaseModel):
    clause_id: str
    title: str
    text: str
    policy: Optional[str] = None
    tolerance_percentage: Decimal = Decimal("0.00")
    relevance_score: float = 0.0
    match_source: str = "vector"

class ContractRAG:
    """
    Motor Vectorial RAG para contratos comerciales masivos y extensos usando ChromaDB.
    Indexa contratos Markdown, PDFs o modelos CommercialContract para recuperación semántica.
    """
    
    def __init__(self, db_path="data/vector_db"):
        self.db_path = Path(db_path)
        self.db_path.mkdir(parents=True, exist_ok=True)
        
        if chromadb is None:
            raise ImportError("Se requiere instalar chromadb: pip install chromadb")
            
        self.client = chromadb.PersistentClient(path=str(self.db_path))

    def ingest_contract_markdown(self, case_id: str, markdown_path: Path) -> VectorContract:
        """
        Ingesta e indexa un contrato en Markdown (incluyendo contratos de 50+ cláusulas).
        Detecta encabezados de cláusulas de forma agnóstica a numeración y formato.
        """
        collection_name = f"contract_{Path(case_id).name}"
        collection = self.client.get_or_create_collection(name=collection_name)
        
        # Si la colección ya tiene documentos indexados adecuadamente (>1), retornar
        if collection.count() > 1:
            return VectorContract(
                contract_id=case_id,
                collection_name=collection_name,
                clauses_count=collection.count()
            )
        elif collection.count() == 1:
            try:
                self.client.delete_collection(name=collection_name)
                collection = self.client.get_or_create_collection(name=collection_name)
            except Exception:
                pass
            
        try:
            with open(markdown_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except Exception:
            with open(markdown_path, "r", encoding="latin-1", errors="replace") as f:
                content = f.read()
        
        # Normalizar si el archivo tiene saltos de línea escapados como literal '\n'
        if "\\n" in content and (content.count("\\n") > content.count("\n") or "\n" not in content[:500]):
            content = content.replace("\\n", "\n")
            
        # Dividir el contrato usando expresiones regulares por encabezados
        pattern = r'\n(?=##\s*(?:CLÁUSULA|CLAUSULA|CLAUSE|SECCIÓN|SECCION|SECTION|ARTÍCULO|ARTICULO))'
        clauses = re.split(pattern, content, flags=re.IGNORECASE)
        if len(clauses) <= 1:
            clauses = re.split(r'\n(?=##\s+)', content)
            
        documents = []
        ids = []
        metadatas = []
        
        for idx, clause in enumerate(clauses):
            clause = clause.strip()
            if not clause:
                continue
                
            first_line = clause.split('\n')[0].replace('#', '').strip()
            
            # Extraer clause_id y título
            # Ejemplo: "CLÁUSULA 37: Política de Averías y Tolerancia Logística"
            header_parts = first_line.split(':', 1)
            raw_id = header_parts[0].strip()
            raw_title = header_parts[1].strip() if len(header_parts) > 1 else first_line
            
            c_id = raw_id if raw_id else f"CLAUSE-{idx}"
            c_title = raw_title if raw_title else f"Cláusula {c_id}"
            
            documents.append(clause)
            ids.append(f"clause_{idx}")
            metadatas.append({
                "clause_id": c_id,
                "title": c_title,
                "case_id": case_id,
                "idx": idx
            })
            
        if documents:
            collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
        return VectorContract(
            contract_id=case_id,
            collection_name=collection_name,
            clauses_count=len(documents)
        )

    def ingest_commercial_contract(self, case_id: str, contract: CommercialContract) -> VectorContract:
        """Indexa un modelo CommercialContract directamente en ChromaDB."""
        collection_name = f"contract_{Path(case_id).name}"
        collection = self.client.get_or_create_collection(name=collection_name)
        
        if collection.count() == 0 and contract.clauses:
            documents = []
            ids = []
            metadatas = []
            
            for idx, c in enumerate(contract.clauses):
                full_text = f"## {c.clause_id}: {c.title}\n{c.text}\nPolitica: {c.policy}\nTolerancia: {c.tolerance_percentage}%"
                documents.append(full_text)
                ids.append(f"clause_{idx}_{c.clause_id}")
                metadatas.append({
                    "clause_id": c.clause_id,
                    "title": c.title,
                    "policy": c.policy,
                    "case_id": case_id,
                    "idx": idx
                })
                
            collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
        return VectorContract(
            contract_id=case_id,
            collection_name=collection_name,
            clauses_count=len(contract.clauses)
        )
        
    def search_clauses(self, collection_name: str, query: str, n_results: int = 2) -> list[str]:
        """Búsqueda vectorial tradicional de cláusulas (compatibilidad hacia atrás)."""
        collection = self.client.get_collection(name=collection_name)
        results = collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        if results['documents'] and len(results['documents']) > 0:
            return results['documents'][0]
        return []

    def search_clauses_rich(self, collection_name: str, query: str, n_results: int = 3) -> List[Dict[str, Any]]:
        """
        Búsqueda vectorial semántica con metadatos estructurados (clause_id, title, distance).
        """
        collection = self.client.get_collection(name=collection_name)
        results = collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        detailed: List[Dict[str, Any]] = []
        if results and results.get('documents') and len(results['documents']) > 0:
            docs = results['documents'][0]
            metas = results.get('metadatas', [[]])[0] if results.get('metadatas') else [{}] * len(docs)
            dists = results.get('distances', [[]])[0] if results.get('distances') else [0.0] * len(docs)
            
            for doc, meta, dist in zip(docs, metas, dists):
                meta_dict = meta if isinstance(meta, dict) else {}
                detailed.append({
                    "clause_id": meta_dict.get("clause_id", "RAG-MATCH"),
                    "title": meta_dict.get("title", "Cláusula Contractual"),
                    "text": doc,
                    "policy": meta_dict.get("policy", "GENERAL"),
                    "distance": dist,
                    "case_id": meta_dict.get("case_id", "")
                })
        return detailed
