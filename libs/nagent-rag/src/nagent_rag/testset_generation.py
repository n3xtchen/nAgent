
import logging
import uuid
import json
import asyncio
import numpy as np
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from dataclasses import asdict

from ragas.testset import TestsetGenerator as RagasTestsetGen
from ragas.testset.graph import KnowledgeGraph, Node, NodeType
from ragas.testset.transforms import apply_transforms, default_transforms, default_transforms_for_prechunked
from ragas.llms import BaseRagasLLM
from ragas.embeddings import BaseRagasEmbeddings
from langchain_core.documents import Document
from langchain_text_splitters import TokenTextSplitter

from .validation import TestCase
from .eval import GoogleGenAIWrapper

logger = logging.getLogger(__name__)

class TestsetGenerator(ABC):
    """Abstract base class for testset generators."""

    @abstractmethod
    async def generate(self, documents: List[Document], testset_size: int, **kwargs) -> List[TestCase]:
        """Generate test cases from documents."""
        pass

class RagasTestsetGenerator(TestsetGenerator):
    """Ragas-based testset generator."""

    def __init__(
        self,
        generator_llm: BaseRagasLLM,
        embeddings: BaseRagasEmbeddings,
        chunk_size: int = 1000,
        chunk_overlap: int = 100
    ):
        self.generator_llm = generator_llm
        self.embeddings = embeddings
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap


    async def generate(self, documents: List[Document], testset_size: int, **kwargs) -> List[TestCase]:
        """Generate test cases using Ragas."""
        from .eval import generate_testset

        # 1. Prepare Nodes for Knowledge Graph
        nodes = []
        content_to_index = {}

        # If documents are already chunked (e.g. from JSON), we might want to respect that.
        # But Ragas expects specific node structure.

        # Check if we need to split
        # We assume input documents are already "chunks" or "pages" from the JSON loader
        # But to be safe and consistent with Ragas, we might re-split or ensure they are proper nodes.

        # In the reference implementation, it splits documents using TokenTextSplitter
        text_splitter = TokenTextSplitter(chunk_size=self.chunk_size, chunk_overlap=self.chunk_overlap)
        splits = text_splitter.split_documents(documents)

        for i, split in enumerate(splits):
            clean_content = split.page_content.strip()
            content_to_index[clean_content] = i

            nodes.append(
                Node(
                    type=NodeType.CHUNK,
                    properties={
                        "page_content": split.page_content,
                        "filename": split.metadata.get("source", ""),
                        "page_number": split.metadata.get("page", 0),
                        "doc_id": str(i)
                    }
                )
            )

        logger.info(f"✓ Prepared {len(nodes)} nodes for generation")

        # 2. Apply Transforms (Required for Ragas 0.2.x)
        # Ragas requires nodes to be enriched with transforms (Summary, Keyphrases, etc.)
        # for the synthesizer to work.

        # Create KG first
        kg = KnowledgeGraph(nodes=nodes)

        logger.info("🔄 Applying default transforms (this may take a while)...")
        # Since we pre-chunked the documents, use the appropriate transforms
        transforms = default_transforms_for_prechunked(llm=self.generator_llm, embedding_model=self.embeddings)
        apply_transforms(kg, transforms)
        logger.info("✓ Transforms applied")

        # 3. Build Knowledge Graph (Save it)
        # Use a temporary path for KG
        kg_path = f"temp_kg_{uuid.uuid4()}.json"
        kg.save(kg_path)

        try:
            # 4. Generate Testset
            logger.info(f"🚀 Generating testset (size={testset_size})...")

            # generate_testset from eval.py is a wrapper around ragas.testset.generate
            ragas_dataset = generate_testset(
                generator_llm=self.generator_llm,
                embeddings=self.embeddings,
                kg_path=kg_path,
                testset_size=testset_size,
                run_config=kwargs.get("run_config")
            )

            # 5. Convert to TestCase
            test_cases = []
            df = ragas_dataset.to_pandas()

            for idx, row in df.iterrows():
                question = row.get("user_input") or row.get("question")
                answer = row.get("reference") or row.get("ground_truth") or row.get("answer")
                contexts = row.get("reference_contexts") or row.get("contexts") or []
                eval_type = row.get("eval_type", "")

                # Convert contexts to docs_indices and preserve hop sequence
                docs_indices = []
                source_context_indices = []
                if isinstance(contexts, list) or isinstance(contexts, np.ndarray):
                    # Handle numpy array if pandas returns it
                    ctx_list = contexts.tolist() if hasattr(contexts, 'tolist') else list(contexts)
                    for ctx in ctx_list:
                        if isinstance(ctx, str):
                            clean_ctx = ctx.strip()
                            matched_idx = None

                            import re
                            hop_label = ""
                            hop_match = re.match(r'^(<\d+-hop>)\s*', clean_ctx)
                            if hop_match:
                                hop_label = hop_match.group(1)
                                search_ctx = clean_ctx[len(hop_match.group(0)):].strip()
                            else:
                                search_ctx = clean_ctx

                            if search_ctx in content_to_index:
                                matched_idx = content_to_index[search_ctx]
                                docs_indices.append(matched_idx)
                            else:
                                # Fuzzy match: check if ctx is substring of content or vice versa
                                # This is O(N*M) which is slow for large docs, but okay for small datasets
                                found = False
                                for content, idx in content_to_index.items():
                                    if search_ctx in content or content in search_ctx:
                                        docs_indices.append(idx)
                                        matched_idx = idx
                                        found = True
                                        break
                                if not found:
                                     # Last resort: try to match by partial string
                                     pass

                            if matched_idx is not None:
                                if hop_label:
                                    source_context_indices.append(f"{hop_label} {matched_idx}")
                                else:
                                    source_context_indices.append(matched_idx)
                            else:
                                source_context_indices.append(ctx)
                        else:
                            source_context_indices.append(ctx)

                # Deduplicate and sort
                docs_indices = sorted(list(set(docs_indices)))

                tc = TestCase(
                    id=str(uuid.uuid4()),
                    user_input=str(question),
                    reference=str(answer),
                    docs_indices=docs_indices,
                    description=f"Generated by Ragas ({eval_type})",
                    metadata={
                        "source_context": source_context_indices,
                        "eval_type": str(eval_type)
                    }
                )
                test_cases.append(tc)

            return test_cases

        finally:
            if Path(kg_path).exists():
                try:
                    Path(kg_path).unlink()
                except Exception as e:
                    logger.warning(f"Failed to delete temp file {kg_path}: {e}")

