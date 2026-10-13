# 08号：把自写的 MCP 行情服务接进 07 的主图
# 架构：08的mcp_agent → 07的build_main_graph(三件套 + MCP行情工具) → 05底座
# 注意：MCP 工具是异步的，所以整条链路用 async 跑

import asyncio, os, sys

# 1.接入07号（拿到三件套工具和 build_main_graph）
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "07_langgraph_main"))
import graph_agent
print("07已接入：三件套工具 + build_main_graph ✅")

from langchain_core.messages import AIMessage, HumanMessage
from langchain_mcp_adapters.client import MultiServerMCPClient

SERVER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stock_server.py")
PYTHON = sys.executable  # 当前环境解释器

async def build_agent_with_mcp():
    # 2.连接自写的 MCP server（stdio 方式：适配器自己启动子进程并管理通信）
    client = MultiServerMCPClient({
        "stock": {
            "command": PYTHON,
            "args": [SERVER],
            "transport": "stdio",
        }
    })
    mcp_tools = await client.get_tools()
    print(f"MCP 工具已接入：{[t.name for t in mcp_tools]} ✅")
    # 3.三件套 + MCP 工具，重搭主图（07里留的 tools_list 接入点在这里用上）
    return graph_agent.build_main_graph(graph_agent.tools + mcp_tools)

async def main():
    app = await build_agent_with_mcp()
    while True:
        query = input("\n请问（输入q退出）:").strip()
        if query.lower() == "q":
            break
        print("\nAgent 工作过程：")
        async for chunk in app.astream({"messages": [HumanMessage(content=query)]}, stream_mode="values"):
            last = chunk["messages"][-1]
            if not isinstance(last, AIMessage):
                continue
            tool_calls = getattr(last, "tool_calls", None)
            if tool_calls:
                print("🔧 调用工具：", [tc["name"] for tc in tool_calls])
            elif last.content:
                print("💭", last.content)
        print("\n")

if __name__ == "__main__":
    asyncio.run(main())
