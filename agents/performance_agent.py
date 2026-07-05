# agents/performance_agent.py
import os
import asyncio
import contextvars
import dspy
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
from memory.chroma_store import save_memory

class PerformanceSignature(dspy.Signature):
    """
    You are an Elite Enterprise Performance Auditor and Systems Rule Synthesizer.
    Analyze the logs to see what the agents did wrong.
    Generate a strict, 1-sentence system rule to prevent this failure in the future.
    """
    prompt = dspy.InputField(desc="The user feedback and instructions.")
    answer = dspy.OutputField(desc="A strict, 1-sentence system rule.")

async def run_mcp_agent(prompt_str: str, session_id: str) -> str:
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
                # 🧠 Use GPT-4o for better rule synthesis
                llm = dspy.LM('openai/gpt-4o', max_tokens=1000)
                with dspy.context(lm=llm):
                    react_engine = dspy.ReAct(PerformanceSignature, tools=dspy_tools, max_iters=5)
                    # Inject the session ID explicitly into the prompt string
                    enhanced_prompt = f"{prompt_str}\n\nCRITICAL: Always use the read_telemetry_logs tool with the current session_id ('{session_id}')."
                    return react_engine(prompt=enhanced_prompt).answer
            
            return await asyncio.to_thread(execute_dspy)

def performance_agent(prompt: str, session_id: str, tenant_id: str) -> str:
    ctx = contextvars.Context()
    answer = ctx.run(asyncio.run, run_mcp_agent(prompt, session_id))
    
    if "rule:" in answer.lower() or "prevent this" in answer.lower():
         save_memory(session_id, tenant_id, f"Learned Rule: {answer}", category="system_rules")
    
    return answer