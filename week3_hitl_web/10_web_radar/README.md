# 10 号：网页雷达（Streamlit）——三大亮点合体

## 功能说明

把前面的能力全部搬到浏览器上：

- **07 主图**（LangGraph 编排）
- **08 行情工具**（MCP 跨进程调用）
- **09 审核闸**（HITL 人工把关）

最终形成一个**可演示的 Web 应用**：聊天界面 + 批准/驳回按钮 + 行情卡片。

## 🌟 三大亮点合体

| 亮点 | 在 Web 上的呈现 |
| :---: | :--- |
| **① 答案溯源** | AI 回答里带「文件名 + 页码」 |
| **② HITL 审核闸** | 每步行动前弹出「✅ 批准 / ❌ 驳回」按钮 |
| **③ 自写 MCP 行情** | 股价用 `st.metric` 渲染成**行情卡片** |

## 核心流程
用户输入问题
↓ do_submit()
Agent 跑到第一道闸，暂停
↓ gate_open = True
页面显示「审核闸」按钮
↓ 用户点「✅ 批准」
do_approve() → 继续跑到下一道闸或结束
↓ 用户点「❌ 驳回」+ 意见
do_reject() → Agent 按意见重新想
↓ 最终结论
页面渲染完整的聊天记录（含行情卡片）
## 核心知识点

| 知识点 | 说明 |
| :--- | :--- |
| **`asyncio` 常驻事件循环** | Streamlit 每次按钮点击是新线程，需独立循环跑 MCP 异步调用 |
| **`run_coro()`** | 把协程丢进常驻循环，同步等待结果 |
| **`st.session_state`** | 跨按钮点击保存 `app`、`config`、`gate_open` |
| **`st.chat_message`** | 聊天界面组件 |
| **`st.chat_input`** | 底部输入框 |
| **`st.metric`** | 行情卡片（价格 + 涨跌幅） |
| **`st.expander`** | 折叠展示工具结果 |
| **`get_state(config)`** | 从检查点读取真实消息（唯一事实来源） |

## 文件结构
10_web_radar/
├── app.py           # Streamlit 主程序
└── README.md        # 本说明文档
## 运行

```bash
cd week3_hitl_web/10_web_radar
streamlit run app.py