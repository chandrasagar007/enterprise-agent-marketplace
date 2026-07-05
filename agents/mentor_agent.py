# agents/mentor_agent.py
import os
import asyncio
import contextvars
import dspy
import sys

from memory.chroma_store import search_memory, save_memory
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools

class MentorSignature(dspy.Signature):
    """
    You are an elite Executive Strategy Consultant and Leadership Coach.
    Help the user break down complex professional decisions and think from absolute first principles.
    1. ALWAYS call search_mental_models to check internal libraries for frameworks.
    2. Utilize search_web to cross-reference internal concepts with active real-world data.
    3. Provide highly structured advisory updates using clear markdown headings and bullet points.
    """
    prompt = dspy.InputField(desc="The user's strategic objective and historical context.")
    answer = dspy.OutputField(desc="A highly structured advisory response using markdown.")

async def run_mcp_agent(prompt_str: str) -> str:
    python_cmd = os.getenv("PYTHON_CMD", ".venv/bin/python")
    utility_params = StdioServerParameters(command=python_cmd, args=["mcp_servers/utility_server.py"])
    knowledge_params = StdioServerParameters(command=python_cmd, args=["mcp_servers/knowledge_server.py"])
    loop = asyncio.get_running_loop()
    
    async with stdio_client(utility_params) as (read_u, write_u), stdio_client(knowledge_params) as (read_k, write_k):
        async with ClientSession(read_u, write_u) as sess_u, ClientSession(read_k, write_k) as sess_k:
            await sess_u.initialize()
            await sess_k.initialize()
            
            mcp_tools = await load_mcp_tools(sess_u) + await load_mcp_tools(sess_k)
            
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
                    react_engine = dspy.ReAct(MentorSignature, tools=dspy_tools, max_iters=5)
                    return react_engine(prompt=prompt_str).answer
            
            return await asyncio.to_thread(execute_dspy)

def mentor_agent(prompt: str, session_id: str, tenant_id: str) -> str:
    relevant_memories = search_memory(session_id, tenant_id, prompt, category="mentor")
    memory_context = "### Relevant Previous Strategic History:\n" + "\n".join(relevant_memories) if relevant_memories else ""
    enhanced_question = f"{memory_context}\n\nCurrent Strategic Objective:\n{prompt}".strip()

    ctx = contextvars.Context()
    answer = ctx.run(asyncio.run, run_mcp_agent(enhanced_question))

    save_memory(session_id, tenant_id, f"Strategic Objective: {prompt}", category="mentor")
    save_memory(session_id, tenant_id, f"Advisory Response: {answer}", category="mentor")
    return answer