import os
from typing import List, Optional, Dict, Any
from nagent_core.agent import ReActAgent
from nagent_core.tool import CalculatorTool, PythonInterpreterTool, WebSearchTool
from nagent_rag.retriever import BaseRetriever, RetrieverTool
from nagent_rag.query_utils import QueryRewriter, QueryDecomposer

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
        use_query_rewrite: bool = False,
        use_query_decompose: bool = False,
    ):
        self.client = client
        self.retriever = retriever
        self.index_path = index_path
        self.model_name = model_name

        self.use_query_rewrite = use_query_rewrite
        self.use_query_decompose = use_query_decompose

        # 初始化查询优化组件
        self.rewriter = QueryRewriter(client, model_name=model_name)
        self.decomposer = QueryDecomposer(client, model_name=model_name)

        # 如果提供了索引路径且文件存在，则加载
        if self.index_path and os.path.exists(self.index_path):
            self.retriever.load_index(self.index_path)

        self.retriever_tool = RetrieverTool(retriever)
        self.calculator_tool = CalculatorTool()
        self.python_tool = PythonInterpreterTool()
        self.search_tool = WebSearchTool()

        self.agent = ReActAgent(
            client=client,
            tools=[
                self.retriever_tool,
                self.calculator_tool,
                self.python_tool,
                self.search_tool
            ],
            model_name=model_name,
            max_iterations=max_iterations,
        )

    def query(self, user_input: str):
        """
        处理用户查询。
        """
        processed_input = user_input

        # 可选：查询改写
        if self.use_query_rewrite:
            processed_input = self.rewriter.rewrite(user_input)

        # 可选：查询拆分 (目前简单处理，如果是拆分，可以考虑并行或顺序处理，
        # 但 ReActAgent 本身就有多步推理能力，所以这里更多是作为辅助信息提供)
        if self.use_query_decompose:
            sub_queries = self.decomposer.decompose(user_input)
            if len(sub_queries) > 1:
                processed_input = f"原始问题: {user_input}\n请参考以下分解后的子问题进行思考和解决：\n" + "\n".join([f"- {q}" for q in sub_queries])

        return self.agent.query(processed_input)

    def save_index(self, path: Optional[str] = None):
        """
        保存索引。
        """
        target_path = path or self.index_path
        if not target_path:
            raise ValueError("未指定保存路径。")
        self.retriever.save_index(target_path)

    def clear_index(self):
        """
        清空现有索引和文档。
        """
        self.retriever.documents = []
        if self.index_path and os.path.exists(self.index_path):
            os.remove(self.index_path)

    def add_documents(self, documents: List[Dict[str, Any]]):
        """
        添加新文档。
        """
        # 合并现有文档
        existing_docs = self.retriever.documents
        existing_docs.extend(documents)
        self.retriever.fit(existing_docs)
