from typing import List, Any, Dict
from .base import BaseRetriever

class BaseVectorRetriever(BaseRetriever):
    """
    Base class for vector-based retrievers.
    It introduces embedding capabilities and vector similarity search.
    """

    def __init__(self):
        super().__init__()

    def embed_query(self, query: str) -> List[float]:
        """Convert a single query string to a vector embedding."""
        raise NotImplementedError("Subclasses should implement this method.")

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Convert a list of document strings to vector embeddings."""
        raise NotImplementedError("Subclasses should implement this method.")

    def similarity_search_by_vector(self, embedding: List[float], k: int = 3) -> List[Dict[str, Any]]:
        """Search documents by providing a raw vector embedding."""
        raise NotImplementedError("Subclasses should implement this method.")

    def get_top_k(self, query: str, k: int = 3) -> List[Dict[str, Any]]:
        """
        Default implementation for vector retrievers:
        1. Embed the query.
        2. Perform similarity search by vector.
        """
        query_embedding = self.embed_query(query)
        return self.similarity_search_by_vector(query_embedding, k=k)
