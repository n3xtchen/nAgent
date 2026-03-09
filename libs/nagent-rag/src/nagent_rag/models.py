"""
模型工厂模块 - 提供 Ragas 所需的模型实例
"""
from google import genai
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from ragas.embeddings import LangchainEmbeddingsWrapper
from nagent_rag.eval import GoogleGenAIWrapper

def get_ragas_models(client: genai.Client, model_name: str, api_key: str):
    """
    获取 Ragas 生成所需的 LLM 和 Embeddings 实例

    Args:
        client: Google GenAI 客户端实例
        model_name: 生成模型名称
        api_key: Google API 密钥

    Returns:
        tuple: (generator_llm, embeddings)
    """
    generator_llm = GoogleGenAIWrapper(client=client, model=model_name)
    lc_embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=api_key
    )
    embeddings = LangchainEmbeddingsWrapper(lc_embeddings)

    return generator_llm, embeddings
