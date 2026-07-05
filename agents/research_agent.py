# agents/research_agent.py
import os
import asyncio
import contextvars
import dspy
import sys

# 🛡️ Modern MCP Client Imports
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools

# 🛡️ IMPORT LONG-TERM MEMORY FROM YOUR ARCHITECTURE
from memory.chroma_store import search_memory, save_memory

# ---------------------------------------------------------
# 1. DSPy SIGNATURE
# ---------------------------------------------------------
class ResearchSignature(dspy.Signature):
    """
    You are an elite Enterprise Research Agent. 
    You must use your available tools to gather real-world facts, market data, or current events.
    Synthesize the tool outputs into a highly professional, structured markdown report.
    Do not hallucinate facts; rely strictly on the tool outputs.
    """
    prompt = dspy.InputField(desc="The user's research request, including any historical conversation context.")
    answer = dspy.OutputField(desc="A detailed, factual, and well-structured markdown report answering the user.")

# ---------------------------------------------------------
# 2. ASYNC MCP ENGINE & DSPY BRIDGE
# ---------------------------------------------------------
async def run_mcp_agent(prompt_str: str) -> str:
    """
    Handles the asynchronous lifecycle of connecting to the MCP Server,
    converting the tools, and running the DSPy agent inside an isolated thread.
    """
    python_cmd = os.getenv("PYTHON_CMD", ".venv/bin/python")
    
    server_params = StdioServerParameters(
        command=python_cmd,
        args=["mcp_servers/utility_server.py"]
    )
    
    loop = asyncio.get_running_loop()
    
    # 1. The connection MUST stay open while the agent executes
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            mcp_tools = await load_mcp_tools(session)
            
            # 🧠 THE BRIDGE: Convert Async LangChain MCP Tools into Native Sync Python Functions for DSPy
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
                            print(f"[DSPy Tool Error] {lc_tool.name} failed: {str(e)}", file=sys.stderr, flush=True)
                            return f"Tool execution failed: {str(e)}"
                            
                    sync_tool_wrapper.__name__ = lc_tool.name.replace("-", "_")
                    sync_tool_wrapper.__doc__ = lc_tool.description
                    return sync_tool_wrapper
                    
                dspy_tools.append(make_dspy_tool(tool))
            
            # 2. Run the DSPy agent inside a synchronous thread to prevent Event Loop blocking
            def execute_dspy():
                print("[DSPy Engine] Initializing isolated ReAct execution context thread...", file=sys.stderr, flush=True)
                llm = dspy.LM('openai/gpt-4o-mini', max_tokens=2000)
                with dspy.context(lm=llm):
                    react_engine = dspy.ReAct(ResearchSignature, tools=dspy_tools, max_iters=5)
                    result = react_engine(prompt=prompt_str)
                    print(f"[DSPy Engine] Finished. Generated response length: {len(result.answer)} characters.", file=sys.stderr, flush=True)
                    return result.answer
            
            response = await asyncio.to_thread(execute_dspy)
            return response

# ---------------------------------------------------------
# 3. SYNCHRONOUS LANGGRAPH WRAPPER WITH STATE HOOKS
# ---------------------------------------------------------
def research_agent(prompt: str, session_id: str, tenant_id: str) -> str:
    """
    Acts as the synchronous bridge. Isolates the inner async execution 
    from the outer LangGraph state to prevent Checkpointer collision.
    """
    relevant_memories = search_memory(session_id, tenant_id, prompt, category="research")
    memory_context = ""
    if relevant_memories:
        memory_context = "### Relevant Previous Research Context:\n" + "\n".join(relevant_memories)

    enhanced_question = f"{memory_context}\n\nCurrent Research Objective:\n{prompt}".strip()

    ctx = contextvars.Context()
    answer = ctx.run(asyncio.run, run_mcp_agent(enhanced_question))

    save_memory(session_id, tenant_id, f"User Research Question: {prompt}", category="research")
    save_memory(session_id, tenant_id, f"Research Findings: {answer}", category="research")

    return answer