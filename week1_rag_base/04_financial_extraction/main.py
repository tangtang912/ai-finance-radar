import os
from typing import Optional
from pydantic import BaseModel,Field,ConfigDict
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI

data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data")
index = os.path.join(data_dir,"faiss_index")

#1.加载索引
embedder = DashScopeEmbeddings(model="text-embedding-v3")
db = FAISS.load_local(index,embedder,allow_dangerous_deserialization=True)
print("索引加载完成✅")

#2.指标模型——「雷达」的核心：只有结构化，才能和往年自动对比
#   注意：大模型只负责"报原文"，不做任何算术——算术永远交给代码
class IndicatorItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name:str = Field(description="指标中文名，如：营业收入")
    raw_value:str = Field(description="摘录原文中的数字，原样摘抄（可含千分位逗号），绝对不要换算")
    raw_unit:str = Field(description="摘录原文中的单位：：千元/百万元/亿元/%/个基点")
    source_page:Optional[int] = Field(default=None,description="摘录所在页码")

class IndicatorResults(BaseModel):
    model_config = ConfigDict(extra="ignore")
    company:str = Field(description="公司简称，如：工业富联")
    year:str = Field(description="年报年份，如：2025")
    indicator_list:list[IndicatorItem] = Field(description="提取所有的指标项")
    missing_note:str = Field(default = "",description="摘录里没有的指标，如实说明缺什么")

#3.单位换算——确定性计算，放代码里不放提示词里
def convert_to_100_million_yuan(raw_value:str,raw_unit:str):
    try:
        n = float(raw_value.replace(",","").strip())
    except ValueError:
        return None
    if raw_unit == "千元":
        return round(n / 100000,2)
    if raw_unit == "百万元":
        return round(n / 100,2)
    if raw_unit == "亿元":
        return round(n,2)
    return None # %、个基点 这类不需要换算

#4.接入大模型
llm = ChatOpenAI(
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    api_key=os.environ["DASHSCOPE_API_KEY"],
    model="qwen-plus",
)

#5.问答循环
while True:
    query = input("请问(输入q退出):").strip()
    if query.lower() == "q":
        break

    # 1️⃣.找出语义相近的8处
    hits = db.similarity_search(query,k=8)

    # 2️⃣.拼提示词（摘录➕出处）
    content = ""
    for i,chunk in enumerate(hits,1):
        file_name = os.path.basename(chunk.metadata["source"])
        content += f"[content{i}]({file_name}第{chunk.metadata['page']+1}页) \n{chunk.page_content}\n\n"

    prompt = f"""你是财报数据提取引擎。请根据下面的年报摘录，把用户要的指标提取成JSON。
规则：
1. raw_value=摘录原文里的数字，原样照抄（千分位逗号保留也可以，但数字里不要带单位符号或空格，如%要写进raw_unit字段），raw_unit=摘录原文里的单位。绝对不要做任何换算。
2. 摘录里没有的指标不要编造，写进missing_note。如果用户要的口径没有精确数值、但有最接近口径的数据，把最接近口径放进列表、name写实际口径（如"云计算业务收入"），并在missing_note里解释口径差异。
3. source_page填对应content标记里写的页码。
4. 只输出JSON本身，不要输出任何其他文字，不要用```包裹。

JSON格式:
{{"company":"工业富联","year":"2025","indicator_list":[{{"name":"营业收入","raw_value":"902,887,188","raw_unit":"千元","source_page":17}}],"missing_note":""}}
{content}
用户要提取：{query}
JSON
"""
    # 3️⃣.大模型输出JSON，pydantic校验
    raw = llm.invoke(prompt).content.strip()
    if raw.startswith("```"):
        raw = raw.split("\n",1)[1].rsplit("```",1)[0]
    try:
        result = IndicatorResults.model_validate_json(raw)
    except Exception as e:
        print("大模型没通过pydantic检查：")
        print(e)
        print("模型原始输出：",raw)
        continue

    # 4️⃣.展示：先原样，再代码换算
    print("\n提取结果：")
    print(result.model_dump_json(indent=2,ensure_ascii=False))
    print("\n代码算的（不靠大模型）:")
    for x in result.indicator_list:
        v = convert_to_100_million_yuan(x.raw_value,x.raw_unit)
        if v is None:
            print(f" {x.name}:{x.raw_value}{x.raw_unit}")
        else:
            print(f"{x.name}:{x.raw_value}{x.raw_unit}={v}亿元")
    if result.missing_note:
        print("\n摘录缺失说明：", result.missing_note)

