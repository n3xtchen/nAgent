from typing import List, Dict, Any, Optional

class RecursiveCharacterTextSplitter:
    """
    递归字符切分器。
    优先在自然边界（换行、空格等）切分，以尽可能保持语义完整性。
    """
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        separators: Optional[List[str]] = None
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", " ", ""]

    def split_text(self, text: str) -> List[str]:
        """
        将文本切分为块。
        """
        return self._recursive_split(text, self.separators)

    def _recursive_split(self, text: str, separators: List[str]) -> List[str]:
        """
        核心递归切分逻辑。
        """
        final_chunks = []

        # 如果文本已经足够小，直接返回
        if len(text) <= self.chunk_size:
            return [text]

        # 选择当前的切分符
        separator = separators[-1]
        new_separators = []
        for i, s in enumerate(separators):
            if s in text:
                separator = s
                new_separators = separators[i+1:]
                break

        # 按当前切分符切分
        if separator:
            splits = text.split(separator)
        else:
            # 如果没有切分符（即空字符串分隔），则按字符切分
            splits = list(text)

        # 重新组合这些片段，尽量填满 chunk_size
        current_doc = []
        total_len = 0

        for s in splits:
            if total_len + len(s) + (len(separator) if current_doc else 0) <= self.chunk_size:
                current_doc.append(s)
                total_len += len(s) + (len(separator) if current_doc else 0)
            else:
                if current_doc:
                    doc_content = separator.join(current_doc)
                    if len(doc_content) > self.chunk_size:
                        # 如果单个片段就超标了，递归深入切分
                        final_chunks.extend(self._recursive_split(doc_content, new_separators))
                    else:
                        final_chunks.append(doc_content)

                    # 处理重叠 (overlap)
                    # 简单实现：保留尾部内容作为重叠部分
                    # 这里的 overlap 处理可以更精细，这里采用基础策略
                    while current_doc and total_len > self.chunk_overlap:
                        removed = current_doc.pop(0)
                        total_len -= len(removed) + len(separator)

                current_doc.append(s)
                total_len += len(s) + (len(separator) if len(current_doc) > 1 else 0)

        if current_doc:
            doc_content = separator.join(current_doc)
            if len(doc_content) > self.chunk_size:
                final_chunks.extend(self._recursive_split(doc_content, new_separators))
            else:
                final_chunks.append(doc_content)

        return final_chunks

    def split_documents(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        切分带有元数据的文档列表。
        """
        chunked_docs = []
        for doc in documents:
            content = doc.get("content", "")
            metadata = doc.get("metadata", {}).copy()

            chunks = self.split_text(content)
            for i, chunk in enumerate(chunks):
                chunk_metadata = metadata.copy()
                chunk_metadata["chunk_index"] = i
                # 生成全局唯一的 ID，如果原文档有 ID 则作为前缀，否则直接用索引
                doc_id = doc.get("id", "doc")
                final_id = f"{doc_id}_{i}" if "id" in doc else str(len(chunked_docs))

                chunked_docs.append({
                    "id": final_id,
                    "content": chunk,
                    "metadata": chunk_metadata
                })
        return chunked_docs
