# mcp_servers/knowledge_server.py
import os
from mcp.server.fastmcp import FastMCP
import chromadb
from chromadb.utils import embedding_functions

mcp = FastMCP("Enterprise_Knowledge_Server")

WORKSPACE_DIR = os.path.abspath(os.getcwd())
CHROMA_PATH = os.path.join(WORKSPACE_DIR, "chroma_db")
PROFILE_PATH = os.path.join(WORKSPACE_DIR, "rag", "career_data", "master_cheat_sheet.md")

# Initialize Chroma connection safely
try:
    chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
    ef = embedding_functions.OpenAIEmbeddingFunction(
        api_key=os.environ.get("OPENAI_API_KEY"),
        model_name="text-embedding-3-small"
    )
    codebase_collection = chroma_client.get_collection(name="codebase_knowledge", embedding_function=ef)
    books_collection = chroma_client.get_collection(name="mental_models_knowledge", embedding_function=ef)
    career_collection = chroma_client.get_collection(name="career_knowledge", embedding_function=ef)
except Exception as e:
    print(f"Warning: Could not initialize ChromaDB. Make sure it exists. Details: {e}")

@mcp.tool()
def search_codebase(query: str) -> str:
    """Search the local project codebase to inspect files or analyze structural layouts."""
    try:
        results = codebase_collection.query(query_texts=[query], n_results=3)
        if not results or not results['documents'] or not results['documents'][0]:
            return "No relevant codebase components found."
        
        output = []
        for doc, meta in zip(results['documents'][0], results['metadatas'][0]):
            output.append(f"File: {meta.get('file_path', 'Unknown')}\nCode Snippet:\n{doc}\n")
        return "\n---\n".join(output)
    except Exception as e:
        return f"Database error: {str(e)}"

@mcp.tool()
def search_mental_models(query: str) -> str:
    """Search internal strategic frameworks and documentation libraries."""
    try:
        results = books_collection.query(query_texts=[query], n_results=3)
        if not results or not results['documents'] or not results['documents'][0]:
            return "No relevant strategic guidelines found."
        
        output = []
        for doc, meta in zip(results['documents'][0], results['metadatas'][0]):
            output.append(f"Source: {meta.get('source', 'Unknown')} (Page {meta.get('page', 'N/A')})\nExcerpt:\n{doc}\n")
        return "\n---\n".join(output)
    except Exception as e:
        return f"Database error: {str(e)}"

@mcp.tool()
def search_career_history(query: str) -> str:
    """Search the user's personal career history, resume, and architectural wins."""
    try:
        results = career_collection.query(query_texts=[query], n_results=3)
        if not results or not results['documents'] or not results['documents'][0]:
            return "No relevant career history found."
        
        output = []
        for doc, meta in zip(results['documents'][0], results['metadatas'][0]):
            output.append(f"Category: {meta.get('category', 'General')}\nDetail:\n{doc}\n")
        return "\n---\n".join(output)
    except Exception as e:
        return f"Database error: {str(e)}"

@mcp.tool()
def read_master_career_profile() -> str:
    """Reads the user's fully synthesized FAANG Master Career Profile."""
    try:
        if not os.path.exists(PROFILE_PATH):
            return f"Error: Master Profile not found at {PROFILE_PATH}"
        with open(PROFILE_PATH, "r", encoding="utf-8") as f:
            return f.read()[:25000] 
    except Exception as e:
        return f"Error reading Master Profile: {str(e)}"

if __name__ == "__main__":
    mcp.run()