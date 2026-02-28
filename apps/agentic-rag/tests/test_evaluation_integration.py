import pytest
from unittest.mock import MagicMock, AsyncMock
from agentic_rag.rag import AgenticRAG
from nagent_rag.retriever import BaseRetriever
from nagent_rag.eval import reasoning_steps_metric

@pytest.mark.asyncio
async def test_agentic_rag_aquery_and_metric_integration():
    """
    集成验证：AgenticRAG.aquery 产生 trace，并且推理步数指标能正确解析该 trace。
    """
    mock_llm = MagicMock()
    mock_llm.aio = MagicMock()

    # 模拟两轮推理
    response1 = MagicMock()
    response1.text = "Thought: I need to retrieve information.\nAction: retrieve(some query)"
    response2 = MagicMock()
    response2.text = "Thought: I have the answer.\nFinal Answer: This is the integrated answer."

    mock_llm.aio.models.generate_content = AsyncMock(side_effect=[response1, response2])

    mock_retriever = MagicMock(spec=BaseRetriever)
    mock_retriever.retrieve = MagicMock(return_value="Some retrieved content")
    mock_retriever.documents = []

    rag = AgenticRAG(client=mock_llm, retriever=mock_retriever)

    # 1. 验证 aquery 产生 trace
    result = await rag.aquery("Test integrated query")
    assert result["answer"] == "This is the integrated answer."
    assert "trace" in result
    trace = result["trace"]
    assert len(trace) == 2

    # 2. 验证评估指标能处理该 trace
    metric_res = await reasoning_steps_metric.ascore(trace=trace)
    assert metric_res.value == 2.0
    assert "2" in metric_res.reason
