# 验证框架快速参考

## 🚀 快速开始

### 1. 自动生成测试数据集 (推荐)
```bash
# 从文档目录生成 10 个测试用例
uv run python apps/agentic-rag/src/agentic_rag/generate_dataset.py \
  --docs my_docs_folder \
  --output my_dataset.json \
  --size 10
```

### 2. 运行默认验证程序
```bash
# 使用 calculator 验证集
uv run python -m agentic_rag.validation_runner \
  --config examples/validation/calculator.json
```

### 3. 使用自定义配置与并发控制
```bash
# 指定配置文件和并发数 (提高执行效率)
uv run python -m agentic_rag.validation_runner \
  --config examples/validation/my_custom_validation.json \
  --concurrency 5

# 指定独立的数据集和文档库 (实现数据与配置解耦)
uv run python -m agentic_rag.validation_runner \
  --config examples/validation/calculator.json \
  --dataset my_dataset.json \
  --docs my_docs_folder \
  --concurrency 3

# 指定输出目录和 RAG 类型 (agentic 或 simple)
uv run python -m agentic_rag.validation_runner \
  --output my_results_directory \
  --rag_type simple
```

### 3. 验证框架功能
```bash
# 运行框架完整性验证
uv run python verify_validation.py
```

## 📦 导入框架

### 基本导入
```python
from nagent_rag.validation import (
    ValidationConfig,
    ValidationRunner,
    ValidationResult,
    TestCase,
    MetricScore,
    MetricType,
    ValidationSummary,
    ValidationReport,
)
```

### 加载配置
```python
# 从配置文件加载
config = ValidationConfig.from_json('examples/validation/calculator.json')

# 从配置文件加载，但使用独立的测试集
config = ValidationConfig.from_json(
    'examples/validation/calculator.json',
    dataset_path='examples/validation/custom_dataset.json'
)
```

### 创建自定义验证程序
```python
from nagent_rag.validation import ValidationRunner, ValidationResult, MetricScore, MetricType

class MyValidator(ValidationRunner):
    async def run_test_case(self, test_case):
        # 执行具体验证逻辑 (例如调用 aquery)
        answer = "生成答案"

        metrics = {
            "my_metric": MetricScore(
                name="My Metric",
                value=4.5,
                metric_type=MetricType.CUSTOM,
            )
        }

        return ValidationResult(
            test_case_id=test_case.id,
            user_input=test_case.user_input,
            reference=test_case.reference,
            prediction=answer,
            metrics=metrics,
        )

# 运行验证，设置最大并发数为 5
# summary = await runner.run(max_concurrency=5)
```

## 📁 项目结构

```
nAgent/
├── libs/nagent-rag/src/nagent_rag/
│   ├── __init__.py                    (添加框架导出)
│   ├── validation.py                  (核心框架)
│   ├── eval.py
│   └── retriever.py
├── apps/agentic-rag/src/agentic_rag/
│   ├── validation_runner.py           (通用验证程序入口)
│   ├── main.py
│   └── rag.py
├── examples/
│   ├── validation/
│   │   ├── calculator.json            (自包含验证配置)
│   │   └── calculator_dataset.json    (独立数据集示例)
│   └── ...
├── docs/
│   ├── VALIDATION_FRAMEWORK.md        (详细文档)
│   ├── VALIDATION_QUICKSTART.md       (快速参考)
│   └── ...
├── verify_validation.py               (框架验证脚本)
└── README.md
```

## ⚙️ 配置文件格式

### 最小配置
```json
{
  "version": "1.0",
  "name": "验证程序名称",
  "description": "描述信息",
  "test_cases": [
    {
      "id": "test_1",
      "user_input": "问题",
      "reference": "答案"
    }
  ]
}
```

