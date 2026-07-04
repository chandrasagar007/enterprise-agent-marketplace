# mcp_servers/utility_server.py
import os
from datetime import datetime
from mcp.server.fastmcp import FastMCP
from tavily import TavilyClient
from dotenv import load_dotenv

load_dotenv()

# 1. Initialize the MCP Server
# This is essentially exactly like initializing a FastAPI app
mcp = FastMCP("Enterprise_Utility_Server")

# 2. Define the tools using the @mcp.tool() decorator
# The docstrings are CRITICAL. The LLM reads these to know how to use the tool.

@mcp.tool()
def get_current_datetime() -> str:
    """Returns the current date and time."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

@mcp.tool()
def calculator(expression: str) -> str:
    """
    Perform mathematical calculations on expressions.
    Example input: '2500000 / 30 / 24 / 3600'
    """
    allowed = {"__builtins__": None}
    try:
        result = eval(expression, allowed, {})
        return str(result)
    except Exception as e:
        return f"Calculation error: {e}"

@mcp.tool()
def search_web(query: str) -> str:
    """
    Search the live web using Tavily.
    Use this to pull deep research, current real-world trends, or external market data.
    """
    try:
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            return "Error: TAVILY_API_KEY is not set in the environment."
            
        client = TavilyClient(api_key=api_key)
        response = client.search(query=query, search_depth="advanced", max_results=3)
        
        output = []
        for i, result in enumerate(response.get("results", []), start=1):
            output.append(
                f"{i}. {result.get('title')}\n"
                f"URL: {result.get('url')}\n"
                f"Content: {result.get('content')}\n"
            )
        return "\n".join(output)
    except Exception as e:
        return f"Search failed: {e}"

if __name__ == "__main__":
    # Run the server over standard input/output (stdio)
    mcp.run()