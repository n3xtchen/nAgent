from nagent_rag.retriever import SimpleKeywordRetriever, RetrieverTool

def test_retriever_tool():
    retriever = SimpleKeywordRetriever()
    docs = ["Apple is red", "Banana is yellow", "Cherry is red"]
    retriever.fit(docs)

    tool = RetrieverTool(retriever)
    result = tool.run("red")

    assert "Apple is red" in result
    assert "Cherry is red" in result
    assert "Banana is yellow" not in result

def test_retriever_tool_no_results():
    retriever = SimpleKeywordRetriever()
    retriever.fit(["Something"])

    tool = RetrieverTool(retriever)
    result = tool.run("Nonexistent")

    assert result == "没有找到相关文档。"
