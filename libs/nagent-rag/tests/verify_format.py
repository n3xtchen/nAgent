import json
import os
from nagent_rag.chunking import ChunkingProcessor

def verify():
    # 目标文件
    target_file = "outputs/数据仓库工具箱维度建模权威指南（第3版）/2.md"
    if not os.path.exists(target_file):
        print(f"错误: 找不到文件 {target_file}")
        return

    # 初始化处理器 (设置较小的 chunk_size 以产生多个分块)
    processor = ChunkingProcessor(chunk_size=1000, chunk_overlap=200)

    print(f"正在处理文件: {target_file}...")
    chunked_docs = processor.process_path(target_file)

    if not chunked_docs:
        print("错误: 未生成任何分块")
        return

    print(f"生成了 {len(chunked_docs)} 个分块。")

    # 检查第一个分块的格式
    first_doc = chunked_docs[0]
    required_keys = ["id", "content", "metadata"]

    is_valid = all(key in first_doc for key in required_keys)

    print("\n--- 格式检查 ---")
    for key in required_keys:
        status = "✅" if key in first_doc else "❌"
        print(f"{key}: {status}")

    if is_valid:
        print("\n结论: 格式与 rag_data.json 一致 (包含 id, content, metadata)")
    else:
        print("\n结论: 格式不一致!")

    # 打印示例数据
    print("\n--- 分块示例 (前2个) ---")
    print(json.dumps(chunked_docs[:2], ensure_ascii=False, indent=2))

if __name__ == "__main__":
    verify()
