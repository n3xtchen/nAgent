import pytest
from nagent_rag.retrievers.base import BaseRetriever

class ConcreteRetriever(BaseRetriever):
    def get_top_k(self, query: str, k: int = 3):
        return [{"content": "Mock result", "_score": 1.0}]

    def save_index(self, file_path: str):
        pass

    def load_index(self, file_path: str):
        pass

def test_base_retriever_fit():
    retriever = ConcreteRetriever()

    # Test with string list
    docs = ["doc1", "doc2"]
    retriever.fit(docs)
    assert len(retriever.documents) == 2
    assert retriever.documents[0] == {"content": "doc1"}
    assert retriever.documents[1] == {"content": "doc2"}

    # Test with dict list
    docs_dict = [{"content": "doc1", "metadata": {"source": "test"}}, {"content": "doc2"}]
    retriever.fit(docs_dict)
    assert len(retriever.documents) == 2
    assert retriever.documents[0]["metadata"] == {"source": "test"}

    # Test with other types
    docs_other = [123, 456.7]
    retriever.fit(docs_other)
    assert len(retriever.documents) == 2
    assert retriever.documents[0] == {"content": "123"}
    assert retriever.documents[1] == {"content": "456.7"}

def test_base_retriever_not_implemented():
    base = BaseRetriever()
    with pytest.raises(NotImplementedError):
        base.get_top_k("query")

    with pytest.raises(NotImplementedError):
        base.save_index("path")

    with pytest.raises(NotImplementedError):
        base.load_index("path")
