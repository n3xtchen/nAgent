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

## Agentic RAG 验证工具

项目包含通用的验证框架，用于支持配置文件驱动的验证工作流。

### 快速验证

```bash
# 运行默认验证程序（使用 examples/validation/calculator.json）
uv run python -m agentic_rag.validation_runner

# 指定自定义配置文件
uv run python -m agentic_rag.validation_runner --config examples/validation/calculator.json

# 指定输出目录
uv run python -m agentic_rag.validation_runner --output my_output_dir
```

### 验证框架完整性

```bash
# 运行框架验证脚本
uv run python verify_validation.py
```

### 更多信息

- [验证框架详细文档](docs/VALIDATION_FRAMEWORK.md)
- [验证框架快速参考](docs/VALIDATION_QUICKSTART.md)
- [验证框架源代码](libs/nagent-rag/src/nagent_rag/validation.py)

## 文档

- [Agentic RAG 设计文档 (PRD)](docs/PRD_Agentic_RAG.md)
- [验证框架文档](docs/VALIDATION_FRAMEWORK.md)
- [验证框架快速参考](docs/VALIDATION_QUICKSTART.md)
