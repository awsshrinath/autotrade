from gpt_runner.firestore_client import fetch_recent_market_snapshots
from gpt_runner.rag.rag_utils import add_to_memory

def index_recent_market_data():
    snapshots = fetch_recent_market_snapshots()
    for snapshot in snapshots:
        text = snapshot['text']
        metadata = snapshot.get('metadata', {})
        add_to_memory(text, metadata)