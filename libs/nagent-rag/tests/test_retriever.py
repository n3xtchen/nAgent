from nagent_rag import SimpleKeywordRetriever

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
    assert results[0][0] == 0
    assert results[0][1] == 1

    # Test query with multiple matches
    results = retriever.get_top_k("is a", k=2)
    assert len(results) == 2
    # Both doc 0 and doc 1 have "is" and "a" (if space split)
    assert results[0][1] == 2
    assert results[1][1] == 2

def test_tokenizer_fallback():
    # Test with non-existent tokenizer or missing jieba
    retriever = SimpleKeywordRetriever(tokenizer="jieba")
    docs = ["你好 世界"]
    retriever.fit(docs)
    results = retriever.get_top_k("你好", k=1)
    assert len(results) == 1
