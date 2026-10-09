import os
import re
from pathlib import Path
from pydantic import BaseModel

try:
    import chromadb
except ImportError:
    chromadb = None

class VectorContract(BaseModel):
    contract_id: str
    is_vectorized: bool = True
    collection_name: str

class ContractRAG:
    """Motor Vectorial RAG para contratos masivos usando ChromaDB."""
    
    def __init__(self, db_path="data/vector_db"):
        self.db_path = Path(db_path)
        self.db_path.mkdir(parents=True, exist_ok=True)
        
        if chromadb is None:
            raise ImportError("Se requiere instalar chromadb: pip install chromadb")
            
        self.client = chromadb.PersistentClient(path=str(self.db_path))

    def ingest_contract_markdown(self, case_id: str, markdown_path: Path) -> VectorContract:
        collection_name = f"contract_{Path(case_id).name}"
        collection = self.client.get_or_create_collection(name=collection_name)
        
        if collection.count() == 0:
            with open(markdown_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Dividir el contrato gigante usando expresiones regulares (por encabezados)
            clauses = re.split(r'\n(?=## CLÁUSULA)', content)
            
            documents = []
            ids = []
            metadatas = []
            
            for idx, clause in enumerate(clauses):
                clause = clause.strip()
                if not clause:
                    continue
                title_line = clause.split('\n')[0].replace('#', '').strip()
                
                documents.append(clause)
                ids.append(f"clause_{idx}")
                metadatas.append({"title": title_line, "case_id": case_id})
                
            if documents:
                collection.add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
            
        return VectorContract(contract_id=case_id, collection_name=collection_name)
        
    def search_clauses(self, collection_name: str, query: str, n_results: int = 2) -> list[str]:
        collection = self.client.get_collection(name=collection_name)
        results = collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        if results['documents'] and len(results['documents']) > 0:
            return results['documents'][0]
        return []
