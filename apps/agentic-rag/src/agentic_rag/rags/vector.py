from typing import Optional, Dict, Any
from nagent_rag.retrievers.base import BaseRetriever
from nagent_core.llm import LLMClient
from .base import BaseRAG

class VectorRAG(BaseRAG):
    """
    基于向量检索的 RAG 系统 (已简化为 Simple 模式)。
    直接使用 Retriever 进行语义检索，然后将上下文喂给大模型一次性回答，不使用 Agent 多跳推理。
    """
    def __init__(
        self,
        client,
        retriever: BaseRetriever,
        model_name: str = "gemini-2.0-flash",
        max_iterations: int = 5, # 保留参数为了兼容 main.py
        index_path: Optional[str] = None,
        use_query_rewrite: bool = False, # 暂时保留，但在简化的流程中可以选择不使用
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

        self.llm_client = LLMClient(client)

    def _build_prompt(self, user_input: str, context: str) -> str:
        return f"""你是一个智能问答助手。请基于以下通过语义检索到的参考内容回答用户的问题。
如果参考内容中没有相关信息，请明确告知用户。

【参考内容】
{context}

【用户问题】
{user_input}
"""

    def query(self, user_input: str) -> Dict[str, Any]:
        """
        处理用户查询。
        """
        # 1. 向量语义检索 (默认 k=3)
        docs = self.retriever.get_top_k(user_input)

        if not docs:
            context = "没有找到相关的语义匹配结果。"
        else:
            formatted_results = []
            for i, doc in enumerate(docs):
                content = doc.get("content", "")
                doc_id = doc.get("id", f"doc_{i}")
                score = doc.get("_score", "N/A")
                result_str = f"【结果 {i+1}】(ID: {doc_id}, Score: {score})\n内容: {content}"
                formatted_results.append(result_str)
            context = "\n\n---\n\n".join(formatted_results)

        # 2. 组装 Prompt
        prompt = self._build_prompt(user_input, context)

        # 3. 生成回答
        try:
            response = self.llm_client.generate_content(
                model=self.model_name,
                contents=prompt,
            )
            answer = response.text
        except Exception as e:
            answer = f"生成答案时发生错误: {str(e)}"

        # 4. 构造 Trace (模拟步骤以便 main.py 正常打印)
        trace = [
            {
                "step": 1,
                "action": "vector_search",
                "action_input": user_input,
                "observation": context,
            }
        ]

        result = {
            "answer": answer,
            "trace": trace,
        }

        self._save_trace(user_input, result)
        return result

    async def aquery(self, user_input: str) -> Dict[str, Any]:
        """
        处理用户查询 (异步)。
        """
        # 1. 向量语义检索
        docs = self.retriever.get_top_k(user_input)

        if not docs:
            context = "没有找到相关的语义匹配结果。"
        else:
            formatted_results = []
            for i, doc in enumerate(docs):
                content = doc.get("content", "")
                doc_id = doc.get("id", f"doc_{i}")
                score = doc.get("_score", "N/A")
                result_str = f"【结果 {i+1}】(ID: {doc_id}, Score: {score})\n内容: {content}"
                formatted_results.append(result_str)
            context = "\n\n---\n\n".join(formatted_results)

        # 2. 组装 Prompt
        prompt = self._build_prompt(user_input, context)

        # 3. 生成回答
        try:
            response = await self.llm_client.agenerate_content(
                model=self.model_name,
                contents=prompt,
            )
            answer = response.text
        except Exception as e:
            answer = f"生成答案时发生错误: {str(e)}"

        # 4. 构造 Trace
        trace = [
            {
                "step": 1,
                "action": "vector_search",
                "action_input": user_input,
                "observation": context,
            }
        ]

        result = {
            "answer": answer,
            "trace": trace,
        }

        self._save_trace(user_input, result)
        return result
