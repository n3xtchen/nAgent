import os
import tempfile
from nagent_rag.chunking import ChunkingProcessor
from nagent_rag.retrievers.keyword import SimpleKeywordRetriever

def test_rag_chunking_integration():
    # 创建一个长文本文件
    long_text = "Python is a programming language. " * 50 # 足够长
    long_text += "SpecialKeyphrase "
    long_text += "Java is another language. " * 50

    with tempfile.NamedTemporaryFile(suffix=".txt", mode="w", delete=False) as f:
        f.write(long_text)
        temp_path = f.name

    try:
        # 使用 ChunkingProcessor
        processor = ChunkingProcessor(chunk_size=200, chunk_overlap=50)
        chunked_docs = processor.process_path(temp_path)

        assert len(chunked_docs) > 1

        # 传入 Retriever
        retriever = SimpleKeywordRetriever()
        retriever.fit(chunked_docs)

        # 检索特殊关键字
        results = retriever.get_top_k("SpecialKeyphrase", k=1)
        assert len(results) == 1
        assert "SpecialKeyphrase" in results[0]["content"]
        # 确认内容被切分了，结果不应该是整个长文本
        assert len(results[0]["content"]) < len(long_text)
    finally:
        os.remove(temp_path)