### 完整配置
```json
{
  "version": "1.0",
  "name": "验证程序名称",
  "description": "描述信息",
  "model_config": {
    "model_name": "gemini-2.0-flash",
    "max_iterations": 5
  },
  "rag_data": [
    {
      "id": "doc1",
      "content": "文档内容...",
      "metadata": {"source": "file.txt"}
    }
  ],
  "test_cases": [
    {
      "id": "test_1",
      "user_input": "问题文本",
      "reference": "参考答案",
      "docs_indices": ["doc1"],
      "description": "测试描述"
    }
  ],
  "metadata": {
    "created": "2026-03-01",
    "author": "作者名"
  }
}
```

## 📊 输出文件

验证程序运行后生成的文件：

```
outputs/
├── logs/
│   ├── validation.log                 # 验证程序日志
│   └── validation_framework.log       # 框架日志
└── results/
    └── validation/
        ├── validation_results.json     # JSON 格式结果 (包含指标理由)
        ├── validation_results.csv      # CSV 格式结果
        └── traces/                     # 推理过程 trace 日志 (支持异步持久化)
            ├── query_0.json
            ├── query_1.json
            └── ...
```

### validation_results.json 结构
```json
{
  "config": {
    "name": "验证程序名称",
    "description": "描述",
    "version": "1.0"
  },
  "summary": {
    "total_tests": 5,
    "passed_tests": 4,
    "failed_tests": 1,
    "pass_rate": 80.0,
    "metrics_average": {
      "correctness": 4.2,
      "relevance": 4.0
    }
  },
  "results": [
    {
      "test_case_id": "test_1",
      "prediction": "生成答案",
      "metrics": {
        "correctness": {
          "name": "Correctness",
          "value": 4.5,
          "metric_type": "correctness",
          "reason": "评分理由文本"
        }
      }
    }
  ]
}
```

## 🔍 指标类型

框架支持的指标类型：

| 类型 | 说明 | 范围 |
|------|------|------|
| CORRECTNESS | 答案准确性 | 0-5 |
| RELEVANCE | 答案相关性 | 0-5 |
| FAITHFULNESS | 答案忠实性 (检测幻觉) | 0-5 |
| CONTEXT_RECALL | 上下文召回率 (评估检索质量) | 0-1 |
| REASONING_STEPS | 推理步数 | >= 0 |
| CUSTOM | 自定义指标 | 自定义 |

## 🛠️ 常见任务

### 创建新的验证场景

1. **创建配置文件** (examples/validation/my_task.json)
```json
{
  "version": "1.0",
  "name": "My Task Validation",
  "description": "Validate my task",
  "test_cases": [...]
}
```

2. **创建验证程序** (在你的项目中)
```python
from nagent_rag.validation import ValidationRunner

class MyTaskValidator(ValidationRunner):
    async def run_test_case(self, test_case):
        # 实现验证逻辑
        pass

async def main():
    config = ValidationConfig.from_json('examples/validation/my_task.json')
    runner = MyTaskValidator(config)
    summary = await runner.run(max_concurrency=3)
    runner.save_results_json()
```

### 保存和共享配置

```python
# 保存配置
config.to_json('examples/validation/my_validation.json')

# 加载共享的配置
config = ValidationConfig.from_json('examples/validation/my_validation.json')
```

### 查看日志

```bash
# 查看所有日志
tail -f outputs/logs/*.log

# 查看验证程序日志
tail -f outputs/logs/validation.log

# 搜索日志
grep "ERROR" outputs/logs/*.log
grep "✓" outputs/logs/*.log
```

## ❓ FAQ

**Q: 如何修改测试用例？**
A: 编辑相应的 JSON 配置文件，或使用 `--dataset` 参数指定独立的数据集文件。

**Q: 如何提高验证效率？**
A: 使用 `--concurrency N` 参数（如 `--concurrency 5`）开启并发验证。

**Q: 为什么 traces 目录是空的？**
A: 确保在初始化 `AgenticRAG` 时指定了 `trace_dir` 参数。

---

**最后更新**: 2026-03-02
**框架版本**: 1.1 (增强版)
