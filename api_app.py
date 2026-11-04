# -*- coding: utf-8 -*-
"""升级包第③步：FastAPI 接口 + 登录鉴权
把 03_cli_qa 的问答能力包装成 HTTP 服务：
  POST /ask   财报问答（X-API-Key 鉴权，公网防刷）
  GET  /health 健康检查
跑法：
  export API_KEY=你的密钥        # 启动前必须设置，否则拒绝启动
  uvicorn api_app:app --host 0.0.0.0 --port 8000
请求示例：
  curl -X POST http://localhost:8000/ask \
    -H "X-API-Key: 你的密钥" -H "Content-Type: application/json" \
    -d '{"question": "工业富联2025年的营业收入是多少？"}'
"""
import os

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI

BASE = os.path.dirname(os.path.abspath(__file__))
INDEX = os.path.join(BASE, "data", "faiss_index")

app = FastAPI(title="AI 财报异动雷达 API", version="2.0.0")


class AskRequest(BaseModel):
    question: str


class Source(BaseModel):
    file: str
    page: int
    snippet: str


class AskResponse(BaseModel):
    answer: str
    sources: list[Source]


# 鉴权密钥：启动时从环境变量读取，缺失直接拒绝启动（防裸奔）
API_KEY = os.environ.get("API_KEY", "")
if not API_KEY:
    raise RuntimeError("缺少环境变量 API_KEY：export API_KEY=你的密钥 后再启动")


def _get_pipeline():
    """懒加载：索引和大模型首次请求时才加载（启动快、内存可控）"""
    if _get_pipeline._cache is None:
        embedder = DashScopeEmbeddings(model="text-embedding-v3")
        db = FAISS.load_local(INDEX, embedder, allow_dangerous_deserialization=True)
        llm = ChatOpenAI(
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            api_key=os.environ["DASHSCOPE_API_KEY"],
            model="qwen-plus",
        )
        _get_pipeline._cache = (db, llm)
    return _get_pipeline._cache


_get_pipeline._cache = None

PROMPT = """你是财务分析助手。请只根据下面的年报摘录回答用户问题。

规则：
1. 摘录里没有的内容，直说"摘录里没找到"，不要编造，也不要自行估算或推算摘录外的数字。
2. 摘录里没有问题的精确口径、但有相关口径的数据时，先给出最接近的数据和出处，再用一句话说明口径差异。
3. 金额单位是"千元/百万元"。换算：1亿元=100,000千元=100百万元。先换算再写，写完检查数量级。
4. 回答开头先写明公司和年份（如：工业富联2025年……）。
5. 注明出处时必须写"文件名+页码"（从content标记里抄），不能只写content编号。

{content}

用户问题：{question}
请回答："""


@app.get("/health")
def health():
    return {"status": "ok", "service": "财报异动雷达", "version": "2.0.0"}


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest, x_api_key: str | None = Header(default=None)):
    # 鉴权：密钥比对（演示用直比；生产可换 JWT/签名）
    # 注意：Header 写成可选再手动判断，缺失 Key 和错误 Key 都归一为 401
    # （若写成 Header(...) 必填，缺失时 FastAPI 校验层直接返回 422，语义不统一）
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="无效的 API Key")

    db, llm = _get_pipeline()

    # 1️⃣ 语义检索 Top-8
    hits = db.similarity_search(req.question, k=8)

    # 2️⃣ 拼提示词（摘录 + 出处）
    content = ""
    sources = []
    for i, chunk in enumerate(hits, 1):
        fname = os.path.basename(chunk.metadata["source"])
        page = chunk.metadata["page"] + 1
        content += f"[content{i}]({fname}第{page}页）\n{chunk.page_content}\n\n"
        sources.append(Source(file=fname, page=page, snippet=chunk.page_content[:100]))

    # 3️⃣ 问答
    prompt = PROMPT.format(content=content, question=req.question)
    answer = llm.invoke(prompt).content

    return AskResponse(answer=answer, sources=sources)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
