import os
from typing import List, Optional, Dict, Any
from nagent_core.agent import ReActAgent
from nagent_core.tool import CalculatorTool
from nagent_rag.retriever import BaseRetriever, RetrieverTool

class AgenticRAG:
    """
    Agentic RAG 系统。
    使用 ReActAgent 决定何时进行检索。
    """
    def __init__(
        self,
        client,
        retriever: BaseRetriever,
        model_name: str = "gemini-2.0-flash",
        max_iterations: int = 5,
        index_path: Optional[str] = None,
    ):
        self.retriever = retriever
        self.index_path = index_path

        # 如果提供了索引路径且文件存在，则加载
        if self.index_path and os.path.exists(self.index_path):
            self.retriever.load_index(self.index_path)

        self.retriever_tool = RetrieverTool(retriever)
        self.calculator_tool = CalculatorTool()

        self.agent = ReActAgent(
            client=client,
            tools=[self.retriever_tool, self.calculator_tool],
            model_name=model_name,
            max_iterations=max_iterations,
        )

    def query(self, user_input: str):
        """
        处理用户查询。
        """
        return self.agent.query(user_input)

    def save_index(self, path: Optional[str] = None):
        """
        保存索引。
        """
        target_path = path or self.index_path
        if not target_path:
            raise ValueError("未指定保存路径。")
        self.retriever.save_index(target_path)

    def add_documents(self, documents: List[Dict[str, Any]]):
        """
        添加新文档并重新训练（对于 SimpleKeywordRetriever 来说就是更新列表）。
        """
        # 合并现有文档
        existing_docs = self.retriever.documents
        existing_docs.extend(documents)
        self.retriever.fit(existing_docs)
