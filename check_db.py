import chromadb
import os

# 1. Connect to the local database
db_path = os.path.abspath("./chroma_db") 
print(f"Connecting to database at: {db_path}\n")

client = chromadb.PersistentClient(path=db_path)

# 2. Target the correct collection
collection_name = "mental_models_knowledge" 

try:
    collection = client.get_collection(name=collection_name)
    
    # Fetch all data (metadata and documents)
    results = collection.get(include=["metadatas", "documents"])
    
    total_chunks = len(results['ids'])
    print(f"--- Successfully loaded '{collection_name}' ---")
    print(f"Total embedded text chunks: {total_chunks}\n")
    
    if total_chunks == 0:
        print("The collection exists, but it is empty!")
    else:
        # 3. Extract unique book titles/sources from metadata
        unique_books = set()
        for metadata in results["metadatas"]:
            if metadata:
                # Depending on how you ingested it, the book name is usually under 'source' or 'title'
                book_name = metadata.get("source") or metadata.get("title") or "Unknown Source"
                
                # Clean up the file path if it's stored as a file name (e.g., /docs/volume1.pdf -> volume1.pdf)
                clean_name = os.path.basename(str(book_name))
                unique_books.add(clean_name)
        
        print("📚 UNIQUE BOOKS SAVED IN DATABASE:")
        for book in sorted(unique_books):
            print(f"  ✅ {book}")
        
        print("\n" + "="*50 + "\n")
        
        # 4. Show a sample of the actual content (first 3 chunks just to verify)
        print("🔍 SAMPLE CONTENT (First 3 chunks):")
        for i in range(min(3, total_chunks)):
            print(f"\n[Source: {results['metadatas'][i]}]")
            print(f"Snippet: {results['documents'][i][:200]}...")
            
except Exception as e:
    print(f"\n❌ Could not load collection '{collection_name}'. Error: {e}")