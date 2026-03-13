# 通用验证程序框架实现完成

## 📋 概述

已成功实现了一个**通用的验证程序框架**，用于支持配置文件驱动的验证工作流。该框架不仅限于 calculator 验证，可扩展支持多种验证场景。

## 🏗️ 架构设计

### 核心组件

#### 1. **ValidationConfig** - 验证配置数据模型
- 支持从 JSON 文件加载配置
- 包含：名称、描述、版本、模型配置、测试用例列表
- 支持保存配置为 JSON 文件（便于版本控制和共享）
- **支持解耦加载**：可以通过 `dataset_path` 参数独立加载测试用例，覆盖配置文件中的默认值。

```python
# 从配置文件加载
config = ValidationConfig.from_json('examples/validation/calculator.json')

# 从配置文件加载，但使用独立的测试集
config = ValidationConfig.from_json(
    'examples/validation/calculator.json',
    dataset_path='examples/validation/custom_dataset.json'
)
```

#### 2. **TestCase** - 测试用例数据模型
- 字段：id, user_input, reference, docs_indices, description, metadata
- 支持从字典创建，便于 JSON 反序列化
- 包含文档索引信息，支持多文档验证

#### 3. **TestsetGenerator** - 自动化测试集生成器
- **基于 Ragas**: 集成 Ragas 框架，利用 LLM 自动构建知识图谱
- **自动生成**: 从文档直接生成高质量问答对 (QA Pairs)
- **多跳(hop)上下文**: 支持正则解析并在元数据中保留多跳上下文标识
- **缓存优化**: 引入 `DiskCacheBackend` 替代原有的封装，并使用原生 `GoogleEmbeddings` 以避免重复调用提升速度
- **格式兼容**: 生成结果直接输出为 `TestCase` 格式，无缝接入验证框架
- **场景覆盖**: 支持推理 (Reasoning)、条件 (Conditioning)、多上下文 (Multi-context) 等多种评估类型

#### 4. **ValidationRunner** - 通用验证程序基类
- 可扩展的抽象基类，子类需实现 `run_test_case()` 方法
- 完整的验证流程管理：初始化、循环、汇总、报告生成
- **并发执行支持**：`run()` 方法支持 `max_concurrency` 参数，通过 `asyncio.Semaphore` 实现并发控制。
- 支持异步执行，高效处理 I/O 密集操作

```python
class MyValidator(ValidationRunner):
    async def run_test_case(self, test_case):
        # 实现具体验证逻辑 (例如调用 aquery)
        return ValidationResult(...)

# 运行验证，设置最大并发数为 5
summary = await runner.run(max_concurrency=5)
```

#### 4. **ValidationResult** - 验证结果数据模型
- 存储单个测试用例的执行结果
- 包含：用户输入、参考答案、生成答案、多个评估指标、错误信息等
- 支持序列化为字典（用于 JSON/CSV 输出）

#### 5. **MetricScore** - 评估指标得分
- 支持多种指标类型：Correctness, Relevance, Faithfulness, Reasoning Steps, Context Recall
- 每个指标包含：名称、数值、指标类型、解释原因

#### 6. **ValidationSummary** - 验证总结
- 自动计算统计数据：平均值、最小值、最大值
- 包含：通过数、失败数、通过率、总耗时

#### 7. **ValidationReport** - 报告生成器
- 支持多种输出格式：JSON、CSV、文本
- 自动生成详细的验证报告

## 📁 文件清单

### 新增文件

| 文件 | 位置 | 说明 |
|-----|------|------|
| `validation.py` | `libs/nagent-rag/src/nagent_rag/` | **核心框架模块**（470 行代码） |
| `validation/calculator.json` | `examples/` | **Calculator 验证配置文件** |
| `validation_runner.py` | `apps/agentic-rag/src/agentic_rag/` | **改进的验证程序**（使用新框架） |
| `testset_generation.py` | `libs/nagent-rag/src/nagent_rag/` | **自动化测试集生成模块** (基于 Ragas) |
| `generate_dataset.py` | `apps/agentic-rag/src/agentic_rag/` | **测试集生成脚本** |
| `verify_validation.py` | 项目根目录 | **框架验证脚本** |

### 修改的文件

| 文件 | 位置 | 改动 |
|-----|------|------|
| `__init__.py` | `libs/nagent-rag/src/nagent_rag/` | 添加验证框架类的导出 |

### 删除的文件

| 文件 | 说明 |
|-----|------|
| `apps/agentic-rag/tests/calculator_validation_runner.py` | 已移至 src/agentic_rag/ 并通用化 |
| `examples/validation_calculator.json` | 已移至 examples/validation/ |

## 🚀 使用指南

### 基本使用

#### 1. 加载配置文件
```python
from nagent_rag.validation import ValidationConfig

config = ValidationConfig.from_json('examples/validation/calculator.json')
print(f"配置名称: {config.name}")
print(f"测试用例数: {len(config.test_cases)}")
```

