from typing import List

class QueryRewriter:
    """
    简单的查询改写器。
    """
    def rewrite(self, query: str) -> str:
        """
        目前只是简单的返回原查询，以后可以集成 LLM 来优化查询。
        """
        return query.strip()

def simple_query_expansion(query: str) -> List[str]:
    """
    简单的查询扩展逻辑。
    """
    return [query]
