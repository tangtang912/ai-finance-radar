import os,sqlite3
from  typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI

data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data")
index = os.path.join(data_dir, "faiss_index")

#1.加载索引
embedder = DashScopeEmbeddings(model="text-embedding-v3")
db = FAISS.load_local(index, embedder, allow_dangerous_deserialization=True)
print("索引加载完成✅")

#2.指标模型（大模型只报原文，不做算术）
class IndicatorItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: str = Field(description="指标中文名，如：营业收入")
    raw_value: str = Field(description="摘录原文里的数字，原样照抄（可含千分位逗号），绝对不要换算")
    raw_unit: str = Field(description="摘录原文里的单位：元/千元/百万元/亿元/%/个基点")
    source_page: Optional[int] = Field(default=None, description="摘录所在页码")

class IndicatorResult(BaseModel):
    model_config = ConfigDict(extra="ignore")
    company: str = Field(description="公司简称")
    year: str = Field(description="年报年份")
    indicator_list: list[IndicatorItem] = Field(description="提取出的所有指标")
    missing_note: str = Field(default="", description="摘录里没有的指标，如实说明缺什么")

#3.单位换算——确定性计算，放代码里
def convert_to_100_million_yuan(raw_value: str, raw_unit: str):
    try:
        n = float(raw_value.replace(",", "").strip())
    except ValueError:
        return None
    if raw_unit == "元":
        return round(n / 100000000, 2)
    if raw_unit == "千元":
        return round(n / 100000, 2)
    if raw_unit == "百万元":
        return round(n / 100, 2)
    if raw_unit == "亿元":
        return round(n, 2)
    return None  # %、个基点 这类不需要换算

#4.接入大模型
llm = ChatOpenAI(
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    api_key=os.environ["DASHSCOPE_API_KEY"],
    model="qwen-plus",
)

#5.数据库初始化
def open_metric_db():
    conn = sqlite3.connect(os.path.join(data_dir,"metrics.db"))
    conn.execute("""CREATE TABLE IF NOT EXISTS metric_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company TEXT,
        year TEXT,
        indicator TEXT,
        value REAL,
        unit TEXT,
        source_page INTEGER,
        extracted_at TEXT)"""
        )
    return conn

#6.指标名称标准化
def normalize_indicator_name(name):
    if "营业收入" in name:
        return "营业收入"
    if "净利润" in name:
        return "归母净利润"
    if "净息差" in name:
        return "净息差"
    if "不良贷款率" in name:
        return "不良贷款率"
    return name

#7.提取函数
def extract_indicators(query):
    hits = db.similarity_search(query,k=8)
    content = ""
    for i,chunk in enumerate(hits,1):
        file_name = os.path.basename(chunk.metadata["source"])
        content += f"[content{i}]({file_name}第{chunk.metadata['page']+1}页)\n{chunk.page_content}\n\n"

    prompt = f"""你是财报数据提取引擎。请根据下面的年报摘录，把用户要的指标提取成JSON。

规则：
1. raw_value=摘录原文里的数字，原样照抄（千分位逗号保留也可以，但数字里不要带单位符号或空格，如%要写进raw_unit），raw_unit=摘录原文里的单位。绝对不要做任何换算。
2. 摘录里没有的指标不要编造，写进missing_note。
3. source_page填对应content标记里写的页码。
4. 只输出JSON本身，不要输出任何其他文字，不要用```包裹。

JSON格式：
{{"company":"...","year":"...","indicator_list":[{{"name":"营业收入","raw_value":"902,887,188","raw_unit":"千元","source_page":17}}],"missing_note":"..."}}

{content}

用户要提取：{query}
JSON："""

    raw = llm.invoke(prompt).content.strip()
    if raw.startswith("```"):
        raw = raw.split("\n",1)[1].rsplit("```",1)[0]
    try:
        return IndicatorResult.model_validate_json(raw)
    except Exception as e:
        print(f"校验失败:,{e}")
        print(f"模型原始输出：",raw[:200])
        return None

#8.批量提取
def batch_extract(conn):
    task_list = [
        ("工业富联", ["营业收入和归母净利润"]),
        ("紫金矿业", ["营业收入和归母净利润"]),
        ("兴业银行", ["营业收入和归母净利润", "净息差和不良贷款率"]),
    ]
    for company,questions in task_list:
        for year in["2024" , "2025"]:
            for indicator_question in questions:
                question =  f"{company}{year}年{indicator_question}"
                print(f"\n提取中:{question}...")
                result = extract_indicators(question)
                if result is None:
                    continue
                for x in result.indicator_list:
                    name =  normalize_indicator_name(x.name)
                    v = convert_to_100_million_yuan(x.raw_value,x.raw_unit)
                    if v is not None and x.raw_unit in ("元", "千元", "百万元", "亿元"):
                        value,unit = v,"亿元"
                    else:
                        try:
                            value = float(x.raw_value.replace(",","").replace("%","").replace(" ","").strip())
                        except ValueError:
                            continue
                        unit = x.raw_unit if x.raw_unit else "%"
                    conn.execute(
                        "INSERT INTO metric_records(company, year, indicator, value, unit, source_page, extracted_at)"
                        "VALUES(?,?,?,?,?,?,datetime('now','localtime'))",
                        (company,year,name,value,unit,x.source_page))
                    conn.commit()
                    print(f"✅{name} {year} :{value} {unit} 第{x.source_page}页")
                if result.missing_note:
                    print(f"  📝 缺失说明：{result.missing_note[:80]}……")

#9.对比报告
def compare_report(conn):
    print("\n" + "=" * 56)
    print("📡 异动雷达报告")
    print("=" * 56)
    groups = conn.execute(
        "SELECT DISTINCT company, indicator FROM metric_records ORDER by company, indicator").fetchall()
    for company,indicator in groups:
        def fetch(year):
            return conn.execute(
                "SELECT value, unit FROM metric_records WHERE company =? AND indicator =? AND year =? ORDER BY id DESC LIMIT 1",
                (company,indicator,year)).fetchone()
        r24, r25 = fetch("2024"),fetch("2025")
        if r24 is None or r25 is None:
            print(f"{company} {indicator}:只有一年数据，跳过")
            continue
        v24, u24 = r24
        v25, u25 = r25
        if u24 == "亿元":
            change_rate = (v25 - v24) / v24 * 100
            mark = "⚠️" if abs(change_rate) >= 20 else  ""
            print(f"{company} {indicator} : {v24}→ {v25}亿元 ({change_rate:+.1f}%){mark}")
        else:
            diff = v25 - v24
            mark = "⚠️" if abs(diff) >= 0.25 else  ""
            print(f"{company} {indicator} :{v24}% → {v25}% ({diff:+.2f}个百分点){mark}")

#10.main 代码块
if __name__ == '__main__':
    conn = open_metric_db()
    batch_extract(conn)
    compare_report(conn)
    conn.close()
    print("指标库位置：",os.path.join(data_dir,"metrics.db"))















