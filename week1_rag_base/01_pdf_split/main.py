import os

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import glob, json, re

#0.目录页指纹：连续点连线是目录的专属特征
def is_toc_or_noise(chunk):
    t = chunk.page_content
    if re.search(r"[\.…]{4,}", t):
        return True
    if len(t.strip()) < 20:
        return True
    return False

#1.年报目录和文件
data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data")
contents = os.path.join(data_dir, "年报PDF")
files = sorted(glob.glob(contents + "/*.pdf"))
print(f"找到 {len(files)} 份年报")

#2.构造切块器
splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50,
)

#3.循环每份文件，切块
all_chunks = []
for file in files:
    loader = PyPDFLoader(file)
    pages = loader.load()
    chunks = splitter.split_documents(pages)
    all_chunks.extend(chunks)
    file_name = file.split("/")[-1]
    print(f"{file_name}:{len(chunks)}块")
print(f"共切出{len(all_chunks)}块")

#3.5.过滤目录页和封面噪音
all_chunks = [c for c in all_chunks if not is_toc_or_noise(c)]
print(f"过滤后剩{len(all_chunks)}块")

#4.存盘
stores = []
for c in all_chunks:
    file_name = c.metadata["source"].split("/")[-1].replace(".pdf", "")
    stores.append({
        "content": f"[{file_name}]" + c.page_content,
        "source": c.metadata["source"],
        "page": c.metadata["page"],
    })

with open(os.path.join(data_dir, "split.json"), "w", encoding="utf-8") as f:
    json.dump(stores, f, ensure_ascii=False)
print("数据已保存至 data/split.json")

#5.抽查文件
for c in all_chunks[:2]:
    print("="*40)
    print("source:",c.metadata["source"],"第",c.metadata["page"]+1,"页")
    print("content:",c.page_content[:150])
