# agents/research_agent.py
import os
import asyncio
import contextvars
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

# 🛡️ Modern MCP Client Imports
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools

# 🛡️ IMPORT LONG-TERM MEMORY FROM YOUR ARCHITECTURE
from memory.chroma_store import search_memory, save_memory

async def run_mcp_agent(prompt_str: str) -> str:
    """
    Handles the asynchronous lifecycle of connecting to the MCP Server,
    fetching tools, and running the agent inside an isolated loop.
    """
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    # 🐳 Dynamic path for Docker vs Local
    python_cmd = os.getenv("PYTHON_CMD", ".venv/bin/python")
    
    server_params = StdioServerParameters(
        command=python_cmd,
        args=["mcp_servers/utility_server.py"]
    )
    
    # 1. The connection MUST stay open while the agent executes
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await load_mcp_tools(session)
            
            research_prompt = (
                "You are a Principal Market Researcher and Data Analyst.\n"
                "You have access to standardized tools via the Model Context Protocol.\n"
                "Your goal is to provide deep, factual, and highly structured market intelligence.\n\n"
                "Rules for using search tools:\n"
                "1. NEVER search using full sentences or paragraphs. Only use short, targeted keywords.\n"
                "2. If your first search returns no results, try broader or alternative keywords.\n"
                "3. Always verify current market data, trends, or unit economics using the tool before answering.\n\n"
                "Formatting Rules:\n"
                "1. Structure your answers with clear headings, subheadings, and bullet points.\n"
                "2. If providing financial figures, market sizes, or statistics, cite the source URL context.\n"
                "3. Do not guess. If data is unavailable after 2 distinct search attempts, explicitly state what is unknown.\n\n"
                "🛡️ CRITICAL ERROR HANDLING (MICRO-HEALING):\n"
                "If a tool returns an error, do not panic. Read the exact error message, "
                "understand why your parameters failed, adjust them, and try again. "
                "If it fails multiple times, explicitly tell the user the tool is currently unavailable."
            )

            # 2. Run the async agent execution
            agent_executor = create_react_agent(llm, tools=tools, prompt=research_prompt)
            
            # 🛡️ Execute with a recursion limit to cap the retry loop and prevent system crashes
            response = await agent_executor.ainvoke(
                {"messages": [("human", prompt_str)]},
                config={"recursion_limit": 15}
            )
            
            return response["messages"][-1].content


# LEVEL 11: MCP-Powered Sync Wrapper with Context Isolation
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

    # 🚀 Create a blank context bubble for the async runtime
    ctx = contextvars.Context()
    
    # Run the async MCP loop entirely inside the isolated bubble
    answer = ctx.run(asyncio.run, run_mcp_agent(enhanced_question))

    save_memory(session_id, tenant_id, f"User Research Question: {prompt}", category="research")
    save_memory(session_id, tenant_id, f"Research Findings: {answer}", category="research")

    return answer