import os
import argparse
import json
from dotenv import load_dotenv
from google import genai
from nagent_rag.retriever import SimpleKeywordRetriever
from agentic_rag.rags import AgenticRAG

def main():
    load_dotenv()

    parser = argparse.ArgumentParser(description="Agentic RAG CLI")
    parser.add_argument("query", type=str, help="The question to ask the agent")
    parser.add_argument("--model", type=str, default="gemini-2.0-flash", help="Gemini model name")
    parser.add_argument("--max-iterations", type=int, default=5, help="Max reasoning iterations")
    parser.add_argument("--index-path", type=str, help="Path to save or load the index file")
    parser.add_argument("--add-docs", type=str, help="Path to a JSON file containing documents to add")
    parser.add_argument("--rewrite", action="store_true", help="Enable query rewriting")
    parser.add_argument("--decompose", action="store_true", help="Enable query decomposition")
    parser.add_argument("--trace-dir", type=str, help="Directory to save reasoning traces")

    args = parser.parse_args()

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set.")
        return

    client = genai.Client(api_key=api_key)

    retriever = SimpleKeywordRetriever()

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
                    rag_system.add_documents(new_docs)
                    print(f"Added {len(new_docs)} documents.")
                else:
                    print("Error: Document file must contain a JSON list.")
        else:
            print(f"Error: Document file not found: {args.add_docs}")

    # 如果有新文档且指定了索引路径，自动保存
    if args.add_docs and args.index_path:
        rag_system.save_index()
        print(f"Index saved to {args.index_path}")

    print(f"Querying: {args.query}")
    print("-" * 20)

    result = rag_system.query(args.query)

    print("\n" + "=" * 20)
    print("Final Answer:")
    print(result["answer"])
    print("=" * 20)

if __name__ == "__main__":
    main()
