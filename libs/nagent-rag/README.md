# nagent-rag

RAG (Retrieval-Augmented Generation) components for nAgent.

## Features

- **BaseRetriever**: Standard interface for all retrieval implementations.
- **SimpleKeywordRetriever**: Keyword-based search using simple tokenization or jieba.
- **RetrieverTool**: A tool wrapper that allows agents to use any retriever.
- **QueryRewriter**: Utilities for refining and expanding search queries.
- **TestsetGenerator**: Automated test dataset generation using Ragas, supporting Knowledge Graph construction, n-hop context extraction, `DiskCacheBackend` for faster generation, decoupled model dependencies via `get_ragas_models`, and seamless TestCase export.
