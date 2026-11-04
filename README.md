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
| **亮点②** | HITL 审核闸：结论生成前人工确认 | `09_hitl_audit` |
| **亮点③** | 自研 akshare 行情 MCP server | `08_mcp_quotes` |

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

### 第 2 周：Agent 与实时数据（10.2–10.9）✅ 已完成

| 编号 | 模块 | 内容 | 状态 |
| :---: | :--- | :--- | :---: |
| 05 | `05_radar` | 异动雷达：SQLite 指标库 + 阈值对比 | ✅ |
| 06 | `06_agent_analyst` | Agent 分析师：`@tool` + `create_agent` | ✅ |
| 07 | `07_langgraph_main` | 主图 + 检索子图，把 6 号拆开重搭 | ✅ |
| 08 | `08_mcp_quotes` | 行情 MCP server + Agent 接入（**亮点③**） | ✅ |

**周验收**：问「工业富联现在股价多少？顺便说说它年报里的异动」→ Agent 走完全流程 ✅

### 第 3 周：审核与门面（10.10–10.14）✅ 已完成

| 编号 | 模块 | 内容 | 状态 |
| :---: | :--- | :--- | :---: |
| 09 | `09_hitl_audit` | HITL 审核闸：`interrupt_before` 拦结论（**亮点②**） | ✅ |
| 10 | `10_web_radar` | Streamlit 两页 + 审核按钮 + 行情卡片 | ✅ |