def load_rag_data(path: Union[str, Path]) -> List[Document]:
    """Load RAG data from JSON or other formats."""
    from langchain_community.document_loaders import PyPDFLoader, TextLoader, UnstructuredMarkdownLoader

    path = Path(path)
    documents = []

    if path.is_file():
        if path.suffix.lower() == ".json":
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if isinstance(data, list):
                for item in data:
                    content = item.get("page_content", "")
                    metadata = item.get("metadata", {})
                    # Ensure metadata is dict
                    if not isinstance(metadata, dict):
                        metadata = {}
                    documents.append(Document(page_content=content, metadata=metadata))
            else:
                logger.warning(f"JSON file {path} does not contain a list.")
        elif path.suffix.lower() == ".pdf":
             loader = PyPDFLoader(str(path))
             documents.extend(loader.load())
        elif path.suffix.lower() == ".txt":
             loader = TextLoader(str(path))
             documents.extend(loader.load())
        elif path.suffix.lower() == ".md":
             loader = UnstructuredMarkdownLoader(str(path))
             documents.extend(loader.load())
    elif path.is_dir():
        files = list(path.glob("**/*"))
        for file_path in files:
            if file_path.name.startswith("."): # Skip hidden files
                continue
            if file_path.is_file():
                try:
                    # Recursive call for single file
                    docs = load_rag_data(file_path)
                    documents.extend(docs)
                except Exception as e:
                    logger.warning(f"Failed to load file {file_path}: {e}")

    logger.info(f"Loaded {len(documents)} documents from {path}")
    return documents
