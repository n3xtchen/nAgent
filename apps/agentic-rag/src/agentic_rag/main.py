import os
import argparse
import json
from dotenv import load_dotenv
from google import genai
from nagent_rag.retrievers.keyword import SimpleKeywordRetriever
from nagent_rag.retrievers.chroma import ChromaRetriever
from nagent_rag.models import get_embeddings
from agentic_rag.rags import AgenticRAG, SimpleRAG, VectorRAG

def main():
    load_dotenv()

    parser = argparse.ArgumentParser(description="Agentic RAG CLI")
    parser.add_argument("query", type=str, help="The question to ask the agent")
    parser.add_argument("--rag-type", type=str, choices=["agentic", "simple", "vector"], default="agentic", help="Type of RAG to use")
    parser.add_argument("--model", type=str, default="gemini-2.0-flash", help="Gemini model name")
    parser.add_argument("--max-iterations", type=int, default=5, help="Max reasoning iterations")
    parser.add_argument("--index-path", type=str, help="Path to save or load the index file")
    parser.add_argument("--add-docs", type=str, help="Path to a JSON file containing documents to add")
    parser.add_argument("--rewrite", action="store_true", help="Enable query rewriting")
    parser.add_argument("--decompose", action="store_true", help="Enable query decomposition")
    parser.add_argument("--trace-dir", type=str, help="Directory to save reasoning traces")

    args = parser.parse_args()

    if not args.add_docs:
        print("Error: 必须通过 --add-docs 指定文档数据 (JSON文件)。")
        return

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set.")
        return

    client = genai.Client(api_key=api_key)

    if args.rag_type == "vector":
        embeddings = get_embeddings(client=client)
        retriever = ChromaRetriever(embedding_function=embeddings)
    else:
        # 使用 jieba 分词以支持中文关键字检索
        retriever = SimpleKeywordRetriever(tokenizer="jieba")

    if args.rag_type == "simple":
        rag_system = SimpleRAG(
            client=client,
            retriever=retriever,
            model_name=args.model,
            trace_dir=args.trace_dir
        )
    elif args.rag_type == "vector":
        rag_system = VectorRAG(
            client=client,
            retriever=retriever,
            model_name=args.model,
            trace_dir=args.trace_dir
        )
    else:
        rag_system = AgenticRAG(
            client=client,
            retriever=retriever,
            model_name=args.model,
            max_iterations=args.max_iterations,
            index_path=args.index_path,
            use_query_rewrite=args.rewrite,
            use_query_decompose=args.decompose,
            trace_dir=args.trace_dir
        )

    # 如果指定了要添加的文档
    if args.add_docs:
        if os.path.exists(args.add_docs):
            with open(args.add_docs, "r", encoding="utf-8") as f:
                new_docs = json.load(f)
                if isinstance(new_docs, list):
                    rag_system.clear_index()
                    rag_system.add_documents(new_docs)
                    print(f"Added {len(new_docs)} documents.")
                else:
                    print("Error: Document file must contain a JSON list.")
                    return
        else:
            print(f"Error: Document file not found: {args.add_docs}")
            return

    # 如果有新文档且指定了索引路径，自动保存
    if args.add_docs and args.index_path:
        rag_system.save_index()
        print(f"Index saved to {args.index_path}")

    print(f"Querying: {args.query}")
    print("-" * 20)

    result = rag_system.query(args.query)

    # 提取并打印检索到的内容
    trace = result.get("trace", [])
    retrieved_contexts = []

    for step in trace:
        action = step.get("action")
        tool_name = ""
        query = ""

        # 处理 SimpleRAG (字符串) 和 ReActAgent (元组) 两种不同的 trace 格式
        if isinstance(action, str):
            tool_name = action
            query = step.get("action_input", "")
        elif isinstance(action, tuple) and len(action) >= 2:
            tool_name = action[0]
            query = action[1]

        # 匹配可能用于检索的工具名称
        if tool_name in ["retrieve", "vector_search"]:
            context = step.get("observation", "")
            retrieved_contexts.append(f"检索工具: {tool_name}\n检索查询: {query}\n检索结果:\n{context}")

    if retrieved_contexts:
        print("\n" + "=" * 20)
        print("检索到的内容 (Retrieved Contexts):")
        for i, ctx in enumerate(retrieved_contexts):
            print(f"\n--- 检索过程 {i+1} ---")
            print(ctx)

    print("\n" + "=" * 20)
    print("Final Answer:")
    print(result["answer"])
    print("=" * 20)

if __name__ == "__main__":
    main()
