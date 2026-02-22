import os
import argparse
from dotenv import load_dotenv
from google import genai
from nagent_rag.retriever import SimpleKeywordRetriever
from agentic_rag.rag import AgenticRAG

def main():
    load_dotenv()

    parser = argparse.ArgumentParser(description="Agentic RAG CLI")
    parser.add_argument("query", type=str, help="The question to ask the agent")
    parser.add_argument("--model", type=str, default="gemini-2.0-flash", help="Gemini model name")
    parser.add_argument("--max-iterations", type=int, default=5, help="Max reasoning iterations")

    args = parser.parse_args()

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set.")
        return

    client = genai.Client(api_key=api_key)

    # 初始化一个基础检索器（这里可以使用空数据，或者在 example.py 中演示带数据的）
    # 在这个简单的 CLI 中，我们默认初始化一个没有文档的检索器
    # 真正的知识应该通过外部注入
    retriever = SimpleKeywordRetriever()

    rag_system = AgenticRAG(
        client=client,
        retriever=retriever,
        model_name=args.model,
        max_iterations=args.max_iterations
    )

    print(f"Querying: {args.query}")
    print("-" * 20)

    result = rag_system.query(args.query)

    print("\n" + "=" * 20)
    print("Final Answer:")
    print(result["answer"])
    print("=" * 20)

if __name__ == "__main__":
    main()
