import os
import json
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS

#1.目录和文件
data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data")
chunk_file = os.path.join(data_dir, "split.json")
index = os.path.join(data_dir, "faiss_index")

#2.读取json
with open(chunk_file,"r",encoding="utf-8")as f:
    chunk_list = json.load(f)
print(f"读回{len(chunk_list)}块")

files = []
for chunk in chunk_list:
    files.append(Document(
        page_content=chunk["content"],
        metadata = {"source":chunk["source"],"page":chunk["page"]}
    ))

#3.向量化
embedder = DashScopeEmbeddings(model="text-embedding-v3")
text_vector = embedder.embed_query("2025年净利润是多少")
print(f"embedding正常，向量维度：{len(text_vector)}")

#4.建立索引+存盘
print("正在建索引……")
db = FAISS.from_documents(files,embedder)
db.save_local(index)
print(f"索引已保存到{index}")

#5.验收+语义检索
for query in ["2025年净利润是多少", "铜价变动对公司有什么影响", "净息差下降的原因"]:
    print("\n"+"=" *50)
    print(f"提问:",query)
    hits = db.similarity_search(query,k=2)
    for i,chunk in enumerate(hits,1):
        file_name = os.path.basename(chunk.metadata["source"])
        print(f"[{i}]{file_name}第{chunk.metadata['page']+1}页")
        print(f"{chunk.page_content[:80]}...")




