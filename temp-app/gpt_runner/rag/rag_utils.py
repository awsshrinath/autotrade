from .embedder import embed_text
from .vector_store import add_document, save_index

def add_to_memory(text: str, metadata: dict):
    vec = embed_text(text)
    add_document(vec, metadata)
    save_index()