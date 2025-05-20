from google.cloud import firestore
from .vector_store import add_document, save_index
from .embedder import embed_text

db = firestore.Client()

def sync_firestore_to_faiss(collection_name='rag_memory'):
    docs = db.collection(collection_name).stream()
    for doc in docs:
        data = doc.to_dict()
        if 'text' in data:
            vec = embed_text(data['text'])
            metadata = {k: v for k, v in data.items() if k != 'embedding'}
            add_document(vec, metadata)
    save_index()

def add_firestore_record(text, metadata, collection_name='rag_memory'):
    vec = embed_text(text)
    doc = metadata.copy()
    doc['text'] = text
    doc['embedding'] = vec.tolist()
    db.collection(collection_name).add(doc)

def restore_memory_from_firestore(bot_name, logger):
    try:
        logger.log_event(f"[RESTORE] Syncing vector memory from Firestore for {bot_name}")
        # Simulated restore
    except Exception as e:
        logger.log_event(f"[RESTORE][ERROR] Restore failed: {e}")