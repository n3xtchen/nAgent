import os
import shutil
import pytest
from unittest.mock import MagicMock
from nagent_rag.retriever import BaseRetriever
from agentic_rag.rag import AgenticRAG

def test_agentic_rag_trace_persistence():
    trace_dir = "test_traces"
    if os.path.exists(trace_dir):
        shutil.rmtree(trace_dir)

    mock_llm = MagicMock()
    # 模拟同步生成内容
    response = MagicMock()
    response.text = "Thought: I am done.\nFinal Answer: Hello world"
    mock_llm.models.generate_content.return_value = response

    mock_retriever = MagicMock(spec=BaseRetriever)
    mock_retriever.documents = []

    rag = AgenticRAG(client=mock_llm, retriever=mock_retriever, trace_dir=trace_dir)

    # 执行查询
    rag.query("Hi")

    # 验证目录和文件是否存在
    assert os.path.exists(trace_dir)
    files = os.listdir(trace_dir)
    assert len(files) == 1
    assert files[0].endswith(".json")

    # 验证内容
    import json
    with open(os.path.join(trace_dir, files[0]), 'r', encoding='utf-8') as f:
        data = json.load(f)
        assert data["user_input"] == "Hi"
        assert data["answer"] == "Hello world"
        assert "trace" in data

    # 清理
    shutil.rmtree(trace_dir)
    print("Trace persistence test passed!")

if __name__ == "__main__":
    test_agentic_rag_trace_persistence()
