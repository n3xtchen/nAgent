# nagent-rag

RAG (Retrieval-Augmented Generation) components for nAgent.

## Features

- **BaseRetriever**: Standard interface for all retrieval implementations.
- **SimpleKeywordRetriever**: Keyword-based search using simple tokenization or jieba.
- **RetrieverTool**: A tool wrapper that allows agents to use any retriever.
- **QueryRewriter**: Utilities for refining and expanding search queries.
