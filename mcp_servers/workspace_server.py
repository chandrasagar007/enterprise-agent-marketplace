# mcp_servers/workspace_server.py
import os
from mcp.server.fastmcp import FastMCP

# 1. Initialize the Workspace MCP Server
mcp = FastMCP("Enterprise_Workspace_Server")

WORKSPACE_DIR = os.path.abspath(os.getcwd())

@mcp.tool()
def list_workspace_files(directory: str = ".") -> str:
    """Lists all code files in the given directory to understand the project structure."""
    target_path = os.path.abspath(os.path.join(WORKSPACE_DIR, directory))
    
    if not target_path.startswith(WORKSPACE_DIR):
         return "ERROR: Path traversal detected. Access denied. You must stay within the workspace."
    
    try:
        files = []
        for root, dirs, filenames in os.walk(target_path):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
            for filename in filenames:
                if filename.endswith(('.py', '.md', '.json', '.txt', '.env.example')):
                    rel_path = os.path.relpath(os.path.join(root, filename), WORKSPACE_DIR)
                    files.append(rel_path)
        return "Available files:\n" + "\n".join(files) if files else "No readable files found."
    except Exception as e:
        return f"ERROR: Could not list files. Details: {str(e)}"

@mcp.tool()
def read_local_file(file_path: str) -> str:
    """Reads the exact content of a local file. Use this to inspect code architecture."""
    target_path = os.path.abspath(os.path.join(WORKSPACE_DIR, file_path))
    
    if not target_path.startswith(WORKSPACE_DIR):
        return "ERROR: Path traversal detected. Access denied."
    
    if not os.path.exists(target_path):
        return f"ERROR: File not found at {file_path}."
        
    try:
        with open(target_path, 'r', encoding='utf-8') as f:
            content = f.read()
            max_chars = 10000
            if len(content) > max_chars:
                return content[:max_chars] + f"\n\n...[TRUNCATED: File exceeds {max_chars} characters]"
            return content
    except Exception as e:
        return f"ERROR: Could not read file. Details: {str(e)}"

@mcp.tool()
def write_local_file(file_path: str, content: str) -> str:
    """Writes or overwrites a local file with the provided content."""
    target_path = os.path.abspath(os.path.join(WORKSPACE_DIR, file_path))
    
    if not target_path.startswith(WORKSPACE_DIR):
        return "ERROR: Path traversal detected. Access denied."
    
    try:
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        with open(target_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"SUCCESS: File successfully written to {file_path}"
    except Exception as e:
        return f"ERROR: Could not write file. Details: {str(e)}"

@mcp.tool()
def delete_local_file(file_path: str) -> str:
    """Deletes a local file. Use with extreme caution."""
    target_path = os.path.abspath(os.path.join(WORKSPACE_DIR, file_path))
    
    if not target_path.startswith(WORKSPACE_DIR):
        return "ERROR: Path traversal detected. Access denied."
    
    if not os.path.exists(target_path):
        return f"ERROR: File not found at {file_path}"
    
    try:
        os.remove(target_path)
        return f"SUCCESS: File {file_path} successfully deleted."
    except Exception as e:
        return f"ERROR: Could not delete file. Details: {str(e)}"

@mcp.tool()
def read_telemetry_logs(session_id: str) -> str:
    """Reads the recent API logs to analyze execution times, token usage, and latency for a given session."""
    log_path = os.path.join(WORKSPACE_DIR, "logs", "api.log")
    
    if not os.path.exists(log_path):
        return "ERROR: No telemetry logs found."
        
    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            recent_lines = lines[-150:]
            
        session_logs = [line for line in recent_lines if session_id in line]
        
        if not session_logs:
            return f"No telemetry data found for session: {session_id}. Look at the general recent logs instead:\n" + "".join(recent_lines[-20:])
            
        return "Telemetry Data Found:\n" + "".join(session_logs)
        
    except Exception as e:
        return f"ERROR: Could not read telemetry logs. Details: {str(e)}"

if __name__ == "__main__":
    mcp.run()