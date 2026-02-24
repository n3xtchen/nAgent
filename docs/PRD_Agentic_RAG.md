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

### Phase 3: 生产级优化与长效管理 (Production & Optimization)
*   **向量数据库集成**：引入外部向量数据库支持，应对更大规模的数据检索需求。
*   **长效记忆 (Memory)**：引入对话上下文管理（如 ConversationBuffer/Summary），支持多轮复杂对话。
*   **性能优化**：全面实现异步并发调用（Async/Parallel），支持单轮产生多个并行 Action。
*   **评估与监控 (Evaluation & Monitoring)**：集成 RAGAS 评估框架，建立 Trace 追踪机制，量化推理轨迹与回答质量。

## 7. 评估与质量控制

### 7.1 衡量指标
- **答案准确率 (Answer Accuracy)**：针对基准测试集的回答准确程度。
- **检索相关性 (Retrieval Relevance)**：检索出的 Top-K 文档与问题的相关度。
- **推理步数 (Reasoning Steps)**：衡量 Agent 解决问题的效率，避免陷入无限循环。

### 7.2 评估工具
- 使用 RAGAS 或类似框架进行自动化评估。
- 建立人工反馈数据集，持续微调 Prompt 策略。
