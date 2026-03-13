# Agentic RAG - Phase 1

这是 Agentic RAG 项目的第一阶段实现，重点在于建立基础的 Agent 循环（ReAct）并将其与检索工具（Retriever）集成。

## 功能特性

- **多 RAG 策略支持**: 支持基于大模型的简单 RAG (`SimpleRAG`) 和基于 Agent 的复杂 RAG (`AgenticRAG`)。
- **ReAct 智能体**: 使用 `nagent-core` 提供的 `ReActAgent` 进行多步推理。
- **检索集成**: 将 `nagent-rag` 的检索器封装为可调用的工具（对 Agentic RAG）。
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

## 验证工具 (Validation Tool)

项目提供了一个通用的验证运行器 `validation_runner.py`，支持通过配置文件驱动的多维度评估。

### 运行验证
```bash
# 1. 使用默认配置运行 (calculator 验证)
uv run python -m agentic_rag.validation_runner \
    --config examples/validation/calculator.json

# 2. 指定验证场景和并发控制 (提高执行效率)
uv run python -m agentic_rag.validation_runner \
    --config examples/validation/calculator.json \
    --concurrency 5

# 3. 指定独立的数据集和文档库 (实现数据与配置解耦)
uv run python -m agentic_rag.validation_runner \
    --config examples/validation/calculator.json \
    --dataset examples/validation/custom_dataset.json \
    --docs examples/validation/custom_docs.json \
    --output outputs/custom_validation \
    --concurrency 3
```

### CLI 参数说明
- `--config`: 验证配置文件路径 (**必填**)。
- `--dataset`: 独立测试集文件路径（JSON 格式）。若提供，将覆盖 config 中的 `test_cases`。
- `--docs`: 独立文档库文件路径（JSON 格式）。若提供，将优先使用；否则使用 config 中的 `rag_data`。
- `--output`: 结果输出目录（默认：`outputs/results/validation`）。
- `--concurrency`: 并发测试用例数（默认：3）。在 API 配额受限时可设为 `1`。
- `--rag_type`: 指定 RAG 实现类型 (`agentic` 或 `simple`)，若指定则会覆盖配置文件中的默认设定。

### 验证指标
- **Correctness (准确性)**: 基于 LLM 裁判评估生成答案与参考答案的一致性。
- **Answer Relevance (相关性)**: 评估答案是否直接回答了原始问题。
- **Faithfulness (忠实性)**: 检查答案是否完全由检索到的文档支持（检测幻觉）。
- **Context Recall (上下文召回率)**: 通过提取 Trace 评估检索出的上下文对参考答案的覆盖率。
- **Reasoning Steps (推理步数)**: Agent 完成任务所需的推理迭代步数。

### 输出说明
验证结果保存在指定目录：
- `validation_results.json`: 结构化详细数据，包含评分理由。
- `validation_results.csv`: 便于表格处理的简报。
- `traces/*.json`: 记录每个用例的完整推理步骤 (Trace ID 对应文件名)。

## 自动化测试集生成 (Dataset Generation)

项目提供了基于 Ragas 的自动化测试数据集生成工具，能够根据文档自动构建知识图谱并生成问答对（QA Pairs）。

### 使用方法

```bash
uv run python apps/agentic-rag/src/agentic_rag/generate_dataset.py \
    --docs <文档路径> \
    --output <输出文件路径> \
    --size <生成数量>
```

### 参数说明

- `--docs`: 文档来源路径，支持单个文件 (.pdf, .txt, .md, .json) 或包含这些文件的目录。
- `--output`: 生成的测试集 JSON 文件保存路径 (e.g., `tests/data/generated_testset.json`)。
- `--size`: 生成测试用例的数量 (默认: 10)。
- `--model`: 用于生成的 LLM 模型名称 (默认: `gemini-2.0-flash`)。

### 输出格式

生成的 JSON 文件包含 `TestCase` 对象列表，每个对象包含：
- `user_input`: 生成的问题。
- `reference`: 参考答案。
- `docs_indices`: 引用文档的索引列表。
- `metadata`: 包含源上下文（包括多跳 n-hop 标识）和评估类型（如 reasoning, conditioning 等）。

生成过程已引入 `DiskCacheBackend` 以复用 API 调用结果，大幅提升生成速度。这个生成的数据集可以直接用于 `validation_runner` 进行自动化评估。

## 项目结构

- `src/agentic_rag/rags/`: RAG 核心实现目录。
  - `base.py`: 基础 RAG 抽象类。
  - `agentic.py`: 基于 ReAct Agent 的复杂 RAG 实现。
  - `simple.py`: 传统的单次检索与生成 (Simple RAG) 实现。
- `src/agentic_rag/main.py`: CLI 入口。
- `src/agentic_rag/chunk_cli.py`: 文档分块工具 CLI。
- `example.py`: 演示如何注入文档并进行问答。

## 工具: 文档分块 (Document Chunking)

该工具可以将长文本文件（.md, .txt, .py 等）切分为较小的块，并保存为兼容 RAG 系统格式的 JSON 文件。

### 使用方法

```bash
uv run python -m agentic_rag.chunk_cli <路径> [选项]
```

### 参数说明

- `path`: 必填。要处理的文件或目录路径。
- `--chunk-size`: 分块大小（字符数，默认 1000）。
- `--chunk-overlap`: 相邻分块的重叠大小（字符数，默认 200）。
- `--output`: 输出 JSON 文件路径。如果未指定，结果将打印到控制台。
- `--recursive`: 如果路径是目录，是否递归搜索子目录。

### 示例

```bash
# 处理目录并保存到文件
uv run python -m agentic_rag.chunk_cli ./docs --recursive --output my_docs.json

# 处理单个文件并配置分块大小
uv run python -m agentic_rag.chunk_cli README.md --chunk-size 500 --chunk-overlap 50
```

## 下一步计划 (Phase 2)

- 引入更多工具（WebSearch, Calculator）。
- 优化 Prompt 提升推理稳定性。
- 支持流式输出 Thought 过程。
