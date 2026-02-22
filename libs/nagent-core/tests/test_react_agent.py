import pytest
from unittest.mock import MagicMock
from nagent_core.agent import ReActAgent
from nagent_core.tool import BaseTool

class MockTool(BaseTool):
    def run(self, query: str) -> str:
        return f"Results for {query}"

def test_react_agent_loop():
    # Mock the LLM client
    mock_llm = MagicMock()

    # 定义模拟 LLM 的连续输出
    # 第一次输出 Thought 和 Action
    response1 = MagicMock()
    response1.text = "Thought: I need to search for the capital of France.\nAction: retrieve(France)"

    # 第二次输出 Final Answer
    response2 = MagicMock()
    response2.text = "Thought: I now know the answer.\nFinal Answer: Paris"

    mock_llm.models.generate_content.side_effect = [response1, response2]

    tool = MockTool(name="retrieve", description="Search tool")
    agent = ReActAgent(client=mock_llm, tools=[tool], max_iterations=2)

    result = agent.query("What is the capital of France?")

    assert result["answer"] == "Paris"
    assert mock_llm.models.generate_content.call_count == 2

def test_react_agent_max_iterations():
    mock_llm = MagicMock()
    response = MagicMock()
    response.text = "Thought: I'm thinking...\nAction: retrieve(something)"
    mock_llm.models.generate_content.return_value = response

    tool = MockTool(name="retrieve", description="Search tool")
    # 设置 max_iterations=2，模拟达到上限
    agent = ReActAgent(client=mock_llm, tools=[tool], max_iterations=2)

    result = agent.query("test")
    assert "Reached max iterations" in result["answer"]
