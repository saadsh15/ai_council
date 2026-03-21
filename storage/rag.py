import json
import os
from pathlib import Path
from typing import List, Dict, Optional
from utils.embeddings import Embedder, cosine_similarity
from datetime import datetime

RAG_STORAGE = Path("storage/rag_index.json")

class MemoryItem:
    def __init__(self, text: str, embedding: List[float], metadata: Dict = None):
        self.text = text
        self.embedding = embedding
        self.metadata = metadata or {}
        self.timestamp = self.metadata.get('timestamp', datetime.utcnow().isoformat())

class VectorStore:
    def __init__(self, storage_path: Path = RAG_STORAGE):
        self.storage_path = storage_path
        self.items: List[MemoryItem] = []
        self._load()

    def _load(self):
        if self.storage_path.exists():
            try:
                with open(self.storage_path, "r") as f:
                    data = json.load(f)
                    for item in data:
                        self.items.append(MemoryItem(
                            text=item['text'],
                            embedding=item['embedding'],
                            metadata=item.get('metadata', {})
                        ))
            except Exception as e:
                print(f"Error loading RAG index: {e}")

    def save(self):
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        data = [
            {
                "text": item.text,
                "embedding": item.embedding,
                "metadata": item.metadata
            } for item in self.items
        ]
        with open(self.storage_path, "w") as f:
            json.dump(data, f)

    def add(self, text: str, embedding: List[float], metadata: Dict = None):
        self.items.append(MemoryItem(text, embedding, metadata))
        self.save()

    def search(self, query_embedding: List[float], top_k: int = 3) -> List[Dict]:
        """Search for top_k most similar items."""
        if not query_embedding:
            return []
            
        scored_items = []
        for item in self.items:
            similarity = cosine_similarity(query_embedding, item.embedding)
            scored_items.append({
                "text": item.text,
                "similarity": similarity,
                "metadata": item.metadata
            })
            
        # Sort by similarity
        scored_items.sort(key=lambda x: x['similarity'], reverse=True)
        return scored_items[:top_k]
