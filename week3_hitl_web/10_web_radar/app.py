# 10号：网页雷达（Streamlit）——三大亮点合体
# 07主图（LangGraph编排）+ 08行情工具（MCP）+ 09审核闸（HITL）搬进网页：
# 聊天界面 + 批准/驳回按钮 + 行情卡片
# 跑法：在 week3_hitl_web/10_web_radar 下执行 streamlit run app.py

import asyncio, os, re, sys, threading
import streamlit as st

# 1. 接入 07（路径从本文件爬两层到项目根，再进 week2_agent）
BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE, "..", "..", "week2_agent", "07_langgraph_main"))
import graph_agent

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command
from langchain_mcp_adapters.client import MultiServerMCPClient

SERVER = os.path.join(BASE, "..", "..", "week2_agent", "08_mcp_quotes", "stock_server.py")
PYTHON = sys.executable

# 2. MCP 是异步的，而 Streamlit 每次点击按钮都是新线程——
#    开一个常驻事件循环线程，所有协程都丢给它跑（否则 MCP 会话会被反复拆毁）
_loop = asyncio.new_event_loop()
threading.Thread(target=_loop.run_forever, daemon=True).start()

def run_coro(coro):
    """把协程丢给常驻循环，等它跑完拿结果"""
    return asyncio.run_coroutine_threadsafe(coro, _loop).result()

async def build_app():
    """组装网页版主图：07三件套 + 08行情工具 + 09审核闸开关"""
    client = MultiServerMCPClient({
        "stock": {"command": PYTHON, "args": [SERVER], "transport": "stdio"},
    })
    mcp_tools = await client.get_tools()
    return graph_agent.build_main_graph(
        graph_agent.tools + mcp_tools,
        checkpointer=MemorySaver(),
        interrupt_before=["agent"],
    )

def ensure_app():
    """第一次运行时组装，之后复用（session_state 跨按钮点击保存）"""
    if "app" not in st.session_state:
        st.session_state.app = run_coro(build_app())
    if "config" not in st.session_state:
        st.session_state.config = {"configurable": {"thread_id": "web-1"}}
    if "gate_open" not in st.session_state:
        st.session_state.gate_open = False

ensure_app()
app = st.session_state.app
config = st.session_state.config

# 3. 状态读取（和 09 一样的两个判断）
def get_messages():
    return app.get_state(config).values.get("messages", [])

def is_finished():
    """最后一条是"没有工具调用"的AIMessage = agent 已给出最终答复"""
    msgs = get_messages()
    if not msgs:
        return False
    last = msgs[-1]
    return isinstance(last, AIMessage) and not getattr(last, "tool_calls", None)

# 4. 三个动作：提问 / 批准 / 驳回——每个动作跑到下一道闸或结束
def do_submit(question):
    run_coro(app.ainvoke({"messages": [HumanMessage(content=question)]}, config))
    st.session_state.gate_open = not is_finished()

def do_approve():
    run_coro(app.ainvoke(Command(resume=True), config))
    st.session_state.gate_open = not is_finished()

def do_reject(feedback):
    run_coro(app.aupdate_state(config, {"messages": [HumanMessage(content=feedback)]}))
    run_coro(app.ainvoke(Command(resume=True), config))
    st.session_state.gate_open = not is_finished()

# 5. 行情卡片：把 get_realtime_quote 的固定格式文本解析成数字，用 st.metric 展示
def to_text(content):
    """消息内容可能是 str，也可能是 content blocks 列表——统一转成纯文本"""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(b.get("text", "") for b in content if isinstance(b, dict))
    return str(content)

def parse_quote(text):
    m = re.search(r"(\d{6})\s*最新价\s*([\d.]+)\s*元，涨跌\s*[+\-]?[\d.]+\s*元（([+\-]?[\d.]+)%）", text)
    if m:
        return m.group(1), float(m.group(2)), float(m.group(3))
    m = re.search(r"(\d{6})\s*最新交易日\s*[\d\-]+：收\s*([\d.]+)，.*?涨跌幅\s*([+\-]?[\d.]+)%", text)
    if m:
        return m.group(1), float(m.group(2)), float(m.group(3))
    return None

def render_tool(tm):
    """工具结果：行情类渲染成卡片，其余折叠显示"""
    text = to_text(tm.content)
    card = parse_quote(text) if tm.name == "get_realtime_quote" else None
    if card:
        code, price, pct = card
        with st.expander(f"📈 行情卡片 · {code}", expanded=True):
            st.metric(label=f"{code} 最新价", value=f"{price} 元", delta=f"{pct}%")
            st.caption(text)
    else:
        with st.expander(f"🔧 工具：{tm.name}"):
            st.text(text[:500])

# 6. 页面骨架：侧边栏 + 聊天流 + 审核闸
st.set_page_config(page_title="AI财报异动雷达", page_icon="📡")
st.title("📡 AI财报异动雷达 · 网页版")
st.caption("07 主图（LangGraph）+ 08 行情（MCP）+ 09 审核闸（HITL）")

with st.sidebar:
    st.markdown("## 三大亮点")
    st.markdown("- ① 答案溯源：数字带文件名+页码\n- ② HITL：每步行动人工审核\n- ③ 自写 MCP：行情工具跨进程调用")
    if st.button("🔄 清空会话"):
        # 注意：旧 MCP 子进程随本次进程结束统一回收，演示项目可接受
        st.session_state.clear()
        st.rerun()

# 聊天流：从检查点读真实消息渲染（检查点 = 唯一事实来源）
for m in get_messages():
    if isinstance(m, HumanMessage):
        with st.chat_message("user"):
            st.markdown(to_text(m.content))
    elif isinstance(m, AIMessage):
        if m.content:
            with st.chat_message("assistant"):
                st.markdown(to_text(m.content))
    else:  # ToolMessage：工具执行结果
        render_tool(m)

# 审核闸（09 的网页版）：闸开着就显示按钮，关着就显示提问框
if st.session_state.gate_open:
    st.divider()
    st.warning("⏸️ 审核闸：Agent 下一步要行动，请审核")
    c1, c2 = st.columns([1, 2])
    if c1.button("✅ 批准继续", use_container_width=True):
        do_approve()
        st.rerun()
    with c2:
        fb = st.text_input("驳回意见（可留空）", key="reject_input")
        if st.button("❌ 驳回并给意见", use_container_width=True):
            do_reject(fb.strip() or "请重新分析")
            st.rerun()
else:
    question = st.chat_input("问点什么？（如：工业富联年报营收异动后股价有什么反应）")
    if question:
        do_submit(question)
        st.rerun()
