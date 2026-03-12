import os
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class TextLoader:
    """
    负责从指定路径加载文本文件内容。
    """
    def __init__(self, supported_extensions: Optional[List[str]] = None):
        if supported_extensions is None:
            self.supported_extensions = [".txt", ".md", ".py", ".js", ".json", ".yaml", ".yml", ".html"]
        else:
            self.supported_extensions = supported_extensions

    def load(self, path: str, recursive: bool = True) -> List[Dict[str, Any]]:
        """
        加载文件或目录下的所有文本文件。
        """
        documents = []
        if os.path.isfile(path):
            doc = self._load_file(path)
            if doc:
                documents.append(doc)
        elif os.path.isdir(path):
            for root, _, files in os.walk(path):
                for file in files:
                    if any(file.endswith(ext) for ext in self.supported_extensions):
                        file_path = os.path.join(root, file)
                        doc = self._load_file(file_path)
                        if doc:
                            documents.append(doc)
                if not recursive:
                    break
        else:
            logger.warning(f"路径不存在: {path}")

        return documents

    def _load_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        读取单个文件的内容。
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            return {
                "content": content,
                "metadata": {
                    "source": file_path,
                    "filename": os.path.basename(file_path)
                }
            }
        except Exception as e:
            logger.error(f"无法读取文件 {file_path}: {e}")
            return None
