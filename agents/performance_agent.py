# agents/performance_agent.py
import os
import asyncio
import contextvars
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
# 🧠 ADDED: Import ChromaDB save functionality
from memory.chroma_store import save_memory

async def run_mcp_agent(prompt_str: str, session_id: str) -> str:
    """Handles async connection to Workspace Server to parse telemetry streams."""
    llm = ChatOpenAI(model="gpt-4o", temperature=0.2) # Use GPT-4o for better rule synthesis
    
    python_cmd = os.getenv("PYTHON_CMD", ".venv/bin/python")
    
    server_params = StdioServerParameters(
        command=python_cmd,
        args=["mcp_servers/workspace_server.py"]
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await load_mcp_tools(session)
            
            system_prompt = (
                "You are an Elite Enterprise Performance Auditor and Systems Rule Synthesizer.\n"
                f"CRITICAL: Always use the `read_telemetry_logs` tool with the current session_id ('{session_id}').\n"
                "If the user is submitting negative feedback, analyze the logs to see what the agents did wrong.\n"
                "Generate a strict, 1-sentence system rule to prevent this failure in the future."
            )

            agent_executor = create_react_agent(llm, tools=tools, prompt=system_prompt)
            response = await agent_executor.ainvoke(
                {"messages": [("human", prompt_str)]},
                config={"recursion_limit": 15} # 🛡️ Micro-Healing Limit
            )
            return response["messages"][-1].content


def performance_agent(prompt: str, session_id: str, tenant_id: str) -> str:
    """Synchronous bridge. Automatically saves synthesized rules to Memory."""
    ctx = contextvars.Context()
    answer = ctx.run(asyncio.run, run_mcp_agent(prompt, session_id))
    
    # 🧠 MACRO-LEARNING: Automatically persist the synthesized rule to ChromaDB
    # We only save it if the LLM output looks like a rule (not just a standard chat response)
    if "rule:" in answer.lower() or "prevent this" in answer.lower():
         save_memory(session_id, tenant_id, f"Learned Rule: {answer}", category="system_rules")
    
    return answer