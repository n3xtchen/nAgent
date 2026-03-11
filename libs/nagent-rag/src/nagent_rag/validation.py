"""
通用验证程序框架 - 支持配置文件驱动的验证工作流

核心组件：
- ValidationConfig: 验证配置数据模型，支持从 JSON 加载
- TestCase: 单个测试用例数据模型
- ValidationResult: 验证结果数据模型
- ValidationRunner: 通用验证程序运行器基类
- ValidationReport: 验证结果报告生成器
"""

import json
import csv
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
from enum import Enum
import logging

# 配置日志 - 输出到 outputs/logs 目录
_output_dir = Path("outputs")
_log_dir = _output_dir / "logs"
_log_dir.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(_log_dir / "validation_framework.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """验证指标类型"""
    CORRECTNESS = "correctness"  # 准确性
    RELEVANCE = "relevance"  # 相关性
    FAITHFULNESS = "faithfulness"  # 忠实性
    REASONING_STEPS = "reasoning_steps"  # 推理步数
    CONTEXT_RECALL = "context_recall"  # 召回率
    CUSTOM = "custom"  # 自定义指标


@dataclass
class TestCase:
    """单个测试用例"""
    id: str
    user_input: str
    reference: str
    docs_indices: List[str | int] = field(default_factory=list)
    description: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TestCase":
        """从字典创建 TestCase 实例"""
        return cls(
            id=data["id"],
            user_input=data["user_input"],
            reference=data["reference"],
            docs_indices=data.get("docs_indices", []),
            description=data.get("description"),
            metadata=data.get("metadata", {}),
        )


@dataclass
class MetricScore:
    """单个指标得分"""
    name: str
    value: float
    metric_type: MetricType
    reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "value": self.value,
            "metric_type": self.metric_type.value,
            "reason": self.reason,
        }


@dataclass
class ValidationResult:
    """单个测试用例的验证结果"""
    test_case_id: str
    user_input: str
    reference: str
    prediction: str
    metrics: Dict[str, MetricScore] = field(default_factory=dict)
    trace_length: Optional[int] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "test_case_id": self.test_case_id,
            "user_input": self.user_input,
            "reference": self.reference,
            "prediction": self.prediction,
            "metrics": {k: v.to_dict() for k, v in self.metrics.items()},
            "trace_length": self.trace_length,
            "error": self.error,
            "metadata": self.metadata,
        }


@dataclass
class ValidationConfig:
    """验证配置数据模型"""
    name: str
    description: str
    version: str = "1.0"
    rag_config: Dict[str, Any] = field(default_factory=dict)
    rag_data: List[Dict[str, Any]] = field(default_factory=list)
    test_cases: List[TestCase] = field(default_factory=list)
    model_config: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_json(cls, json_path: str | Path, dataset_path: Optional[str | Path] = None) -> "ValidationConfig":
        """从 JSON 文件加载配置

        Args:
            json_path: 配置文件路径
            dataset_path: 可选的数据集文件路径（若提供则覆盖配置文件中的测试用例）
        """
        path = Path(json_path)
        logger.info(f"📂 加载验证配置: {path}")

        if not path.exists():
            raise FileNotFoundError(f"配置文件不存在: {path}")

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 优先从独立数据集加载测试用例
        test_cases_data = data.get("test_cases", [])
        if dataset_path:
            dataset_path = Path(dataset_path)
            logger.info(f"📂 从独立数据集加载测试用例: {dataset_path}")
            if not dataset_path.exists():
                raise FileNotFoundError(f"数据集文件不存在: {dataset_path}")
            with open(dataset_path, "r", encoding="utf-8") as f:
                ds_data = json.load(f)
                # 如果数据集是列表，则直接作为测试用例；如果是字典，则尝试获取 test_cases 字段
                if isinstance(ds_data, list):
                    test_cases_data = ds_data
                else:
                    test_cases_data = ds_data.get("test_cases", ds_data)

        # 解析测试用例
        test_cases = [
            TestCase.from_dict(tc) for tc in test_cases_data
        ]

        config = cls(
            name=data.get("name", "验证程序"),
            description=data.get("description", ""),
            version=data.get("version", "1.0"),
            rag_config=data.get("rag_config", {}),
            rag_data=data.get("rag_data", []),
            test_cases=test_cases,
            model_config=data.get("model_config", {}),
            metadata=data.get("metadata", {}),
        )

        logger.info(f"✓ 已加载 {len(config.test_cases)} 个测试用例")
        if config.rag_data:
             logger.info(f"✓ 已加载 {len(config.rag_data)} 条 RAG 数据")

        return config

    def to_json(self, json_path: str | Path) -> None:
        """保存配置为 JSON 文件"""
        path = Path(json_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "rag_config": self.rag_config,
            "rag_data": self.rag_data,
            "test_cases": [asdict(tc) for tc in self.test_cases],
            "model_config": self.model_config,
            "metadata": self.metadata,
        }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"✓ 配置已保存: {path}")


@dataclass
class ValidationSummary:
    """验证总结"""
    total_tests: int
    passed_tests: int
    failed_tests: int
    metrics_average: Dict[str, float]
    metrics_min: Dict[str, float]
    metrics_max: Dict[str, float]
    total_time: float  # 秒

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "total_tests": self.total_tests,
            "passed_tests": self.passed_tests,
            "failed_tests": self.failed_tests,
            "pass_rate": (
                (self.passed_tests / self.total_tests * 100)
                if self.total_tests > 0
                else 0
            ),
            "metrics_average": self.metrics_average,
            "metrics_min": self.metrics_min,
            "metrics_max": self.metrics_max,
            "total_time": self.total_time,
        }


class ValidationRunner(ABC):
    """验证程序运行器基类"""

    def __init__(
        self,
        config: ValidationConfig,
        output_dir: Optional[str | Path] = None,
    ):
        """初始化验证运行器

        Args:
            config: 验证配置
            output_dir: 输出目录，默认为 outputs/results
        """
        self.config = config
        # 默认输出到 outputs/results
        if output_dir is None:
            self.output_dir = Path("outputs") / "results"
        else:
            self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results: List[ValidationResult] = []
        self.start_time = None
        self.end_time = None

    @abstractmethod
    async def run_test_case(self, test_case: TestCase) -> ValidationResult:
        """执行单个测试用例（子类需要实现）

        Args:
            test_case: 测试用例

        Returns:
            验证结果
        """
        pass

    async def run(self, max_concurrency: int = 1) -> ValidationSummary:
        """执行完整的验证流程

        Args:
            max_concurrency: 最大并发数，默认为 1（串行）

        Returns:
            验证总结
        """
        import time
        import asyncio

        self.start_time = time.time()
        self.results = []

        logger.info("=" * 80)
        logger.info(f"🚀 开始验证: {self.config.name}")
        logger.info(f"📝 描述: {self.config.description}")
        logger.info(f"并发限制: {max_concurrency}")
        logger.info("=" * 80)

        if max_concurrency <= 1:
            # 串行执行
            for i, test_case in enumerate(self.config.test_cases, 1):
                logger.info(f"\n[测试 {i}/{len(self.config.test_cases)}] {test_case.id}")
                logger.info(f"❓ 问题: {test_case.user_input}")
                logger.info("-" * 80)

                try:
                    result = await self.run_test_case(test_case)
                    self.results.append(result)

                    if result.error:
                        logger.error(f"❌ 测试失败: {result.error}")
                    else:
                        logger.info("✓ 测试成功")

                    # 显示指标
                    if result.metrics:
                        logger.info("\n📊 指标结果:")
                        for metric_name, score in result.metrics.items():
                            if score.metric_type == MetricType.REASONING_STEPS:
                                logger.info(
                                    f"  • {metric_name}: {score.value:.0f}"
                                )
                            elif score.metric_type == MetricType.CONTEXT_RECALL:
                                logger.info(
                                    f"  • {metric_name}: {score.value:.2f}"
                                )
                            else:
                                logger.info(
                                    f"  • {metric_name}: {score.value:.2f}/5.0"
                                )
                                if score.reason:
                                    logger.info(f"    {score.reason}")

                except Exception as e:
                    logger.error(f"❌ 测试执行异常: {e}")
                    import traceback
                    traceback.print_exc()
        else:
            # 并发执行
            semaphore = asyncio.Semaphore(max_concurrency)

            async def _run_with_semaphore(idx, tc):
                async with semaphore:
                    logger.info(f"🚀 启动并发测试 [{idx}/{len(self.config.test_cases)}]: {tc.id}")
                    try:
                        res = await self.run_test_case(tc)
                        if res.error:
                            logger.error(f"❌ 测试 {tc.id} 失败: {res.error}")
                        else:
                            logger.info(f"✓ 测试 {tc.id} 成功")
                        return res
                    except Exception as e:
                        logger.error(f"❌ 测试 {tc.id} 异常: {e}")
                        return ValidationResult(
                            test_case_id=tc.id,
                            user_input=tc.user_input,
                            reference=tc.reference,
                            prediction="",
                            error=str(e)
                        )

            tasks = [
                _run_with_semaphore(i, tc)
                for i, tc in enumerate(self.config.test_cases, 1)
            ]
            self.results = await asyncio.gather(*tasks)

        self.end_time = time.time()
        summary = self._generate_summary()

        logger.info("\n" + "=" * 80)
        logger.info("📈 验证完成")
        logger.info("=" * 80)

        return summary

    def _generate_summary(self) -> ValidationSummary:
        """生成验证总结"""
        import time

        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if not r.error)
        failed_tests = total_tests - passed_tests

        # 计算指标平均值
        metrics_average = {}
        metrics_min = {}
        metrics_max = {}

        if self.results and self.results[0].metrics:
            for metric_name in self.results[0].metrics:
                values = [
                    r.metrics[metric_name].value
                    for r in self.results
                    if metric_name in r.metrics and not r.error
                ]

                if values:
                    metrics_average[metric_name] = sum(values) / len(values)
                    metrics_min[metric_name] = min(values)
                    metrics_max[metric_name] = max(values)

        total_time = (
            (self.end_time - self.start_time) if self.end_time else 0
        )

        return ValidationSummary(
            total_tests=total_tests,
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            metrics_average=metrics_average,
            metrics_min=metrics_min,
            metrics_max=metrics_max,
            total_time=total_time,
        )

    def print_summary(self, summary: ValidationSummary) -> None:
        """打印验证总结"""
        logger.info("\n📊 验证结果总结:")
        logger.info(f"  总测试数: {summary.total_tests}")
        logger.info(f"  通过数: {summary.passed_tests}")
        logger.info(f"  失败数: {summary.failed_tests}")
        logger.info(f"  通过率: {summary.to_dict()['pass_rate']:.1f}%")

        if summary.metrics_average:
            logger.info("\n📈 平均指标:")
            for metric_name, value in summary.metrics_average.items():
                if metric_name in ["reasoning_steps"]:
                    logger.info(f"  {metric_name}: {value:.2f}")
                elif metric_name in ["context_recall"]:
                    logger.info(f"  {metric_name}: {value:.2f}")
                else:
                    logger.info(f"  {metric_name}: {value:.2f}/5.0")

            logger.info("\n🎯 指标范围:")
            for metric_name in summary.metrics_average:
                min_val = summary.metrics_min.get(metric_name, 0)
                max_val = summary.metrics_max.get(metric_name, 0)
                logger.info(
                    f"  {metric_name}: {min_val:.2f} - {max_val:.2f}"
                )

        logger.info(f"\n⏱️  总耗时: {summary.total_time:.2f} 秒")

    def save_results_json(self, output_path: Optional[str | Path] = None) -> Path:
        """保存详细结果为 JSON"""
        path = Path(output_path or self.output_dir / "validation_results.json")
        path.parent.mkdir(parents=True, exist_ok=True)

        summary = self._generate_summary()

        data = {
            "config": {
                "name": self.config.name,
                "description": self.config.description,
                "version": self.config.version,
            },
            "summary": summary.to_dict(),
            "results": [r.to_dict() for r in self.results],
        }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"✓ 结果已保存到: {path}")
        return path

    def save_results_csv(self, output_path: Optional[str | Path] = None) -> Path:
        """保存结果为 CSV"""
        path = Path(output_path or self.output_dir / "validation_results.csv")
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", newline="", encoding="utf-8") as f:
            if not self.results:
                logger.warning("没有结果可保存")
                return path

            # 获取所有指标名称
            metric_names = []
            if self.results and self.results[0].metrics:
                metric_names = list(self.results[0].metrics.keys())

            fieldnames = [
                "test_case_id",
                "user_input",
                "reference",
                "prediction",
                "error",
                "trace_length",
            ] + metric_names

            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for result in self.results:
                row = {
                    "test_case_id": result.test_case_id,
                    "user_input": result.user_input,
                    "reference": result.reference,
                    "prediction": result.prediction,
                    "error": result.error or "",
                    "trace_length": result.trace_length or "",
                }

                for metric_name, score in result.metrics.items():
                    row[metric_name] = f"{score.value:.2f}"

                writer.writerow(row)

        logger.info(f"✓ CSV 结果已保存到: {path}")
        return path


class ValidationReport:
    """验证结果报告生成器"""

    def __init__(self, results: List[ValidationResult], config: ValidationConfig):
        """初始化报告生成器

        Args:
            results: 验证结果列表
            config: 验证配置
        """
        self.results = results
        self.config = config

    def generate_text_report(self) -> str:
        """生成文本报告"""
        lines = []
        lines.append("=" * 80)
        lines.append(f"验证报告: {self.config.name}")
        lines.append(f"描述: {self.config.description}")
        lines.append(f"版本: {self.config.version}")
        lines.append("=" * 80)
        lines.append("")

        lines.append(f"总测试数: {len(self.results)}")
        passed = sum(1 for r in self.results if not r.error)
        failed = len(self.results) - passed
        lines.append(f"通过数: {passed}")
        lines.append(f"失败数: {failed}")
        if len(self.results) > 0:
            lines.append(f"通过率: {passed / len(self.results) * 100:.1f}%")
        lines.append("")

        # 详细结果
        lines.append("详细结果:")
        lines.append("-" * 80)
        for i, result in enumerate(self.results, 1):
            lines.append(f"\n[测试 {i}] {result.test_case_id}")
            lines.append(f"问题: {result.user_input}")
            lines.append(f"参考答案: {result.reference}")
            lines.append(f"生成答案: {result.prediction}")

            if result.error:
                lines.append(f"错误: {result.error}")
            else:
                lines.append("✓ 成功")

            if result.metrics:
                lines.append("指标:")
                for metric_name, score in result.metrics.items():
                    lines.append(f"  • {metric_name}: {score.value:.2f}")

        return "\n".join(lines)

    def save_text_report(self, output_path: str | Path) -> None:
        """保存文本报告"""
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            f.write(self.generate_text_report())

        logger.info(f"✓ 文本报告已保存到: {path}")
