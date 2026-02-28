# Agentic RAG 产品设计文档 (PRD)

## 1. 产品背景与定位

### 1.1 背景
传统的 Simple RAG 系统主要依赖于“检索-增强-生成”的线性流程。虽然在处理简单查询时效果良好，但在面对复杂任务（如多步推理、含糊不清的查询、跨文档对比等）时，往往表现不佳。

### 1.2 定位
**Agentic RAG** 旨在通过引入“智能体 (Agent)”概念，将检索过程从被动的流程执行转变为主动的自主决策。它具备查询重写、多步检索、自反思以及工具化调用的能力，能够像人类专家一样处理复杂的信息检索和整合任务。

## 2. 核心功能定义

### 2.1 智能查询理解
- **查询重写 (Query Rewriting)**：将用户原始、可能含糊的自然语言查询改写为更适合搜索引擎或向量数据库检索的关键词或短语。
- **查询拆解 (Query Decomposition)**：将复杂的组合问题拆分为多个子问题，逐个解决后再进行汇总。

### 2.2 检索工具化 (Retrieval as a Tool)
- 将不同的检索源（如本地向量库、网络搜索、数据库查询）封装为 Agent 可调用的工具。
- Agent 根据当前任务的上下文，自主决定调用哪种工具以及调用的参数。

### 2.3 思考循环 (Reasoning Loop)
- **ReAct 模式**：遵循 "Reasoning + Acting" 循环，在每一步行动前先进行思考，执行后观察结果并调整后续策略。
- **多步推理**：能够根据前一步检索到的信息，动态生成下一步的检索请求，直至收集到足够的信息回答问题。

### 2.4 自反思与评估 (Self-Reflection)
- **结果验证**：在生成最终答案前，自我检查检索到的信息是否足以支撑回答，或检查生成的答案是否符合事实。
- **反馈闭环**：如果初次检索结果质量较差，Agent 能够自动触发重试逻辑或调整检索参数。

## 3. 数据接入与存储 (Data Ingestion & Storage)

### 3.1 数据接入 (Data Ingestion)
- **预处理说明**：系统假定文档已经由外部工具完成切分（Chunking）和基础清洗，本项目核心关注点在于 Agent 的决策与检索应用。
- **接入接口**：提供标准接口接收 JSON 格式的文档分片（Chunks）列表。
- **数据结构规范**：
  ```json
  {
    "id": "string",          // 唯一标识符
    "content": "string",     // 文档正文内容
    "metadata": {            // 扩展元数据
      "source": "string"     // 来源（如文件名）
    }
  }
  ```

### 3.2 存储与索引 (Storage & Indexing)
- **内存存储**：运行时使用内存存储预处理后的文档分片，确保 Agent 快速访问。
- **文件持久化**：支持将内存中的索引状态保存为本地文件（如 JSON）。应用重启时，可快速从本地文件加载知识库状态，无需重新接入。
- **轻量级搜索**：基于内存索引提供高效的关键词检索（BM25），后续可扩展至本地向量计算。

## 4. 应用集成 (Application Integration)

### 4.1 Agent 调用流程
1. **意图判断**：Agent 接收查询，判断是否需要外部知识。
2. **工具调用**：Agent 调用 `Retriever` 工具访问内存存储或已加载的持久化索引。
3. **结果整合**：Agent 整合检索结果，决定是继续检索还是生成最终答案。

### 4.2 开发者接口 (Python API)
- `rag.add_documents(chunks)`：动态推送到 RAG 系统。
- `rag.save_index(file_path)`：持久化当前索引到磁盘。
- `rag.load_index(file_path)`：从磁盘加载索引。

### 4.3 示例场景
开发者可以将处理好的 JSON 格式文档加载到系统，Agent 即可针对这些本地数据进行专业问答。

## 5. 系统架构

### 5.1 模块化设计
系统分为三个核心层次：
1.  **Agent Core**: 负责意图识别、决策调度和对话上下文管理。基于 `nagent-core` 构建。
2.  **RAG Tools**: 包含各种 Retriever（向量检索、关键词检索、混合检索等）。基于 `nagent-rag` 构建。
3.  **Application Layer**: `apps/agentic-rag` 作为最终的集成应用，提供 API 或 UI 接口。

