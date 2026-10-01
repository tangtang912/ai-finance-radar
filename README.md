# 📡 AI 财报异动雷达

> 基于 **RAG + LangGraph + MCP** 的 A 股财报智能分析系统  
> 让 AI 帮你从年报中挖掘财务异动，自动对比两期指标，生成带溯源的智能分析报告

---

## 🎯 项目目标

1. **RAG 底座**：把 A 股年报 PDF 变成可检索的知识库
2. **财务指标提取**：结构化提取营收、净利、毛利率、经营现金流
3. **异动对比**：两期指标同比计算，生成「异动清单」（附溯源）
4. **Agent + MCP**：接入 akshare 行情 MCP，实现「股票行情 + 财报异动」一站式问答
5. **HITL 审核闸**：关键结论生成前人工确认，确保可靠性
6. **Streamlit 界面**：上传 PDF / 提问 / 异动清单卡片 / 行情卡片

---

## 🧩 技术栈

| 模块 | 技术 |
| :--- | :--- |
| **RAG** | LangChain + DashScope Embedding + FAISS |
| **PDF 解析** | pypdf |
| **结构化提取** | pydantic |
| **Agent 框架** | LangGraph |
| **工具协议** | MCP（Model Context Protocol） |
| **行情数据** | akshare |
| **Web 后端** | FastAPI |
| **Web 前端** | Streamlit |
| **LLM** | 通义千问（DashScope） |

---

## 📅 4 周计划

### 第 1 周：RAG 底座（9.21–9.27）

| 任务 | 内容 | 产出 |
| :---: | :--- | :--- |
| 1 | 装包（akshare、faiss-cpu、pypdf 等）；下载年报 PDF | 数据就位 |
| 2-3 | PDF 加载 → 切块 → DashScope embedding → FAISS 向量库 | 检索链路通 |
| 4 | 命令行问答 + 溯源（答案附来源页码） | 第一个亮点落地 |
| 5 | 财务指标结构化提取（营收/净利/毛利率/经营现金流，pydantic） | 异动对比的原料 |

**周验收**：问「XX 公司 2025 年营收多少」→ 带页码答出；指标字段能抽全

### 第 2 周：Agent + 异动对比 + MCP（9.28–10.4）

| 任务 | 内容 | 产出 |
| :---: | :--- | :--- |
| 1-2 | 异动对比：两期指标 pandas 算同比 → 模型生成「异动清单」 | 招牌功能落地 |
| 3 | LangGraph 主图 + 检索子图（子图嵌套实战） | 架构成型 |
| 4 | akshare 行情 MCP server（仿错题本 MCP 写法）+ 测试客户端验证 | 第二个 MCP |
| 5 | Agent 接入：bind_tools + MCP client 连自己的 server | 全链路通 |

**周验收**：问「茅台现在股价多少？顺便说说它年报里的异动」→ Agent 走完全流程

### 第 3 周：组装 + 审核闸 + 界面（10.5–10.11）

| 任务 | 内容 | 产出 |
| :---: | :--- | :--- |
| 1-2 | HITL 审核闸：interrupt_before 拦在「生成分析结论」前 | 第二个亮点落地 |
| 3-4 | Streamlit 界面：上传 PDF / 提问框 / 异动清单卡片 / 行情卡片 | 可演示 |
| 5 | 向量库落盘 + 全流程贯通 | 整体跑通 |

**周验收**：浏览器里完整走一遍：上传 → 提问 → 异动清单 → 审核 → 出结论

### 第 4 周：收尾冲刺（10.12–10.14）

| 任务 | 内容 |
| :---: | :--- |
| 1 | GitHub 上传 + README（架构图 + 演示截图） |
| 2 | 简历项目栏定稿 + 面试故事排练 |
| 3 | 《面试知识库》更新 + 录 1 分钟演示视频 |

---

## 📂 项目结构
ai-finance-radar/
├── README.md
├── .gitignore
├── LICENSE
├── requirements.txt
│
├── week1_rag_base/ # 第1周：RAG 底座
│ ├── 01_pdf_split/ # ✅ PDF加载+切块
│ │ ├── main.py
│ │ └── README.md
│ ├── 02_embedding_faiss/ # 📅 待学习
│ ├── 03_cli_qa/ # 📅 待学习
│ └── 04_financial_extraction/ # 📅 待学习
│
├── week2_agent_mcp/ # 第2周：Agent + MCP
│ ├── 01_anomaly_comparison/ # 📅 待学习
│ ├── 02_langgraph_main/ # 📅 待学习
│ ├── 03_akshare_mcp/ # 📅 待学习
 └── 04_agent_integration/ # 📅 待学习
│
├── week3_ui_review/ # 第3周：界面 + 审核闸
│ ├── 01_hitl_review/ # 📅 待学习
│ ├── 02_streamlit_ui/ # 📅 待学习
│ └── 03_persistence/ # 📅 待学习
│
├── week4_final/ # 第4周：收尾冲刺
│ └── README.md # 📅 待补充
│
└── data/ # 数据存储
├── 年报PDF/ # 年报 PDF（不上传）
│ ├── 紫金矿业2024年报.pdf
│ ├── 紫金矿业2025年报.pdf
│ ├── 工业富联2024年报.pdf
│ ├── 工业富联2025年报.pdf
│ ├── 招商银行2024年报.pdf
│ └── 招商银行2025年报.pdf
└── split.json # 切块结果（自动生成）

text

---

## 🚀 快速开始

### 1. 克隆仓库
```bash
git clone https://github.com/你的用户名/ai-finance-radar.git
cd ai-finance-radar
2. 安装依赖

bash
pip install -r requirements.txt
3. 配置环境变量

创建 .env 文件：

env
DASHSCOPE_API_KEY=sk-xxxxxxxx
4. 准备年报 PDF

从 巨潮资讯网 下载以下公司的 2024 / 2025 年报：

紫金矿业（601899）
工业富联（601138）
招商银行（600036）
放入 data/年报PDF/ 文件夹，例如：

text
data/年报PDF/
├── 紫金矿业2024年报.pdf
├── 紫金矿业2025年报.pdf
├── 工业富联2024年报.pdf
├── 工业富联2025年报.pdf
├── 招商银行2024年报.pdf
└── 招商银行2025年报.pdf

---

## 🚀 快速开始

### 1. 克隆仓库
```bash
git clone https://github.com/你的用户名/ai-finance-radar.git
cd ai-finance-radar
