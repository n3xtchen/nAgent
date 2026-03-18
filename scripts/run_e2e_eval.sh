#!/bin/bash
# 遇到错误立即退出
set -e

# ==========================================
# 参数解析与配置
# ==========================================
INPUT_FILE=$1
OUTPUT_BASE_DIR=$2
# 可选参数：测试集大小，默认为 10
TESTSET_SIZE=${3:-10}
# 固定配置，如有需要也可作为参数传入
CONFIG_FILE="outputs/dim_modeling_config.json"

# 参数校验
if [ -z "$INPUT_FILE" ] || [ -z "$OUTPUT_BASE_DIR" ]; then
    echo "❌ 错误: 缺少必要的参数"
    echo "用法: $0 <输入Markdown文件路径> <输出基础目录名称> [测试集大小]"
    echo "示例: $0 ./outputs/数据仓库工具箱维度建模权威指南（第3版）/6.md dim_modeling_6 10"
    exit 1
fi

# ==========================================
# 变量定义
# ==========================================
# 统一的输出根目录
OUTPUT_DIR="outputs/results/$OUTPUT_BASE_DIR"
# 文档切片输出文件
DOCS_JSON="$OUTPUT_DIR/rag_data.json"
# 测试集输出文件
TS_JSON="$OUTPUT_DIR/ts.json"

echo "=================================================="
echo "🚀 启动 Agentic RAG 端到端评估流水线"
echo "📁 输入文件: $INPUT_FILE"
echo "📁 输出目录: $OUTPUT_DIR"
echo "📏 测试集大小: $TESTSET_SIZE"
echo "=================================================="

# 创建基础输出目录
mkdir -p "$OUTPUT_DIR"

# ==========================================
# 步骤 1: 文档切片 (Chunking)
# ==========================================
echo ""
echo "[1/5] 📄 正在进行文档切片 (Chunking)..."
uv run python -m agentic_rag.chunk_cli "$INPUT_FILE" --output "$DOCS_JSON"

# ==========================================
# 步骤 2: 生成测试集 (Generate Dataset)
# ==========================================
echo ""
echo "[2/5] 🧠 正在生成测试数据集..."
uv run python apps/agentic-rag/src/agentic_rag/generate_dataset.py \
    --docs "$DOCS_JSON" \
    --output "$TS_JSON" \
    --size "$TESTSET_SIZE"

# ==========================================
# 步骤 3-5: 循环执行三种 RAG 架构的验证
# ==========================================
# 定义三种架构类型并循环执行
RAG_TYPES=("vector" "simple" "agentic")
STEP_NUM=3

for RAG_TYPE in "${RAG_TYPES[@]}"; do
    echo ""
    echo "[$STEP_NUM/5] 🔍 正在验证 RAG 架构: ${RAG_TYPE}..."

    # 为每种架构指定独立的输出子目录
    RAG_OUTPUT_DIR="${OUTPUT_DIR}_${RAG_TYPE}"

    uv run python -m agentic_rag.validation_runner \
        --config "$CONFIG_FILE" \
        --docs "$DOCS_JSON" \
        --dataset "$TS_JSON" \
        --output "$RAG_OUTPUT_DIR" \
        --rag_type "$RAG_TYPE"

    STEP_NUM=$((STEP_NUM+1))
done

echo ""
echo "=================================================="
echo "🎉 恭喜！端到端评估流水线全部执行完毕！"
echo "📊 请前往 outputs/results/ 目录下查看详细结果："
echo "   - Vector RAG 结果: ${OUTPUT_DIR}_vector/validation_results.csv"
echo "   - Simple RAG 结果: ${OUTPUT_DIR}_simple/validation_results.csv"
echo "   - Agentic RAG 结果: ${OUTPUT_DIR}_agentic/validation_results.csv"
echo "=================================================="
