#!/usr/bin/env python3
"""
通用 Agentic RAG 验证工具

该脚本支持通过配置文件驱动的验证工作流，不仅限于 calculator 验证，可扩展支持多种验证场景：
- 默认使用 examples/validation/calculator.json
- 可通过 --config 参数指定自定义配置文件

执行方式：
  uv run python -m agentic_rag.validation_runner
  uv run python -m agentic_rag.validation_runner --config examples/validation/calculator.json
  uv run python apps/agentic-rag/src/agentic_rag/validation_runner.py
"""
import os
import argparse
import asyncio
import logging
from pathlib import Path
from dotenv import load_dotenv
from google import genai

# 配置日志 - 输出到 logs 目录
_log_dir = Path("logs")
_log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(_log_dir / "validation.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# 导入项目模块
from agentic_rag.rags import AgenticRAG, SimpleRAG, VectorRAG
from nagent_rag.retrievers.keyword import SimpleKeywordRetriever
from nagent_rag.retrievers.chroma import ChromaRetriever
from nagent_rag.validation import ValidationConfig, ValidationRunner, MetricScore, MetricType, ValidationResult
from nagent_rag.eval import (
    correctness_metric,
    faithfulness_metric,
    answer_relevance_metric,
    reasoning_steps_metric,
)


# 加载环境变量
load_dotenv()


class AgenticRAGValidationRunner(ValidationRunner):
    """通用 Agentic RAG 验证程序运行器"""

    def __init__(
        self,
        config: ValidationConfig,
        client,
        all_docs,
        output_dir=None,
    ):
        """初始化 Agentic RAG 验证运行器

        Args:
            config: 验证配置
            client: Gemini 客户端
            all_docs: 所有文档
            output_dir: 输出目录
        """
        super().__init__(config, output_dir)
        self.client = client
        self.all_docs = all_docs
        self.rag = None
        self.rag_type = config.model_config.get("rag_type", "agentic")
        # 预构建 ID 映射以提高检索效率
        self.doc_map = {str(d.get("id")): d["content"] for d in self.all_docs if isinstance(d, dict) and "id" in d and "content" in d}

    async def _init_rag(self):
        """初始化 Agentic RAG"""
        if self.rag:
            return

        # 创建检索器
        print("🔍 正在初始化检索器...")
        if self.rag_type.lower() == "vector":
            retriever = ChromaRetriever()
        else:
            retriever = SimpleKeywordRetriever()
        retriever.fit(self.all_docs)

        # 初始化 RAG
        trace_dir = self.output_dir / "traces"
        trace_dir.mkdir(parents=True, exist_ok=True)

        print(f"🤖 正在初始化 {self.rag_type} RAG...")
        model_name = self.config.model_config.get("model_name", "gemini-2.0-flash")

        if self.rag_type.lower() == "simple":
            self.rag = SimpleRAG(
                client=self.client,
                retriever=retriever,
                model_name=model_name,
                trace_dir=str(trace_dir),
            )
        elif self.rag_type.lower() == "vector":
            self.rag = VectorRAG(
                client=self.client,
                retriever=retriever,
                model_name=model_name,
                trace_dir=str(trace_dir),
            )
        else:
            self.rag = AgenticRAG(
                client=self.client,
                retriever=retriever,
                model_name=model_name,
                max_iterations=self.config.model_config.get("max_iterations", 5),
                trace_dir=str(trace_dir),
            )

    async def run_test_case(self, test_case):
        """执行单个测试用例"""
        if not self.rag:
            await self._init_rag()

        try:
            # 执行查询
            print(f"⏳ [{test_case.id}] 正在执行查询...")
            # 使用 aquery 异步调用
            result = await self.rag.aquery(test_case.user_input)
            answer = result["answer"]
            trace = result.get("trace", [])

            print(f"✓ [{test_case.id}] 生成的答案: {answer[:100]}{'...' if len(answer) > 100 else ''}")
            print(f"✓ [{test_case.id}] 推理步数: {len(trace)}")

            # 计算评估指标
            print(f"📊 [{test_case.id}] 正在计算评估指标...")
            metrics = {}

            # 1. 准确性
            c_res = await correctness_metric.ascore(
                user_input=test_case.user_input,
                reference=test_case.reference,
                prediction=answer,
                client=self.client,
                model_name=self.config.model_config.get("model_name", "gemini-2.0-flash")
            )
            metrics["correctness"] = MetricScore(
                name="Correctness",
                value=c_res.value,
                metric_type=MetricType.CORRECTNESS,
                reason=getattr(c_res, "reason", None),
            )

            # 2. 相关性
            r_res = await answer_relevance_metric.ascore(
                user_input=test_case.user_input,
                prediction=answer,
                client=self.client,
                model_name=self.config.model_config.get("model_name", "gemini-2.0-flash")
            )
            metrics["answer_relevance"] = MetricScore(
                name="Answer Relevance",
                value=r_res.value,
                metric_type=MetricType.RELEVANCE,
                reason=getattr(r_res, "reason", None),
            )

            # 3. 推理步数
            s_res = await reasoning_steps_metric.ascore(trace=trace)
            metrics["reasoning_steps"] = MetricScore(
                name="Reasoning Steps",
                value=s_res.value,
                metric_type=MetricType.REASONING_STEPS,
            )

            # 4. 上下文召回率 (Context Recall)
            if test_case.docs_indices:
                import re
                expected_doc_ids = set(str(idx) for idx in test_case.docs_indices)
                actual_doc_ids = set()
                for step in trace:
                    if step.get("action") == "retrieve":
                        observation = step.get("observation", "")
                        extracted_ids = re.findall(r"\(ID:\s*(.*?)\)", observation)
                        actual_doc_ids.update(extracted_ids)

                if expected_doc_ids:
                    recall = len(expected_doc_ids.intersection(actual_doc_ids)) / len(expected_doc_ids)
                    metrics["context_recall"] = MetricScore(
                        name="Context Recall",
                        value=recall,
                        metric_type=MetricType.CONTEXT_RECALL,
                    )

            # 5. 忠实性（需要上下文）
            retrieved_docs = ""

            for idx in test_case.docs_indices:
                if isinstance(idx, int):
                    if 0 <= idx < len(self.all_docs):
                        retrieved_docs += self.all_docs[idx]["content"] + "\n\n"
                elif isinstance(idx, str):
                    if idx in self.doc_map:
                        retrieved_docs += self.doc_map[idx] + "\n\n"

            if retrieved_docs:
                f_res = await faithfulness_metric.ascore(
                    context=retrieved_docs,
                    prediction=answer,
                    client=self.client,
                    model_name=self.config.model_config.get("model_name", "gemini-2.0-flash")
                )
                metrics["faithfulness"] = MetricScore(
                    name="Faithfulness",
                    value=f_res.value,
                    metric_type=MetricType.FAITHFULNESS,
                    reason=getattr(f_res, "reason", None),
                )

            # 创建验证结果
            validation_result = ValidationResult(
                test_case_id=test_case.id,
                user_input=test_case.user_input,
                reference=test_case.reference,
                prediction=answer,
                metrics=metrics,
                trace_length=len(trace),
                error=None,
                metadata={"doc_indices": test_case.docs_indices},
            )

            return validation_result

        except Exception as e:
            print(f"\n❌ 测试 {test_case.id} 执行失败: {e}")
            import traceback
            traceback.print_exc()

            return ValidationResult(
                test_case_id=test_case.id,
                user_input=test_case.user_input,
                reference=test_case.reference,
                prediction="",
                error=str(e),
            )


async def main():
    """主程序"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(
        description="通用 Agentic RAG 验证工具 - 支持配置文件驱动的验证工作流"
    )
    parser.add_argument(
        "--config",
        type=str,
        required=True,
        help="验证配置文件路径 (必填)",
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default=None,
        help="独立测试集文件路径（若提供，则覆盖 config 中的 test_cases）",
    )
    parser.add_argument(
        "--docs",
        type=str,
        default=None,
        help="独立文档库文件路径（若提供则优先使用，否则使用 config 中的 rag_data）",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="outputs/results/validation",
        help="输出目录（默认: outputs/results/validation）",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=3,
        help="并发测试用例数（默认: 3）",
    )
    parser.add_argument(
        "--rag_type",
        type=str,
        default=None,
        choices=["agentic", "simple", "vector"],
        help="RAG 实现类型 (agentic, simple 或 vector)，若指定则覆盖配置文件中的设定",
    )
    args = parser.parse_args()

    # 确定路径
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = Path.cwd() / args.config

    dataset_path = None
    if args.dataset:
        dataset_path = Path(args.dataset)
        if not dataset_path.is_absolute():
            dataset_path = Path.cwd() / args.dataset

    # 验证环境变量
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ 错误：未设置 GEMINI_API_KEY 环境变量")
        return

    print("=" * 80)
    print("通用 Agentic RAG 验证 - 并发解耦版")
    print("=" * 80)

    # 加载配置
    try:
        config = ValidationConfig.from_json(config_path, dataset_path=dataset_path)
        if args.rag_type:
            config.model_config["rag_type"] = args.rag_type
    except Exception as e:
        print(f"❌ 加载配置/数据集失败: {e}")
        return

    if dataset_path:
        print(f"✓ 已加载独立测试集: {dataset_path}")

    # 加载文档
    print("📂 加载测试文档...")
    all_docs = []

    # 1. 优先使用配置中的 rag_data
    if config.rag_data:
        print(f"✓ 使用配置中的 rag_data ({len(config.rag_data)} 条)")
        all_docs = config.rag_data

    # 2. 如果配置中没有，则必须从 --docs 参数加载
    elif args.docs:
        docs_path = Path(args.docs)
        if not docs_path.is_absolute():
            docs_path = Path.cwd() / args.docs

        if not docs_path.exists():
            print(f"❌ 错误：指定文档文件不存在: {docs_path}")
            return

        import json
        try:
            with open(docs_path, 'r', encoding='utf-8') as f:
                all_docs = json.load(f)
            print(f"✓ 已加载 {len(all_docs)} 个文档 (路径: {docs_path})")
        except json.JSONDecodeError as e:
            print(f"❌ 错误：文档文件格式错误 (非 JSON): {e}")
            return
        except Exception as e:
            print(f"❌ 错误：加载文档文件失败: {e}")
            return
    else:
        # 不再支持默认回退到 calculator_demo.json
        print("❌ 错误：必须提供 RAG 文档数据")
        print("  - 方式 1: 在配置文件中包含 'rag_data' 字段")
        print("  - 方式 2: 使用 --docs 参数指定文档文件")
        return

    # 验证文档格式
    if not all_docs:
        print("❌ 错误：文档数据为空")
        return

    print("🔍 验证文档格式...")
    doc_ids = set()
    for i, doc in enumerate(all_docs):
        if not isinstance(doc, dict):
            print(f"❌ 错误：文档 #{i+1} 格式错误，应为字典")
            return
        if "id" not in doc:
             print(f"❌ 错误：文档 #{i+1} 缺少必要字段 'id'")
             return
        if "content" not in doc:
             print(f"❌ 错误：文档 #{i+1} 缺少必要字段 'content'")
             return
        doc_ids.add(str(doc["id"]))
    print("✓ 文档格式验证通过")

    # 验证测试用例引用的文档是否存在
    print("🔍 验证测试用例文档引用...")
    missing_refs = []

    for tc in config.test_cases:
        for idx in tc.docs_indices:
            # 如果是字符串 ID，检查是否存在于文档 ID 集合中
            if isinstance(idx, str):
                if idx not in doc_ids:
                    missing_refs.append(f"{tc.id} -> {idx} (ID)")
            # 如果是整数索引，检查是否越界
            elif isinstance(idx, int):
                if idx < 0 or idx >= len(all_docs):
                    missing_refs.append(f"{tc.id} -> {idx} (Index)")

    if missing_refs:
        print(f"❌ 错误：发现 {len(missing_refs)} 个无效的文档引用")
        print(f"  无效引用示例: {missing_refs[:3]}...")
        return
    else:
        print("✓ 文档引用验证通过")

    print("\n")

    # 初始化 Gemini 客户端
    print("🔑 正在初始化 Gemini 客户端...")
    client = genai.Client(api_key=api_key)

    # 创建验证运行器
    output_dir = Path(args.output)
    runner = AgenticRAGValidationRunner(
        config=config,
        client=client,
        all_docs=all_docs,
        output_dir=output_dir,
    )

    # 执行验证 (增加并发支持)
    summary = await runner.run(max_concurrency=args.concurrency)

    # 打印总结
    runner.print_summary(summary)

    # 保存结果
    print("\n💾 正在保存结果...")
    runner.save_results_json()
    runner.save_results_csv()

    # 性能评级
    print("\n🎯 质量评级:")
    avg_correctness = summary.metrics_average.get("correctness", 0)
    if avg_correctness >= 4.0:
        print(f"  准确性: ✓ 优秀 (≥4.0) - {avg_correctness:.2f}")
    elif avg_correctness >= 3.0:
        print(f"  准确性: △ 良好 (3.0-3.9) - {avg_correctness:.2f}")
    else:
        print(f"  准确性: ✗ 需改进 (<3.0) - {avg_correctness:.2f}")

    avg_relevance = summary.metrics_average.get("answer_relevance", 0)
    if avg_relevance >= 4.0:
        print(f"  相关性: ✓ 优秀 (≥4.0) - {avg_relevance:.2f}")
    elif avg_relevance >= 3.0:
        print(f"  相关性: △ 良好 (3.0-3.9) - {avg_relevance:.2f}")
    else:
        print(f"  相关性: ✗ 需改进 (<3.0) - {avg_relevance:.2f}")

    avg_faithfulness = summary.metrics_average.get("faithfulness", 0)
    if avg_faithfulness > 0:
        if avg_faithfulness >= 4.0:
            print(f"  忠实性: ✓ 优秀 (≥4.0) - {avg_faithfulness:.2f}")
        elif avg_faithfulness >= 3.0:
            print(f"  忠实性: △ 良好 (3.0-3.9) - {avg_faithfulness:.2f}")
        else:
            print(f"  忠实性: ✗ 需改进 (<3.0) - {avg_faithfulness:.2f}")

    avg_steps = summary.metrics_average.get("reasoning_steps", 0)
    if avg_steps > 0:
        if avg_steps <= 3:
            print(f"  效率: ✓ 优秀 (≤3步) - {avg_steps:.2f}")
        elif avg_steps <= 5:
            print(f"  效率: △ 良好 (4-5步) - {avg_steps:.2f}")
        else:
            print(f"  效率: ✗ 需改进 (>5步) - {avg_steps:.2f}")

    avg_recall = summary.metrics_average.get("context_recall", -1)
    if avg_recall >= 0:
        if avg_recall >= 0.8:
            print(f"  召回率: ✓ 优秀 (≥0.8) - {avg_recall:.2f}")
        elif avg_recall >= 0.5:
            print(f"  召回率: △ 良好 (0.5-0.79) - {avg_recall:.2f}")
        else:
            print(f"  召回率: ✗ 需改进 (<0.5) - {avg_recall:.2f}")

    print(f"\n📁 结果保存位置: {output_dir}")
    print(f"📁 Trace 日志位置: {output_dir}/traces")
    print("\n✓ 验证完成！")


if __name__ == "__main__":
    asyncio.run(main())
