from typing import List, Any
from nagent_core.tool import BaseTool

class BaseRetriever:
    """
    Base class for retrievers.
    Subclasses should implement the fit and get_top_k methods.
    """

    def __init__(self):
        self.documents = []

    def fit(self, documents: List[str]):
        """Store the documents"""
        self.documents = documents

    def get_top_k(self, query: str, k: int = 3) -> List[tuple]:
        """Retrieve top-k most relevant documents for the query."""
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

    def get_top_k(self, query: str, k: int = 3) -> List[tuple]:
        """Get top k documents by keyword match count"""
        scores = []

        for i, doc in enumerate(self.documents):
            match_count = self._count_keyword_matches(query, doc)
            scores.append((i, match_count))

        # Sort by match count (descending)
        scores.sort(key=lambda x: x[1], reverse=True)

        return scores[:k]

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
        top_k = self.retriever.get_top_k(query)
        # 过滤掉评分为 0 的结果
        relevant_results = [idx for idx, score in top_k if score > 0]

        if not relevant_results:
            return "没有找到相关文档。"

        results = []
        for idx in relevant_results:
            results.append(self.retriever.documents[idx])

        return "\n---\n".join(results)
