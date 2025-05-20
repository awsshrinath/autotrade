from .embedder import embed_text
from .vector_store import search_similar

def retrieve_similar_context(query: str, top_k=5):
    query_vec = embed_text(query)
    return search_similar(query_vec, top_k)