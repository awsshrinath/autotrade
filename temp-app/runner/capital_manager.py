
from google.cloud import firestore

db = firestore.Client()

def allocate_capital(total_capital):
    allocation = {
        "safe_strategies": round(total_capital * 0.6),  # VWAP + ORB
        "scalp": round(total_capital * 0.1),
        "reserve": round(total_capital * 0.3)
    }
    allocation["slot_size"] = {
        "stock": allocation["safe_strategies"] // 2,
        "futures": allocation["safe_strategies"] // 2,
        "options": allocation["scalp"]
    }

    db.collection("gpt_runner").document("capital_allocations").set(allocation)
    print("[CAPITAL] Allocation pushed to Firestore:", allocation)
    return allocation
