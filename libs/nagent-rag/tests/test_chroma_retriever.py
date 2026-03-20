import os
import uuid
import pytest
from unittest.mock import MagicMock, patch
import sys

@pytest.fixture
def mock_chromadb():
    # Setup mock chromadb module
    mock_chroma = MagicMock()
    mock_client = MagicMock()
    mock_collection = MagicMock()

    mock_chroma.PersistentClient.return_value = mock_client
    mock_client.get_or_create_collection.return_value = mock_collection

    # We need to mock the import of chromadb in the module
    with patch.dict("sys.modules", {
        "chromadb": mock_chroma,
        "chromadb.config": MagicMock(),
        "chromadb.api.types": MagicMock()
    }):
        # Reload the module to use the mocked chromadb
        import importlib
        import nagent_rag.retrievers.chroma
        importlib.reload(nagent_rag.retrievers.chroma)

        from nagent_rag.retrievers.chroma import ChromaRetriever

        yield mock_chroma, mock_client, mock_collection, ChromaRetriever

def test_chroma_retriever_init(mock_chromadb):
    mock_chroma, mock_client, mock_collection, ChromaRetriever = mock_chromadb

    # Use patch to mock os.makedirs to prevent directory creation during test
    with patch("os.makedirs") as mock_makedirs:
        with patch("os.path.exists", return_value=False):
            retriever = ChromaRetriever(collection_name="test_col", persist_directory="test_dir")

            mock_makedirs.assert_called_once_with("test_dir")
            mock_chroma.PersistentClient.assert_called_once_with(path="test_dir")
            mock_client.get_or_create_collection.assert_called_once_with(
                name="test_col",
                embedding_function=None
            )

def test_chroma_retriever_fit(mock_chromadb):
    mock_chroma, mock_client, mock_collection, ChromaRetriever = mock_chromadb

    with patch("os.makedirs"), patch("os.path.exists", return_value=True):
        retriever = ChromaRetriever()

        docs = [
            {"content": "Doc 1", "metadata": {"source": "web", "count": 1, "nested": {"a": 1}}},
            {"content": "Doc 2", "id": "custom-id-2"}
        ]

        retriever.fit(docs)

        mock_collection.upsert.assert_called_once()
        call_kwargs = mock_collection.upsert.call_args.kwargs

        assert len(call_kwargs["ids"]) == 2
        assert call_kwargs["ids"][1] == "custom-id-2"
        assert len(call_kwargs["documents"]) == 2
        assert call_kwargs["documents"] == ["Doc 1", "Doc 2"]
        assert len(call_kwargs["metadatas"]) == 2

        # Check metadata sanitization
        meta1 = call_kwargs["metadatas"][0]
        assert meta1["source"] == "web"
        assert meta1["count"] == 1
        assert meta1["nested"] == "{'a': 1}" # str conversion

        assert call_kwargs["metadatas"][1] is None

def test_chroma_retriever_get_top_k(mock_chromadb):
    mock_chroma, mock_client, mock_collection, ChromaRetriever = mock_chromadb

    # Mock the return of query
    mock_collection.query.return_value = {
        "ids": [["id1", "id2"]],
        "documents": [["Doc 1 match", "Doc 2 match"]],
        "metadatas": [[{"source": "test"}, None]],
        "distances": [[0.1, 0.5]]
    }

    with patch("os.makedirs"), patch("os.path.exists", return_value=True):
        retriever = ChromaRetriever()

        results = retriever.get_top_k("query string", k=2)

        mock_collection.query.assert_called_once_with(
            query_texts=["query string"],
            n_results=2
        )

        assert len(results) == 2
        assert results[0]["id"] == "id1"
        assert results[0]["content"] == "Doc 1 match"
        assert results[0]["metadata"] == {"source": "test"}
        assert results[0]["_score"] == 0.1

        assert results[1]["id"] == "id2"
        assert "metadata" not in results[1]
        assert results[1]["_score"] == 0.5

