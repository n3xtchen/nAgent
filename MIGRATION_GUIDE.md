# 项目重新组织 - 迁移指南

## 📌 概览

本项目已完成了验证工具的重新组织和通用化。如果您有现有代码需要适配新的结构，请按本指南进行更新。

---

## 🔧 迁移步骤

### 1. 更新导入语句

#### 核心框架导入（无需改动）
```python
# ✓ 这些导入保持不变
from nagent_rag.validation import (
    ValidationConfig,
    ValidationRunner,
    ValidationResult,
    TestCase,
    MetricScore,
    MetricType,
)
```

#### 验证程序导入（需更新）
```python
# ❌ 旧方式（不再有效）
from apps.agentic_rag.tests.calculator_validation_runner import CalculatorValidationRunner

# ✅ 新方式
from agentic_rag.validation_runner import AgenticRAGValidationRunner
```

---

### 2. 更新配置文件路径

#### 默认配置路径
```python
# ❌ 旧路径
config = ValidationConfig.from_json('examples/validation_calculator.json')

# ✅ 新路径
config = ValidationConfig.from_json('examples/validation/calculator.json')
```

#### 自定义配置路径
```python
# ❌ 旧示例
runner = MyValidator(
    config=config,
    config_path='examples/my_validation.json'
)

# ✅ 新示例
runner = MyValidator(
    config=config,
    config_path='examples/validation/my_validation.json'
)
```

---

### 3. 更新演示数据路径

#### 演示数据加载
```python
# ❌ 旧方式
demo_path = Path("examples/calculator_demo.json")

# ✅ 新方式（推荐）
demo_path = Path("examples/validation/calculator_demo.json")

# ✅ 旧方式仍可用（向后兼容）
demo_path = Path("examples/calculator_demo.json")
```

---

### 4. 更新命令行调用

#### 运行验证程序

```bash
# ❌ 旧命令
uv run python apps/agentic-rag/tests/calculator_validation_runner.py
uv run python apps/agentic-rag/tests/calculator_validation_runner.py \
  --config examples/validation_calculator.json

# ✅ 新命令（推荐）
uv run python -m agentic_rag.validation_runner
uv run python -m agentic_rag.validation_runner \
  --config examples/validation/calculator.json

# ✅ 新命令（备选）
uv run python apps/agentic-rag/src/agentic_rag/validation_runner.py
uv run python apps/agentic-rag/src/agentic_rag/validation_runner.py \
  --config examples/validation/calculator.json
```

#### 验证框架

```bash
# ❌ 旧命令
uv run python verify_validation_framework.py

# ✅ 新命令
uv run python verify_validation.py
```

---

### 5. 更新类名引用

#### 继承和使用

```python
# ❌ 旧方式
class MyCustomValidator(CalculatorValidationRunner):
    async def run_test_case(self, test_case):
        # ...

# ✅ 新方式
class MyCustomValidator(AgenticRAGValidationRunner):
    async def run_test_case(self, test_case):
        # ...
```

---

## 📝 配置文件迁移

### 如果您有自定义配置文件

1. **创建新的配置文件位置**
   ```bash
   mkdir -p examples/validation
   ```

2. **移动或复制您的配置文件**
   ```bash
   # 假设您有自定义配置 my_validation.json
   cp examples/my_validation.json examples/validation/my_validation.json
   ```

3. **更新配置文件中的路径引用**
   ```json
   {
     "version": "1.0",
     "name": "My Custom Validation",
     "description": "...",
     "model_config": { ... },
     "test_cases": [
       {
         "id": "test_1",
         "user_input": "...",
         "reference": "...",
         // 如果有文件路径引用，确保相对路径正确
       }
     ]
   }
   ```

4. **更新代码中的路径**
   ```python
   # ❌ 旧路径
   config = ValidationConfig.from_json('examples/my_validation.json')

   # ✅ 新路径
   config = ValidationConfig.from_json('examples/validation/my_validation.json')
   ```

