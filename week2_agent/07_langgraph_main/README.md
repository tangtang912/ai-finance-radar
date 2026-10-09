# 07 号：LangGraph 主图 + 检索子图

## 功能说明

把 6 号的 Agent 用 **LangGraph 手写重搭**，演示两个关键概念：

1. **手写主图**：agent ↔ tools 循环（不依赖 `create_agent` 黑盒）
2. **子图嵌套**：把"检索 → 格式化"打包成独立小图，工具内部调用

## 架构分层图

```
┌──────────────────────────────────────────────┐
│ 主图（AgentState）                            │
│                                              │
│ START → agent ─┬─→ tools → agent（循环）      │
│                └─→ END（无工具调用时）         │
│                                              │
│ agent 节点内部调用 3 个工具                    │
│ tools 节点 = ToolNode([3个工具])              │
└──────────────────────────────────────────────┘
↓ 工具内部
┌──────────────────────────────────────────────┐
│ 检索子图（RetrievalState）                    │
│                                              │
│ START → retrieve → format → END              │
└──────────────────────────────────────────────┘
↓ 底层能力
┌──────────────────────────────────────────────┐
│ 05底座（radar 模块）                          │
│ FAISS 索引 + extract_indicators + SQLite     │
└──────────────────────────────────────────────┘
```

## 核心知识点

| 知识点 | 说明 |
| :--- | :--- |
| **手写主图** | `StateGraph` + `add_node` + `add_conditional_edges` |
| **ReAct 循环** | `agent → tools → agent` 形成闭环 |
| **条件路由** | `route_after_agent` 判断有无 `tool_calls` |
| **ToolNode** | LangGraph 预置节点，自动执行工具调用 |
| **子图嵌套** | `retrieval_graph.invoke()` 在工具内部运行 |
| **`add_messages`** | LangGraph 预置 reducer，自动合并消息 |
| **`bind_tools`** | 把工具绑定到 LLM，模型可自主调用 |

## 文件结构

```
07_langgraph_main/
├── graph_agent.py  # 主程序（main.py 不能当模块名，故命名 graph_agent.py）
├── draw_graph.py   # 辅助脚本：一键生成主图/子图的流程图
└── README.md       # 本说明文档
```

## 三层结构详解

### 第 1 层：检索子图

```python
class RetrievalState(TypedDict):
    question: str      # 输入：用户问题
    hits: list         # 中间：检索到的文档
    context: str       # 输出：格式化文本

# START → retrieve → format → END
```

为什么独立成子图？

- 检索逻辑可以独立测试和复用
- 未来想换检索策略（如混合检索、多路召回），只改子图，不影响主图

### 第 2 层：三个工具

| 工具 | 内部实现 |
| :--- | :--- |
| `search_annual_report` | 调用检索子图 |
| `extract_financial_indicators` | 调用 `radar.extract_indicators` |
| `compare_two_years` | 查 `radar.open_metric_db()` |

### 第 3 层：主图（agent ↔ tools）

```
START → agent
         ↓
   有 tool_calls？
    ├─ 是 → tools → agent（回到模型）
    └─ 否 → END
```

为什么手写而不直接用 create_agent？

- 完全掌控执行流程，方便后续插入 HITL 审核闸
- 可以自定义中间件、日志、状态记录

## 运行

```bash
cd week2_agent/07_langgraph_main
python graph_agent.py
```
