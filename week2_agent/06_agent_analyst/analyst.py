import os,sys

from langchain_core.tools import tool
from langchain.agents import create_agent
from langchain_core.messages import AIMessage

#1.导入radar
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),"..","05_radar"))
import radar
print("radar底座已接入：索引+提取+换算+指标库 全部可用 ✅")

#2.定义tools
@tool(description="""在年报知识库里语义检索相关段落。
何时使用：当需要查找异动原因、业务背景、管理层解释等文字性内容时使用。
参数：
- question (str)：要查的问题，如'工业富联AI服务器增长的原因'
返回：带页码的4段摘录，格式为 [编号]文件名第X页：内容前200字
""")
def search_annual_report(question: str) ->str:
    hits = radar.db.similarity_search(question,k=4)
    lines = []
    for i,chunk in enumerate(hits,1):
        file_name = os.path.basename(chunk.metadata["source"])
        lines.append(f"[{i}]{file_name}第{chunk.metadata['page']+1}页:\n {chunk.page_content[:200]}")
    return "\n".join(lines)

@tool(description="""从财报知识库提取某公司某年的财务指标，并换算成亿元。
何时使用：当需要拿到某公司某年具体指标的数值时使用（如营业收入、归母净利润）。
参数：
- company (str)：公司简称，可选 工业富联 / 紫金矿业 / 兴业银行
- year (str)：年份，可选 2024 或 2025
- indicators (str)：指标名，顿号分隔，如'营业收入、归母净利润'
返回：每个指标的 名称 + 换算后数值 + 单位 + 出处页码；找不到的指标会在'缺失说明'中列出。
""")
def extract_financial_indicators(company:str,year:str,indicators:str) -> str:
    result = radar.extract_indicators(f"{company}{year}年{indicators}")
    if result is None:
        return "提取失败"
    lines = []
    for x in result.indicator_list:
        v = radar.convert_to_100_million_yuan(x.raw_value, x.raw_unit)
        if v is not None and x.raw_unit in ("元", "千元", "百万元", "亿元"):
            lines.append(f"{x.name}: {v}亿元 (第{x.source_page}页)")
        else:
            lines.append(f"{x.name}: {x.raw_value}{x.raw_unit or '%'} (第{x.source_page}页)")
    if result.missing_note:
        lines.append("缺失说明：" + result.missing_note)
    return "\n".join(lines)

@tool(description="""对比某公司某指标2024和2025两年的数值，判断是否异动。
何时使用：当需要判断某个指标是否发生明显变化时使用。
参数：
- company (str)：公司简称，如'工业富联'
- indicator (str)：指标名，如'营业收入'、'净息差'
返回：两年数值 + 变化率/差值 + 是否异动（金额类阈值20%，比率类阈值0.25个百分点）。
注意：数据来自5号脚本写入的指标库，若数据不全请先跑5号脚本。
""")
def compare_two_years(company:str,indicator:str) ->str:
    conn = radar.open_metric_db()
    def fetch(year):
        return conn.execute(
            "SELECT value, unit FROM metric_records WHERE company =? AND indicator =? AND year =? ORDER BY id DESC LIMIT 1",
            (company,indicator,year)).fetchone()
    r24,r25 = fetch("2024"), fetch("2025")
    conn.close()
    if r24 is None or r25 is None:
        return f"{company}{indicator}:指标库数据不全"
    v24 , u24 = r24
    v25 , u25 = r25
    if u24 == "亿元":
        change_rate = (v25 - v24) / v24 * 100
        mark = "⚠️异动" if abs(change_rate) >= 20 else "平稳"
        return f"{company}{indicator} :{v24}→ {v25}亿元,{change_rate:+.1f}%({mark})"
    diff = v25 -v24
    mark = "⚠️异动" if abs(diff) >= 0.25 else "平稳"
    return f"{company}{indicator} : {v24}% → {v25}%,{diff:+.2f}个百分点 ({mark})"

#3.组装agent
def build_agent():
    return create_agent(
        model = radar.llm,
        tools = [search_annual_report,extract_financial_indicators,compare_two_years],
        system_prompt="""你是财报异动分析师。必须按ReAct方式工作：思考→调用工具→观察结果→再思考，直到能回答为止。
规则：
1. 分析公司异动时：先用 extract_financial_indicators 拿数据，用 compare_two_years 算变化，用 search_annual_report 找原因。
2. 所有数字必须来自工具返回结果，禁止编造。
3. 每轮只调用一个工具。
4. 最后给出结论：哪家公司、哪个指标异动最明显，原因是什么，并注明出处页码。""",
    )

#4.问答循环
if __name__ == '__main__':
    agent = build_agent()
    while True:
        query = input("\n 请问(输入q退出)：").strip()
        if query.lower() == "q":
            break
        print("\n agent 工作进程 ：")
        for chunk in agent.stream({"messages":[{"role":"user","content":query}]}, stream_mode="values"):
            last = chunk["messages"][-1]
            if not isinstance(last,AIMessage):
                continue
            tool_calls = getattr(last,"tool_calls",None)
            if tool_calls:
                print("🔧调用工具:",[tc["name"] for tc in tool_calls])
            elif last.content:
                print("💭",last.content)
        print("\n")



