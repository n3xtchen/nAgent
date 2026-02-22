import pytest
from unittest.mock import MagicMock
from agentic_rag.rag import AgenticRAG
from nagent_rag.retriever import SimpleKeywordRetriever

def test_agentic_rag_integration():
    # 1. 准备数据和 Retriever
    docs = [
        "Claude is an AI developed by Anthropic.",
        "GPT is an AI developed by OpenAI.",
        "Gemini is an AI developed by Google."
    ]
    retriever = SimpleKeywordRetriever()
    retriever.fit(docs)

    # 2. Mock LLM
    mock_llm = MagicMock()

    # 模拟第一次调用：决定调用检索工具
    response1 = MagicMock()
    response1.text = "Thought: I need to know about Claude.\nAction: retrieve(Claude)"

    # 模拟第二次调用：根据检索结果给出答案
    response2 = MagicMock()
    response2.text = "Thought: I have retrieved the information.\nFinal Answer: Claude is developed by Anthropic."

    mock_llm.models.generate_content.side_effect = [response1, response2]

    # 3. 初始化 AgenticRAG
    rag = AgenticRAG(client=mock_llm, retriever=retriever)

    # 4. 执行查询
    result = rag.query("Who developed Claude?")

    # 5. 验证
    assert "Anthropic" in result["answer"]
    assert mock_llm.models.generate_content.call_count == 2