### 5.2 接口规范
- 扩展 `BaseRetriever` 接口，使其支持更复杂的元数据过滤和参数化配置。
- 统一工具调用协议，确保 Agent 可以无缝切换不同的检索后端。

## 6. 演进路线图 (Roadmap)

### Phase 1: 基础构建 (Foundation - 已完成)
*   **核心 Agent 循环**：实现基于 `ReAct` (Thought-Action-Observation) 的 `ReActAgent` 推理循环。
*   **基础工具抽象**：定义 `BaseTool` 接口，规范化工具定义与调用方式。
*   **单工具集成**：将现有的 `nagent-rag` 检索功能封装为 `RetrieverTool`。
*   **编排层实现**：在 `apps/agentic-rag` 中完成 Agent 与 Retriever 的初步集成。
*   **可运行程序**：提供 CLI 入口点和示例脚本，支持端到端的基础问答流程。

### Phase 2: 本地化与持久化 (Localization & Persistence)
*   **文件存储支持**：实现基于本地文件的索引保存与读取功能，支持应用状态持久化。
*   **多文档管理**：增强数据接入能力，支持多来源、大规模文档分片的内存管理。
*   **多工具支持 (Multi-tools)**：新增 WebSearch、Calculator 或代码执行工具，实现 Agent 的多工具选择与组合能力。
*   **高级 RAG 逻辑集成**：实现 Agent 触发的查询拆解 (Query Decomposition) 和自主查询改写逻辑。

### Phase 3: 生产级优化与评估 (Production & Evaluation)
*   **评估与监控 (Evaluation & Monitoring)**：集成 RAGAS 评估框架，建立 Trace 追踪机制，量化推理轨迹与回答质量。
*   **系统鲁棒性增强**：完善错误处理机制（如 LLM 超时、工具调用失败重试），确保生产环境下的稳定性。
*   **提示词工程优化 (Prompt Engineering)**：针对生产场景优化 Agent 推理模版，减少幻觉并提升回答的专业性。

## 7. 评估与质量控制

### 7.1 评估指标体系

Agentic RAG 系统采用 4 个核心评估指标来全面衡量 RAG 系统的质量。这些指标由位于 `libs/nagent-rag/src/nagent_rag/eval.py` 的评估框架库提供，确保评估的一致性和可复用性。

#### 7.1.1 准确性 (Correctness) - 0~5 分

**定义**：评估生成答案与参考答案之间的一致程度，即答案的事实正确性。

**评估维度**：
- **事实正确性**：陈述的信息是否真实准确
- **关键信息完整性**：答案是否涵盖了参考答案的所有重要信息点
- **语义一致性**：表达的意思是否准确，是否有逻辑错误

**评分参考**：
- **5 分**：完美。答案完全准确、完整，涵盖所有关键信息，无任何错误
- **4 分**：很好。基本准确，涵盖主要信息，缺少一些 minor 细节或附加信息
- **3 分**：一般。有一些错误或重要信息遗漏，但基本意思表达准确
- **2 分**：较差。有多个错误或重要信息缺失，但不是完全错误
- **1 分**：很差。错误明显且影响理解，基本不准确
- **0 分**：完全错误或无关

**重要性**：准确性是最直接的质量指标，衡量答案的事实基础。

#### 7.1.2 忠实性 (Faithfulness) - 0~5 分

**定义**：评估生成的答案是否完全由检索到的文档内容支持，防止模型产生幻觉 (Hallucination)。这是 RAG 系统特别关键的指标。

**评估要点**：
- **答案的每个陈述**是否都能在检索到的上下文中找到明确的依据
- **不超出文档范围**：即使某信息在现实世界中是正确的，如果超出检索文档，也属于幻觉
- **指出幻觉的具体部分**：明确指出哪些陈述是文档中没有提及的

**评分参考**：
- **5 分**：完全忠实。答案的每一个陈述都有文档中的明确依据，零幻觉
- **4 分**：基本忠实。大部分陈述有依据，仅有非必要的自主拓展内容
- **3 分**：部分忠实。有部分陈述有依据，但包含一些超出文档的信息
- **2 分**：大部分不忠实。超出文档的内容占大多数
- **1 分**：严重幻觉。大部分陈述无依据
- **0 分**：完全幻觉。答案与文档内容无关或完全是编造的

