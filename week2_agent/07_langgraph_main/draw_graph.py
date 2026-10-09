import os, sys

# 把本文件夹加入搜索路径，保证能找到 graph_agent 模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import graph_agent  # 执行模块级代码：接入雷达、组装两张图

# 让两张图各画一张"图纸"（mermaid 文本），写进 graph.md
parts = []
for title, g in [("主图（agent↔tools 循环）", graph_agent.main_graph),
                 ("检索子图（retrieve→format）", graph_agent.retrieval_graph)]:
    parts.append(f"## {title}\n\n```mermaid\n{g.get_graph().draw_mermaid()}\n```\n")

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "graph.md")
with open(out, "w", encoding="utf-8") as f:
    f.write("# 07 LangGraph 的图\n\n" + "\n".join(parts))

print("已生成 graph.md ✅ 在 PyCharm 里打开它，点右上角预览图标即可看到渲染后的图")
