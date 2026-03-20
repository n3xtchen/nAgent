import os
import uuid
from typing import List, Any, Dict, Optional
from .vector import BaseVectorRetriever

try:
    import chromadb
    from chromadb.config import Settings
    from chromadb.api.types import EmbeddingFunction, Documents, Embeddings
except ImportError:
    chromadb = None
    EmbeddingFunction = object
    Documents = Any
    Embeddings = Any

class RagasEmbeddingWrapper:
    """
    Wrapper to use Ragas embeddings with ChromaDB.
    """
    def __init__(self, ragas_embeddings: Any):
        self.ragas_embeddings = ragas_embeddings

    def name(self) -> str:
        return "ragas_embedding_wrapper"

    def __call__(self, input: Documents) -> Embeddings:
        return self.embed_documents(input)

    def embed_documents(self, input: Documents) -> Embeddings:
        # GoogleEmbeddings uses embed_texts for list of documents
        if hasattr(self.ragas_embeddings, "embed_texts"):
            return self.ragas_embeddings.embed_texts(input)
        elif hasattr(self.ragas_embeddings, "embed_documents"):
            return self.ragas_embeddings.embed_documents(input)
        else:
            raise AttributeError(f"Embedding object {type(self.ragas_embeddings)} has no embed_texts or embed_documents method")

    def embed_query(self, input: Documents) -> Embeddings:
        # ChromaDB query_texts can pass a list of query strings (even for a single query)
        if hasattr(self.ragas_embeddings, "embed_texts"):
            # Ragas GoogleEmbeddings expects a list of texts for embed_texts
            return self.ragas_embeddings.embed_texts(input)
        elif hasattr(self.ragas_embeddings, "embed_query"):
            # embed_query usually takes a single string, handle list correctly
            return [self.ragas_embeddings.embed_query(q) for q in input]
        else:
            raise AttributeError(f"Embedding object {type(self.ragas_embeddings)} has no embed_text or embed_query method")

class ChromaRetriever(BaseVectorRetriever):
    """
    Retriever implementation using ChromaDB.
    """

    def __init__(
        self,
        collection_name: str = "default_collection",
        persist_directory: str = "./chroma_db",
        embedding_function: Optional[Any] = None
    ):
        super().__init__()
        if chromadb is None:
            raise ImportError("chromadb is not installed. Please install it using `pip install chromadb` or `uv add chromadb`.")

        self.persist_directory = persist_directory
        self.collection_name = collection_name

        # Ensure directory exists
        if not os.path.exists(persist_directory):
            os.makedirs(persist_directory)

        self.client = chromadb.PersistentClient(path=persist_directory)

        # Use custom embedding function if provided
        self.embedding_function = embedding_function
        chroma_ef = None
        if embedding_function:
            chroma_ef = RagasEmbeddingWrapper(embedding_function)

        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=chroma_ef
        )

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

        self.collection.upsert(
            ids=ids,
            documents=texts,
            metadatas=metadatas
        )

    def embed_query(self, query: str) -> List[float]:
        """
        Convert a single query string to a vector embedding using the provided embedding function.
        """
        if self.embedding_function:
            if hasattr(self.embedding_function, "embed_text"):
                return self.embedding_function.embed_text(query)
            elif hasattr(self.embedding_function, "embed_query"):
                return self.embedding_function.embed_query(query)
            else:
                raise AttributeError(f"Embedding object {type(self.embedding_function)} has no embed_text or embed_query method")
        raise ValueError("No embedding function provided to ChromaRetriever. Cannot embed query.")

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Convert a list of document strings to vector embeddings using the provided embedding function.
        """
        if self.embedding_function:
            if hasattr(self.embedding_function, "embed_texts"):
                return self.embedding_function.embed_texts(texts)
            elif hasattr(self.embedding_function, "embed_documents"):
                return self.embedding_function.embed_documents(texts)
            else:
                raise AttributeError(f"Embedding object {type(self.embedding_function)} has no embed_texts or embed_documents method")
        raise ValueError("No embedding function provided to ChromaRetriever. Cannot embed documents.")

    def similarity_search_by_vector(self, embedding: List[float], k: int = 3) -> List[Dict[str, Any]]:
        results = self.collection.query(
            query_embeddings=[embedding],
            n_results=k
        )
        return self._format_results(results)

    def get_top_k(self, query: str, k: int = 3) -> List[Dict[str, Any]]:
        """
        Use Chroma's built-in text querying.
        If an embedding function was provided at init, Chroma will use it automatically.
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

    def clear(self):
        """
        Clear the ChromaDB collection and in-memory documents.
        """
        super().clear()

        # Delete the collection from ChromaDB
        try:
            self.client.delete_collection(name=self.collection_name)
        except ValueError:
            # Collection might not exist, ignore
            pass

        # Recreate an empty collection
        chroma_ef = None
        if self.embedding_function:
            chroma_ef = RagasEmbeddingWrapper(self.embedding_function)

        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=chroma_ef
        )

    def save_index(self, file_path: str):
        """Chroma automatically persists to disk."""
        pass

    def load_index(self, file_path: str):
        """Chroma automatically loads from disk upon initialization."""
        pass
