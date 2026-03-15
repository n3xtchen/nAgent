import pytest
from unittest.mock import Mock, patch
from agentic_rag.rags.vector import VectorRAG
from nagent_rag.retrievers.base import BaseRetriever

class MockRetriever(BaseRetriever):
    def get_top_k(self, query: str, k: int = 3):
        return [
            {"id": "doc_1", "content": "Vector RAG is awesome.", "_score": 0.9},
            {"id": "doc_2", "content": "RAG systems use vector databases.", "_score": 0.8}
        ]

    def fit(self, documents):
        pass

    def save_index(self, path):
        pass

    def load_index(self, path):
        pass

@pytest.fixture
def mock_client():
    client = Mock()
    client.models.generate_content.return_value = Mock(text="Mock response from agent")
    return client

def test_vector_rag_initialization(mock_client):
    retriever = MockRetriever()
    rag = VectorRAG(client=mock_client, retriever=retriever, model_name="test-model")

    assert rag.model_name == "test-model"
    assert rag.retriever == retriever
    # Check if tools are initialized
    assert len(rag.agent.tools) == 5
    assert "vector_search" in rag.agent.tools

def test_vector_search_tool():
    from agentic_rag.tools.vector_tools import VectorSearchTool
    retriever = MockRetriever()
    tool = VectorSearchTool(retriever)

    result = tool.run("test query")
    assert "Vector RAG is awesome." in result
    assert "Score: 0.9" in result
    assert "doc_1" in result
