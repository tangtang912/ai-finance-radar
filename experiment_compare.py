# -*- coding: utf-8 -*-
"""升级包第②步：长上下文 vs RAG 对比实验
同一 20 题评测集（test_questions.json）跑两个方案，记录三指标：正确率 / 耗时 / token 成本

方案A（RAG）：qwen-plus + Top-8 检索上下文 —— 现有架构
方案B（长上下文）：qwen-long（1M 窗口）+ 整份年报全文 —— 不检索直接答
判定：qwen-plus 作 judge，对照答案页原文判断回答正确性

跑法：python experiment_compare.py --limit 3   （先试跑 3 题）
      python experiment_compare.py              （全量 20 题）
输出：终端汇总表 + data/compare_results.json"""
import argparse
import json
import os
import time
from collections import defaultdict

from langchain_community.embeddings import DashScopeEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI

BASE = os.path.dirname(os.path.abspath(__file__))
QUESTIONS = os.path.join(BASE, "test_questions.json")
SPLIT = os.path.join(BASE, "data", "split.json")
INDEX = os.path.join(BASE, "data", "faiss_index")
OUTPUT = os.path.join(BASE, "data", "compare_results.json")

# 两个方案的模型：RAG 用常规窗口，长上下文用 1M 窗口（整份年报 24-45 万 tokens，128K 装不下）
llm_rag = ChatOpenAI(
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    api_key=os.environ["DASHSCOPE_API_KEY"],
    model="qwen-plus",
)
llm_long = ChatOpenAI(
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    api_key=os.environ["DASHSCOPE_API_KEY"],
    model="qwen-long",
)
llm_judge = ChatOpenAI(
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    api_key=os.environ["DASHSCOPE_API_KEY"],
    model="qwen-plus",
    temperature=0,
)

RULES = """你是财务分析助手。请只根据下面的年报内容回答用户问题。

规则：
1. 内容里没有的信息，直说"没找到"，不要编造，也不要自行估算或推算内容外的数字。
2. 金额单位是"千元/百万元"。换算：1亿元=100,000千元=100百万元。先换算再写，写完检查数量级。
3. 回答开头先写明公司和年份（如：工业富联2025年……）。
4. 注明出处时写明"文件名+页码"。"""


def load_all():
    """加载：切分原文（拼全文 + 答案页原文）+ FAISS 索引 + 评测集"""
    chunks = json.load(open(SPLIT, encoding="utf-8"))
    # 按文件拼全文（长上下文用）
    fulltext = defaultdict(list)
    for c in chunks:
        fname = os.path.basename(c["source"])
        fulltext[fname].append(c)
    for f in fulltext:
        fulltext[f].sort(key=lambda c: (c["page"],))
    fulltext = {f: "\n\n".join(c["content"] for c in cs) for f, cs in fulltext.items()}

    # 答案页原文（judge 的对照基准）：(file, page) 命中的 chunks 拼接
    gt_text = {}
    for q in json.load(open(QUESTIONS, encoding="utf-8")):
        parts = []
        for a in q["answers"]:
            for c in chunks:
                if os.path.basename(c["source"]) == a["file"] and c["page"] + 1 in a["pages"]:
                    parts.append(c["content"])
        gt_text[q["id"]] = "\n".join(parts)

    embedder = DashScopeEmbeddings(model="text-embedding-v3")
    db = FAISS.load_local(INDEX, embedder, allow_dangerous_deserialization=True)
    questions = json.load(open(QUESTIONS, encoding="utf-8"))
    return fulltext, gt_text, db, questions


def ask_rag(db, q):
    """方案A：Top-8 检索 + qwen-plus"""
    hits = db.similarity_search(q["question"], k=8)
    content = ""
    for i, chunk in enumerate(hits, 1):
        fname = os.path.basename(chunk.metadata["source"])
        content += f"[content{i}]({fname}第{chunk.metadata['page']+1}页）\n{chunk.page_content}\n\n"
    prompt = f"{RULES}\n\n以下为检索到的年报摘录：\n\n{content}\n\n用户问题：{q['question']}\n请回答："
    t0 = time.time()
    r = llm_rag.invoke(prompt)
    usage = r.response_metadata.get("token_usage", {})
    return r.content, time.time() - t0, usage


