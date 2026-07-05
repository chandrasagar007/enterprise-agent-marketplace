# agents/coding_agent.py
import os
import asyncio
import contextvars
import dspy
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools

class CodingSignature(dspy.Signature):
    """
    You are an elite Enterprise Software Architect.
    Navigate the local file system using your tools, analyze the codebase, and provide precise engineering answers.
    1. NEVER guess file paths. Execute list_workspace_files on the root first.
    2. Use read_file only on files that actually exist.
    3. Provide clean, factual architectural summaries based ONLY on the actual files you read.
    """
    prompt = dspy.InputField(desc="The user's codebase query.")
    answer = dspy.OutputField(desc="A precise, factual architectural summary or code explanation.")

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
                        print(f"[DSPy Tool Call] Invoking {lc_tool.name} with query: '{query}'", file=sys.stderr, flush=True)
                        try:
                            future = asyncio.run_coroutine_threadsafe(lc_tool.ainvoke({"query": query}), loop)
                            result = str(future.result())
                            print(f"[DSPy Tool Success] Resolved {lc_tool.name}", file=sys.stderr, flush=True)
                            return result
                        except Exception as e:
                            return f"Tool execution failed: {str(e)}"
                    sync_tool_wrapper.__name__ = lc_tool.name.replace("-", "_")
                    sync_tool_wrapper.__doc__ = lc_tool.description
                    return sync_tool_wrapper
                dspy_tools.append(make_dspy_tool(tool))
            
            def execute_dspy():
                llm = dspy.LM('openai/gpt-4o-mini', max_tokens=2000)
                with dspy.context(lm=llm):
                    react_engine = dspy.ReAct(CodingSignature, tools=dspy_tools, max_iters=5)
                    return react_engine(prompt=prompt_str).answer
            
            return await asyncio.to_thread(execute_dspy)

def coding_agent(prompt: str, session_id: str, tenant_id: str) -> str:
    ctx = contextvars.Context()
    return ctx.run(asyncio.run, run_mcp_agent(prompt))