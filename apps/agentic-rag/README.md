# Agentic RAG - Phase 1

这是 Agentic RAG 项目的第一阶段实现，重点在于建立基础的 Agent 循环（ReAct）并将其与检索工具（Retriever）集成。

## 功能特性

- **ReAct 智能体**: 使用 `nagent-core` 提供的 `ReActAgent` 进行多步推理。
- **检索集成**: 将 `nagent-rag` 的检索器封装为智能体可调用的工具。
- **可运行程序**: 提供 CLI 接口和示例脚本。

## 快速开始

### 1. 环境准备

确保你已经安装了 `uv`。

克隆仓库后，在根目录下安装依赖：

```bash
uv sync
```

### 2. 配置 API Key

在根目录下创建 `.env` 文件（或在 `apps/agentic-rag/.env`），并添加你的 Gemini API Key：

```env
GEMINI_API_KEY=你的_GEMINI_API_KEY
```

### 3. 运行示例脚本

示例脚本预置了一些关于项目本身的文档，并演示了智能体如何检索这些信息来回答问题。

```bash
uv run python apps/agentic-rag/src/example.py
```

### 4. 使用 CLI 交互

你可以通过命令行直接向智能体提问：

```bash
uv run -m agentic_rag.main "什么是 Agentic RAG？"
```

## 项目结构

- `src/agentic_rag/rag.py`: 核心编排逻辑，连接 Agent 和 Retriever。
- `src/agentic_rag/main.py`: CLI 入口。
- `example.py`: 演示如何注入文档并进行问答。

## 下一步计划 (Phase 2)

- 引入更多工具（WebSearch, Calculator）。
- 优化 Prompt 提升推理稳定性。
- 支持流式输出 Thought 过程。
