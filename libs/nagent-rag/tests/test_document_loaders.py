import os
import tempfile
from nagent_rag.document_loaders import TextLoader

def test_text_loader_file():
    with tempfile.NamedTemporaryFile(suffix=".txt", mode="w", delete=False) as f:
        f.write("Hello TextLoader")
        temp_path = f.name

    try:
        loader = TextLoader()
        docs = loader.load(temp_path)
        assert len(docs) == 1
        assert docs[0]["content"] == "Hello TextLoader"
        assert docs[0]["metadata"]["filename"] == os.path.basename(temp_path)
    finally:
        os.remove(temp_path)

def test_text_loader_directory():
    with tempfile.TemporaryDirectory() as temp_dir:
        with open(os.path.join(temp_dir, "test1.txt"), "w") as f:
            f.write("Content 1")
        with open(os.path.join(temp_dir, "test2.md"), "w") as f:
            f.write("Content 2")
        with open(os.path.join(temp_dir, "test3.bin"), "wb") as f:
            f.write(b"\x00\x01\x02")

        loader = TextLoader()
        docs = loader.load(temp_dir)
        # Should only load .txt and .md
        assert len(docs) == 2
        contents = [d["content"] for d in docs]
        assert "Content 1" in contents
        assert "Content 2" in contents
