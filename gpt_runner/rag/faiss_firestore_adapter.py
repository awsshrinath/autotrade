import datetime

from google.cloud import firestore

from runner.logger import Logger

from .embedder import embed_text
from .vector_store import save_to_vector_store

# Create a logger for this module
logger = Logger(today_date=datetime.datetime.now().strftime("%Y-%m-%d"))

try:
    db = firestore.Client()
except Exception as e:
    print(f"[FIRESTORE] Failed to initialize client: {e}")
    db = None


def sync_firestore_to_faiss(collection_name="rag_memory", bot_name="default"):
    """
    Sync documents from Firestore to the FAISS vector store.

    Args:
        collection_name (str): The name of the Firestore collection
        bot_name (str): The name of the bot to associate with the vector store
    """
    if not db:
        logger.log_event("[SYNC] Firestore client not available")
        return

    try:
        docs = db.collection(collection_name).stream()
        vector_data = []

        for doc in docs:
            data = doc.to_dict()
            if "text" in data:
                # Embed the text if it doesn't have an embedding
                if "embedding" not in data:
                    embedding = embed_text(data["text"], logger)
                else:
                    embedding = data["embedding"]

                # Add to vector data
                vector_data.append(
                    {"text": data["text"], "embedding": embedding}
                )

        # Save to vector store
        if vector_data:
            save_to_vector_store(bot_name, vector_data, logger)
            logger.log_event(
                f"[SYNC] Synced {len(vector_data)} documents from Firestore to FAISS"
            )
    except Exception as e:
        logger.log_event(f"[SYNC][ERROR] Failed to sync from Firestore: {e}")


def add_firestore_record(text, metadata, collection_name="rag_memory"):
    vec = embed_text(text)
    doc = metadata.copy()
    doc["text"] = text
    doc["embedding"] = vec.tolist()
    db.collection(collection_name).add(doc)


def restore_memory_from_firestore(bot_name, logger):
    try:
        logger.log_event(
            f"[RESTORE] Syncing vector memory from Firestore for {bot_name}"
        )
        # Simulated restore
    except Exception as e:
        logger.log_event(f"[RESTORE][ERROR] Restore failed: {e}")
