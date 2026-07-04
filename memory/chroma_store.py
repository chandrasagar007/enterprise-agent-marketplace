import chromadb
import uuid
import os
from chromadb.utils import embedding_functions

# 1. Initialize the persistent client globally
client = chromadb.PersistentClient(
    path="./chroma_db"
)

# 2. Define the fast OpenAI Embedding Function
openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key=os.environ.get("OPENAI_API_KEY"),
    model_name="text-embedding-3-small"
)

# 3. Apply the embedding function to the collection
collection = client.get_or_create_collection(
    name="user_memory",
    embedding_function=openai_ef
)

def save_memory(
    session_id: str,
    tenant_id: str,
    text: str,
    category: str
):
    collection.add(
        ids=[str(uuid.uuid4())],
        documents=[text],
        metadatas=[
            {
                "session_id": session_id,
                "tenant_id": tenant_id, # LEVEL 8: Inject Tenant Metadata
                "category": category
            }
        ]
    )

def search_memory(
    session_id: str,
    tenant_id: str,
    query: str,
    category: str,
    n_results: int = 3
):
    # LEVEL 8: Force strict $and matching on both session AND tenant
    results = collection.query(
        query_texts=[query],
        n_results=n_results,
        where={
            "$and": [
                {"session_id": {"$eq": session_id}},
                {"tenant_id": {"$eq": tenant_id}},
                {"category": {"$eq": category}}
            ]
        }
    )

    if results and "documents" in results and results["documents"]:
        return results["documents"][0]

    return []