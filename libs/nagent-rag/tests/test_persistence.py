import os
import json
import pytest
from nagent_rag.retrievers.keyword import SimpleKeywordRetriever

def test_persistence(tmp_path):
    # 1. Prepare data
    docs = [
        {"id": "1", "content": "Python is a programming language.", "metadata": {"category": "tech"}},
        {"id": "2", "content": "The capital of France is Paris.", "metadata": {"category": "geography"}},
    ]
    index_file = os.path.join(tmp_path, "index.json")

    # 2. Create retriever and fit
    retriever = SimpleKeywordRetriever()
    retriever.fit(docs)

    # 3. Save index
    retriever.save_index(index_file)
    assert os.path.exists(index_file)

    # 4. Load index into a new instance
    new_retriever = SimpleKeywordRetriever()
    new_retriever.load_index(index_file)

    # 5. Verify content
    assert len(new_retriever.documents) == 2
    assert new_retriever.documents[0]["id"] == "1"
    assert new_retriever.documents[1]["content"] == "The capital of France is Paris."

    # 6. Verify retrieval works
    results = new_retriever.get_top_k("Python")
    assert len(results) >= 1
    assert results[0]["id"] == "1"
    assert results[0]["_score"] > 0

def test_structured_retrieval():
    docs = [
        {"id": "doc_a", "content": "Apple is a fruit.", "metadata": {"type": "food"}},
        {"id": "doc_b", "content": "Banana is also a fruit.", "metadata": {"type": "food"}},
    ]
    retriever = SimpleKeywordRetriever()
    retriever.fit(docs)

    results = retriever.get_top_k("Apple")
    assert len(results) == 1
    assert results[0]["id"] == "doc_a"
    assert "metadata" in results[0]
    assert results[0]["metadata"]["type"] == "food"
    assert "_score" in results[0]
