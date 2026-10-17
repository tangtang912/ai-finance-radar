# 评测脚本：检索命中率
# 20 道测试题（test_questions.json），每题标注标准答案所在页码
# 判定：Top-8 检索结果中是否存在 chunk 命中标准答案的 (文件, 页码)
# 跑法：python eval_retrieval.py
# 输出：终端表格 + data/eval_results.json（供 README / 简历填评测数据）

import json
import os
from collections import Counter

from langchain_community.embeddings import DashScopeEmbeddings
from langchain_community.vectorstores import FAISS

BASE = os.path.dirname(os.path.abspath(__file__))
INDEX = os.path.join(BASE, "data", "faiss_index")
QUESTIONS = os.path.join(BASE, "test_questions.json")
OUTPUT = os.path.join(BASE, "data", "eval_results.json")

def main():
    # 1. 加载索引（与 03_cli_qa 相同的加载方式）
    embedder = DashScopeEmbeddings(model="text-embedding-v3")
    db = FAISS.load_local(INDEX, embedder, allow_dangerous_deserialization=True)
    print("索引加载完成✅")

    questions = json.load(open(QUESTIONS, encoding="utf-8"))
    results = []
    hit_count = 0

    print(f"\n{'题号':<4} {'公司':<6} {'结果':<4} {'首个命中名次':<10} 问题")
    print("-" * 100)

    for q in questions:
        hits = db.similarity_search(q["question"], k=8)

        # Top-8 里每个 chunk 的 (文件名, PDF页码=page+1)
        hit_pages = []
        for chunk in hits:
            fname = os.path.basename(chunk.metadata["source"])
            hit_pages.append((fname, chunk.metadata["page"] + 1))

        # 判定：标准答案的任一 (file, page) 是否出现在 Top-8
        first_rank = None
        matched = False
        for rank, (fname, page) in enumerate(hit_pages, 1):
            for ans in q["answers"]:
                if fname == ans["file"] and page in ans["pages"]:
                    matched = True
                    first_rank = rank
                    break
            if matched:
                break

        if matched:
            hit_count += 1

        # Top-8 文件构成（检查是否混入其他公司的文件）
        files_in_top8 = sorted({f.split("_")[0] for f, _ in hit_pages})

        results.append({
            "id": q["id"],
            "company": q["company"],
            "question": q["question"],
            "hit": matched,
            "first_rank": first_rank,
            "files_in_top8": files_in_top8,
            "top8_pages": [{"file": f, "page": p} for f, p in hit_pages],
        })

        mark = "✅" if matched else "❌"
        rank_str = f"第{first_rank}名" if first_rank else "-"
        print(f"{q['id']:<4} {q['company']:<6} {mark:<4} {rank_str:<10} {q['question']}")

    # 2. 汇总
    total = len(questions)
    rate = hit_count / total * 100
    print("\n" + "=" * 60)
    print(f"📊 检索命中率：{hit_count}/{total} = {rate:.0f}%")
    print("=" * 60)

    by_company = Counter()
    by_company_hit = Counter()
    for r in results:
        by_company[r["company"]] += 1
        if r["hit"]:
            by_company_hit[r["company"]] += 1
    for company in sorted(by_company):
        c_hit, c_total = by_company_hit[company], by_company[company]
        print(f"  {company}: {c_hit}/{c_total} ({c_hit/c_total*100:.0f}%)")

    # 混入其他公司文件的题数（文件串扰）
    cross = [r for r in results if len(r["files_in_top8"]) > 1]
    print(f"\n  文件串扰：{len(cross)} 题的 Top-8 混入了其他公司文件")

    # 3. 落盘
    summary = {
        "total": total,
        "hit": hit_count,
        "rate": round(rate, 1),
        "by_company": {c: {"hit": by_company_hit[c], "total": by_company[c]} for c in by_company},
        "cross_file_questions": len(cross),
    }
    json.dump({"summary": summary, "details": results},
              open(OUTPUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"\n结果已写入：{OUTPUT}")


if __name__ == "__main__":
    main()
