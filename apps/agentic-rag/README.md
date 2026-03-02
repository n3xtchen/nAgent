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

## 验证工具 (Validation Tool)

项目提供了一个通用的验证运行器 `validation_runner.py`，支持通过配置文件驱动的多维度评估。

### 运行验证
```bash
# 1. 使用默认配置运行 (calculator 验证)
uv run python -m agentic_rag.validation_runner

# 2. 指定验证场景和并发控制 (提高执行效率)
uv run python -m agentic_rag.validation_runner \
    --config examples/validation/calculator.json \
    --concurrency 5

# 3. 指定独立的数据集和文档库 (实现数据与配置解耦)
uv run python -m agentic_rag.validation_runner \
    --dataset examples/validation/calculator_dataset.json \
    --docs examples/validation/calculator_demo.json \
    --output outputs/custom_validation \
    --concurrency 3
```

### CLI 参数说明
- `--config`: 验证配置文件路径（默认：`examples/validation/calculator.json`）。
- `--dataset`: 独立测试集文件路径（JSON 格式）。若提供，将覆盖 config 中的 `test_cases`。
- `--docs`: 独立文档库文件路径（JSON 格式）。若未提供，默认从 config 同级目录查找。
- `--output`: 结果输出目录（默认：`outputs/results/validation`）。
- `--concurrency`: 并发测试用例数（默认：3）。在 API 配额受限时可设为 `1`。

### 验证指标
- **Correctness (准确性)**: 基于 LLM 裁判评估生成答案与参考答案的一致性。
- **Answer Relevance (相关性)**: 评估答案是否直接回答了原始问题。
- **Faithfulness (忠实性)**: 检查答案是否完全由检索到的文档支持（检测幻觉）。
- **Reasoning Steps (推理步数)**: Agent 完成任务所需的推理迭代步数。

### 输出说明
验证结果保存在指定目录：
- `validation_results.json`: 结构化详细数据，包含评分理由。
- `validation_results.csv`: 便于表格处理的简报。
- `traces/*.json`: 记录每个用例的完整推理步骤 (Trace ID 对应文件名)。

## 项目结构

- `src/agentic_rag/rag.py`: 核心编排逻辑，连接 Agent 和 Retriever。
- `src/agentic_rag/main.py`: CLI 入口。
- `example.py`: 演示如何注入文档并进行问答。

## 下一步计划 (Phase 2)

- 引入更多工具（WebSearch, Calculator）。
- 优化 Prompt 提升推理稳定性。
- 支持流式输出 Thought 过程。
