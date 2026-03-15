import os
import uuid
from typing import List, Any, Dict
from .vector import BaseVectorRetriever

try:
    import chromadb
    from chromadb.config import Settings
except ImportError:
    chromadb = None

class ChromaRetriever(BaseVectorRetriever):
    """
    Retriever implementation using ChromaDB.
    """

    def __init__(self, collection_name: str = "default_collection", persist_directory: str = "./chroma_db"):
        super().__init__()
        if chromadb is None:
            raise ImportError("chromadb is not installed. Please install it using `pip install chromadb` or `uv add chromadb`.")
            
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        
        # Ensure directory exists
        if not os.path.exists(persist_directory):
            os.makedirs(persist_directory)
            
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collection = self.client.get_or_create_collection(name=collection_name)

    def fit(self, documents: List[Any]):
        """
        Store the documents into Chroma.
        """
        super().fit(documents)
        
        if not self.documents:
            return
            
        ids = []
        texts = []
        metadatas = []
        
        for idx, doc in enumerate(self.documents):
            doc_id = doc.get("id", str(uuid.uuid4()))
            doc["id"] = doc_id  # Update original doc with generated ID
            
            ids.append(doc_id)
            texts.append(doc.get("content", ""))
            
            # Extract metadata and convert nested dicts or non-primitive types if needed
            meta = doc.get("metadata", {})
            # Chroma requires metadata values to be str, int, float or bool
            safe_meta = {}
            for k, v in meta.items():
                if isinstance(v, (str, int, float, bool)):
                    safe_meta[k] = v
                else:
                    safe_meta[k] = str(v)
            metadatas.append(safe_meta if safe_meta else None)

        self.collection.add(
            ids=ids,
            documents=texts,
            metadatas=metadatas
        )

    def embed_query(self, query: str) -> List[float]:
        """
        Chroma implicitly handles embedding via its default embedding function unless overridden.
        Normally, we don't need to manually expose it if we just use collection.query().
        But to adhere to the base class, we can mock or use the internal embedding function.
        For simplicity, we let get_top_k use Chroma's native string query.
        """
        # Note: If a custom embedding function is used, we would call it here.
        # But Chroma handles it in collection.query directly.
        pass

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        pass

    def similarity_search_by_vector(self, embedding: List[float], k: int = 3) -> List[Dict[str, Any]]:
        results = self.collection.query(
            query_embeddings=[embedding],
            n_results=k
        )
        return self._format_results(results)
        
    def get_top_k(self, query: str, k: int = 3) -> List[Dict[str, Any]]:
        """
        Override get_top_k to use Chroma's built-in text querying,
        which handles embedding internally.
        """
        results = self.collection.query(
            query_texts=[query],
            n_results=k
        )
        return self._format_results(results)
        
    def _format_results(self, results: Dict) -> List[Dict[str, Any]]:
        """Format Chroma query results into standard dict format."""
        formatted_docs = []
        
        if not results.get("documents") or not results["documents"][0]:
            return formatted_docs
            
        # Chroma returns lists of lists (for batched queries)
        # We assume single query
        docs = results["documents"][0]
        ids = results["ids"][0]
        metadatas = results["metadatas"][0] if results.get("metadatas") else [None] * len(docs)
        distances = results["distances"][0] if results.get("distances") else [None] * len(docs)
        
        for doc, id_, meta, dist in zip(docs, ids, metadatas, distances):
            formatted_doc = {
                "id": id_,
                "content": doc,
                "_score": dist  # In Chroma, distance is returned (lower is better for L2)
            }
            if meta:
                formatted_doc["metadata"] = meta
            formatted_docs.append(formatted_doc)
            
        return formatted_docs

    def save_index(self, file_path: str):
        """Chroma automatically persists to disk."""
        pass

    def load_index(self, file_path: str):
        """Chroma automatically loads from disk upon initialization."""
        pass
