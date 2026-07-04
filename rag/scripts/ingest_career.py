# rag/scripts/ingest_career.py
import os
import uuid
import sys
from dotenv import load_dotenv
import chromadb
from chromadb.utils import embedding_functions
from pypdf import PdfReader

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
load_dotenv()

def chunk_text(text: str, max_chars: int = 1000, overlap: int = 200) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + max_chars
        chunks.append(text[start:end])
        start += (max_chars - overlap)
    return chunks

def extract_text_from_pdf(pdf_path: str) -> str:
    text = ""
    try:
        reader = PdfReader(pdf_path)
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
    except Exception as e:
        print(f"⚠️ Warning: Could not read {pdf_path}. Error: {e}")
    return text

def run_career_ingestion():
    print("🚀 Initializing Dynamic PDF Career Ingestion Pipeline...")
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ ERROR: OPENAI_API_KEY missing from environment.")
        return

    # 1. ABSOLUTE PATH FIX for Target Directory
    target_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../career_data"))
    pdf_files = [f for f in os.listdir(target_dir) if f.lower().endswith('.pdf')]
    
    # 2. ABSOLUTE PATH FIX for ChromaDB
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../chroma_db"))
    chroma_client = chromadb.PersistentClient(path=db_path)
    
    ef = embedding_functions.OpenAIEmbeddingFunction(
        api_key=api_key,
        model_name="text-embedding-3-small"
    )

    collection_name = "career_knowledge"
    try:
        chroma_client.delete_collection(name=collection_name)
        print(f"🧹 Flushed old collection index: '{collection_name}'")
    except Exception:
        pass

    career_collection = chroma_client.create_collection(name=collection_name, embedding_function=ef)
    print(f"📁 Created fresh vector collection storage: '{collection_name}' in {db_path}")

    total_chunks = 0
    for filename in pdf_files:
        file_path = os.path.join(target_dir, filename)
        print(f"📄 Reading and extracting: {filename}...")
        
        raw_text = extract_text_from_pdf(file_path)
        if not raw_text.strip():
            print(f"   ⚠️ Skipping {filename} - No extractable text found.")
            continue
            
        chunks = chunk_text(raw_text)
        documents, metadatas, ids = [], [], []

        for idx, chunk in enumerate(chunks):
            documents.append(chunk)
            metadatas.append({"source": filename, "ingested_at": "2026-06-15"})
            ids.append(f"career_{filename.replace(' ', '_')}_{idx}_{str(uuid.uuid4())[:8]}")

        career_collection.add(documents=documents, metadatas=metadatas, ids=ids)
        total_chunks += len(documents)
        print(f"   ✅ Ingested {len(documents)} chunks from {filename}")

    print(f"\n✨ SUCCESS: Vectorization complete! Ingested {total_chunks} total blocks into '{collection_name}'.")

if __name__ == "__main__":
    run_career_ingestion()