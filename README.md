# nAgent

个人智能代理项目。

## 项目结构

项目采用 `uv` workspace 进行管理，分为应用 (`apps/`) 和库 (`libs/`)。

### 核心库 (`libs/`)

- **`nagent-core`**: 核心代理逻辑，包含 `ReActAgent` 和工具基类。
- **`nagent-rag`**: RAG 相关组件，包含各类 Retriever 和检索工具封装。

### 应用 (`apps/`)

- **`agentic-rag`**: 基于智能体循环的 RAG 应用，支持自主检索决策。
- **`nagent`**: (旧版/其他) 代理应用。

## 快速开始

1. 安装依赖:
   ```bash
   uv sync
   ```

2. 运行测试:
   ```bash
   uv run pytest
   ```

## 文档

- [Agentic RAG 设计文档 (PRD)](docs/PRD_Agentic_RAG.md)
