import json
from typing import List, Any, Dict, Optional
from nagent_core.tool import BaseTool

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
                # Create a copy to avoid modifying original and include score
                doc_with_score = doc.copy()
                doc_with_score["_score"] = match_count
                scored_docs.append(doc_with_score)

        # Sort by score (descending)
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

class RetrieverTool(BaseTool):
    """
    包装 Retriever 的工具，供 Agent 调用。
    """
    def __init__(self, retriever: BaseRetriever, name: str = "retrieve", description: str = "从文档库中检索相关信息"):
        super().__init__(name, description)
        self.retriever = retriever

    def run(self, query: str) -> str:
        """
        根据查询语句检索相关文档。
        """
        top_k_docs = self.retriever.get_top_k(query)

        if not top_k_docs:
            return "没有找到相关文档。"

        formatted_results = []
        for i, doc in enumerate(top_k_docs):
            content = doc.get("content", "")
            doc_id = doc.get("id", f"doc_{i}")
            metadata = doc.get("metadata", {})

            result_str = f"【结果 {i+1}】(ID: {doc_id})\n"
            if metadata:
                meta_str = ", ".join([f"{k}: {v}" for k, v in metadata.items()])
                result_str += f"元数据: {meta_str}\n"
            result_str += f"内容: {content}"
            formatted_results.append(result_str)

        return "\n\n---\n\n".join(formatted_results)
