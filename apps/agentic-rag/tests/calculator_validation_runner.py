#!/usr/bin/env python3
"""
使用 calculator_demo.json 验证 agentic-rag 的准确率
执行方式：uv run python apps/agentic-rag/tests/calculator_validation_runner.py
"""
import os
import json
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from google import genai

# 导入项目模块
from agentic_rag.rag import AgenticRAG
from nagent_rag.retriever import SimpleKeywordRetriever
from nagent_rag.eval import correctness_metric, faithfulness_metric, answer_relevance_metric, reasoning_steps_metric


# 加载环境变量
load_dotenv()


def load_calculator_demo():
    """加载 calculator_demo.json 数据"""
    demo_path = Path(__file__).parent.parent.parent.parent / "examples" / "calculator_demo.json"
    print(f"📂 加载文件: {demo_path}")
    with open(demo_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def create_test_cases():
    """创建基于 calculator_demo.json 的测试用例"""
    docs = load_calculator_demo()

    test_cases = [
        {
            "id": "calc_budget_1",
            "user_input": "Project Pig 的研发费用和市场推广费用总共是多少?",
            "reference": "研发费用 500,000 元，市场推广 200,000 元，总共是 700,000 元。",
            "docs_indices": [0],  # 使用第一个文档
        },
        {
            "id": "calc_budget_2",
            "user_input": "Project Pig 的预算中，运营维护费用占总预算的百分比是多少?",
            "reference": "总预算是 500,000 + 200,000 + 150,000 + 50,000 = 900,000 元。运营维护 150,000 元占比是 150,000/900,000 = 16.67%。",
            "docs_indices": [0],
        },
        {
            "id": "calc_pricing",
            "user_input": "如果购买 150 个 nAgent 企业版席位，一个月需要支付多少美元?",
            "reference": "基础价格：150 * 29 = 4,350 美元。由于超过 100 个席位，享受 8.5 折优惠：4,350 * 0.85 = 3,697.5 美元。",
            "docs_indices": [1],
        },
        {
            "id": "perf_analysis",
            "user_input": "在 Agentic RAG 系统的查询过程中，知识检索耗时最长吗?",
            "reference": "根据性能测试，单次查询耗时：意图识别 0.2 秒，知识检索 0.7 秒，答案生成 0.3 秒。知识检索耗时 0.7 秒确实最长。",
            "docs_indices": [2],
        },
        {
            "id": "calc_multi_doc",
            "user_input": "Project Pig 的行政支出和 nAgent 订阅一个月的基础费用（单用户）是否相同?",
            "reference": "Project Pig 行政支出是 50,000 元，nAgent 企业版订阅费用是 29 美元/月/用户，不相同（单位和数值都不同）。",
            "docs_indices": [0, 1],
        }
    ]

    return test_cases, docs


async def run_validation():
    """运行完整的验证流程"""
    print("=" * 80)
    print("Agentic RAG 准确率验证 - 基于 calculator_demo.json")
    print("=" * 80)

    # 加载测试数据
    test_cases, all_docs = create_test_cases()
    print(f"✓ 已加载 {len(test_cases)} 个测试用例\n")

    # 初始化客户端
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ 错误：未设置 GEMINI_API_KEY 环境变量")
        return

    print("🔑 正在初始化 Gemini 客户端...")
    client = genai.Client(api_key=api_key)

    # 创建检索器
    print("🔍 正在初始化检索器...")
    retriever = SimpleKeywordRetriever()
    doc_contents = [doc["content"] for doc in all_docs]
    retriever.fit(doc_contents)

    # 初始化 Agentic RAG
    trace_dir = Path("calculator_validation_traces")
    trace_dir.mkdir(exist_ok=True)

    print("🤖 正在初始化 Agentic RAG...")
    rag = AgenticRAG(
        client=client,
        retriever=retriever,
        model_name="gemini-2.0-flash",
        max_iterations=5,
        trace_dir=str(trace_dir),
    )

    # 存储结果
    results = []
    metrics_summary = {
        "correctness": [],
        "faithfulness": [],
        "answer_relevance": [],
        "reasoning_steps": []
    }

    print("\n" + "=" * 80)
    print("开始执行测试用例...\n")

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n[测试 {i}/{len(test_cases)}] {test_case['id']}")
        print(f"❓ 问题: {test_case['user_input']}")
        print("-" * 80)

        try:
            # 执行查询
            print("⏳ 正在执行查询...")
            result = rag.query(test_case["user_input"])
            answer = result["answer"]
            trace = result.get("trace", [])

            print(f"✓ 生成的答案: {answer[:150]}{'...' if len(answer) > 150 else ''}")
            print(f"✓ 推理步数: {len(trace)}")

            # 计算评估指标
            print("\n📊 正在计算评估指标...")

            # 1. 准确性
            print("  • 准确性 (Correctness)...", end=" ", flush=True)
            c_res = await correctness_metric.ascore(
                user_input=test_case["user_input"],
                reference=test_case["reference"],
                prediction=answer,
                client=client,
                model_name="gemini-2.0-flash"
            )
            print(f"✓ {c_res.value:.1f}/5.0")
            metrics_summary["correctness"].append(c_res.value)

            # 2. 相关性
            print("  • 相关性 (Answer Relevance)...", end=" ", flush=True)
            r_res = await answer_relevance_metric.ascore(
                user_input=test_case["user_input"],
                prediction=answer,
                client=client,
                model_name="gemini-2.0-flash"
            )
            print(f"✓ {r_res.value:.1f}/5.0")
            metrics_summary["answer_relevance"].append(r_res.value)

            # 3. 推理步数
            s_res = await reasoning_steps_metric.ascore(trace=trace)
            print(f"  • 推理步数 (Reasoning Steps): {s_res.value:.0f}")
            metrics_summary["reasoning_steps"].append(s_res.value)

            # 4. 忠实性（需要上下文）
            retrieved_docs = ""
            for idx in test_case.get("docs_indices", []):
                if idx < len(all_docs):
                    retrieved_docs += all_docs[idx]["content"] + "\n\n"

            print("  • 忠实性 (Faithfulness)...", end=" ", flush=True)
            if retrieved_docs:
                f_res = await faithfulness_metric.ascore(
                    context=retrieved_docs,
                    prediction=answer,
                    client=client,
                    model_name="gemini-2.0-flash"
                )
                print(f"✓ {f_res.value:.1f}/5.0")
                metrics_summary["faithfulness"].append(f_res.value)
            else:
                print("⊘ (无上下文)")
                f_res = None

            # 保存结果
            results.append({
                "test_id": test_case["id"],
                "user_input": test_case["user_input"],
                "reference": test_case["reference"],
                "prediction": answer,
                "trace_length": len(trace),
                "correctness": c_res.value,
                "answer_relevance": r_res.value,
                "reasoning_steps": s_res.value,
                "faithfulness": f_res.value if f_res else None,
            })

        except Exception as e:
            print(f"\n❌ 测试 {test_case['id']} 执行失败: {e}")
            import traceback
            traceback.print_exc()

    # 生成总结报告
    print("\n" + "=" * 80)
    print("📈 验证结果总结")
    print("=" * 80)

    if results:
        # 计算平均值
        avg_correctness = sum(metrics_summary["correctness"]) / len(metrics_summary["correctness"]) if metrics_summary["correctness"] else 0
        avg_relevance = sum(metrics_summary["answer_relevance"]) / len(metrics_summary["answer_relevance"]) if metrics_summary["answer_relevance"] else 0
        avg_steps = sum(metrics_summary["reasoning_steps"]) / len(metrics_summary["reasoning_steps"]) if metrics_summary["reasoning_steps"] else 0
        avg_faithfulness = sum(metrics_summary["faithfulness"]) / len(metrics_summary["faithfulness"]) if metrics_summary["faithfulness"] else 0

        print(f"\n📊 平均指标:")
        print(f"  准确性 (Correctness):     {avg_correctness:.2f}/5.0")
        print(f"  相关性 (Answer Relevance): {avg_relevance:.2f}/5.0")
        print(f"  忠实性 (Faithfulness):     {avg_faithfulness:.2f}/5.0")
        print(f"  平均推理步数:            {avg_steps:.2f}")

        # 质量评级
        print(f"\n🎯 质量评级:")
        if avg_correctness >= 4.0:
            print(f"  准确性: ✓ 优秀 (≥4.0)")
        elif avg_correctness >= 3.0:
            print(f"  准确性: △ 良好 (3.0-3.9)")
        else:
            print(f"  准确性: ✗ 需改进 (<3.0)")

        if avg_relevance >= 4.0:
            print(f"  相关性: ✓ 优秀 (≥4.0)")
        elif avg_relevance >= 3.0:
            print(f"  相关性: △ 良好 (3.0-3.9)")
        else:
            print(f"  相关性: ✗ 需改进 (<3.0)")

        if avg_faithfulness > 0 and avg_faithfulness >= 4.0:
            print(f"  忠实性: ✓ 优秀 (≥4.0)")
        elif avg_faithfulness > 0 and avg_faithfulness >= 3.0:
            print(f"  忠实性: △ 良好 (3.0-3.9)")
        elif avg_faithfulness > 0:
            print(f"  忠实性: ✗ 需改进 (<3.0)")

        if avg_steps <= 3:
            print(f"  效率: ✓ 优秀 (≤3步)")
        elif avg_steps <= 5:
            print(f"  效率: △ 良好 (4-5步)")
        else:
            print(f"  效率: ✗ 需改进 (>5步)")

        # 保存详细报告
        report_path = Path("calculator_validation_report.json")
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump({
                "summary": {
                    "total_tests": len(results),
                    "avg_correctness": avg_correctness,
                    "avg_relevance": avg_relevance,
                    "avg_faithfulness": avg_faithfulness,
                    "avg_reasoning_steps": avg_steps,
                },
                "details": results
            }, f, ensure_ascii=False, indent=2)

        print(f"\n📄 详细报告已保存到: {report_path}")
        print(f"📁 Trace 日志位置:   {trace_dir}")

    print("\n✓ 验证完成！")


if __name__ == "__main__":
    asyncio.run(run_validation())
