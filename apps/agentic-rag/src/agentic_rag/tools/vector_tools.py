from typing import Any, Dict
from nagent_core.tool import BaseTool
from nagent_rag.retrievers.base import BaseRetriever

class VectorSearchTool(BaseTool):
    """
    基于向量相似度的检索工具。
    """
    def __init__(self, retriever: BaseRetriever, name: str = "vector_search", description: str = "使用向量检索技术（如语义相似度匹配）从文档库中查找与查询最相关的内容"):
        super().__init__(name, description)
        self.retriever = retriever

    def run(self, query: str) -> str:
        top_k_docs = self.retriever.get_top_k(query)

        if not top_k_docs:
            return "没有找到相关的语义匹配结果。"

        formatted_results = []
        for i, doc in enumerate(top_k_docs):
            content = doc.get("content", "")
            doc_id = doc.get("id", f"doc_{i}")
            metadata = doc.get("metadata", {})
            score = doc.get("_score", "N/A")

            result_str = f"【语义结果 {i+1}】(ID: {doc_id}, Score: {score})\n"
            if metadata:
                meta_str = ", ".join([f"{k}: {v}" for k, v in metadata.items()])
                result_str += f"元数据: {meta_str}\n"
            result_str += f"内容: {content}"
            formatted_results.append(result_str)

        return "\n\n---\n\n".join(formatted_results)

class VectorStoreTool(BaseTool):
    """
    向量存储工具，允许 Agent 在运行时将新的内容写入向量库。
    """
    def __init__(self, retriever: BaseRetriever, name: str = "vector_store", description: str = "将新的文档或内容保存到向量数据库中以供后续检索"):
        super().__init__(name, description)
        self.retriever = retriever

    def run(self, content: str, doc_id: str = None) -> str:
        """
        保存内容到向量库。
        """
        doc = {"content": content}
        if doc_id:
            doc["id"] = doc_id
        
        try:
            self.retriever.fit([doc])
            return f"成功将内容保存到向量库 (ID: {doc.get('id', 'N/A')})。"
        except Exception as e:
            return f"保存内容到向量库失败: {str(e)}"
