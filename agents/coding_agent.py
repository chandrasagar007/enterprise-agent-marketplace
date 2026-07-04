# agents/coding_agent.py
import os
import asyncio
import contextvars
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

# 🛡️ MCP Client & Adapter Imports
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools

async def run_mcp_agent(prompt_str: str) -> str:
    """Handles async connection to Workspace Server and runs the ReAct loop."""
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    # 🐳 Dynamic path for Docker vs Local
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
                "You are an elite Enterprise Software Architect.\n"
                "Your job is to navigate the local file system using your tools, analyze the codebase, and provide precise engineering answers.\n"

                "CRITICAL INSTRUCTIONS:\n"
                "1. NEVER guess file paths. You MUST execute `list_workspace_files` (or equivalent tool) on the root directory FIRST to understand the structure.\n"
                "2. Once you see the actual file names, use `read_file` only on the files that exist.\n"
                "3. Provide clean, factual architectural summaries based ONLY on the actual files you read.\n\n"
                "🛡️ CRITICAL ERROR HANDLING (MICRO-HEALING):\n"
                "If a tool returns an error, do not panic. Read the exact error message, "
                "understand why your parameters failed, adjust them, and try again. "
                "If it fails multiple times, explicitly tell the user the tool is currently unavailable."
            )

            agent_executor = create_react_agent(llm, tools=tools, prompt=system_prompt)
            
            # 🛡️ Apply the retry ceiling to prevent infinite loops
            response = await agent_executor.ainvoke(
                {"messages": [("human", prompt_str)]},
                config={"recursion_limit": 15}
            )
            return response["messages"][-1].content


def coding_agent(prompt: str, session_id: str, tenant_id: str) -> str:
    """
    Synchronous bridge with Context Isolation. 
    Prevents the outer SqliteSaver from clashing with the inner async tools.
    """
    ctx = contextvars.Context()
    return ctx.run(asyncio.run, run_mcp_agent(prompt))