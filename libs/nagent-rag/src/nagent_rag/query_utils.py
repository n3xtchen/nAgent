from typing import List, Any
import logging
from nagent_core.llm import LLMClient

logger = logging.getLogger(__name__)

class QueryRewriter:
    """
    使用 LLM 改写查询以优化检索效果。
    """
    def __init__(self, client, model_name: str = "gemini-2.0-flash"):
        self.client = client
        self.llm_client = LLMClient(client)
        self.model_name = model_name

    def rewrite(self, query: str) -> str:
        """
        将原始查询改写为更适合检索的关键词或短语。
        """
        prompt = f"""
你是一个搜索专家。请将以下用户查询改写为更适合在文档库中进行关键词检索的短语或问题。
目标是提高检索的相关性。只输出改写后的文本，不要有任何解释。

原始查询: {query}

改写后的查询:"""
        try:
            response = self.llm_client.generate_content(
                model=self.model_name,
                contents=prompt,
            )
            rewritten_query = response.text.strip()
            logger.info(f"Query rewritten: '{query}' -> '{rewritten_query}'")
            return rewritten_query
        except Exception as e:
            logger.error(f"Error rewriting query: {e}")
            return query

class QueryDecomposer:
    """
    使用 LLM 将复杂查询拆分为多个简单的子查询。
    """
    def __init__(self, client, model_name: str = "gemini-2.0-flash"):
        self.client = client
        self.llm_client = LLMClient(client)
        self.model_name = model_name

    def decompose(self, query: str) -> List[str]:
        """
        将复杂查询拆分为子查询列表。
        """
        prompt = f"""
你是一个分析专家。请将以下复杂的查询拆分为 2-3 个更简单的、可以独立检索或回答的子查询。
每个子查询应该是一行。不要输出任何其他内容。

复杂查询: {query}

子查询列表:"""
        try:
            response = self.llm_client.generate_content(
                model=self.model_name,
                contents=prompt,
            )
            sub_queries = [q.strip() for q in response.text.strip().split("\n") if q.strip()]
            logger.info(f"Query decomposed: '{query}' -> {sub_queries}")
            return sub_queries if sub_queries else [query]
        except Exception as e:
            logger.error(f"Error decomposing query: {e}")
            return [query]

def simple_query_expansion(query: str) -> List[str]:
    """
    简单的查询扩展逻辑。目前仅返回原查询。
    """
    return [query]
