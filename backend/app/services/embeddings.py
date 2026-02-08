import hashlib
from typing import List

import numpy as np
from openai import OpenAI

from app.config import settings

def _hash_embedding(text: str, dims: int = 384) -> List[float]:
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    seed = int.from_bytes(digest[:8], "big")
    rng = np.random.default_rng(seed)
    vec = rng.normal(size=dims)
    vec = vec / np.linalg.norm(vec)
    return vec.astype(float).tolist()


def embed_texts(texts: List[str]) -> List[List[float]]:
    if not texts:
        return []
    if settings.openai_api_key:
        client = OpenAI(api_key=settings.openai_api_key)
        response = client.embeddings.create(
            model=settings.openai_embedding_model,
            input=texts,
        )
        return [item.embedding for item in response.data]
    return [_hash_embedding(text) for text in texts]
