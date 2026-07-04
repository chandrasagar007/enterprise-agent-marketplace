# agents/mentor_agent.py
import os
import asyncio
import contextvars
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from memory.chroma_store import search_memory, save_memory

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools

async def run_mcp_agent(prompt_str: str) -> str:
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
    
    # 🐳 Dynamic path for Docker vs Local
    python_cmd = os.getenv("PYTHON_CMD", ".venv/bin/python")
    
    # 1. Define both server connections
    utility_params = StdioServerParameters(command=python_cmd, args=["mcp_servers/utility_server.py"])
    knowledge_params = StdioServerParameters(command=python_cmd, args=["mcp_servers/knowledge_server.py"])
    
    # 2. Open dual stdio streams simultaneously
    async with stdio_client(utility_params) as (read_u, write_u), stdio_client(knowledge_params) as (read_k, write_k):
        async with ClientSession(read_u, write_u) as sess_u, ClientSession(read_k, write_k) as sess_k:
            
            await sess_u.initialize()
            await sess_k.initialize()
            
            # Combine tools from both isolated servers
            tools = await load_mcp_tools(sess_u) + await load_mcp_tools(sess_k)
            
            mentor_prompt = (
                "You are an elite Executive Strategy Consultant and Leadership Coach.\n"
                "Your goal is to help the user break down complex professional decisions and think from absolute first principles.\n\n"
                "Rules for tool usage:\n"
                "1. When asked about strategy or framework applications, ALWAYS call `search_mental_models` to check internal libraries.\n"
                "2. Utilize `search_web` to cross-reference internal concepts with active real-world data.\n\n"
                "Formatting Rules:\n"
                "1. Provide highly structured advisory updates using clear markdown headings and bullet points.\n\n"
                "🛡️ CRITICAL ERROR HANDLING (MICRO-HEALING):\n"
                "If a tool returns an error, do not panic. Read the exact error message, "
                "understand why your parameters failed, adjust them, and try again. "
                "If it fails multiple times, explicitly tell the user the tool is currently unavailable."
            )

            agent_executor = create_react_agent(llm, tools=tools, prompt=mentor_prompt)
            
            # 🛡️ Apply the retry ceiling to prevent infinite loops
            response = await agent_executor.ainvoke(
                {"messages": [("human", prompt_str)]},
                config={"recursion_limit": 15}
            )
            return response["messages"][-1].content


def mentor_agent(prompt: str, session_id: str, tenant_id: str) -> str:
    relevant_memories = search_memory(session_id, tenant_id, prompt, category="mentor")
    memory_context = "### Relevant Previous Strategic History:\n" + "\n".join(relevant_memories) if relevant_memories else ""
    enhanced_question = f"{memory_context}\n\nCurrent Strategic Objective:\n{prompt}".strip()

    ctx = contextvars.Context()
    answer = ctx.run(asyncio.run, run_mcp_agent(enhanced_question))

    save_memory(session_id, tenant_id, f"Strategic Objective: {prompt}", category="mentor")
    save_memory(session_id, tenant_id, f"Advisory Response: {answer}", category="mentor")

    return answer