---

## 🔍 常见问题

### Q: 旧的 calculator_demo.json 还能用吗？

**A**: 可以。为了向后兼容，我们在 `examples/` 目录中保留了 `calculator_demo.json`。但建议使用新位置的 `examples/validation/calculator_demo.json`。

### Q: 我的代码中有硬编码的旧路径，怎么办？

**A**: 有三种方案：
1. 更新所有硬编码路径为新路径（推荐）
2. 保留旧路径，因为 `examples/calculator_demo.json` 仍然存在
3. 使用环境变量或配置文件管理路径

### Q: 如何创建新的验证场景？

**A**: 按以下步骤：
1. 在 `examples/validation/` 目录下创建新的配置文件（如 `qa.json`）
2. 创建对应的验证程序类（继承 `AgenticRAGValidationRunner` 或 `ValidationRunner`）
3. 实现 `run_test_case()` 方法
4. 运行验证：`uv run python your_validator.py --config examples/validation/qa.json`

### Q: 框架 API 有改变吗？

**A**: 没有。`nagent_rag.validation` 模块的 API 完全保持不变。只有文件位置和命名有所调整。

### Q: 我应该更新我的项目吗？

**A**: 取决于以下因素：
- ✅ **应该更新**：如果您计划创建多个验证场景
- ✅ **应该更新**：如果您想遵循新的项目结构规范
- ⚠️ **可以不更新**：如果您只有简单的单一验证使用场景，旧代码仍可用
- ❌ **必须更新**：如果您依赖导入 `CalculatorValidationRunner`

### Q: 升级会影响现有的验证结果吗？

**A**: 不会。验证框架本身的功能和行为完全相同。输出格式和结果也保持一致。

---

## 📚 相关文档

| 文档 | 位置 | 说明 |
|------|------|------|
| 详细框架文档 | `docs/VALIDATION_FRAMEWORK.md` | 框架设计和完整 API |
| 快速参考 | `docs/VALIDATION_QUICKSTART.md` | 常见使用示例 |
| 变更汇总 | `REORGANIZATION_SUMMARY.md` | 详细的变更列表 |
| 对比分析 | `IMPLEMENTATION_COMPARISON.md` | 前后对比和改进说明 |
| 项目首页 | `README.md` | 项目概览和快速开始 |

---

## ✅ 迁移检查清单

在完成迁移后，请检查以下内容：

- [ ] 更新了所有 import 语句
- [ ] 更新了所有配置文件路径
- [ ] 更新了所有命令行调用
- [ ] 更新了所有硬编码的文件路径
- [ ] 运行了验证脚本确保一切正常
- [ ] 更新了相关文档和注释
- [ ] 测试了验证程序的运行
- [ ] 确认了向后兼容性需求
- [ ] 更新了 CI/CD 脚本（如有）
- [ ] 通知了团队成员新的项目结构

---

## 🚀 快速迁移检查

```bash
# 验证新文件已创建
ls apps/agentic-rag/src/agentic_rag/validation_runner.py && echo "✓ 验证程序位置正确"

# 验证新配置文件位置
ls examples/validation/calculator.json && echo "✓ 配置文件位置正确"

# 验证文档已更新
ls docs/VALIDATION_FRAMEWORK.md && echo "✓ 文档位置正确"

# 运行验证脚本
uv run python verify_validation.py && echo "✓ 框架完整性验证通过"
```

---

## 📞 获得帮助

- 查看 `docs/VALIDATION_FRAMEWORK.md` 了解框架详细信息
- 查看 `docs/VALIDATION_QUICKSTART.md` 查看代码示例
- 运行 `uv run python -m agentic_rag.validation_runner --help` 查看命令行帮助
- 查看项目的 Git 历史了解具体变更

---

**迁移指南版本**: 1.0
**发布日期**: 2026-03-01
**更新日期**: 2026-03-01
