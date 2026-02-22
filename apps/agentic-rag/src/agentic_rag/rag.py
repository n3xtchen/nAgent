from typing import List, Optional
from nagent_core.agent import ReActAgent
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
    ):
        self.retriever = retriever
        self.retriever_tool = RetrieverTool(retriever)
        self.agent = ReActAgent(
            client=client,
            tools=[self.retriever_tool],
            model_name=model_name,
            max_iterations=max_iterations,
        )

    def query(self, user_input: str):
        """
        处理用户查询。
        """
        return self.agent.query(user_input)
