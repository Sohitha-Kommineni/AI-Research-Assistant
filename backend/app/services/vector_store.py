from typing import List, Tuple

import numpy as np


def cosine_similarity(query: List[float], vectors: List[List[float]]) -> List[float]:
    if not vectors:
        return []
    query_vec = np.array(query, dtype=float)
    query_vec = query_vec / (np.linalg.norm(query_vec) + 1e-8)
    matrix = np.array(vectors, dtype=float)
    matrix = matrix / (np.linalg.norm(matrix, axis=1, keepdims=True) + 1e-8)
    return (matrix @ query_vec).tolist()


def top_k(similarities: List[float], k: int) -> List[int]:
    if not similarities:
        return []
    indices = np.argsort(similarities)[::-1][:k]
    return indices.astype(int).tolist()
