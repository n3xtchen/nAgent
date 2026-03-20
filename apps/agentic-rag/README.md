# Agentic RAG - Phase 1

这是 Agentic RAG 项目的第一阶段实现，重点在于建立基础的 Agent 循环（ReAct）并将其与检索工具（Retriever）集成。

## 功能特性

- **多 RAG 策略支持**: 支持基于大模型的简单 RAG (`SimpleRAG`) 和基于 Agent 的复杂 RAG (`AgenticRAG`)。
- **ReAct 智能体**: 使用 `nagent-core` 提供的 `ReActAgent` 进行多步推理。
- **检索集成**: 将 `nagent-rag` 的检索器封装为可调用的工具（对 Agentic RAG）。
- **可运行程序**: 提供 CLI 接口和示例脚本。

## 环境准备 (Environment Setup)

### 1. 安装依赖

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

## 开发流程 (Development Process)

### 评估流程 (Evaluation Process)

#### 第一步：数据准备与分块 (Document Chunking)

该工具可以将长文本文件（.md, .txt, .py 等）切分为较小的块，并保存为兼容 RAG 系统格式的 JSON 文件。

**基础用法 (端到端可执行示例):**

这里我们直接将本项目的 README 文件作为示例数据源进行切分：

```bash
uv run python -m agentic_rag.chunk_cli apps/agentic-rag/README.md --output demo_docs.json
```

**其他参数说明**

- `path`: 必填。要处理的文件或目录路径。
- `--chunk-size`: 分块大小（字符数，默认 1000）。
- `--chunk-overlap`: 相邻分块的重叠大小（字符数，默认 200）。
- `--output`: 输出 JSON 文件路径。如果未指定，结果将打印到控制台。
- `--recursive`: 如果路径是目录，是否递归搜索子目录。

#### 第二步：自动化测试集生成 (Dataset Generation)

项目提供了基于 Ragas 的自动化测试数据集生成工具，能够根据文档自动构建知识图谱并生成问答对（QA Pairs）。

**基础用法 (端到端可执行示例):**

*注意：生成多跳测试集需要文档之间有足够的关联度。简单的 README 文件可能会因为提取不到足够的关系而报错。因此，在这个示例中，我们使用项目自带的、内容更丰富的 `examples/demo_docs.json` 来生成测试集。*

```bash
uv run python apps/agentic-rag/src/agentic_rag/generate_dataset.py \
    --docs examples/demo_docs.json \
    --output demo_dataset.json \
    --size 2
```

**其他参数说明**

- `--docs`: 文档来源路径，支持单个文件 (.pdf, .txt, .md, .json) 或包含这些文件的目录。
- `--output`: 生成的测试集 JSON 文件保存路径。
- `--size`: 生成测试用例的数量 (默认: 10)。
- `--model`: 用于生成的 LLM 模型名称 (默认: `gemini-2.0-flash`)。

#### 第三步：测试验证 (Test Validation)

项目提供了一个通用的验证运行器 `validation_runner.py`，支持通过配置文件驱动的多维度评估。

**基础用法 (端到端可执行示例):**

这里我们直接运行项目内置的自包含（Self-contained）计算器验证配置。这个配置文件自带了测试文档和问题，可以直接运行看效果：

```bash
uv run python -m agentic_rag.validation_runner --config examples/validation/calculator.json
```

**其他验证方式与参数说明**

```bash
# 指定验证场景和并发控制 (提高执行效率)
uv run python -m agentic_rag.validation_runner \
    --config examples/validation/calculator.json \
    --concurrency 5

# 指定独立的数据集和文档库 (实现数据与配置解耦)
uv run python -m agentic_rag.validation_runner \
    --config examples/validation/calculator.json \
    --dataset demo_dataset.json \
    --docs demo_docs.json \
    --output outputs/custom_validation
```

**CLI 参数说明**

- `--config`: 验证配置文件路径 (**必填**)。
- `--dataset`: 独立测试集文件路径（JSON 格式）。若提供，将覆盖 config 中的 `test_cases`。
- `--docs`: 独立文档库文件路径（JSON 格式）。若提供，将优先使用；否则使用 config 中的 `rag_data`。
- `--output`: 结果输出目录（默认：`outputs/results/validation`）。
- `--concurrency`: 并发测试用例数（默认：3）。在 API 配额受限时可设为 `1`。
- `--rag_type`: 指定 RAG 实现类型 (`agentic`, `simple` 或 `vector`)，若指定则会覆盖配置文件中的默认设定。

