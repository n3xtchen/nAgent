"""
测试数据集生成程序 - 基于 Ragas
"""
import asyncio
import json
import logging
import os
from dataclasses import asdict
from pathlib import Path

from nagent_rag.eval import GoogleGenAIWrapper
from nagent_rag.testset_generation import RagasTestsetGenerator, load_rag_data

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def generate_dataset_task(
    docs_path: str,
    output_path: str,
    generator_llm,
    embeddings,
    testset_size: int = 10,
    chunk_size: int = 1000,
    chunk_overlap: int = 100,
):
    """
    生成测试数据集任务
    """
    # 1. 加载数据
    documents = load_rag_data(docs_path)
    if not documents:
        raise ValueError(f"未找到可加载的文档: {docs_path}")

    # 2. 初始化生成器
    generator = RagasTestsetGenerator(
        generator_llm=generator_llm,
        embeddings=embeddings,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )

    # 3. 生成测试用例
    test_cases = await generator.generate(
        documents=documents,
        testset_size=testset_size
    )

    # 4. 保存结果
    output_data = [asdict(tc) for tc in test_cases]
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    logger.info(f"✓ 测试集已保存到: {output_path}")

if __name__ == "__main__":
    import argparse
    from langchain_google_genai import GoogleGenerativeAIEmbeddings
    from google import genai

    parser = argparse.ArgumentParser(description="生成 RAG 测试数据集")
    parser.add_argument("--docs", required=True, help="文档路径 (文件或目录)")
    parser.add_argument("--output", required=True, help="输出 JSON 文件路径")
    parser.add_argument("--size", type=int, default=10, help="生成测试用例数量")
    parser.add_argument("--model", default="gemini-2.0-flash", help="使用的 Gemini 模型")

    args = parser.parse_args()

    # 初始化 LLM 和 Embeddings
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        try:
            from dotenv import load_dotenv
            load_dotenv()
            api_key = os.environ.get("GOOGLE_API_KEY")
        except ImportError:
            pass

    if not api_key:
        print("❌ 错误: 未设置 GOOGLE_API_KEY 环境变量")
        exit(1)

    # 使用新的 Google GenAI Client
    client = genai.Client(api_key=api_key)

    # 包装器适配 Ragas
    from ragas.embeddings import LangchainEmbeddingsWrapper
    generator_llm = GoogleGenAIWrapper(client=client, model=args.model)
    lc_embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001", google_api_key=api_key)
    embeddings = LangchainEmbeddingsWrapper(lc_embeddings)

    try:
        asyncio.run(generate_dataset_task(
            docs_path=args.docs,
            output_path=args.output,
            generator_llm=generator_llm,
            embeddings=embeddings,
            testset_size=args.size
        ))
    except Exception as e:
        print(f"❌ 程序执行出错: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
