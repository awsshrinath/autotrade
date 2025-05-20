import faiss
import numpy as np
import json
import os

def save_to_vector_store(bot_name, vector_data, logger):
    try:
        vectors = np.array([v["embedding"] for v in vector_data]).astype(np.float32)
        texts = [v["text"] for v in vector_data]

        index = faiss.IndexFlatL2(len(vectors[0]))
        index.add(vectors)

        faiss.write_index(index, f"{bot_name}_index.faiss")
        with open(f"{bot_name}_metadata.json", "w") as f:
            json.dump([{"text": t} for t in texts], f)

        logger.log_event(f"[VECTOR_STORE] Saved {len(texts)} vectors for {bot_name}")
    except Exception as e:
        logger.log_event(f"[VECTOR_STORE][ERROR] Save failed: {e}")

def load_vector_index(bot_name):
    try:
        index_path = f"{bot_name}_index.faiss"
        meta_path = f"{bot_name}_metadata.json"

        if not os.path.exists(index_path) or not os.path.exists(meta_path):
            return None, []

        index = faiss.read_index(index_path)
        with open(meta_path, "r") as f:
            metadata = json.load(f)

        return index, metadata
    except Exception as e:
        return None, [{"text": f"[LOAD ERROR] {e}"}]
