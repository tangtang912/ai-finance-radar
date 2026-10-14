import os, sys
from typing import Annotated, TypedDict
from langchain_core.tools import tool
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode

# 1.接入5号底座
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "05_radar"))
import radar
print("radar底座已接入：索引+提取+换算+指标库 全部可用 ✅")

# ==================== 第 1 层：检索子图（子图嵌套实战） ====================
# 把"检索 → 格式化"两条流水线打包成一个独立的小图，大图把它当节点用

class RetrievalState(TypedDict):
    question: str
    hits: list
    context: str

def retrieve_node(state: RetrievalState):
    """节点1：语义检索，召回4段最相关的年报摘录（和6号一致，方便10题对照）"""
    hits = radar.db.similarity_search(state["question"], k=4)
    return {"hits": hits}

def format_node(state: RetrievalState):
    """节点2：把摘录格式化成带页码的文本"""
    lines = []
    for i, chunk in enumerate(state["hits"], 1):
        file_name = os.path.basename(chunk.metadata["source"])
        lines.append(f"[{i}]{file_name}第{chunk.metadata['page']+1}页：{chunk.page_content[:200]}")
    return {"context": "\n".join(lines)}

def build_retrieval_graph():
    """检索子图：START → retrieve → format → END"""
    g = StateGraph(RetrievalState)
    g.add_node("retrieve", retrieve_node)
    g.add_node("format", format_node)
    g.add_edge(START, "retrieve")
    g.add_edge("retrieve", "format")
    g.add_edge("format", END)
    return g.compile()

retrieval_graph = build_retrieval_graph()

# ==================== 第 2 层：三个工具（和6号一致，检索工具改为调用子图） ====================

@tool(description="""在年报知识库里语义检索相关段落。
何时使用：当需要查找异动原因、业务背景、管理层解释等文字性内容时使用。
参数：question (str)：要查的问题，如'工业富联AI服务器增长的原因'
返回：带页码的4段摘录。""")
def search_annual_report(question: str) -> str:
    # 工具内部跑一个子图——这就是"子图嵌套"：工具 → 子图 → 底座
    result = retrieval_graph.invoke({"question": question})
    return result["context"]

@tool(description="""从财报知识库提取某公司某年的财务指标，并换算成亿元。
何时使用：当需要拿到某公司某年具体指标的数值时使用（如营业收入、归母净利润）。
参数：company 公司简称（工业富联/紫金矿业/兴业银行）、year 年份（2024或2025）、indicators 指标名（顿号分隔，如'营业收入、归母净利润'）。
返回：每个指标的 名称 + 换算后数值 + 单位 + 出处页码；找不到的指标在'缺失说明'中列出。""")
def extract_financial_indicators(company: str, year: str, indicators: str) -> str:
    result = radar.extract_indicators(f"{company}{year}年{indicators}")
    if result is None:
        return "提取失败"
    lines = []
    for x in result.indicator_list:
        v = radar.convert_to_100_million_yuan(x.raw_value, x.raw_unit)
        if v is not None and x.raw_unit in ("元", "千元", "百万元", "亿元"):
            lines.append(f"{x.name}: {v} 亿元（第{x.source_page}页）")
        else:
            lines.append(f"{x.name}: {x.raw_value}{x.raw_unit or '%'}（第{x.source_page}页）")
    if result.missing_note:
        lines.append("缺失说明：" + result.missing_note)
    return "\n".join(lines)

@tool(description="""对比某公司某指标2024和2025两年的数值，判断是否异动。
何时使用：当需要判断某个指标是否发生明显变化时使用。
参数：company 公司简称、indicator 指标名（如'营业收入'、'净息差'）。
返回：两年数值 + 变化率/差值 + 是否异动（金额类阈值20%，比率类阈值0.25个百分点）。
注意：数据来自5号脚本写入的指标库，若数据不全请先跑5号脚本。""")
def compare_two_years(company: str, indicator: str) -> str:
    conn = radar.open_metric_db()
    def fetch(year):
        return conn.execute(
            "SELECT value, unit FROM metric_records WHERE company=? AND indicator=? AND year=? ORDER BY id DESC LIMIT 1",
            (company, indicator, year)).fetchone()
    r24, r25 = fetch("2024"), fetch("2025")
    conn.close()
    if r24 is None or r25 is None:
        return f"{company} {indicator}：指标库数据不全（可能还没跑5号脚本）"
    v24, u24 = r24
    v25, u25 = r25
    if u24 == "亿元":
        change_rate = (v25 - v24) / v24 * 100
        mark = "⚠️异动" if abs(change_rate) >= 20 else "平稳"
        return f"{company} {indicator}: {v24}亿 → {v25}亿，{change_rate:+.1f}%（{mark}）"
    diff = v25 - v24
    mark = "⚠️异动" if abs(diff) >= 0.25 else "平稳"
    return f"{company} {indicator}: {v24}% → {v25}%，{diff:+.2f}个百分点（{mark}）"


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

tools = [search_annual_report, extract_financial_indicators, compare_two_years]

def route_after_agent(state: AgentState):
    """路由器：还有工具调用→去 tools 节点继续循环；没有→结束"""
    last = state["messages"][-1]
    if getattr(last, "tool_calls", None):
        return "tools"
    return "end"

SYSTEM_RULES = """你是财报异动分析师，必须遵守：
1. 所有数字必须来自工具返回结果，禁止编造或估算工具外的数据。
2. 所需数据没有工具能提供时，明确说明"没有对应工具/数据"，绝不编数字。
3. 最终结论注明数字出处（如页码、工具名）。"""

def build_main_graph(tools_list=None, **compile_kwargs):
    """组装主图。tools_list 不给就用本文件自带的三件套；08号会把 MCP 行情工具传进来
    compile_kwargs 原样透传给 g.compile()——09号的 checkpointer/interrupt_before 从这进"""
    use_tools = tools if tools_list is None else tools_list
    llm_with = radar.llm.bind_tools(use_tools)

    def agent_node(state: AgentState):
        """模型节点：思考 + 决定下一步（调用哪个工具，还是直接回答）"""
        messages = [SystemMessage(content=SYSTEM_RULES)] + state["messages"]
        return {"messages": [llm_with.invoke(messages)]}

    g = StateGraph(AgentState)
    g.add_node("agent", agent_node)               # 模型节点
    g.add_node("tools", ToolNode(use_tools))      # 工具节点（08号的MCP行情工具也加在这里）
    g.add_edge(START, "agent")
    g.add_conditional_edges("agent", route_after_agent, {"tools": "tools", "end": END})
    g.add_edge("tools", "agent")                  # 工具用完回到模型，形成循环
    # 09号 HITL 审核闸走这里：build_main_graph(checkpointer=..., interrupt_before=["agent"])
    return g.compile(**compile_kwargs)

main_graph = build_main_graph()
print("手写图已组装：主图（agent↔tools 循环）+ 检索子图（retrieve→format）✅")

# 4.问答循环——和6号一样的"门"：被10号导入时不卡在input里
if __name__ == "__main__":
    while True:
        query = input("\n请问（输入q退出）:").strip()
        if query.lower() == "q":
            break
        print("\nAgent 工作过程：")
        for chunk in main_graph.stream({"messages": [HumanMessage(content=query)]}, stream_mode="values"):
            last = chunk["messages"][-1]
            if not isinstance(last, AIMessage):
                continue
            tool_calls = getattr(last, "tool_calls", None)
            if tool_calls:
                print("🔧 调用工具：", [tc["name"] for tc in tool_calls])
            elif last.content:
                print("💭", last.content)
        print("\n")

