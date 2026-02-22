import os
from dotenv import load_dotenv
from google import genai
from nagent_rag.retriever import SimpleKeywordRetriever
from agentic_rag.rag import AgenticRAG

def run_example():
    load_dotenv()

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set.")
        return

    client = genai.Client(api_key=api_key)

    # 1. 创建检索器并添加一些示例文档
    retriever = SimpleKeywordRetriever()
    retriever.fit([
        "Agentic RAG 是由智能体驱动的检索增强生成技术。",
        "Phase 1 的目标是实现基础的 ReAct 循环和工具集成。",
        "nAgent 是一个用于构建自主智能体的实验性框架。",
        "Gemini 是 Google 开发的多模态大语言模型系列。"
    ])

    # 2. 初始化 Agentic RAG 系统
    rag_system = AgenticRAG(
        client=client,
        retriever=retriever,
        model_name="gemini-2.0-flash"
    )

    # 3. 执行查询
    query = "nAgent 框架是做什么用的？Phase 1 的目标是什么？"
    print(f"执行示例查询: {query}\n")

    result = rag_system.query(query)

    print("\n最终答案:")
    print(result["answer"])

if __name__ == "__main__":
    run_example()
