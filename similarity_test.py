#!usr/bin/env python3

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

model = SentenceTransformer("all-MiniLM-L6-v2")

def calculate_similarity(text1: str, text2: str) -> float:
    embeddings = model.encode([text1, text2])

    similarity = cosine_similarity([embeddings[0]], [embeddings[1]]) [0][0]
    return similarity

if __name__ == "__main__":

    chosen = "I appreciate your question. Let me explain..."
    rejected = "I appreciate your question. Let me explain..."

    score = calculate_similarity(chosen, rejected)
    print(f"Similarity: {score:.3f}")
