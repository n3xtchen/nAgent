"""
模型工厂模块 - 提供 Ragas 所需的模型实例
"""
from google import genai
from ragas.embeddings import GoogleEmbeddings
from ragas.cache import DiskCacheBackend
from nagent_rag.eval import GoogleGenAIWrapper

def get_ragas_models(client: genai.Client, model_name: str, cache_dir: str = ".ragas_cache"):
    """
    获取 Ragas 生成所需的 LLM 和 Embeddings 实例

    Args:
        client: Google GenAI 客户端实例
        model_name: 生成模型名称
        cache_dir: Ragas 缓存目录

    Returns:
        tuple: (generator_llm, embeddings)
    """
    # 启用 Ragas 内置缓存
    ragas_cache = DiskCacheBackend(cache_dir=cache_dir)

    generator_llm = GoogleGenAIWrapper(client=client, model=model_name, cache=ragas_cache)
    embeddings = GoogleEmbeddings(
        model="gemini-embedding-001",
        client=client,
        cache=ragas_cache
    )

    return generator_llm, embeddings
