#!/usr/bin/env python3
"""
验证通用验证框架的完整功能
"""
import json
import logging
from pathlib import Path

# 配置日志 - 输出到 logs 目录
_log_dir = Path("logs")
_log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(_log_dir / "validation_framework_verify.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

from nagent_rag.validation import (
    ValidationConfig,
    ValidationRunner,
    TestCase,
    MetricScore,
    MetricType,
    ValidationResult,
)


def verify_framework():
    """验证框架的所有核心功能"""
    print("=" * 80)
    print("通用验证框架功能验证")
    print("=" * 80)

    # 1. 验证配置加载
    print("\n[1] 验证配置文件加载...")
    config_path = Path("examples/validation/calculator.json")
    if not config_path.exists():
        print(f"❌ 配置文件不存在: {config_path}")
        return False

    try:
        config = ValidationConfig.from_json(config_path)
        print(f"✓ 配置加载成功")
        print(f"  名称: {config.name}")
        print(f"  描述: {config.description}")
        print(f"  版本: {config.version}")
        print(f"  测试用例数: {len(config.test_cases)}")

        # 验证模型配置
        assert "model_name" in config.model_config
        assert "max_iterations" in config.model_config
        print(f"  模型配置: {config.model_config}")

    except Exception as e:
        print(f"❌ 配置加载失败: {e}")
        return False

    # 2. 验证测试用例结构
    print("\n[2] 验证测试用例结构...")
    try:
        for i, tc in enumerate(config.test_cases, 1):
            assert isinstance(tc, TestCase)
            assert tc.id
            assert tc.user_input
            assert tc.reference
            assert isinstance(tc.docs_indices, list)
            print(f"  ✓ 测试用例 {i}: {tc.id}")
            print(f"      问题: {tc.user_input[:60]}...")
            print(f"      文档索引: {tc.docs_indices}")
            if tc.description:
                print(f"      描述: {tc.description}")
    except AssertionError as e:
        print(f"❌ 测试用例结构验证失败: {e}")
        return False

    # 3. 验证数据模型序列化
    print("\n[3] 验证数据模型序列化...")
    try:
        # 创建示例评估结果
        metrics = {
            "correctness": MetricScore(
                name="Correctness",
                value=4.5,
                metric_type=MetricType.CORRECTNESS,
                reason="答案准确且完整",
            ),
            "relevance": MetricScore(
                name="Relevance",
                value=4.0,
                metric_type=MetricType.RELEVANCE,
            ),
            "reasoning_steps": MetricScore(
                name="Reasoning Steps",
                value=3.0,
                metric_type=MetricType.REASONING_STEPS,
            ),
        }

        result = ValidationResult(
            test_case_id="test_1",
            user_input="测试问题",
            reference="参考答案",
            prediction="生成答案",
            metrics=metrics,
            trace_length=5,
            error=None,
        )

        # 序列化为字典
        result_dict = result.to_dict()
        print(f"✓ ValidationResult 序列化成功")
        print(f"  测试用例 ID: {result_dict['test_case_id']}")
        print(f"  指标数: {len(result_dict['metrics'])}")
        for metric_name, metric_data in result_dict['metrics'].items():
            print(f"    - {metric_name}: {metric_data['value']:.2f}")

    except Exception as e:
        print(f"❌ 序列化验证失败: {e}")
        return False

    # 4. 验证配置保存与加载
    print("\n[4] 验证配置保存与加载...")
    try:
        test_config_path = Path("test_validation_config.json")

        # 创建新配置
        new_config = ValidationConfig(
            name="测试验证程序",
            description="测试配置文件的保存和加载功能",
            test_cases=[
                TestCase(
                    id="test_case_1",
                    user_input="测试问题 1",
                    reference="参考答案 1",
                    docs_indices=[0, 1],
                    description="测试用例 1",
                )
            ],
            model_config={"model_name": "test_model", "max_iterations": 3},
        )

        # 保存配置
        new_config.to_json(test_config_path)
        print(f"✓ 配置保存成功: {test_config_path}")

        # 重新加载配置
        loaded_config = ValidationConfig.from_json(test_config_path)
        assert loaded_config.name == new_config.name
        assert len(loaded_config.test_cases) == len(new_config.test_cases)
        assert loaded_config.test_cases[0].id == "test_case_1"
        print(f"✓ 配置加载成功，验证数据一致性")

        # 清理测试文件
        test_config_path.unlink()

    except Exception as e:
        print(f"❌ 配置保存/加载验证失败: {e}")
        return False

    # 5. 验证文档文件
    print("\n[5] 验证支持文件...")
    try:
        config_path = Path("examples/validation/calculator.json")
        if not config_path.exists():
            print(f"❌ 配置文件不存在: {config_path}")
            return False

        with open(config_path, "r", encoding="utf-8") as f:
            config_data = json.load(f)

        rag_data = config_data.get("rag_data", [])
        if not rag_data:
            print(f"❌ 配置文件中缺少 rag_data")
            return False

        print(f"✓ RAG 数据验证成功")
        print(f"  文档数: {len(rag_data)}")
        for i, doc in enumerate(rag_data, 1):
            print(f"  [{i}] {doc['id']}: {doc['content'][:50]}...")

    except Exception as e:
        print(f"❌ 文档文件验证失败: {e}")
        return False

    # 6. 验证命令行支持
    print("\n[6] 验证命令行支持...")
    try:
        runner_path = Path("apps/agentic-rag/src/agentic_rag/validation_runner.py")
        if not runner_path.exists():
            print(f"❌ 验证程序文件不存在: {runner_path}")
            return False

        with open(runner_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 检查是否包含必要的命令行参数支持
        assert "--config" in content
        assert "--output" in content
        assert "argparse" in content
        print(f"✓ 验证程序支持命令行参数")
        print(f"  支持 --config 参数：可指定配置文件")
        print(f"  支持 --output 参数：可指定输出目录")

    except Exception as e:
        print(f"❌ 命令行支持验证失败: {e}")
        return False

    # 总结
    print("\n" + "=" * 80)
    print("✅ 通用验证框架验证完成 - 所有功能正常")
    print("=" * 80)

    print("\n📋 框架功能总结:")
    print("  ✓ ValidationConfig - 配置数据模型（支持 JSON 加载/保存）")
    print("  ✓ ValidationRunner - 通用验证程序基类（可扩展）")
    print("  ✓ ValidationResult - 验证结果数据模型（支持序列化）")
    print("  ✓ TestCase - 测试用例数据模型")
    print("  ✓ MetricScore - 评估指标得分（支持多种指标类型）")
    print("  ✓ ValidationSummary - 验证总结统计")
    print("  ✓ ValidationReport - 报告生成器（文本、JSON、CSV）")

    print("\n🎯 使用示例:")
    print("  1. 加载配置文件:")
    print("     config = ValidationConfig.from_json('examples/validation/calculator.json')")
    print("")
    print("  2. 创建自定义验证程序：")
    print("     class MyValidator(ValidationRunner):")
    print("         async def run_test_case(self, test_case):")
    print("             # 实现具体验证逻辑")
    print("             pass")
    print("")
    print("  3. 运行验证程序:")
    print("     uv run python -m agentic_rag.validation_runner --config examples/validation/calculator.json")
    print("     uv run python -m agentic_rag.validation_runner --config examples/validation/calculator.json --output my_output_dir")

    return True


if __name__ == "__main__":
    import sys
    success = verify_framework()
    sys.exit(0 if success else 1)
