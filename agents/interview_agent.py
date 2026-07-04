# agents/interview_agent.py
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
    llm = ChatOpenAI(model="gpt-4o", temperature=0.4)
    
    # 🐳 Dynamic path for Docker vs Local
    python_cmd = os.getenv("PYTHON_CMD", ".venv/bin/python")
    
    server_params = StdioServerParameters(
        command=python_cmd, 
        args=["mcp_servers/knowledge_server.py"]
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await load_mcp_tools(session)
            
            system_prompt = (
                "You are a FAANG Principal Product Leader and a ruthless 'Bar Raiser' interviewer.\n"
                "The user is preparing for a highly competitive Senior/Principal AI Product Manager interview.\n\n"
                "YOUR DIRECTIVES:\n"
                "1. You MUST call `read_master_career_profile` FIRST to understand the user's actual background.\n"
                "2. Generate a brutally specific, high-pressure System Design or Behavioral question that forces the user to apply their past frameworks to the hiring company's needs.\n"
                "3. If the user is answering a question, grade their structural delivery and rewrite into a pristine STAR-method framework.\n\n"
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


def interview_agent(prompt: str, session_id: str, tenant_id: str) -> str:
    relevant_memories = search_memory(session_id, tenant_id, prompt, category="interview")
    memory_context = f"### Previous Interview Context:\n{chr(10).join(relevant_memories)}\n\n" if relevant_memories else ""
    enhanced_question = f"{memory_context}Current User Input:\n{prompt}".strip()

    ctx = contextvars.Context()
    answer = ctx.run(asyncio.run, run_mcp_agent(enhanced_question))

    save_memory(session_id, tenant_id, f"User: {prompt}", category="interview")
    save_memory(session_id, tenant_id, f"Agent: {answer}", category="interview")

    return answer