**验证指标**

- **Correctness (准确性)**: 基于 LLM 裁判评估生成答案与参考答案的一致性。
- **Answer Relevance (相关性)**: 评估答案是否直接回答了原始问题。
- **Faithfulness (忠实性)**: 检查答案是否完全由检索到的文档支持（检测幻觉）。
- **Context Recall (上下文召回率)**: 通过提取 Trace 评估检索出的上下文对参考答案的覆盖率。
- **Reasoning Steps (推理步数)**: Agent 完成任务所需的推理迭代步数。

**输出说明**

验证结果保存在指定目录：
- `validation_results.json`: 结构化详细数据，包含评分理由。
- `validation_results.csv`: 便于表格处理的简报。
- `traces/*.json`: 记录每个用例的完整推理步骤 (Trace ID 对应文件名)。

### 生产应用 (Production Application)

#### 运行示例脚本

示例脚本预置了一些关于项目本身的文档，并演示了智能体如何检索这些信息来回答问题。这是了解系统如何通过代码初始化的最快方式：

```bash
uv run python apps/agentic-rag/src/example.py
```

#### 使用 CLI 交互

你可以通过命令行直接向智能体提问。注意：最新版本中，为了保证 RAG 系统的正常工作，**必须提供数据源**。

**基础用法 (端到端可执行示例):**

你可以直接复制以下命令，它会先将当前的 README.md 分块，然后启动 Agentic RAG 来回答关于本项目的问题：

```bash
# 1. 解析当前文档作为数据源
uv run python -m agentic_rag.chunk_cli apps/agentic-rag/README.md --output demo_docs.json

# 2. 指定数据源进行查询
uv run -m agentic_rag.main "这个项目支持哪些 RAG 策略？" --add-docs demo_docs.json
```

**高级用法 (指定 RAG 类型和其他选项):**

CLI 支持多种 RAG 策略 (`agentic`, `simple`, `vector`) 以及查询改写等高级功能：

- `agentic`: 多步推理、利用工具检索与计算。
- `simple`: 使用本地关键字检索分词库的单次直给模式。
- `vector`: 使用 ChromaDB 的语义向量检索的单次直给模式。

```bash
uv run -m agentic_rag.main "什么是 Agentic RAG？" \
    --add-docs my_docs.json \
    --rag-type agentic \
    --rewrite \
    --decompose
```

**CLI 参数说明:**

- `query`: 必填，你想要询问的问题。
- `--rag-type`: 指定 RAG 策略，可选值：`agentic` (默认), `simple`, `vector`。
- `--add-docs`: 包含要添加的文档的 JSON 文件路径 (使用 `chunk_cli` 生成)。
- `--index-path`: 保存或加载索引文件的路径。
- `--model`: 使用的 Gemini 模型名称。
- `--rewrite`: 开启查询重写 (Query Rewriting)。
- `--decompose`: 开启查询分解 (Query Decomposition)。
- `--trace-dir`: 保存推理 Trace 的目录。

## 项目结构

- `src/agentic_rag/rags/`: RAG 核心实现目录。
  - `base.py`: 基础 RAG 抽象类。
  - `agentic.py`: 基于 ReAct Agent 的复杂 RAG 实现 (支持多步推理与工具调用)。
  - `simple.py`: 传统的单次检索与生成 (Simple RAG) 实现，默认使用关键字检索。
  - `vector.py`: 基于 Chroma 的单次向量语义检索与生成实现 (无需 Agent 多步推理，直给式)。
- `src/agentic_rag/main.py`: CLI 入口。
- `src/agentic_rag/chunk_cli.py`: 文档分块工具 CLI。
- `example.py`: 演示如何注入文档并进行问答。

## 下一步计划 (Phase 2)

- 引入更多工具（WebSearch, Calculator）。
- 优化 Prompt 提升推理稳定性。
- 支持流式输出 Thought 过程。