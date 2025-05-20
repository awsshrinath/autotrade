import faiss
import numpy as np
import os
import pickle

VECTOR_DIM = 384

index = faiss.IndexFlatIP(VECTOR_DIM)
data = []

def load_index(path="gpt_runner/rag/faiss.index", meta_path="gpt_runner/rag/meta.pkl"):
    global index, data
    if os.path.exists(path):
        index = faiss.read_index(path)
        with open(meta_path, "rb") as f:
            data = pickle.load(f)

def save_index(path="gpt_runner/rag/faiss.index", meta_path="gpt_runner/rag/meta.pkl"):
    faiss.write_index(index, path)
    with open(meta_path, "wb") as f:
        pickle.dump(data, f)

def add_document(embedding, metadata):
    global data
    data.append(metadata)
    index.add(np.array([embedding]))

def search_similar(embedding, top_k=5):
    scores, ids = index.search(np.array([embedding]), top_k)
    return [(data[i], scores[0][idx]) for idx, i in enumerate(ids[0])]