def ask_long(fulltext, q):
    """方案B：整份年报全文 + qwen-long（1M 窗口）"""
    fname = q["answers"][0]["file"]
    text = fulltext[fname]
    prompt = f"{RULES}\n\n以下为《{fname}》全文（节选自年报文本）：\n\n{text}\n\n用户问题：{q['question']}\n请回答："
    t0 = time.time()
    r = llm_long.invoke(prompt)
    usage = r.response_metadata.get("token_usage", {})
    return r.content, time.time() - t0, usage


def judge(q, gt, answer):
    """qwen-plus 判定：回答与答案页原文是否一致"""
    prompt = f"""你是评测员。判断模型回答是否正确。

用户问题：{q['question']}
标准答案所在页原文：
{gt[:3000]}

模型回答：
{answer[:2000]}

判断标准：回答中的核心数字/结论与标准答案一致则正确；回答"没找到"或核心数字错误则判错。
只输出 JSON：{{"correct": true 或 false, "reason": "一句话理由"}}"""
    r = llm_judge.invoke(prompt)
    raw = r.content.strip()
    try:
        start = raw.find("{")
        end = raw.rfind("}") + 1
        d = json.loads(raw[start:end])
        return d.get("correct", False), d.get("reason", "")
    except Exception:
        return False, "judge 输出解析失败"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="只跑前 N 题（试跑用）")
    args = ap.parse_args()

    fulltext, gt_text, db, questions = load_all()
    if args.limit:
        questions = questions[: args.limit]
    print(f"评测集 {len(questions)} 题，开始对比实验……\n")

    results = []
    for q in questions:
        row = {"id": q["id"], "question": q["question"]}
        print(f"[{q['id']:>2}] {q['question'][:40]}……")

        # 方案A：RAG
        try:
            ans, secs, usage = ask_rag(db, q)
            ok, reason = judge(q, gt_text[q["id"]], ans)
            row["rag"] = {"answer": ans, "correct": ok, "seconds": round(secs, 1),
                          "in_tokens": usage.get("prompt_tokens", 0),
                          "out_tokens": usage.get("completion_tokens", 0), "reason": reason}
            print(f"      RAG      {'✅' if ok else '❌'} {secs:.0f}s 入{usage.get('prompt_tokens', 0)}t")
        except Exception as e:
            row["rag"] = {"error": str(e)[:120]}
            print(f"      RAG      ⚠️ 失败：{str(e)[:80]}")

        # 方案B：长上下文
        try:
            ans, secs, usage = ask_long(fulltext, q)
            ok, reason = judge(q, gt_text[q["id"]], ans)
            row["longctx"] = {"answer": ans, "correct": ok, "seconds": round(secs, 1),
                              "in_tokens": usage.get("prompt_tokens", 0),
                              "out_tokens": usage.get("completion_tokens", 0), "reason": reason}
            print(f"      长上下文 {'✅' if ok else '❌'} {secs:.0f}s 入{usage.get('prompt_tokens', 0)}t")
        except Exception as e:
            row["longctx"] = {"error": str(e)[:120]}
            print(f"      长上下文 ⚠️ 失败：{str(e)[:80]}")

        results.append(row)

    json.dump(results, open(OUTPUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    # 汇总
    def stats(key):
        rows = [r[key] for r in results if key in r and "error" not in r[key]]
        if not rows:
            return None
        correct = sum(1 for r in rows if r["correct"])
        avg_s = sum(r["seconds"] for r in rows) / len(rows)
        avg_in = sum(r["in_tokens"] for r in rows) / len(rows)
        avg_out = sum(r["out_tokens"] for r in rows) / len(rows)
        return {"n": len(rows), "acc": f"{correct}/{len(rows)}", "avg_s": round(avg_s, 1),
                "avg_in": int(avg_in), "avg_out": int(avg_out)}

    s_rag = stats("rag")
    s_long = stats("longctx")
    print("\n" + "=" * 70)
    print("汇总对比")
    print("=" * 70)
    if s_rag:
        print(f"方案A RAG      ：正确率 {s_rag['acc']} ｜ 平均 {s_rag['avg_s']}s ｜ 平均输入 {s_rag['avg_in']}t / 输出 {s_rag['avg_out']}t")
    if s_long:
        print(f"方案B 长上下文：正确率 {s_long['acc']} ｜ 平均 {s_long['avg_s']}s ｜ 平均输入 {s_long['avg_in']}t / 输出 {s_long['avg_out']}t")
    print(f"\n结果已写入 {OUTPUT}")


if __name__ == "__main__":
    main()
