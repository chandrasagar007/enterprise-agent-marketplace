import os
import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 1. Dynamically resolve paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "../../"))
CHROMA_PATH = os.path.join(PROJECT_ROOT, "chroma_db")
ENV_PATH = os.path.join(PROJECT_ROOT, ".env")
DATA_PATH = os.path.join(PROJECT_ROOT, "rag", "data")

# Load environment variables
load_dotenv(dotenv_path=ENV_PATH)

# 2. Connect to Chroma DB
client = chromadb.PersistentClient(path=CHROMA_PATH)
openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key=os.environ.get("OPENAI_API_KEY"),
    model_name="text-embedding-3-small"
)

# 3. Create a dedicated collection just for Mental Models
collection = client.get_or_create_collection(
    name="mental_models_knowledge", 
    embedding_function=openai_ef
)

def ingest_books(data_dir=DATA_PATH):
    print(f"Scanning books in: {data_dir}")
    
    # Ensure the data directory exists
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        print(f"Created directory at {data_dir}. Please add your PDFs here and run again.")
        return

    # Smart chunking that respects paragraphs and sentences
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    
    for file in os.listdir(data_dir):
        file_path = os.path.join(data_dir, file)
        documents = []
        
        if file.endswith(".pdf"):
            print(f"Reading PDF: {file}...")
            loader = PyPDFLoader(file_path)
            documents = loader.load()
        elif file.endswith(".txt"):
            print(f"Reading Text file: {file}...")
            loader = TextLoader(file_path)
            documents = loader.load()
        else:
            continue
            
        chunks = text_splitter.split_documents(documents)
        
        for i, chunk in enumerate(chunks):
            collection.add(
                ids=[f"{file}_chunk_{i}"],
                documents=[chunk.page_content],
                metadatas=[{"source": file, "page": chunk.metadata.get("page", 0)}]
            )
        print(f"Successfully ingested: {file}")
        
    print("Mental Models successfully ingested!")

if __name__ == "__main__":
    ingest_books()