**重要性**：忠实性在 RAG 系统中权重最高，因为 RAG 的核心目标就是避免幻觉，确保答案基于真实文档。

#### 7.1.3 相关性 (Answer Relevance) - 0~5 分

**定义**：评估生成的答案与原始用户问题之间的匹配程度，确保 Agent 没有答非所问。

**评估维度**：
- **问题回答度**：答案是否直接回答了用户的问题
- **信息冗余性**：是否包含与问题无关或冗余的信息
- **针对性**：答案是否针对问题的具体内容

**评分参考**：
- **5 分**：高度相关且直接。完全针对问题，无任何冗余信息，表达清晰精准
- **4 分**：相关。主要内容针对问题，有少量冗余或附加信息
- **3 分**：一般相关。回答了问题，但包含较多不必要的信息或补充
- **2 分**：相关度低。答案有所偏离，仅部分相关
- **1 分**：很不相关。答案主要不相关，仅涉及问题的某个方面
- **0 分**：完全不相关或答非所问

**重要性**：相关性防止 Agent 生成虽然"正确"但"跑题"的答案，确保用户体验。

#### 7.1.4 推理步数 (Reasoning Steps) - 1~20 步

**定义**：统计 Agent 完成一个查询任务所需的推理迭代步骤数，衡量 Agent 的推理效率。

**计算方式**：
- 从 Agent 执行轨迹 (Trace) 中统计行动步骤总数
- 每一次 Thought-Action-Observation 循环计为 1 步
- 最终生成答案算作 1 步

**评分参考**（推荐的效率指标）：
- **1~3 步**：✓ **优秀**。推理高效，快速找到答案，避免不必要的重复查询
- **4~5 步**：△ **良好**。正常的多步推理，在合理范围内
- **6~20 步**：✗ **需要优化**。推理过程冗长，可能存在逻辑问题或频繁重复查询

**优化目标**：减少推理步数可以改善用户体验和系统效率，同时反映 Agent 的决策能力。

### 7.2 评估框架实现

#### 7.2.1 框架选择与架构

Agentic RAG 采用 **RAGAS + 自定义 LLM Judge** 的评估架构：

- **RAGAS (RAG Assessment)**：行业标准的 RAG 评估框架，提供指标定义和聚合逻辑
- **LLM Judge**：使用 Google Gemini 作为"裁判"，通过 LLM 的推理能力评估答案质量
- **中文支持**：所有评估 Prompt 均设计为中文优先，同时支持英文回答选项

**库位置**：`libs/nagent-rag/src/nagent_rag/eval.py`

#### 7.2.2 核心类和函数

```python
class GoogleGenAIWrapper(BaseRagasLLM)
```
- Ragas 专用的 LLM 适配器，封装 Google GenAI API 调用
- 支持同步 (`generate_text`) 和异步 (`agenerate_text`) 接口
- 自动添加中文回答提示

```python
async def correctness_metric.ascore(
    user_input: str,
    reference: str,
    prediction: str,
    client,
    model_name: str = "gemini-2.0-flash"
) -> MetricResult
```
- 异步计算准确性评分
- 返回 `MetricResult` 对象，包含 `value` (0-5) 和 `reason` (评分理由)

```python
async def faithfulness_metric.ascore(
    context: str,
    prediction: str,
    client,
    model_name: str = "gemini-2.0-flash"
) -> MetricResult
```
- 异步计算忠实性评分，检测幻觉

```python
async def answer_relevance_metric.ascore(
    user_input: str,
    prediction: str,
    client,
    model_name: str = "gemini-2.0-flash"
) -> MetricResult
```
- 异步计算相关性评分

```python
async def reasoning_steps_metric.ascore(
    trace: Optional[List[Dict[str, Any]]]
) -> MetricResult
```
- 同步计算推理步数（基于 Agent 执行轨迹）

```python
async def run_experiment(
    row: Dict,
    rag_client,
    eval_client,
    eval_model: str = "gemini-2.0-flash"
) -> Dict
```
- 运行单个样本的完整评测实验
- 返回包含所有 4 个指标的评估结果字典

