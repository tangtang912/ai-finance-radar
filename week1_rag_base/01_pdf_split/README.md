# 第 1 周任务 1：PDF 加载 + 切块 + 存盘

## 功能说明

把年报 PDF 变成可检索的文本块，为后续的向量化和 RAG 检索做准备。

## 核心流程
data/年报PDF/*.pdf
↓ PyPDFLoader（逐页加载）
List[Document]（每页一个 Document）
↓ RecursiveCharacterTextSplitter（切块）
List[Document]（每块 500 字符，重叠 50）
↓ 提取内容/出处/页码
data/split.json（结构化存储）

## 核心知识点

| 知识点 | 说明 |
| :--- | :--- |
| `PyPDFLoader` | LangChain 的 PDF 加载器，逐页返回 `Document` |
| `RecursiveCharacterTextSplitter` | 递归字符切块器，按语义边界切割 |
| `chunk_size` | 每块最大字符数（本课 500） |
| `chunk_overlap` | 块间重叠字符数（本课 50），防止信息断层 |
| `metadata` | Document 元数据，含 `source`（文件路径）和 `page`（页码） |

## 数据准备

在项目根目录创建 `data/年报PDF/` 文件夹，放入 2-3 份年报 PDF（从巨潮资讯网下载）。

## 运行

```bash
cd week1_rag_base/01_pdf_split
python main.py
