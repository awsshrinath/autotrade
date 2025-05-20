import faiss
import numpy as np
from gpt_runner.rag.vector_store import load_vector_index

def cosine_similarity(query, vectors):
    query_norm = np.linalg.norm(query)
    vector_norms = np.linalg.norm(vectors, axis=1)
    sim = np.dot(vectors, query) / (vector_norms * query_norm + 1e-10)
    return sim

def retrieve_similar_context(bot_name, query_embedding):
    try:
        index, metadata = load_vector_index(bot_name)
        if index is None:
            return "[RETRIEVER] No index found."

        # Convert query_embedding to numpy
        query_vec = np.array(query_embedding).astype(np.float32).reshape(1, -1)

        # Search FAISS index
        D, I = index.search(query_vec, 1)
        top_idx = I[0][0]
        if top_idx < len(metadata):
            return metadata[top_idx]["text"]
        else:
            return "[RETRIEVER] No matching context found."
    except Exception as e:
        return f"[RETRIEVER][ERROR] {e}"
