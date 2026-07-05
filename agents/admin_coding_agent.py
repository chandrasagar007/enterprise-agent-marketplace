# agents/admin_coding_agent.py
import os
import asyncio
import contextvars
import dspy
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools

class AdminCodingSignature(dspy.Signature):
    """
    You are an Elite Enterprise DevOps Engineer with admin privileges.
    Execute destructive file operations (writes, refactors, deletions) as requested.
    You can safely assume the user has authorized this action.
    1. Execute the requested file modification using your tools.
    2. Return a precise summary of exactly what was modified, created, or deleted.
    """
    prompt = dspy.InputField(desc="The user's destructive codebase query.")
    answer = dspy.OutputField(desc="A precise summary of what was modified, created, or deleted.")

async def run_mcp_agent(prompt_str: str) -> str:
    python_cmd = os.getenv("PYTHON_CMD", ".venv/bin/python")
    server_params = StdioServerParameters(command=python_cmd, args=["mcp_servers/workspace_server.py"])
    loop = asyncio.get_running_loop()
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            mcp_tools = await load_mcp_tools(session)
            
            dspy_tools = []
            for tool in mcp_tools:
                def make_dspy_tool(lc_tool):
                    def sync_tool_wrapper(query: str) -> str:
                        print(f"[DSPy Tool Call] Invoking {lc_tool.name}", file=sys.stderr, flush=True)
                        try:
                            future = asyncio.run_coroutine_threadsafe(lc_tool.ainvoke({"query": query}), loop)
                            return str(future.result())
                        except Exception as e:
                            return f"Tool execution failed: {str(e)}"
                    sync_tool_wrapper.__name__ = lc_tool.name.replace("-", "_")
                    sync_tool_wrapper.__doc__ = lc_tool.description
                    return sync_tool_wrapper
                dspy_tools.append(make_dspy_tool(tool))
            
            def execute_dspy():
                llm = dspy.LM('openai/gpt-4o-mini', max_tokens=2000)
                with dspy.context(lm=llm):
                    react_engine = dspy.ReAct(AdminCodingSignature, tools=dspy_tools, max_iters=5)
                    return react_engine(prompt=prompt_str).answer
            
            return await asyncio.to_thread(execute_dspy)

def admin_coding_agent(prompt: str, session_id: str, tenant_id: str) -> str:
    ctx = contextvars.Context()
    return ctx.run(asyncio.run, run_mcp_agent(prompt))