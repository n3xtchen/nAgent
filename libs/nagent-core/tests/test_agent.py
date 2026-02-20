import pytest
from unittest.mock import MagicMock
from nagent_core.agent import SimpleAgent

def test_simple_agent_query():
    # Mock the LLM client
    mock_llm = MagicMock()
    mock_response = MagicMock()
    mock_response.text = '```json\n{"answer": "Paris is the capital of France."}\n```'
    mock_llm.models.generate_content.return_value = mock_response

    agent = SimpleAgent(client=mock_llm)
    result = agent.query("What is the capital of France?")

    assert result["answer"] == "Paris is the capital of France."
    mock_llm.models.generate_content.assert_called_once()
