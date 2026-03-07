"""
测试数据集生成程序 - 基于 Ragas
"""
import asyncio
import json
import logging
import os
import uuid
from dataclasses import asdict
from pathlib import Path
from typing import List, Dict, Any, Optional

from langchain_community.document_loaders import PyPDFLoader, TextLoader, UnstructuredMarkdownLoader
from langchain_text_splitters import TokenTextSplitter
from ragas.testset.graph import KnowledgeGraph
from ragas.testset.graph import Node, NodeType
from ragas.llms import BaseRagasLLM
from ragas.embeddings import BaseRagasEmbeddings

from nagent_rag.eval import generate_testset, GoogleGenAIWrapper
from nagent_rag.validation import TestCase

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def generate_dataset(
    docs_path: str,
    output_path: str,
    generator_llm: BaseRagasLLM,
    embeddings: BaseRagasEmbeddings,
    testset_size: int = 10,
    chunk_size: int = 1000,
    chunk_overlap: int = 100,
):
    """
    生成测试数据集
    """
    # 1. 加载文档/数据
    logger.info(f"📂 加载数据: {docs_path}")
    path = Path(docs_path)

    nodes = []
    content_to_index = {}

    # 如果是预处理好的 JSON 文件
    if path.suffix.lower() == ".json":
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, list):
             raise ValueError("JSON 文件格式错误: 必须是列表")

        logger.info(f"✓ 从 JSON 加载了 {len(data)} 个数据片段")

        for i, item in enumerate(data):
            content = item.get("page_content", "")
            metadata = item.get("metadata", {})
            filename = metadata.get("source", "")

            clean_content = content.strip()
            content_to_index[clean_content] = i

            nodes.append(
                Node(
                    type=NodeType.DOCUMENT,
                    properties={
                        "page_content": content,
                        "filename": filename,
                        "doc_id": str(i) # 使用索引作为 ID 辅助
                    }
                )
            )

    else:
        # 原有的文档加载逻辑
        documents = []

        if path.is_file():
            files = [path]
        elif path.is_dir():
            files = list(path.glob("**/*"))
        else:
            raise ValueError(f"路径不存在: {docs_path}")

        for file_path in files:
            if file_path.name.startswith("."): # 跳过隐藏文件
                continue

            try:
                if file_path.suffix.lower() == ".pdf":
                    loader = PyPDFLoader(str(file_path))
                    documents.extend(loader.load())
                elif file_path.suffix.lower() == ".txt":
                    loader = TextLoader(str(file_path))
                    documents.extend(loader.load())
                elif file_path.suffix.lower() == ".md":
                     loader = UnstructuredMarkdownLoader(str(file_path))
                     documents.extend(loader.load())
            except Exception as e:
                logger.warning(f"⚠️ 无法加载文件 {file_path}: {e}")

        if not documents:
            raise ValueError("未找到可加载的文档")

        logger.info(f"✓ 已加载 {len(documents)} 个文档片段")

        # 2. 构建知识图谱 (Ragas 需要)
        # Ragas 的 KnowledgeGraph 通常是从 Node 列表构建的
        # 我们需要先切分文档
        text_splitter = TokenTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        splits = text_splitter.split_documents(documents)

        for i, split in enumerate(splits):
            # 清理一下 content，去除多余空白，以便匹配
            clean_content = split.page_content.strip()
            content_to_index[clean_content] = i

            nodes.append(
                Node(
                    type=NodeType.DOCUMENT,
                    properties={
                        "page_content": split.page_content,
                        "filename": split.metadata.get("source", ""),
                        "page_number": split.metadata.get("page", 0)
                    }
                )
            )

    logger.info(f"✓ 准备了 {len(nodes)} 个节点用于生成")

    # 创建临时 KG 文件
    kg_path = f"temp_kg_{uuid.uuid4()}.json"
    kg = KnowledgeGraph(nodes=nodes)
    kg.save(kg_path)

    try:
        # 3. 生成测试集
        logger.info(f"🚀 开始生成测试集 (size={testset_size})...")
        dataset = generate_testset(
            generator_llm=generator_llm,
            embeddings=embeddings,
            kg_path=kg_path,
            testset_size=testset_size
        )

        # 4. 转换为 TestCase 格式
        test_cases = []
        df = dataset.to_pandas()

        for idx, row in df.iterrows():
            # 获取文档索引 (这里简化处理，直接用 context)
            # Ragas 生成的 dataset 包含: user_input, reference, contexts, etc.

            # 兼容不同版本的 Ragas 列名
            question = row.get("user_input") or row.get("question")
            answer = row.get("reference") or row.get("ground_truth") or row.get("answer")
            contexts = row.get("reference_contexts") or row.get("contexts") or []
            eval_type = row.get("eval_type", "")

            # 将 contexts 转换为 docs_indices
            docs_indices = []
            if isinstance(contexts, list):
                for ctx in contexts:
                    if isinstance(ctx, str):
                        # 尝试精确匹配
                        clean_ctx = ctx.strip()
                        if clean_ctx in content_to_index:
                            docs_indices.append(content_to_index[clean_ctx])
                        else:
                            # 尝试模糊匹配（如果 Ragas 稍微修改了文本）
                            # 这里简单实现：如果 ctx 是某个 chunk 的子串，或者某个 chunk 是 ctx 的子串
                            for content, idx in content_to_index.items():
                                if clean_ctx in content or content in clean_ctx:
                                    docs_indices.append(idx)
                                    break

            # 去重
            docs_indices = sorted(list(set(docs_indices)))

            tc = TestCase(
                id=str(uuid.uuid4()),
                user_input=str(question),
                reference=str(answer),
                docs_indices=docs_indices,
                description=f"Generated by Ragas ({eval_type})",
                metadata={
                    "source_context": list(contexts),
                    "eval_type": str(eval_type)
                }
            )
            test_cases.append(tc)

        # 5. 保存为 JSON (直接使用 TestCase 结构)
        output_data = [asdict(tc) for tc in test_cases]

        # 确保存储目录存在
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        logger.info(f"✓ 测试集已保存到: {output_path}")
        return output_path

    finally:
        # 清理临时文件
        if os.path.exists(kg_path):
            try:
                os.remove(kg_path)
            except Exception as e:
                logger.warning(f"无法删除临时文件 {kg_path}: {e}")

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
        # 尝试从 .env 加载
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
    generator_llm = GoogleGenAIWrapper(client=client, model=args.model)
    # 注意：LangChain 目前可能还依赖旧版 SDK，如果这里报错，可能需要回退或者安装旧版 SDK
    # 如果环境只有新版 SDK，LangChain 可能会有问题
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=api_key)

    try:
        asyncio.run(generate_dataset(
            docs_path=args.docs,
            output_path=args.output,
            generator_llm=generator_llm,
            embeddings=embeddings,
            testset_size=args.size
        ))
    except Exception as e:
        print(f"❌ 程序执行出错: {e}")
        exit(1)
