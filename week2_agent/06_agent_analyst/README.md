# Agent-analyst

## 功能说明

把 5 号雷达的能力包装成 **3 个 `@tool`**，用 `create_agent` 组装成能自主决策的财报异动分析师。

## 核心流程
用户提问："工业富联2025年营收异动的原因是什么？"
↓ create_agent（ReAct 循环）
🔧 调用 extract_financial_indicators(工业富联, 2025, 营业收入)
↓ 观察结果
🔧 调用 compare_two_years(工业富联, 营业收入)
↓ 观察结果
🔧 调用 search_annual_report(工业富联营收增长原因)
↓ 观察结果
💭 综合三段信息，给出结论（含页码溯源）

## 三个工具

| 工具 | 封装自 | 作用 |
| :--- | :--- | :--- |
| `search_annual_report` | `radar.db.similarity_search` | 语义检索年报段落（带页码） |
| `extract_financial_indicators` | `radar.extract_indicators` | 提取指定指标并换算成亿元 |
| `compare_two_years` | `radar.open_metric_db` | 查 SQLite 指标库，算同比+标记异动 |

## 核心知识点

| 知识点 | 说明 |
| :--- | :--- |
| **`sys.path.insert`** | 把 05_radar 加入搜索路径，跨文件夹 import |
| **`@tool` 装饰器** | 把普通函数包装成 Agent 可调用工具 |
| **`create_agent`** | LangChain 官方 Agent 创建函数 |
| **`model=radar.llm`** | 复用 5 号模块里已经初始化好的 LLM |
| **`stream_mode="values"`** | 流式观察 Agent 每一步 |
| **ReAct 提示词** | 约束"思考→调用→观察→再思考" |
| **`if __name__ == "__main__"`** | 被 10 号导入时不卡在 `input()` |

## 文件结构
06_agent_analyst/
├── analyst.py # 主程序
└── README.md # 本说明文档

## 依赖

- 5 号 `05_radar` 模块（自动通过 `sys.path` 接入）
- `data/faiss_index/` 已生成
- `data/metrics.db` 已有数据（跑过 5 号脚本）

## 运行

```bash
cd week2_agent/06_agent_analyst
python analyst.py
radar底座已接入：索引+提取+换算+指标库 全部可用✅

请问（输入q退出）: 工业富联2025年营收异动的原因是什么？

Agent 工作过程：
🔧 调用工具：['extract_financial_indicators']
🔧 调用工具：['compare_two_years']
🔧 调用工具：['search_annual_report']
💭 根据工具返回结果：工业富联 2025 年营业收入 9028.87 亿元，同比 +48.2%（⚠️异动），
   增长主要来自云计算及 AI 服务器业务的强劲需求
   （原因段落引用检索结果中的页码）。
