import os
import tempfile
import json
from nagent_rag.retrievers.keyword import SimpleKeywordRetriever

def test_simple_keyword_retriever():
    retriever = SimpleKeywordRetriever()
    docs = [
        "Python is a great programming language",
        "Machine learning is a subset of AI",
        "The quick brown fox jumps over the lazy dog"
    ]
    retriever.fit(docs)

    # Test query that matches one document
    results = retriever.get_top_k("Python", k=1)
    assert len(results) == 1
    assert "Python" in results[0]["content"]
    assert results[0]["_score"] == 1

    # Test query with multiple matches
    results = retriever.get_top_k("is a", k=2)
    assert len(results) == 2
    # Both doc 0 and doc 1 have "is" and "a" (if space split)
    assert results[0]["_score"] == 2
    assert results[1]["_score"] == 2

def test_tokenizer_fallback():
    from unittest.mock import patch
    import sys

    # Force an ImportError for jieba
    with patch.dict("sys.modules", {"jieba": None}):
        retriever = SimpleKeywordRetriever(tokenizer="jieba")
        docs = ["你好 世界"]
        retriever.fit(docs)
        results = retriever.get_top_k("你好", k=1)
        assert len(results) == 1

def test_tokenizer_jieba_success():
    import sys
    from unittest.mock import MagicMock, patch

    # Mock jieba module
    mock_jieba = MagicMock()

    def side_effect(text):
        if text == "你好世界":
            return ["你好", "世界"]
        return [text]

    mock_jieba.cut.side_effect = side_effect

    with patch.dict("sys.modules", {"jieba": mock_jieba}):
        retriever = SimpleKeywordRetriever(tokenizer="jieba")
        docs = ["你好世界"]
        retriever.fit(docs)
        results = retriever.get_top_k("你好", k=1)

        assert len(results) == 1
        assert results[0]["_score"] == 1

def test_keyword_retriever_save_and_load_index():
    retriever = SimpleKeywordRetriever()
    docs = [
        {"content": "Document 1", "metadata": {"id": 1}},
        {"content": "Document 2", "metadata": {"id": 2}}
    ]
    retriever.fit(docs)

    with tempfile.TemporaryDirectory() as temp_dir:
        index_path = os.path.join(temp_dir, "index.json")
        retriever.save_index(index_path)

        assert os.path.exists(index_path)

        with open(index_path, "r", encoding="utf-8") as f:
            saved_docs = json.load(f)
            assert len(saved_docs) == 2
            assert saved_docs[0]["content"] == "Document 1"

        new_retriever = SimpleKeywordRetriever()
        new_retriever.load_index(index_path)

        assert len(new_retriever.documents) == 2
        assert new_retriever.documents[0]["metadata"]["id"] == 1
        assert new_retriever.documents[1]["content"] == "Document 2"

        results = new_retriever.get_top_k("Document", k=2)
        assert len(results) == 2
        assert results[0]["_score"] == 1
        assert results[1]["_score"] == 1
