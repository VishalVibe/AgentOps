import redis
import json
from chromadb import HttpClient
from langchain_chroma import Chroma
from langchain_core.documents import Document
# using some dummy embeddings or real embeddings (but we only have Groq API, let's just use HuggingFace embeddings which is free or local, wait, we need an embedding model)
# I will use HuggingFaceEmbeddings since it's common. I'll need to pip install sentence-transformers.
from langchain_community.embeddings import HuggingFaceEmbeddings
import uuid
import os

class MemoryManager:
    def __init__(self, task_id: str):
        self.task_id = task_id
        
        # Short term memory in Redis
        try:
            self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
        except Exception:
            self.redis_client = None
            
        # Long term memory in ChromaDB
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        
        try:
            self.chroma_client = HttpClient(host="localhost", port=8000)
            self.vector_store = Chroma(
                client=self.chroma_client,
                collection_name="agent_long_term_memory",
                embedding_function=self.embeddings
            )
        except Exception as e:
            self.vector_store = None
            print(f"Warning: ChromaDB not available: {e}")

    # Short Term Memory (Working Memory)
    def save_working_memory(self, state: dict):
        if self.redis_client:
            # We serialize the plan and current status
            self.redis_client.set(f"task:{self.task_id}:state", json.dumps(state, default=str))
            
    def get_working_memory(self):
        if self.redis_client:
            data = self.redis_client.get(f"task:{self.task_id}:state")
            if data:
                return json.loads(data)
        return None
        
    def clear_working_memory(self):
        if self.redis_client:
            self.redis_client.delete(f"task:{self.task_id}:state")

    # Long Term Semantic Memory
    def save_long_term_memory(self, task_description: str, execution_summary: str, lessons_learned: str):
        if self.vector_store:
            doc = Document(
                page_content=f"Task: {task_description}\nSummary: {execution_summary}\nLessons: {lessons_learned}",
                metadata={"task_id": self.task_id}
            )
            self.vector_store.add_documents([doc])
            
    def query_long_term_memory(self, query: str, k: int = 3):
        if self.vector_store:
            results = self.vector_store.similarity_search(query, k=k)
            return [res.page_content for res in results]
        return []
