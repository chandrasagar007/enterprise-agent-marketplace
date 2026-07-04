# agents/performance_agent.py
import os
import asyncio
import contextvars
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

# 🛡️ MCP Client & Adapter Imports
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools

async def run_mcp_agent(prompt_str: str, session_id: str) -> str:
    """Handles async connection to Workspace Server to parse telemetry streams."""
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
                "You are an Elite Enterprise Performance Auditor.\n"
                "Your job is to analyze system latency, token usage, and internal execution steps.\n"
                f"CRITICAL: Always use the `read_telemetry_logs` tool with the current session_id ('{session_id}').\n"
                "1. You MUST look for log lines containing 'STEP='.\n"
                "2. Provide a strict chronological timeline of how long each specific internal node took to execute.\n"
                "3. Identify which specific node caused the bottleneck."
            )

            agent_executor = create_react_agent(llm, tools=tools, prompt=system_prompt)
            response = await agent_executor.ainvoke({"messages": [("human", prompt_str)]})
            return response["messages"][-1].content


def performance_agent(prompt: str, session_id: str, tenant_id: str) -> str:
    """Synchronous bridge with Context Isolation for Performance Telemetry Auditor."""
    ctx = contextvars.Context()
    return ctx.run(asyncio.run, run_mcp_agent(prompt, session_id))