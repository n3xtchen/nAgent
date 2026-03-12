from typing import List, Dict, Any, Optional
from .document_loaders import TextLoader
from .text_splitter import RecursiveCharacterTextSplitter

class ChunkingProcessor:
    """
    结合 Loader 和 Splitter，提供一键式分块处理功能。
    """
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        supported_extensions: Optional[List[str]] = None
    ):
        self.loader = TextLoader(supported_extensions=supported_extensions)
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )

    def process_path(self, path: str, recursive: bool = True) -> List[Dict[str, Any]]:
        """
        加载路径下的文件并进行分块。
        """
        raw_docs = self.loader.load(path, recursive=recursive)
        return self.splitter.split_documents(raw_docs)

    def process_texts(self, texts: List[str]) -> List[Dict[str, Any]]:
        """
        对给定的文本列表进行分块。
        """
        raw_docs = [{"content": text, "metadata": {}} for text in texts]
        return self.splitter.split_documents(raw_docs)
