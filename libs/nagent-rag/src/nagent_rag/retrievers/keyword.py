import json
from typing import List, Any, Dict
from .base import BaseRetriever

class SimpleKeywordRetriever(BaseRetriever):
    """Ultra-simple keyword matching retriever"""

    def __init__(self, tokenizer: str = "split"):
        super().__init__()
        self.tokenizer = tokenizer

    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text according to selected tokenizer"""
        if self.tokenizer == "jieba":
            try:
                import jieba
                return list(jieba.cut(text.lower()))
            except ImportError:
                import warnings
                warnings.warn("jieba not installed, falling back to split tokenizer")
                return text.lower().split()
        return text.lower().split()

    def _count_keyword_matches(self, query: str, document: str) -> int:
        """Count how many query words appear in the document"""
        query_words = self._tokenize(query)
        document_words = self._tokenize(document)
        matches = 0
        for word in query_words:
            if word in document_words:
                matches += 1
        return matches

    def get_top_k(self, query: str, k: int = 3) -> List[Dict[str, Any]]:
        """Get top k documents by keyword match count"""
        scored_docs = []

        for doc in self.documents:
            match_count = self._count_keyword_matches(query, doc.get("content", ""))
            if match_count > 0:
                doc_with_score = doc.copy()
                doc_with_score["_score"] = match_count
                scored_docs.append(doc_with_score)

        scored_docs.sort(key=lambda x: x["_score"], reverse=True)
        return scored_docs[:k]

    def save_index(self, file_path: str):
        """Save documents to a JSON file"""
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self.documents, f, ensure_ascii=False, indent=2)

    def load_index(self, file_path: str):
        """Load documents from a JSON file"""
        with open(file_path, "r", encoding="utf-8") as f:
            self.documents = json.load(f)