```python
async def run_evaluation(
    dataset_name: str,
    rag_client,
    eval_client,
    root_dir: str = "./ragas_data",
    eval_model: str = "gemini-2.0-flash"
) -> ExperimentResult
```
- 批量评测完整数据集并保存结果

### 7.3 评估工具使用指南

#### 7.3.1 导入方式

```python
from nagent_rag.eval import (
    GoogleGenAIWrapper,
    correctness_metric,
    faithfulness_metric,
    answer_relevance_metric,
    reasoning_steps_metric,
    run_experiment,
    run_evaluation,
)
```

#### 7.3.2 单项指标评估

**示例：评估单个答案的准确性**

```python
import asyncio
from google import genai
from nagent_rag.eval import correctness_metric

async def evaluate_answer():
    api_key = "your-gemini-api-key"
    client = genai.Client(api_key=api_key)

    result = await correctness_metric.ascore(
        user_input="Project Pig 的年度预算是多少？",
        reference="Project Pig 的年度预算是 1,000,000 元。",
        prediction="根据文档，Project Pig 的预算分为：研发 500,000 元、推广 200,000 元、运维 150,000 元、行政 50,000 元，总计 900,000 元。",
        client=client,
        model_name="gemini-2.0-flash"
    )

    print(f"准确性评分: {result.value:.1f}/5.0")
    print(f"评分理由: {result.reason}")

asyncio.run(evaluate_answer())
```

**输出示例**：
```
准确性评分: 4.5/5.0
评分理由: 答案提供了分项信息并计算了总额，非常完整。参考答案只给出了总额，实际回答更详细，但如果题目要求的就是总额可认为超出范围。
```

#### 7.3.3 多指标评估单个样本

**示例：完整评测一个问题**

```python
import asyncio
from google import genai
from nagent_rag.eval import (
    correctness_metric,
    faithfulness_metric,
    answer_relevance_metric,
    reasoning_steps_metric,
)

async def evaluate_sample():
    client = genai.Client(api_key="your-api-key")

    test_sample = {
        "user_input": "nAgent 企业版按 100 个席位购买需要多少月费？",
        "reference": "100 个席位 × 29 美元 = 2,900 美元/月",
        "prediction": "nAgent 企业版的定价为每用户 29 美元/月。如果购买 100 个席位，则每月费用为 100 × 29 = 2,900 美元。",
        "context": "nAgent 企业版: 29 美元/用户/月，100+ 用户享受 15% 折扣",
        "trace": [
            {"action": "retrieve", "observation": "found pricing info"},
            {"action": "calculate", "observation": "computed 100 * 29 = 2900"}
        ]
    }

    # 评估 4 个指标
    c_result = await correctness_metric.ascore(
        user_input=test_sample["user_input"],
        reference=test_sample["reference"],
        prediction=test_sample["prediction"],
        client=client
    )

    f_result = await faithfulness_metric.ascore(
        context=test_sample["context"],
        prediction=test_sample["prediction"],
        client=client
    )

    r_result = await answer_relevance_metric.ascore(
        user_input=test_sample["user_input"],
        prediction=test_sample["prediction"],
        client=client
    )

    s_result = await reasoning_steps_metric.ascore(
        trace=test_sample["trace"]
    )

    # 输出结果
    print("=" * 60)
    print("评估结果")
    print("=" * 60)
    print(f"准确性 (Correctness):   {c_result.value:.1f}/5.0  | {c_result.reason}")
    print(f"忠实性 (Faithfulness):  {f_result.value:.1f}/5.0  | {f_result.reason}")
    print(f"相关性 (Answer Relevance): {r_result.value:.1f}/5.0  | {r_result.reason}")
    print(f"推理步数 (Reasoning Steps): {s_result.value:.0f} 步  | {s_result.reason}")

asyncio.run(evaluate_sample())
```

**输出示例**：
```
============================================================
评估结果
============================================================
准确性 (Correctness):   5.0/5.0  | 答案与参考答案完全一致，准确无误
忠实性 (Faithfulness):  5.0/5.0  | 所有陈述都能在上下文中找到依据
相关性 (Answer Relevance): 5.0/5.0  | 答案直接针对问题，完全相关
推理步数 (Reasoning Steps): 2 步  | 共执行了 2 个推理步骤
```

