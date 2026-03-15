from typing import Any, Dict
from nagent_core.tool import BaseTool
from .retrievers.base import BaseRetriever

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
