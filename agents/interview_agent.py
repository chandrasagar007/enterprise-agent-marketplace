# agents/interview_agent.py
import os
import asyncio
import contextvars
import dspy
import sys

from memory.chroma_store import search_memory, save_memory
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools

class InterviewSignature(dspy.Signature):
    """
    You are a FAANG Principal Product Leader and a ruthless 'Bar Raiser' interviewer.
    1. Call read_master_career_profile FIRST to understand the user's background.
    2. Generate a brutally specific, high-pressure System Design or Behavioral question.
    3. If grading, rewrite their answer into a pristine STAR-method framework.
    """
    prompt = dspy.InputField(desc="The user input and interview context.")
    answer = dspy.OutputField(desc="A challenging interview question or a STAR-method grade and rewrite.")

async def run_mcp_agent(prompt_str: str) -> str:
    python_cmd = os.getenv("PYTHON_CMD", ".venv/bin/python")
    server_params = StdioServerParameters(command=python_cmd, args=["mcp_servers/knowledge_server.py"])
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
                llm = dspy.LM('openai/gpt-4o', max_tokens=2000)
                with dspy.context(lm=llm):
                    react_engine = dspy.ReAct(InterviewSignature, tools=dspy_tools, max_iters=5)
                    return react_engine(prompt=prompt_str).answer
            
            return await asyncio.to_thread(execute_dspy)

def interview_agent(prompt: str, session_id: str, tenant_id: str) -> str:
    relevant_memories = search_memory(session_id, tenant_id, prompt, category="interview")
    memory_context = f"### Previous Interview Context:\n{chr(10).join(relevant_memories)}\n\n" if relevant_memories else ""
    enhanced_question = f"{memory_context}Current User Input:\n{prompt}".strip()

    ctx = contextvars.Context()
    answer = ctx.run(asyncio.run, run_mcp_agent(enhanced_question))

    save_memory(session_id, tenant_id, f"User: {prompt}", category="interview")
    save_memory(session_id, tenant_id, f"Agent: {answer}", category="interview")

    return answer