#### 7.3.4 批量评测数据集

**示例：使用 Agentic RAG 和评估框架进行批量评测**

```python
import asyncio
import json
from pathlib import Path
from google import genai
from agentic_rag.rag import AgenticRAG
from nagent_rag.retriever import SimpleKeywordRetriever
from nagent_rag.eval import (
    correctness_metric,
    faithfulness_metric,
    answer_relevance_metric,
    reasoning_steps_metric,
)

async def batch_evaluate_rag(test_cases_file: str):
    """批量评测 Agentic RAG 系统"""

    # 初始化 RAG 系统
    client = genai.Client(api_key="your-api-key")

    with open(test_cases_file, 'r', encoding='utf-8') as f:
        test_cases = json.load(f)

    # 初始化检索器和 RAG
    retriever = SimpleKeywordRetriever()
    doc_contents = [doc["content"] for doc in test_cases.get("documents", [])]
    retriever.fit(doc_contents)

    rag = AgenticRAG(
        client=client,
        retriever=retriever,
        model_name="gemini-2.0-flash",
        max_iterations=5
    )

    # 运行评测
    results = []
    metrics_summary = {
        "correctness": [],
        "faithfulness": [],
        "answer_relevance": [],
        "reasoning_steps": []
    }

    for test_case in test_cases["test_cases"]:
        print(f"评测: {test_case['id']}")

        # 执行 RAG 查询
        rag_result = await rag.aquery(test_case["user_input"])
        answer = rag_result["answer"]
        trace = rag_result.get("trace", [])

        # 计算 4 个指标
        c_result = await correctness_metric.ascore(
            user_input=test_case["user_input"],
            reference=test_case["reference"],
            prediction=answer,
            client=client
        )
        metrics_summary["correctness"].append(c_result.value)

        f_result = await faithfulness_metric.ascore(
            context=test_case.get("context", ""),
            prediction=answer,
            client=client
        )
        metrics_summary["faithfulness"].append(f_result.value)

        r_result = await answer_relevance_metric.ascore(
            user_input=test_case["user_input"],
            prediction=answer,
            client=client
        )
        metrics_summary["answer_relevance"].append(r_result.value)

        s_result = await reasoning_steps_metric.ascore(trace=trace)
        metrics_summary["reasoning_steps"].append(s_result.value)

        results.append({
            "test_id": test_case["id"],
            "user_input": test_case["user_input"],
            "prediction": answer,
            "correctness": c_result.value,
            "faithfulness": f_result.value,
            "answer_relevance": r_result.value,
            "reasoning_steps": s_result.value,
        })

    # 生成评估报告
    print("\n" + "=" * 60)
    print("评估报告")
    print("=" * 60)

    avg_correctness = sum(metrics_summary["correctness"]) / len(metrics_summary["correctness"])
    avg_faithfulness = sum(metrics_summary["faithfulness"]) / len(metrics_summary["faithfulness"])
    avg_relevance = sum(metrics_summary["answer_relevance"]) / len(metrics_summary["answer_relevance"])
    avg_steps = sum(metrics_summary["reasoning_steps"]) / len(metrics_summary["reasoning_steps"])

    print(f"平均准确性:   {avg_correctness:.2f}/5.0")
    print(f"平均忠实性:   {avg_faithfulness:.2f}/5.0")
    print(f"平均相关性:   {avg_relevance:.2f}/5.0")
    print(f"平均推理步数: {avg_steps:.2f}")

    # 保存详细结果
    with open("rag_evaluation_report.json", 'w', encoding='utf-8') as f:
        json.dump({
            "summary": {
                "total_tests": len(results),
                "avg_correctness": avg_correctness,
                "avg_faithfulness": avg_faithfulness,
                "avg_answer_relevance": avg_relevance,
                "avg_reasoning_steps": avg_steps,
            },
            "details": results
        }, f, ensure_ascii=False, indent=2)

    print("\n✓ 报告已保存到 rag_evaluation_report.json")

# 执行批量评测
# asyncio.run(batch_evaluate_rag("test_cases.json"))
```

### 7.4 评估指标关键性说明

