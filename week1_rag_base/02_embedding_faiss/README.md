# 第 1 周任务 2：Embedding + FAISS 向量库

## 功能说明

把任务 1 切好的文本块转换成向量，建立 FAISS 索引，实现语义检索。

## 核心流程
data/split.json（任务1产出）
↓ 读取 + 还原
List[Document]（含内容 + 出处 + 页码）
↓ DashScopeEmbeddings（text-embedding-v3）
向量列表（每块一个 1024 维向量）
↓ FAISS.from_documents()
FAISS 索引 → 落盘到 data/faiss_index/
↓ similarity_search(query, k=2)
最相关的 2 块（含出处和页码）

## 核心知识点

| 知识点 | 说明 |
| :--- | :--- |
| `DashScopeEmbeddings` | 阿里云通义的嵌入模型客户端 |
| `text-embedding-v3` | 嵌入模型名称（1024 维向量） |
| `embed_query()` | 将单条文本转换为向量 |
| `FAISS.from_documents()` | 批量向量化并建立索引 |
| `save_local()` / `load_local()` | 索引落盘 / 加载 |
| `similarity_search(query, k)` | 语义检索，返回最相关的 k 条 |

## 文件结构
02_embedding_faiss/
├── main.py # 主程序
└── README.md # 本说明文档

## 运行

```bash
cd week1_rag_base/02_embedding_faiss
python main.py
