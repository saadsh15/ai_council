import httpx
from typing import List
import numpy as np

class Embedder:
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url

    async def get_embedding(self, text: str, model: str = "all-minilm") -> List[float]:
        """Fetch embedding from Ollama for a given text."""
        url = f"{self.base_url}/api/embeddings"
        payload = {
            "model": model,
            "prompt": text
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(url, json=payload)
                if response.status_code == 200:
                    return response.json().get('embedding', [])
                else:
                    return []
            except Exception as e:
                print(f"Embedding error: {e}")
                return []

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    if not v1 or not v2:
        return 0.0
    
    a = np.array(v1)
    b = np.array(v2)
    
    dot_product = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    
    if norm_a == 0 or norm_b == 0:
        return 0.0
        
    return dot_product / (norm_a * norm_b)
