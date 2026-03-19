import pytest
from nagent_rag.retrievers.vector import BaseVectorRetriever

class ConcreteVectorRetriever(BaseVectorRetriever):
    def embed_query(self, query: str):
        return [0.1, 0.2, 0.3]

    def embed_documents(self, texts: list[str]):
        return [[0.1, 0.2, 0.3] for _ in texts]

    def similarity_search_by_vector(self, embedding: list[float], k: int = 3):
        return [{"content": "Matched vector doc", "_score": 0.9}]

    def save_index(self, file_path: str):
        pass

    def load_index(self, file_path: str):
        pass

def test_base_vector_retriever_get_top_k():
    retriever = ConcreteVectorRetriever()
    results = retriever.get_top_k("test query", k=1)

    assert len(results) == 1
    assert results[0]["content"] == "Matched vector doc"
    assert results[0]["_score"] == 0.9

def test_base_vector_retriever_not_implemented():
    base_vector = BaseVectorRetriever()

    with pytest.raises(NotImplementedError):
        base_vector.embed_query("query")

    with pytest.raises(NotImplementedError):
        base_vector.embed_documents(["doc1"])

    with pytest.raises(NotImplementedError):
        base_vector.similarity_search_by_vector([0.1, 0.2])
