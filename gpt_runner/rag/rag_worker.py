
import os
from datetime import datetime
from gpt_runner.rag.vector_store import VectorStore
from gpt_runner.rag.embedder import get_embedding

VECTOR_DB_PATH = "vector_db/trade_logs.index"

def embed_logs_for_today(log_dir="logs/", bot_name="stock-trader"):
    store = VectorStore(VECTOR_DB_PATH)
    today_str = datetime.now().strftime("%Y-%m-%d")

    embedded_count = 0
    for file_name in os.listdir(log_dir):
        if not file_name.endswith(".jsonl"):
            continue
        file_path = os.path.join(log_dir, file_name)
        with open(file_path, "r") as f:
            for line in f:
                try:
                    if today_str not in line:
                        continue
                    entry = line.strip()
                    vector = get_embedding(entry)
                    store.add(entry, vector)
                    embedded_count += 1
                except Exception as e:
                    print(f"[WARN] Failed to embed log: {e}")
    store.save()
    print(f"[RAG] Embedded {embedded_count} logs for {today_str}")

def get_context_from_logs(query_text: str, top_k=5):
    store = VectorStore(VECTOR_DB_PATH)
    query_vector = get_embedding(query_text)
    results = store.search(query_vector, top_k=top_k)
    return [item["text"] for item in results]
