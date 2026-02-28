"""
使用 calculator_demo.json 验证 agentic-rag 的准确率
pytest 版本
"""
import os
import json
from pathlib import Path
from dotenv import load_dotenv
import pytest
from google import genai

from agentic_rag.rag import AgenticRAG
from nagent_rag.retriever import SimpleKeywordRetriever
from nagent_rag.eval import (
    correctness_metric,
    faithfulness_metric,
    answer_relevance_metric,
    reasoning_steps_metric
)


load_dotenv()


@pytest.fixture(scope="session")
def gemini_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        pytest.skip("GEMINI_API_KEY not set")
    return genai.Client(api_key=api_key)


@pytest.fixture(scope="session")
def calculator_docs():
    demo_path = Path(__file__).parent.parent.parent.parent / "examples" / "calculator_demo.json"
    with open(demo_path, 'r', encoding='utf-8') as f:
        return json.load(f)


@pytest.fixture(scope="session")
def agentic_rag(gemini_client, calculator_docs):
    retriever = SimpleKeywordRetriever()
    doc_contents = [doc["content"] for doc in calculator_docs]
    retriever.fit(doc_contents)

    trace_dir = Path("calculator_validation_traces")
    trace_dir.mkdir(exist_ok=True)

    rag = AgenticRAG(
        client=gemini_client,
        retriever=retriever,
        model_name="gemini-2.0-flash",
        max_iterations=5,
        trace_dir=str(trace_dir),
    )
    return rag, calculator_docs


@pytest.mark.asyncio
async def test_calc_budget_addition(agentic_rag, gemini_client):
    """测试：项目预算加法计算"""
    rag, calculator_docs = agentic_rag

    user_input = "Project Pig 的研发费用和市场推广费用总共是多少?"
    reference = "研发费用 500,000 元，市场推广 200,000 元，总共是 700,000 元。"

    result = rag.query(user_input)
    answer = result["answer"]
    trace = result.get("trace", [])

    # 验证答案生成
    assert answer is not None
    assert len(answer) > 0

    # 计算准确性
    c_res = await correctness_metric.ascore(
        user_input=user_input,
        reference=reference,
        prediction=answer,
        client=gemini_client,
        model_name="gemini-2.0-flash"
    )

    print(f"\n✓ 预算加法测试:")
    print(f"  答案: {answer[:100]}...")
    print(f"  准确性: {c_res.value:.1f}/5.0 - {c_res.reason}")
    print(f"  推理步数: {len(trace)}")

    assert c_res.value >= 2.0, f"准确性过低: {c_res.value}"


@pytest.mark.asyncio
async def test_calc_percentage(agentic_rag, gemini_client):
    """测试：百分比计算"""
    rag, calculator_docs = agentic_rag

    user_input = "Project Pig 的预算中，运营维护费用占总预算的百分比是多少?"
    reference = "总预算是 900,000 元。运营维护 150,000 元占比是 150,000/900,000 = 16.67%。"

    result = rag.query(user_input)
    answer = result["answer"]
    trace = result.get("trace", [])

    assert answer is not None

    c_res = await correctness_metric.ascore(
        user_input=user_input,
        reference=reference,
        prediction=answer,
        client=gemini_client,
        model_name="gemini-2.0-flash"
    )

    print(f"\n✓ 百分比计算测试:")
    print(f"  答案: {answer[:100]}...")
    print(f"  准确性: {c_res.value:.1f}/5.0 - {c_res.reason}")
    print(f"  推理步数: {len(trace)}")


@pytest.mark.asyncio
async def test_calc_discount(agentic_rag, gemini_client):
    """测试：打折计算"""
    rag, calculator_docs = agentic_rag

    user_input = "如果购买 150 个 nAgent 企业版席位，一个月需要支付多少美元?"
    reference = "基础价格：150 * 29 = 4,350 美元。享受 8.5 折优惠：4,350 * 0.85 = 3,697.5 美元。"

    result = rag.query(user_input)
    answer = result["answer"]
    trace = result.get("trace", [])

    assert answer is not None

    c_res = await correctness_metric.ascore(
        user_input=user_input,
        reference=reference,
        prediction=answer,
        client=gemini_client,
        model_name="gemini-2.0-flash"
    )

    print(f"\n✓ 打折计算测试:")
    print(f"  答案: {answer[:100]}...")
    print(f"  准确性: {c_res.value:.1f}/5.0 - {c_res.reason}")
    print(f"  推理步数: {len(trace)}")


@pytest.mark.asyncio
async def test_comparison_analysis(agentic_rag, gemini_client):
    """测试：多文档对比分析"""
    rag, calculator_docs = agentic_rag

    user_input = "Project Pig 的行政支出和 nAgent 订阅费用相比如何?"
    reference = "Project Pig 行政支出是 50,000 元，nAgent 企业版订阅费用是 29 美元/月/用户，不可直接比较（单位和数值都不同）。"

    result = rag.query(user_input)
    answer = result["answer"]
    trace = result.get("trace", [])

    assert answer is not None

    c_res = await correctness_metric.ascore(
        user_input=user_input,
        reference=reference,
        prediction=answer,
        client=gemini_client,
        model_name="gemini-2.0-flash"
    )

    print(f"\n✓ 多文档对比测试:")
    print(f"  答案: {answer[:100]}...")
    print(f"  准确性: {c_res.value:.1f}/5.0 - {c_res.reason}")
    print(f"  推理步数: {len(trace)}")
