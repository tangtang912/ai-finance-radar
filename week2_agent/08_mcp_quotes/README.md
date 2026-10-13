# 08 号：自写行情 MCP server（三大亮点③）

## 功能说明

把 akshare 的行情能力包装成 **MCP 工具**，供 Agent 通过 **MCP 协议**调用，实现"财报异动 + 实时行情"一体化问答。

本模块包含两个文件：
- `stock_server.py`：MCP 服务器（提供 3 个行情工具）
- `mcp_agent.py`：MCP 客户端（把行情工具接进 07 号主图）

---

## 为什么用 MCP 而不是普通 @tool？

| 对比项 | 普通 @tool | MCP server |
| :--- | :--- | :--- |
| 调用方式 | 进程内 import | **跨进程（stdio）** |
| 复用性 | 只能本项目用 | **任何 MCP 客户端**（Claude Desktop / Cursor / 其他 Agent） |
| 语言无关 | Python 内 | **任何语言**都能调 |
| 部署位置 | 跟主程序绑定 | 可独立部署、独立升级 |
| 隔离性 | 与主程序同生共死 | **独立子进程**，互不影响 |

**一句话**：普通 tool 是"内置能力"，MCP server 是"对外服务"。

---

## 完整架构图
┌───────────────────────────────────────────────────────┐
│ mcp_agent.py（08 号客户端） │
│ │
│ ┌─────────────────────────────────────────────────┐ │
│ │ 07 号主图（LangGraph） │ │
│ │ │ │
│ │ agent ↔ tools │ │
│ │ │ │
│ │ tools = [ │ │
│ │ search_annual_report, ← 07 内置 │ │
│ │ extract_financial_indicators, ← 07 内置 │ │
│ │ compare_two_years, ← 07 内置 │ │
│ │ get_stock_code, ← MCP 行情 ★ │ │
│ │ get_realtime_quote, ← MCP 行情 ★ │ │
│ │ get_stock_history, ← MCP 行情 ★ │ │
│ │ ] │ │
│ └─────────────────────────────────────────────────┘ │
│ │
│ MultiServerMCPClient（stdio） │
│ ↓ 启动子进程 │
│ stock_server.py（08 号 MCP server） │
│ ↓ 调用 │
│ akshare（东财行情） │
└───────────────────────────────────────────────────────┘
↓ 底层数据
┌──────────────┐ ┌──────────────┐
│ FAISS 索引 │ │ metrics.db │
│ （年报） │ │ （指标） │
└──────────────┘ └──────────────┘

---

## 三个 MCP 工具

| 工具 | 功能 | 说明 |
| :--- | :--- | :--- |
| `get_stock_code` | 公司名 → 股票代码 | 确定性映射，不靠大模型 |
| `get_realtime_quote` | 查最新行情 | 实时源失败时**自动降级**为日K |
| `get_stock_history` | 查日K历史 | 默认最近45天，返回10个交易日摘要 |

---

## 核心知识点

| 知识点 | 说明 |
| :--- | :--- |
| **`FastMCP("股票行情服务")`** | 创建 MCP 服务器实例 |
| **`@mcp.tool()`** | 把函数注册为 MCP 工具 |
| **`mcp.run()`** | 启动服务器（默认 stdio 传输） |
| **`MultiServerMCPClient`** | LangChain 官方的 MCP 客户端适配器 |
| **`await client.get_tools()`** | 从 MCP server 拉取工具列表 |
| **`_retry()` 重试** | 网络接口断连时自动重试 2 次 |
| **自动降级** | 实时接口失败 → 用日K兜底 |
| **确定性映射** | 公司代码写死在 `COMPANY_CODES`，不靠 LLM |
| **异步调用** | MCP 走 stdio 是异步 IO，整条链用 `async/await` |

---

## 文件结构
08_mcp_quotes/
├── stock_server.py # MCP 服务器（三大工具）
├── mcp_agent.py # MCP 客户端：接进 07 主图
└── README.md # 本说明文档

## 输出
索引加载完成✅
radar底座已接入：索引+提取+换算+指标库 全部可用 ✅
手写图已组装：主图（agent↔tools 循环）+ 检索子图（retrieve→format）✅
07已接入：三件套工具 + build_main_graph ✅
[10/13/26 15:49:27] INFO     Processing request of type            server.py:733
                             ListToolsRequest                                   
MCP 工具已接入：['get_stock_code', 'get_realtime_quote', 'get_stock_history'] ✅

请问（输入q退出）:工业富联现在股价多少？顺便说说它年报里的异动

Agent 工作过程：
🔧 调用工具： ['get_stock_code', 'search_annual_report']
[10/13/26 15:49:58] INFO     Processing request of type            server.py:733
                             CallToolRequest                                    
                    INFO     Processing request of type            server.py:733
                             ListToolsRequest                                   
🔧 调用工具： ['get_realtime_quote']
[10/13/26 15:50:00] INFO     Processing request of type            server.py:733
                             CallToolRequest                                    
                    INFO     Processing request of type            server.py:733
                             ListToolsRequest                                   
💭 截至目前，工业富联（601138）最新股价为 **52.29 元**，上涨 0.24 元（+0.46%），今开 50.46 元，盘中最高 53.30 元，最低 49.66 元。

关于其年报中的“异动”，检索结果显示：

- 多处涉及**其他综合收益**的显著变动：  
  - 2025年年报第198页显示，其他综合收益“本期发生金额”合计为 **-141.14亿元**（税后归属），其中大幅减少主要源于“前期计入其他综合收益当期转入损益/留存收益”的调整及所得税影响；  
  - 对比2024年年报（第130页），权益法下可转损益的其他综合收益已由负转正，且整体其他综合收益变动幅度扩大，反映公司对联营/合营企业投资、外币折算、金融资产重分类等事项的会计处理影响增强。

- 此外，2025年年报第127页披露，“综合收益总额”达 **23.55亿元**，较2024年明显提升（2024年未直接列示但可推知约数亿元量级），主要驱动来自**净利润增长叠加其他综合收益改善**（如金融资产公允价值变动回正）。

需注意：当前检索片段未明确指出“异常”或“风险性异动”，更多体现为**会计政策执行深化与业务结构变化下的正常财务反映**（如AI服务器高毛利订单落地带动利润质量提升）。如需进一步定位具体业务异动原因（如AI服务器收入暴增是否导致毛利率/现金流异动），我可继续调取财务指标或对比分析。
