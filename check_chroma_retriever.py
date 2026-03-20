import os
import shutil
import time

from nagent_rag.retrievers.chroma import ChromaRetriever

def main():
    print("开始测试 ChromaRetriever...")
    persist_dir = "./temp_test_chroma_db"
    
    # 确保开始前没有残留的临时目录
    if os.path.exists(persist_dir):
        shutil.rmtree(persist_dir)
        
    try:
        # 1. 实例化 ChromaRetriever
        print(f"1. 初始化 ChromaRetriever (保存路径: {persist_dir})")
        retriever = ChromaRetriever(
            collection_name="test_collection",
            persist_directory=persist_dir
        )
        
        # 2. 准备数据并进行 Embedding (Fit 过程)
        print("2. 准备测试文档并执行 fit...")
        documents = [
            {
                "id": "doc_ai",
                "content": "人工智能（AI）和机器学习技术正在飞速发展，深刻改变了各行各业的运作方式。深度学习模型在图像识别和自然语言处理方面取得了突破。",
                "metadata": {"category": "technology", "topic": "AI"}
            },
            {
                "id": "doc_weather",
                "content": "明天北京的天气预计为晴转多云，最高气温25摄氏度，最低气温15摄氏度，适合户外活动。",
                "metadata": {"category": "weather", "city": "Beijing"}
            },
            {
                "id": "doc_food",
                "content": "四川火锅以麻、辣、鲜、香著称，底料通常包含牛油、辣椒、花椒和各种香料。它是中国最受欢迎的美食之一。",
                "metadata": {"category": "food", "cuisine": "Sichuan"}
            }
        ]
        
        retriever.fit(documents)
        print(f"   成功存入 {len(documents)} 个文档。")
        
        # 3. 验证 Querying (检索过程)
        print("3. 执行相似度查询...")
        query_text = "机器学习和AI发展"
        top_k = 1
        print(f"   查询文本: '{query_text}'")
        
        results = retriever.get_top_k(query_text, k=top_k)
        
        if not results:
            raise AssertionError("查询结果为空！")
            
        top_doc = results[0]
        print(f"   返回的最相关文档 ID: {top_doc.get('id')}")
        print(f"   返回的文档内容: {top_doc.get('content')[:30]}...")
        print(f"   返回的文档元数据: {top_doc.get('metadata')}")
        print(f"   距离分数 (_score): {top_doc.get('_score')}")
        
        # 断言结果
        assert top_doc.get("id") == "doc_ai", f"期望最相关的文档是 doc_ai, 但得到的是 {top_doc.get('id')}"
        assert top_doc.get("metadata", {}).get("category") == "technology", "文档元数据读取错误"
        print("   ✅ 查询结果符合预期！")
        
        # 4. 验证清理逻辑
        print("4. 测试 clear() 清空逻辑...")
        retriever.clear()
        
        # 清空后应该查询不到或者返回空结果/报错 (这里可以再试着存一个或者简单调用get_top_k)
        results_after_clear = retriever.get_top_k("机器学习", k=1)
        assert len(results_after_clear) == 0, "清空后仍能查询到结果！"
        print("   ✅ 清空逻辑测试通过！")
        
        print("\n✅ 所有验证步骤成功完成！")
        
    except Exception as e:
        print(f"\n❌ 验证失败: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        # 5. 清理临时目录
        if os.path.exists(persist_dir):
            print(f"清理临时目录: {persist_dir}")
            # 等待一小会儿确保 ChromaDB 释放文件锁 (Windows下常见问题)
            time.sleep(1)
            try:
                shutil.rmtree(persist_dir)
            except Exception as e:
                print(f"   警告: 无法完全删除临时目录: {e}")

if __name__ == "__main__":
    main()
