import argparse
import json
import os
import sys
from nagent_rag import ChunkingProcessor

def main():
    parser = argparse.ArgumentParser(description="nAgent RAG 文档分块 CLI")
    parser.add_argument("path", type=str, help="要处理的文件或目录路径")
    parser.add_argument("--chunk-size", type=int, default=1000, help="分块大小 (默认: 1000)")
    parser.add_argument("--chunk-overlap", type=int, default=200, help="重叠大小 (默认: 200)")
    parser.add_argument("--output", type=str, help="输出 JSON 文件路径 (如果未指定，则输出到 stdout)")
    parser.add_argument("--recursive", action="store_true", help="是否递归处理目录")

    args = parser.parse_args()

    if not os.path.exists(args.path):
        print(f"错误: 路径不存在: {args.path}", file=sys.stderr)
        sys.exit(1)

    # 初始化处理器
    processor = ChunkingProcessor(
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap
    )

    try:
        # 处理路径
        chunked_docs = processor.process_path(args.path, recursive=args.recursive)

        if not chunked_docs:
            print(f"警告: 在 {args.path} 中没有找到有效的文本文件或未生成分块。", file=sys.stderr)
            sys.exit(0)

        # 序列化为 JSON
        output_json = json.dumps(chunked_docs, ensure_ascii=False, indent=2)

        # 输出结果
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(output_json)
            print(f"成功将 {len(chunked_docs)} 个分块保存至: {args.output}", file=sys.stderr)
        else:
            print(output_json)

    except Exception as e:
        print(f"处理过程中出错: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
