import os
import json
from datetime import datetime
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

from nagent_rag.retriever import BaseRetriever


class BaseRAG(ABC):
    """
    RAG 基类。
    定义了通用的接口和 Trace 存储等通用逻辑。
    """
    def __init__(
        self,
        client,
        retriever: BaseRetriever,
        model_name: str = "gemini-2.0-flash",
        trace_dir: Optional[str] = None,
        index_path: Optional[str] = None,
    ):
        self.client = client
        self.retriever = retriever
        self.model_name = model_name
        self.trace_dir = trace_dir
        self.index_path = index_path

        if self.trace_dir and not os.path.exists(self.trace_dir):
            os.makedirs(self.trace_dir)

        # 如果提供了索引路径且文件存在，则加载
        if self.index_path and os.path.exists(self.index_path):
            self.retriever.load_index(self.index_path)

    def _save_trace(self, user_input: str, response: Dict[str, Any]):
        """
        持久化保存推理轨迹。
        """
        if not self.trace_dir:
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        trace_id = f"trace_{timestamp}"
        file_path = os.path.join(self.trace_dir, f"{trace_id}.json")

        trace_data = {
            "trace_id": trace_id,
            "timestamp": datetime.now().isoformat(),
            "user_input": user_input,
            "answer": response.get("answer"),
            "trace": response.get("trace", [])
        }

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(trace_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Failed to save trace: {e}")

    @abstractmethod
    def query(self, user_input: str) -> Dict[str, Any]:
        """
        处理用户查询，需返回形如 {"answer": "...", "trace": [...]} 的字典。
        """
        pass

    @abstractmethod
    async def aquery(self, user_input: str) -> Dict[str, Any]:
        """
        处理用户查询 (异步)，需返回形如 {"answer": "...", "trace": [...]} 的字典。
        """
        pass

    def save_index(self, path: Optional[str] = None):
        """
        保存索引。
        """
        target_path = path or self.index_path
        if not target_path:
            raise ValueError("未指定保存路径。")
        self.retriever.save_index(target_path)

    def clear_index(self):
        """
        清空现有索引和文档。
        """
        self.retriever.documents = []
        if self.index_path and os.path.exists(self.index_path):
            os.remove(self.index_path)

    def add_documents(self, documents: List[Dict[str, Any]]):
        """
        添加新文档。
        """
        # 合并现有文档
        existing_docs = self.retriever.documents
        existing_docs.extend(documents)
        self.retriever.fit(existing_docs)
