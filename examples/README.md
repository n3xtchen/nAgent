# Examples

这个目录用于存储演示数据和示例文件。

## Demo 数据

- `demo_docs.json`: 包含关于 Project Pig 和 nAgent 的基础文档分片，适用于 `agentic-rag` 应用。
- `calculator_demo.json`: 包含数值和费用信息，专门用于测试 Agent 的计算能力（`CalculatorTool`）。

## 如何使用

你可以使用以下命令运行 `agentic-rag` 并加载这些 demo 数据：

```bash
uv run -m agentic_rag.main "Project Pig 的核心目标是什么？" --add-docs examples/demo_docs.json --index-path my_index.json
```

### 常用查询示例

1. **基本查询**：`"Project Pig 的核心目标是什么？"`
2. **技术细节**：`"nagent-core 提供了哪些基类？"`
3. **功能特性**：`"Agentic RAG 和传统 RAG 有什么区别？"`
4. **路线图**：`"Project Pig 2.0 计划什么时候发布？"`

### 计算器工具示例

你可以使用 `calculator_demo.json` 来测试 Agent 的计算能力：

```bash
uv run -m agentic_rag.main "Project Pig 的年度总预算是多少？" --add-docs examples/calculator_demo.json --index-path my_index.json
```

**更多计算查询：**
1. `"如果我为公司购买 150 个 nAgent 席位，享受折扣后的月总费用是多少？"`
2. `"Agentic RAG 查询中，检索和生成两个阶段的耗时占比分别是多少？"`