def test_chroma_retriever_similarity_search_by_vector(mock_chromadb):
    mock_chroma, mock_client, mock_collection, ChromaRetriever = mock_chromadb

    mock_collection.query.return_value = {
        "ids": [["v1"]],
        "documents": [["Vector doc match"]],
        "metadatas": [[None]],
        "distances": [[0.2]]
    }

    with patch("os.makedirs"), patch("os.path.exists", return_value=True):
        retriever = ChromaRetriever()

        results = retriever.similarity_search_by_vector([0.1, 0.2, 0.3], k=1)

        mock_collection.query.assert_called_once_with(
            query_embeddings=[[0.1, 0.2, 0.3]],
            n_results=1
        )

        assert len(results) == 1
        assert results[0]["content"] == "Vector doc match"
        assert results[0]["_score"] == 0.2

def test_chroma_retriever_empty_results(mock_chromadb):
    mock_chroma, mock_client, mock_collection, ChromaRetriever = mock_chromadb

    # Mock empty results
    mock_collection.query.return_value = {
        "ids": [[]],
        "documents": [[]],
        "distances": [[]]
    }

    with patch("os.makedirs"), patch("os.path.exists", return_value=True):
        retriever = ChromaRetriever()

        results = retriever.get_top_k("query")
        assert len(results) == 0

def test_chroma_retriever_empty_fit(mock_chromadb):
    mock_chroma, mock_client, mock_collection, ChromaRetriever = mock_chromadb
    with patch("os.makedirs"), patch("os.path.exists", return_value=True):
        retriever = ChromaRetriever()
        retriever.fit([])
        mock_collection.upsert.assert_not_called()

def test_chroma_retriever_pass_methods(mock_chromadb):
    mock_chroma, mock_client, mock_collection, ChromaRetriever = mock_chromadb
    with patch("os.makedirs"), patch("os.path.exists", return_value=True):
        retriever = ChromaRetriever()
        with pytest.raises(ValueError, match="No embedding function provided"):
            retriever.embed_query("test")
        with pytest.raises(ValueError, match="No embedding function provided"):
            retriever.embed_documents(["test"])
        assert retriever.save_index("test") is None
        assert retriever.load_index("test") is None

def test_chroma_retriever_with_custom_embedding(mock_chromadb):
    mock_chroma, mock_client, mock_collection, ChromaRetriever = mock_chromadb

    mock_ef = MagicMock()
    del mock_ef.embed_texts
    del mock_ef.embed_text
    mock_ef.embed_query.return_value = [0.1, 0.2]
    mock_ef.embed_documents.return_value = [[0.1, 0.2], [0.3, 0.4]]

    with patch("os.makedirs"), patch("os.path.exists", return_value=True):
        retriever = ChromaRetriever(embedding_function=mock_ef)

        # Verify initialization
        # The embedding_function passed to get_or_create_collection is a RagasEmbeddingWrapper
        assert mock_client.get_or_create_collection.call_args.kwargs["name"] == "default_collection"
        passed_ef = mock_client.get_or_create_collection.call_args.kwargs["embedding_function"]
        assert passed_ef is not None
        assert passed_ef.name() == "ragas_embedding_wrapper"

        # Test wrapper call
        # Mock Documents and Embeddings are MagicMocks from sys.modules
        passed_ef(["doc1"])
        mock_ef.embed_documents.assert_called_once_with(["doc1"])

        # Test methods
        assert retriever.embed_query("q") == [0.1, 0.2]
        assert retriever.embed_documents(["d1", "d2"]) == [[0.1, 0.2], [0.3, 0.4]]


def test_chroma_retriever_clear(mock_chromadb):
    mock_chroma, mock_client, mock_collection, ChromaRetriever = mock_chromadb
    with patch("os.makedirs"), patch("os.path.exists", return_value=True):
        retriever = ChromaRetriever(collection_name="test_col")

        # Reset mocks to ignore initialization calls
        mock_client.reset_mock()
        mock_collection.reset_mock()

        # Add some dummy documents to in-memory list
        retriever.documents = [{"id": "1", "content": "test"}]

        retriever.clear()

        # Verify in-memory list is cleared
        assert retriever.documents == []

        # Verify chroma client calls
        mock_client.delete_collection.assert_called_once_with(name="test_col")
        mock_client.get_or_create_collection.assert_called_once()

def test_chroma_not_installed():
    # Force ImportError
    with patch.dict("sys.modules", {"chromadb": None}):
        import importlib
        import nagent_rag.retrievers.chroma
        importlib.reload(nagent_rag.retrievers.chroma)

        from nagent_rag.retrievers.chroma import ChromaRetriever

        with pytest.raises(ImportError, match="chromadb is not installed"):
            ChromaRetriever()
