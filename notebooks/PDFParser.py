# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.19.1
#   kernelspec:
#     display_name: nAgent
#     language: python
#     name: nagent
# ---

# %%
import os
import sys
from pathlib import Path

# 将 src 目录添加到 path 以导入 nagent
sys.path.append(str(Path(os.getcwd()).parent / "src"))

# poppler/tesseract(homebrew) 
os.environ["PATH"] = "/opt/homebrew/bin:" + os.environ["PATH"]

# 替换为你的代理端口，通常是 7890, 7897, 1080 等
proxy = "http://127.0.0.1:7890" 

if proxy:
    os.environ["http_proxy"] = proxy
    os.environ["https_proxy"] = proxy
    os.environ["HTTP_PROXY"] = proxy
    os.environ["HTTPS_PROXY"] = proxy

from nagent import PDFParser

# %%
book_name = "数据仓库工具箱维度建模权威指南（第3版）"
chapter = "3"
file = f"../books/{book_name}/{chapter}.pdf"

# %%
parser = PDFParser(output_dir="../output")
output_path = parser.parse(file, book_name=book_name, chapter=chapter)
print(f"解析完成，输出文件：{output_path}")


# %%
