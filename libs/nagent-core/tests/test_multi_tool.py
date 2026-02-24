import pytest
from nagent_core.tool import CalculatorTool
from nagent_core.agent import ReActAgent
from unittest.mock import MagicMock

def test_calculator_tool():
    calc = CalculatorTool()
    assert calc.run("2 + 2") == "4"
    assert calc.run("10 / 2 * 5") == "25.0"
    assert calc.run("(1 + 2) * 3") == "9"
    assert "错误" in calc.run("import os")
    assert "错误" in calc.run("2 + a")

def test_agent_with_calculator():
    # Mock client and response to avoid real API calls
    mock_client = MagicMock()
    calc = CalculatorTool()
    from nagent_core.agent import ReActAgent

    agent = ReActAgent(client=mock_client, tools=[calc])
    assert len(agent.tools) == 1
    assert agent.tools["calculator"] == calc
    assert "calculator" in agent.system_prompt
