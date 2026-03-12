from nagent_rag.text_splitter import RecursiveCharacterTextSplitter

def test_recursive_character_text_splitter_basic():
    splitter = RecursiveCharacterTextSplitter(chunk_size=10, chunk_overlap=0)
    text = "abcdefghij klmnopqrs"
    chunks = splitter.split_text(text)
    # "abcdefghij" is 10 chars. Then " klmnopqrs" starts with space.
    assert "abcdefghij" in chunks
    assert len(chunks) >= 2

def test_recursive_character_text_splitter_with_separators():
    splitter = RecursiveCharacterTextSplitter(chunk_size=15, chunk_overlap=0)
    text = "Hello World\n\nThis is a test."
    chunks = splitter.split_text(text)
    # Should split at \n\n
    assert chunks[0] == "Hello World"
    assert chunks[1] == "This is a test."

def test_split_documents():
    splitter = RecursiveCharacterTextSplitter(chunk_size=10, chunk_overlap=0)
    docs = [{"content": "1234567890 12345", "metadata": {"source": "test"}}]
    chunked_docs = splitter.split_documents(docs)
    assert len(chunked_docs) >= 2
    assert chunked_docs[0]["metadata"]["chunk_index"] == 0
    assert chunked_docs[1]["metadata"]["chunk_index"] == 1
    assert chunked_docs[0]["metadata"]["source"] == "test"
