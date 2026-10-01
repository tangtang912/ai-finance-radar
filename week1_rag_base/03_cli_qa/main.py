import os
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI

data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data")
index = os.path.join(data_dir, "faiss_index")

#1.加载索引
embedder = DashScopeEmbeddings(model="text-embedding-v3")
db = FAISS.load_local(index,embedder,allow_dangerous_deserialization=True)
print("索引加载完成✅")

#2.接入大模型
llm = ChatOpenAI(
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    api_key=os.environ["DASHSCOPE_API_KEY"],
    model="qwen-plus",
)

#3.问答循环
while True:
    query = input("\n请问（输入q退出）:").strip()
    if query.lower() == "q":
        break

    #1️⃣.找出语义相关的8处
    hits = db.similarity_search(query,k=8)

    #2️⃣.拼提示词，摘录➕出处
    content = ""
    for i ,chunk in enumerate(hits,1):
        file_name = os.path.basename(chunk.metadata["source"])
        content += f"[content{i}]({file_name}第{chunk.metadata['page']+1}页）\n{chunk.page_content}\n\n"

    prompt = f"""你是财务分析助手。请只根据下面的年报摘录回答用户问题。

规则：
1. 摘录里没有的内容，直说"摘录里没找到"，不要编造，也不要自行估算或推算摘录外的数字。
2. 摘录里没有问题的精确口径、但有相关口径的数据时，先给出最接近的数据和出处，再用一句话说明口径差异。
   例：问"AI服务器收入"，摘录只有"云计算业务收入"→ 答"报告未单独披露AI服务器收入，最接近的口径是云计算业务收入……"
3. 金额单位是"千元/百万元"。换算：1亿元=100,000千元=100百万元。先换算再写，写完检查数量级（如35,285,561千元=352.86亿元）。
4. 回答开头先写明公司和年份（如：工业富联2025年……）。
5. 注明出处时必须写"文件名+页码"（从content标记里抄），不能只写content编号。例：出自[content1]（工业富联_2025年年报.pdf第14页）。

{content}

用户问题：{query}
请回答："""

    #3️⃣.用户提问
    print("\n回答：")
    print(llm.invoke(prompt).content)

