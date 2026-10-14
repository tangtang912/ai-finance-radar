# 09号：HITL 审核闸（三大亮点②）
# 在 07 主图上加"人工审核闸"：agent 每次要行动前，先停下来等真人批准
# 架构：09的hitl_agent → 07的build_main_graph → compile 时加两个新开关

import os, sys

# 1. 接入07号（拿到 build_main_graph）
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "..", "..", "week2_agent", "07_langgraph_main"))
import graph_agent
print("07已接入：build_main_graph ✅")

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

# 2. 重搭主图，加两个新开关（07 留的 compile_kwargs 后门，从这里传进去）
app = graph_agent.build_main_graph(
    checkpointer=MemorySaver(),   # 开关① 检查点：状态存内存，中断后能接着跑
    interrupt_before=["agent"],   # 开关② 审核闸：每次要进 agent 节点前自动暂停
)

# 3. thread_id：一次会话一个ID，检查点按它分开存，多会话互不串扰
config = {"configurable": {"thread_id": "radar-1"}}

def show_state():
    """看闸前的状态：最后一条消息是什么"""
    last = app.get_state(config).values["messages"][-1]
    if isinstance(last, AIMessage) and getattr(last, "tool_calls", None):
        print("🔧 Agent 想调用工具：", [tc["name"] for tc in last.tool_calls])
    elif isinstance(last, AIMessage):
        print("💭 Agent 说：", str(last.content)[:150])
    else:
        print(f"📨 {type(last).__name__}：", str(last.content)[:150])

def is_finished():
    """跑完了吗：最后一条是"没有工具调用"的AIMessage = agent 已给出最终答复"""
    last = app.get_state(config).values["messages"][-1]
    return isinstance(last, AIMessage) and not getattr(last, "tool_calls", None)

def main():
    while True:
        question = input("\n请问（输入q退出）：").strip()
        if question.lower() == "q":
            break
        # 4. 提交问题：图跑起来，立刻停在第一道闸前
        app.invoke({"messages": [HumanMessage(content=question)]}, config)

        while not is_finished():
            print("\n" + "=" * 54)
            print("⏸️ 审核闸：agent 下一步要行动，请审核：")
            show_state()
            print("=" * 54)
            choice = input("1️⃣ 批准继续   2️⃣ 驳回并给意见   3️⃣ 退出：").strip()
            if choice == "1":
                # 5. 批准 = 放行：从闸前继续跑，直到下一道闸或结束
                app.invoke(Command(resume=True), config)
            elif choice == "2":
                # 6. 驳回 = 把真人意见写进状态，再放行，agent 会按意见重新想
                feedback = input("你的意见：").strip()
                app.update_state(config, {"messages": [HumanMessage(content=feedback)]})
                app.invoke(Command(resume=True), config)
            elif choice == "3":
                print("已退出。用同一个 thread_id 重跑本脚本，可接着审。")
                return
            else:
                print("⚠️ 输入不识别：请输入 1 / 2 / 3（纯数字，不带emoji）")

        last = app.get_state(config).values["messages"][-1]
        print("\n✅ 最终结论：")
        print(last.content)

if __name__ == "__main__":
    main()
