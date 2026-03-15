from typing import List, Any, Dict

class BaseRetriever:
    """
    Base class for retrievers.
    Subclasses should implement the fit, get_top_k, save_index and load_index methods.
    """

    def __init__(self):
        self.documents: List[Dict[str, Any]] = []

    def fit(self, documents: List[Any]):
        """
        Store the documents.
        Each document should be a dict with at least 'content' key,
        or a simple string (which will be converted to a dict).
        Optional keys: 'id', 'metadata'.
        """
        normalized_docs = []
        for doc in documents:
            if isinstance(doc, str):
                normalized_docs.append({"content": doc})
            elif isinstance(doc, dict):
                normalized_docs.append(doc)
            else:
                # Fallback for other types
                normalized_docs.append({"content": str(doc)})
        self.documents = normalized_docs

    def get_top_k(self, query: str, k: int = 3) -> List[Dict[str, Any]]:
        """Retrieve top-k most relevant documents for the query."""
        raise NotImplementedError("Subclasses should implement this method.")

    def save_index(self, file_path: str):
        """Save the index and documents to a file."""
        raise NotImplementedError("Subclasses should implement this method.")

    def load_index(self, file_path: str):
        """Load the index and documents from a file."""
        raise NotImplementedError("Subclasses should implement this method.")
