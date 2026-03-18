from typing import Optional, Dict, Any
from nagent_rag.retrievers.base import BaseRetriever
from nagent_rag.tools import RetrieverTool
from nagent_core.llm import LLMClient
from .base import BaseRAG

class SimpleRAG(BaseRAG):
    """
    最基础的 RAG 实现：
    直接调用 Retriever 获取上下文，结合系统 Prompt 生成答案，不使用多跳推理（Agent）。
    """
    def __init__(
        self,
        client,
        retriever: BaseRetriever,
        model_name: str = "gemini-2.0-flash",
        trace_dir: Optional[str] = None,
        index_path: Optional[str] = None,
        k: int = 3,
    ):
        super().__init__(
            client=client,
            retriever=retriever,
            model_name=model_name,
            trace_dir=trace_dir,
            index_path=index_path,
        )
        self.k = k
        self.llm_client = LLMClient(client)
        self.retriever_tool = RetrieverTool(retriever)

    def _build_prompt(self, user_input: str, context: str) -> str:
        return f"""你是一个智能问答助手。请基于以下检索到的参考内容回答用户的问题。
如果参考内容中没有相关信息，请明确告知用户。

【参考内容】
{context}

【用户问题】
{user_input}
"""

    def _generate_response(self, prompt: str) -> str:
        # 使用 Gemini SDK 同步生成
        response = self.llm_client.generate_content(
            model=self.model_name,
            contents=prompt,
        )
        return response.text

    async def _agenerate_response(self, prompt: str) -> str:
        # 使用 Gemini SDK 异步生成
        response = await self.llm_client.agenerate_content(
            model=self.model_name,
            contents=prompt,
        )
        return response.text

    def query(self, user_input: str) -> Dict[str, Any]:
        """
        处理用户查询（同步）。
        """
        # 1. 检索上下文
        # RetrieverTool.run 会格式化输出，包括 (ID: xxx) 格式，以便 ValidationRunner 匹配
        # 注意：此处强行传递了用户问题，RetrieverTool 内部调用 get_top_k 会使用默认的 k=3
        # 也可以手动调用 self.retriever.get_top_k(user_input, self.k) 再格式化
        docs = self.retriever.get_top_k(user_input, self.k)

        if not docs:
            context = "没有找到相关文档。"
        else:
            formatted_results = []
            for i, doc in enumerate(docs):
                content = doc.get("content", "")
                doc_id = doc.get("id", f"doc_{i}")
                result_str = f"【结果 {i+1}】(ID: {doc_id})\n内容: {content}"
                formatted_results.append(result_str)
            context = "\n\n---\n\n".join(formatted_results)

        # 2. 组装 Prompt 并生成
        prompt = self._build_prompt(user_input, context)
        try:
            answer = self._generate_response(prompt)
        except Exception as e:
            answer = f"生成答案时发生错误: {str(e)}"

        # 3. 构造 Trace (模拟 Agent 的步骤)
        trace = [
            {
                "step": 1,
                "action": "retrieve",
                "action_input": user_input,
                "observation": context,
            }
        ]

        result = {
            "answer": answer,
            "trace": trace,
        }

        # 4. 保存并返回
        self._save_trace(user_input, result)
        return result

    async def aquery(self, user_input: str) -> Dict[str, Any]:
        """
        处理用户查询（异步）。
        """
        # 1. 检索上下文
        docs = self.retriever.get_top_k(user_input, self.k)

        if not docs:
            context = "没有找到相关文档。"
        else:
            formatted_results = []
            for i, doc in enumerate(docs):
                content = doc.get("content", "")
                doc_id = doc.get("id", f"doc_{i}")
                result_str = f"【结果 {i+1}】(ID: {doc_id})\n内容: {content}"
                formatted_results.append(result_str)
            context = "\n\n---\n\n".join(formatted_results)

        # 2. 组装 Prompt 并生成
        prompt = self._build_prompt(user_input, context)
        try:
            answer = await self._agenerate_response(prompt)
        except Exception as e:
            answer = f"生成答案时发生错误: {str(e)}"

        # 3. 构造 Trace (模拟 Agent 的步骤)
        trace = [
            {
                "step": 1,
                "action": "retrieve",
                "action_input": user_input,
                "observation": context,
            }
        ]

        result = {
            "answer": answer,
            "trace": trace,
        }

        # 4. 保存并返回
        self._save_trace(user_input, result)
        return result