#### 7.4.1 指标权重与优先级

在 RAG 系统中，这 4 个指标的重要性顺序为：

| 排序 | 指标 | 权重 | 原因 |
|-----|------|------|------|
| 1 | 忠实性 (Faithfulness) | **40%** | RAG 的核心目标是避免幻觉，确保答案基于真实文档。忠实性失败则其他指标无意义 |
| 2 | 准确性 (Correctness) | **35%** | 衡量答案的事实正确程度，直接影响系统可用性 |
| 3 | 相关性 (Answer Relevance) | **20%** | 确保答案针对问题，防止答非所问 |
| 4 | 推理步数 (Reasoning Steps) | **5%** | 衡量效率，不直接影响答案质量但影响用户体验 |

#### 7.4.2 关键指标说明

**为什么忠实性最重要？**

在 RAG 系统中，用户信任系统的前提是相信答案来自真实文档。如果系统产生幻觉，即使答案看起来"正确"，也会严重损害可信度。典型场景：

- ❌ 错误：系统编造出"Project Pig 的预算是 200 万元"，这在现实中可能是对的，但如果文档中没提到，就是幻觉
- ✓ 正确：系统只说"根据文档，Project Pig 的预算包括…"，即使总额不完全准确，也更诚实

**为什么准确性次之？**

准确性衡量答案的事实基础。如果忠实性有保证，准确性的衡量就很直接了：
- 答案是否与参考答案一致
- 是否包含所有关键信息
- 是否有逻辑或计算错误

**相关性的作用？**

相关性防止"偏离"：即使答案完全忠实和准确，如果答非所问，用户仍然无法得到帮助。例如：
- 问："nAgent 的定价是多少？"
- 错误答案："nAgent 是一个 AI Agent 框架，由…开发。" （虽然事实正确但不相关）
- 正确答案："nAgent 企业版定价为 29 美元/用户/月。" （直接相关）

**推理步数反映效率**

推理步数是 Agent 能力的窗口：
- **1~3 步**：Agent 决策准确，快速定位问题，高效检索
- **4~5 步**：正常多步推理，可接受
- **6+ 步**：可能存在问题，需要优化 Agent 逻辑或 Prompt

### 7.5 评估最佳实践

#### 7.5.1 数据集准备

评估需要标准化的测试数据集，格式如下：

```json
{
  "test_cases": [
    {
      "id": "test_001",
      "user_input": "问题内容",
      "reference": "参考答案或标准答案",
      "context": "评估忠实性时的检索文档内容（可选）"
    }
  ]
}
```

#### 7.5.2 持续评估流程

建议定期运行评估以跟踪系统质量：

1. **开发阶段**：在修改 Agent Prompt 或检索逻辑后立即运行评估
2. **部署前**：使用完整测试集验证新版本的所有指标
3. **上线后**：建立自动化评估流程，定期采样用户查询进行评估
4. **问题诊断**：当指标下降时，分析具体样本找出根本原因

#### 7.5.3 指标改进建议

| 指标 | 改进方向 |
|------|--------|
| 忠实性 ↓ | 优化检索逻辑、增强 Prompt 中的约束条件 |
| 准确性 ↓ | 改进 Agent 的计算能力、优化推理逻辑 |
| 相关性 ↓ | 改进查询理解、优化 Agent 的意图判断 |
| 推理步数 ↑ | 优化 Agent 决策逻辑、减少不必要的重复查询 |

## 8. 待办与未来展望 (Backlog & Future Work)

本章节记录了计划在更远期实现的高级功能与优化方向：

*   **外部向量数据库集成**：引入如 Milvus、Pinecone 或 Weaviate 等专业向量数据库支持，以应对海量数据的索引与高性能检索需求。
*   **长效记忆管理 (Advanced Memory)**：探索基于数据库的对话状态存储，引入 ConversationSummary 或集群记忆，支持更长周期的复杂多轮对话。
*   **高并发性能优化**：全面重构为异步架构（Async/Parallel），支持在单轮推理中产生并并行执行多个 Action，显著降低端到端响应延迟。
*   **多模态检索支持**：研究如何将图片、表格等多模态信息纳入 Agent 的检索与决策范畴。