**周验收**：浏览器里完整走一遍：上传 → 提问 → 异动清单 → 审核 → 出结论 ✅

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
├── week2_agent/ ✅ 10.2-10.9「Agent 与实时数据」
│ ├── 05_radar/ 异动雷达：SQLite + 阈值对比
│ ├── 06_agent_analyst/ Agent 分析师：@tool + create_agent
│ ├── 07_langgraph_main/ 主图 + 检索子图
│ └── 08_mcp_quotes/ 行情 MCP server（亮点③）
│
├── week3_hitl_web/ ✅ 10.10-10.14「审核与门面」
│ ├── 09_hitl_audit/ HITL 审核闸（亮点②）
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
```

---

## 📊 效果评测（10.17 完成）

### 检索命中率：90%（20 题 Top-8 页码级）

- **方法**：20 道测试题（工业富联 7 / 紫金矿业 6 / 兴业银行 7），覆盖财务数字、审计信息、业务分析、行业展望、公司治理、资本运作六类。每题人工标注标准答案所在页码（`test_questions.json`），跑 `eval_retrieval.py` 检查标准页是否出现在 Top-8 检索结果中。
- **结果**：18/20 = 90%；三家公司 **0 文件串扰**（Top-8 从未混入其他公司文件）；核心财务数字题全部第 1–2 名命中。
- **评测口径修正**（过程本身是评测严谨性的证据）：原始口径 65% → 逐题复查发现 6 道错题是答案跨页/多页导致的测试集页码标注过窄（如股东表格标题页与续表差 1 页），人工确认答案内容确在 Top-8 chunk 中后修正页码集合 → 90%。
- **已知边界（2 道真实失败）**：① 年份混淆——问 2025 年报审计所，2024 年报审计报告页（措辞几乎相同）反而排名更高；② 差 1 页——长期股权投资表格整个区域命中，但含答案的那一页未进 Top-8。

### 异动检测准确率：8/8

- **方法**：3 家公司 × 8 个指标（营收/归母净利/净息差/不良贷款率），库值逐项与年报原文核对，触发判定（金额类 ±20%、比率类 ±0.25pp）与人工核算对照。
- **结果**：库值 8/8 与年报原文一致；应触发 3 项（富联营收 +48.2%、富联归母 +52.0%、紫金归母 +61.5%）全部触发，应不触发 5 项全部未触发，0 误报 0 漏报。
- **限定**：样本 8 个指标、均为主要会计数据表中的大数，验证的是管线正确性，不覆盖边缘情况。

### 复现

```bash
# 检索评测（需先在 data/ 下准备年报 PDF 并构建 FAISS 索引，见 01/02 模块）
python eval_retrieval.py   # 输出 20 题明细 + 汇总，结果写入 data/eval_results.json
```

---

## 🔧 工程化升级包（10.30 完成）

在"能用"的基础上补上工程化的四件套：**测试、对比实验、API 服务、容器化**。

### ① 单元测试（pytest）✅

`08_mcp_quotes/test_stock_server.py`，6 个用例覆盖行情服务四个维度：

| 维度 | 用例 | 手段 |
| :--- | :--- | :--- |
| 正常路径 | 代码映射直查 / 实时源正常返回 | 假数据 DataFrame，列名对齐 akshare 真接口 |
| 降级分支 | 实时源异常 → 自动降级日K | `side_effect=Exception` 触发降级，断言「降级源：日K」标记 |
| 重试逻辑 | 第 1 次失败第 2 次成功 | `side_effect=[异常, 假数据]` + `mock.call_count == 2` 证明真的重试 |
| 错误兜底 | 双源全挂 | 断言返回「行情接口暂时不可用」，不抛裸异常 |

原则：**mock 隔离外部依赖**——测试不连真网、结果可控；`patch("stock_server.time.sleep")` 避免真实等待。

```bash
cd week2_agent/08_mcp_quotes
python -m pytest test_stock_server.py -v   # 6 passed
```

### ② 长上下文 vs RAG 对比实验 ✅

**问题**：年报全文 24–45 万 tokens，qwen-long 的 1M 窗口"装得下"——那还要不要 RAG？

**设计**：同一 20 题评测集跑两个方案，qwen-plus 作 judge 对照答案页原文判定，记录正确率 / 耗时 / token 三指标。

| 方案 | 架构 | 模型 |
| :--- | :--- | :--- |
| A：RAG | Top-8 语义检索 + 提示词拼摘录 | qwen-plus |
| B：长上下文 | 整份年报全文直接喂（不检索） | qwen-long（1M 窗口） |

**结果**（20 题全量，10.30 实测）：

| 指标 | 方案A RAG | 方案B 长上下文 |
| :--- | :---: | :---: |
| 正确率 | **13/20（65%）** | 1/19（5%，1 题连接失败） |
| 耗时 | 中位数 2.4s（除 1 题 API 抖动 1247s 外全部 <10s） | 平均 342s，最慢单题 3945s（66 分钟） |
| 平均输入 tokens | 2,920 | 244,821（84 倍） |

**结论：装得下 ≠ 找得到。** 1M 窗口能装下整份年报，但注意力被 45 万字摊薄——错数字、漏结论、混淆年份（把 2024 年报内容混入 2025 回答），正确率从 65% 跌到 5%，还慢两个数量级、贵 84 倍。检索先行把相关摘录缩到 ~3000 tokens 再答，反而又快又准。

**口径说明（评测严谨性）**：
- judge 判定含「出处页码是否正确」：RAG 有 2 题结论正确但引用页码错（如审计所答对、页码引错），按严格口径判错；若只看结论正确性，RAG 为 15/20（75%）
- RAG 错误分布：3 题检索未命中/摘录截断（说「没找到」或遗漏）、2 题页码引用错、1 题占比计算错（1.24%→1.23%）、1 题页码幻觉并混入上一年年报
- 唯一长上下文答对、RAG 答错的题（固定资产余额）说明：检索失败时，长上下文可作为兜底补救——这是两方案互补而非替代的证据

```bash
python experiment_compare.py --limit 3   # 试跑 3 题
python experiment_compare.py             # 全量 20 题，结果写入 data/compare_results.json
```

### ③ FastAPI 接口 + 鉴权 ✅

把问答能力包装成 HTTP 服务，`X-API-Key` 鉴权防公网刷接口。

| 接口 | 说明 |
| :--- | :--- |
| `GET /health` | 健康检查 |
| `POST /ask` | 财报问答，Header 带 `X-API-Key`，返回答案 + 出处列表（文件/页码/摘录） |

- **防裸奔**：`API_KEY` 环境变量缺失时**直接拒绝启动**；缺失 Key 和错误 Key 都归一为 `401`
- **懒加载**：FAISS 索引和大模型首次请求时才加载，启动快、内存可控

```bash
export API_KEY=你的密钥            # 不设置则拒绝启动
uvicorn api_app:app --port 8000

curl -X POST http://localhost:8000/ask \
  -H "X-API-Key: 你的密钥" -H "Content-Type: application/json" \
  -d '{"question": "工业富联2025年的营业收入是多少？"}'
```

### ④ Docker 部署

`Dockerfile`（多阶段层缓存：先装依赖再拷代码）+ `docker-compose.yml` 一键启动；FAISS 索引用 volume 挂载不进镜像，密钥走 `.env`（已被 .gitignore 排除）。

> ⚠️ 本机未安装 Docker，以下命令**未在本机实测**，在服务器/有 Docker 的机器上执行：

```bash
cp .env.example .env   # 填入 API_KEY 和 DASHSCOPE_API_KEY
docker compose up -d --build
curl http://localhost:8000/health
```