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
                "1. You MUST use your provided tools to answer the user's prompt.\n"
                "2. DO NOT provide generic conversational advice (e.g., do not tell the user to run bash commands).\n"
                "3. If you do not know a file path, you MUST execute `list_workspace_files` first to find it.\n"
                "4. Provide clean, factual architectural summaries based ONLY on the actual files you read."
            )

            agent_executor = create_react_agent(llm, tools=tools, prompt=system_prompt)
            response = await agent_executor.ainvoke({"messages": [("human", prompt_str)]})
            return response["messages"][-1].content


def coding_agent(prompt: str, session_id: str, tenant_id: str) -> str:
    """
    Synchronous bridge with Context Isolation. 
    Prevents the outer SqliteSaver from clashing with the inner async tools.
    """
    ctx = contextvars.Context()
    return ctx.run(asyncio.run, run_mcp_agent(prompt))