#### 2. 创建自定义验证程序
```python
from nagent_rag.validation import ValidationRunner, ValidationResult, MetricScore, MetricType

class MyValidator(ValidationRunner):
    async def run_test_case(self, test_case):
        # 实现具体验证逻辑
        result = # ... 执行验证
        metrics = {
            "custom_metric": MetricScore(
                name="Custom Metric",
                value=4.5,
                metric_type=MetricType.CUSTOM,
            )
        }

        return ValidationResult(
            test_case_id=test_case.id,
            user_input=test_case.user_input,
            reference=test_case.reference,
            prediction=result,
            metrics=metrics,
        )
```

#### 3. 运行验证程序
```python
async def main():
    runner = MyValidator(config)
    summary = await runner.run()
    runner.print_summary(summary)
    runner.save_results_json()
    runner.save_results_csv()

asyncio.run(main())
```

### 命令行使用

```bash
# 使用默认配置（examples/validation/calculator.json）
uv run python -m agentic_rag.validation_runner

# 指定自定义配置文件
uv run python -m agentic_rag.validation_runner --config examples/validation/my_validation.json

# 指定输出目录
uv run python -m agentic_rag.validation_runner --output my_output_dir

# 组合使用 (同时指定 RAG 类型)
uv run python -m agentic_rag.validation_runner --config examples/validation/my_validation.json --output results --rag_type simple
```

## 📊 配置文件格式

```json
{
  "version": "1.0",
  "name": "验证程序名称",
  "description": "验证程序描述",
  "model_config": {
    "model_name": "gemini-2.0-flash",
    "max_iterations": 5
  },
  "test_cases": [
    {
      "id": "test_id_1",
      "user_input": "用户问题",
      "reference": "参考答案",
      "docs_indices": [0, 1],
      "description": "测试用例描述"
    }
  ],
  "metadata": {
    "created": "2026-03-01",
    "author": "Team Name"
  }
}
```

## ✨ 关键特性

### 1. **配置文件驱动**
- ✓ 从 JSON 文件加载测试用例
- ✓ 支持保存配置文件（版本控制）
- ✓ 易于扩展新的验证场景

### 2. **灵活的指标系统**
- ✓ 支持多种预定义指标（Correctness, Relevance, Faithfulness, Reasoning Steps, Context Recall）
- ✓ 支持自定义指标
- ✓ 自动计算指标统计（平均、最小、最大）

### 3. **可扩展架构**
- ✓ 抽象基类 `ValidationRunner` 易于继承
- ✓ 支持不同的验证场景（不仅限于 calculator）
- ✓ 模块化的报告生成器

### 4. **完整的报告功能**
- ✓ JSON 格式输出（结构化数据）
- ✓ CSV 格式输出（便于数据分析）
- ✓ 文本报告生成

### 5. **命令行支持**
- ✓ `--config` 参数指定配置文件
- ✓ `--output` 参数指定输出目录
- ✓ `--rag_type` 参数动态切换 RAG 实现 (`agentic` 或 `simple`)
- ✓ 详细的命令行帮助

## 📈 输出文件示例

运行验证程序后生成的输出文件：

```
outputs/
├── logs/
│   ├── validation.log                  # 验证程序日志
│   └── validation_framework.log        # 框架日志
└── results/
    └── validation/
        ├── validation_results.json     # 结构化结果（包含指标详情）
        ├── validation_results.csv      # CSV 格式（便于 Excel 分析）
        └── traces/                     # 推理过程 trace 日志
            ├── query_0.json
            ├── query_1.json
            └── ...
```

## 🧪 验证方法

已创建了验证脚本来验证框架的完整性：

```bash
uv run python verify_validation.py
```

日志输出位置：`logs/validation_framework_verify.log`

验证项目：
1. ✓ 配置文件加载
2. ✓ 测试用例结构
3. ✓ 数据模型序列化
4. ✓ 配置保存与加载
5. ✓ 支持文件完整性
6. ✓ 命令行参数支持

## 🎯 实现总结

| 需求项 | 状态 | 说明 |
|--------|------|------|
| 通用验证框架 | ✅ 完成 | `validation.py` - 核心框架 |
| 配置文件驱动 | ✅ 完成 | `examples/validation/calculator.json` |
| 通用验证程序 | ✅ 完成 | `validation_runner.py` - 支持多种场景 |
| 框架可扩展性 | ✅ 完成 | 支持创建多种验证场景 |
| 报告生成 | ✅ 完成 | JSON、CSV、文本格式 |

## 🔮 未来扩展

框架支持以下扩展场景：

1. **创建新的验证程序**
   ```python
   class DocumentValidationRunner(ValidationRunner):
       async def run_test_case(self, test_case):
           # 文档验证逻辑
           pass
   ```

2. **创建新的配置文件**
   ```
   examples/validation/document.json
   examples/validation/qa.json
   examples/validation/summarization.json
   ```

3. **集成更多评估指标**
   - BERTScore
   - ROUGE
   - BLEU
   - 自定义指标

4. **可视化仪表板**
   - 实时验证进度
   - 指标对比展示
   - 历史趋势分析

## 📝 代码质量

- ✓ 完整的类型注解
- ✓ 详细的文档字符串
- ✓ 模块化设计
- ✓ 异步/等待支持
- ✓ 错误处理完善
- ✓ 日志记录详细

---

**实现日期**: 2026-03-01
**框架版本**: 1.0
**文档版本**: 2.0
