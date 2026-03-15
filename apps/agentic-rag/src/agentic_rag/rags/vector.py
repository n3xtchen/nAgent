from typing import Optional, Dict, Any
from nagent_core.agent import ReActAgent
from nagent_core.tool import CalculatorTool, PythonInterpreterTool, WebSearchTool
from nagent_rag.retrievers.base import BaseRetriever
from nagent_rag.query_utils import QueryRewriter, QueryDecomposer
from ..tools.vector_tools import VectorSearchTool, VectorStoreTool
from .base import BaseRAG

class VectorRAG(BaseRAG):
    """
    基于向量检索的 Agentic RAG 系统。
    使用 VectorSearchTool 进行语义检索，使用 VectorStoreTool 进行动态写入。
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
        trace_dir: Optional[str] = None,
    ):
        super().__init__(
            client=client,
            retriever=retriever,
            model_name=model_name,
            trace_dir=trace_dir,
            index_path=index_path,
        )

        self.use_query_rewrite = use_query_rewrite
        self.use_query_decompose = use_query_decompose

        # 初始化查询优化组件
        self.rewriter = QueryRewriter(client, model_name=model_name)
        self.decomposer = QueryDecomposer(client, model_name=model_name)

        # 使用向量检索和存储工具
        self.vector_tool = VectorSearchTool(retriever)
        self.vector_store_tool = VectorStoreTool(retriever)
        self.calculator_tool = CalculatorTool()
        self.python_tool = PythonInterpreterTool()
        self.search_tool = WebSearchTool()

        self.agent = ReActAgent(
            client=client,
            tools=[
                self.vector_tool,
                self.vector_store_tool,
                self.calculator_tool,
                self.python_tool,
                self.search_tool
            ],
            model_name=model_name,
            max_iterations=max_iterations,
        )

    def query(self, user_input: str) -> Dict[str, Any]:
        """
        处理用户查询。
        """
        processed_input = user_input

        if self.use_query_rewrite:
            processed_input = self.rewriter.rewrite(user_input)

        if self.use_query_decompose:
            sub_queries = self.decomposer.decompose(user_input)
            if len(sub_queries) > 1:
                processed_input = f"原始问题: {user_input}\n请参考以下分解后的子问题进行思考和解决：\n" + "\n".join([f"- {q}" for q in sub_queries])

        result = self.agent.query(processed_input)
        self._save_trace(user_input, result)
        return result

    async def aquery(self, user_input: str) -> Dict[str, Any]:
        """
        处理用户查询 (异步)。
        """
        processed_input = user_input

        if self.use_query_rewrite:
            processed_input = self.rewriter.rewrite(user_input)

        if self.use_query_decompose:
            sub_queries = self.decomposer.decompose(user_input)
            if len(sub_queries) > 1:
                processed_input = f"原始问题: {user_input}\n请参考以下分解后的子问题进行思考和解决：\n" + "\n".join([f"- {q}" for q in sub_queries])

        result = await self.agent.aquery(processed_input)
        self._save_trace(user_input, result)
        return result
