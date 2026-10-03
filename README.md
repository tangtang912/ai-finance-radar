# 📡 AI 财报异动雷达

> 基于 **RAG + Agent + MCP** 的 A 股财报智能分析系统  
> 上传年报 → 自动提取指标 → 同比发现异动 → 实时行情联动 → 人工审核出结论

---

## 🎯 项目目标

从一份 A 股年报 PDF 出发，构建一个**能自动发现财务异动**的智能分析系统：

1. **RAG 底座**：把年报 PDF 变成可检索的知识库（带页码溯源）
2. **指标提取**：用 pydantic 结构化提取营收/净利/毛利率/经营现金流
3. **异动雷达**：两期指标同比对比，超阈值自动标记 ⚠️
4. **Agent 分析师**：Agent 自主调用工具完成"检索 + 提取 + 对比 + 分析"
5. **实时行情**：通过 akshare MCP server 接入股价、涨跌幅等实时数据
6. **HITL 审核闸**：生成最终结论前人工确认，确保可靠性
7. **Web 门面**：Streamlit 网页版，上传 PDF / 提问 / 异动卡片 / 行情卡片

---

## 🧩 技术栈

| 模块 | 技术 |
| :--- | :--- |
| **RAG** | LangChain + DashScope Embedding + FAISS |
| **PDF 解析** | pypdf |
| **结构化提取** | pydantic v2 |
| **Agent 框架** | LangGraph + `create_agent` |
| **工具协议** | MCP（Model Context Protocol） |
| **行情数据** | akshare |
| **数据存储** | SQLite（指标库） |
| **Web 界面** | Streamlit |
| **LLM** | 通义千问（DashScope） |

---

## ⭐ 三大亮点

| 亮点 | 说明 | 对应模块 |
| :---: | :--- | :--- |
| **亮点①** | 带页码溯源的 RAG 问答 | `03_cli_qa` |
| **亮点②** | HITL 审核闸：结论生成前人工确认 | `09_hitl_gate` |
| **亮点③** | 自研 akshare 行情 MCP server | `08_akshare_mcp` |

---

## 📅 三周计划

### 第 1 周：RAG 底座（9.21–10.1）✅ 已完成

| 编号 | 模块 | 内容 | 状态 |
| :---: | :--- | :--- | :---: |
| 01 | `01_pdf_split` | PDF 加载 + 切块 + 目录指纹过滤 | ✅ |
| 02 | `02_embedding_faiss` | DashScope Embedding + FAISS 落盘 | ✅ |
| 03 | `03_cli_qa` | 命令行问答 + 页码溯源（**亮点①**） | ✅ |
| 04 | `04_financial_extraction` | pydantic 结构化指标提取 | ✅ |

**周验收**：问「XX 公司 2025 年营收多少」→ 带页码答出；指标字段能抽全 ✅

### 第 2 周：Agent 与实时数据（10.2–10.9）

| 编号 | 模块 | 内容 | 状态 |
| :---: | :--- | :--- | :---: |
| 05 | `05_radar` | 异动雷达：SQLite 指标库 + 阈值对比 | ✅ |
| 06 | `06_agent_analyst` | Agent 分析师：`@tool` + `create_agent` | 🚧 |
| 07 | `07_langgraph_main` | 主图 + 检索子图，把 6 号拆开重搭 | 📅 |
| 08 | `08_akshare_mcp` | 行情 MCP server + Agent 接入（**亮点③**） | 📅 |

**周验收**：问「工业富联现在股价多少？顺便说说它年报里的异动」→ Agent 走完全流程

### 第 3 周：审核与门面（10.10–10.14）

| 编号 | 模块 | 内容 | 状态 |
| :---: | :--- | :--- | :---: |
| 09 | `09_hitl_gate` | HITL 审核闸：`interrupt_before` 拦结论（**亮点②**） | 📅 |
| 10 | `10_web_radar` | Streamlit 两页 + 审核按钮 + 行情卡片 | 📅 |

**周验收**：浏览器里完整走一遍：上传 → 提问 → 异动清单 → 审核 → 出结论

---

## 📂 项目结构
AI财报异动雷达项目/
│
├── week1_rag_base/ ✅ 已完成（截至 10.1）
│ ├── 01_pdf_split/ 切块 + 目录指纹过滤
│ ├── 02_embedding_faiss/ 向量化 + FAISS 落盘
│ ├── 03_cli_qa/ 问答 + 溯源（亮点①）
│ └── 04_financial_extraction/ pydantic 结构化提取
│
├── week2_agent/ 🚧 10.2-10.9「Agent 与实时数据」
│ ├── 05_radar/ 异动雷达：SQLite + 阈值对比
│ ├── 06_agent_analyst/ Agent 分析师：@tool + create_agent
│ ├── 07_langgraph_main/ 主图 + 检索子图
│ └── 08_akshare_mcp/ 行情 MCP server（亮点③）
│
├── week3_hitl_web/ 📅 10.10-10.14「审核与门面」
│ ├── 09_hitl_gate/ HITL 审核闸（亮点②）
│ └── 10_web_radar/ 网页雷达：Streamlit + 审核按钮
│
└── data/ 数据目录（永不进仓库）
├── 年报PDF/ 紫金矿业/工业富联/兴业银行
├── split.json 切块结果
├── faiss_index/ FAISS 向量库
└── metrics.db SQLite 指标库

---

## 🚀 快速开始

### 1. 克隆仓库
```bash
git clone https://github.com/你的用户名/ai-finance-radar.git
cd ai-finance-radar
