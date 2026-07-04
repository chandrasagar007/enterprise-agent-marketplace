import os
import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv

# 1. Dynamically resolve paths so it always finds your project root
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "../../"))
CHROMA_PATH = os.path.join(PROJECT_ROOT, "chroma_db")
ENV_PATH = os.path.join(PROJECT_ROOT, ".env")

# Load environment variables
load_dotenv(dotenv_path=ENV_PATH)

# 2. Connect to your existing Chroma DB
client = chromadb.PersistentClient(path=CHROMA_PATH)
openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key=os.environ.get("OPENAI_API_KEY"),
    model_name="text-embedding-3-small"
)

# 3. Create a dedicated collection just for the codebase
collection = client.get_or_create_collection(
    name="codebase_knowledge", 
    embedding_function=openai_ef
)

def ingest_codebase(directory=PROJECT_ROOT):
    print(f"Scanning codebase starting from: {directory}")
    
    for root, _, files in os.walk(directory):
        # Ignore virtual environments, git, DB folders, and the rag data folder
        if any(ignore in root for ignore in [".venv", "__pycache__", ".git", "chroma_db", "rag/data"]):
            continue
            
        for file in files:
            if file.endswith(".py") or file.endswith(".md"):
                file_path = os.path.join(root, file)
                
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        
                    # Basic chunking (2000 chars per chunk)
                    chunks = [content[i:i+2000] for i in range(0, len(content), 2000)]
                    
                    for i, chunk in enumerate(chunks):
                        collection.add(
                            ids=[f"{file_path}_chunk_{i}"],
                            documents=[chunk],
                            metadatas=[{"file_path": file_path}]
                        )
                    print(f"Ingested: {file}")
                except Exception as e:
                    print(f"Skipped {file} due to error: {e}")
                
    print("Codebase successfully ingested!")

if __name__ == "__main__":
    ingest_codebase()