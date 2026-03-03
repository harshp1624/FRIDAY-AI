import chromadb
from chromadb.config import Settings
import datetime
import os

class MemoryEngine:
    def __init__(self, db_path="./friday_memory"):
        # Ensure the DB path exists relative to where main script runs it
        self.db_path = db_path
        if not os.path.exists(self.db_path):
            os.makedirs(self.db_path)
            
        # Initialize pure local ChromaDB
        self.client = chromadb.PersistentClient(path=self.db_path)
        
        # Get or create our main conversation collection
        self.collection = self.client.get_or_create_collection(
            name="conversation_history",
            metadata={"hnsw:space": "cosine"}
        )

    def store_memory(self, role: str, text: str):
        """Stores a piece of dialogue into the local vector DB."""
        if not text.strip():
            return
            
        doc_id = f"{role}_{datetime.datetime.now().timestamp()}"
        timestamp_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        metadata = {"role": role, "timestamp": timestamp_str}
        
        self.collection.add(
            documents=[text],
            metadatas=[metadata],
            ids=[doc_id]
        )

    def search_memory(self, query: str, n_results: int = 3):
        """Searches the local DB for relevant past conversations."""
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        context_strings = []
        if results and results['documents'] and results['documents'][0]:
            docs = results['documents'][0]
            metas = results['metadatas'][0]
            for doc, meta in zip(docs, metas):
                context_strings.append(f"[{meta['timestamp']}] {meta['role'].upper()}: {doc}")
                
        return "\n".join(context_strings)

if __name__ == "__main__":
    engine = MemoryEngine()
    engine.store_memory("user", "My favorite color is dark blue.")
    print("Search Result:", engine.search_memory("favorite color"))
