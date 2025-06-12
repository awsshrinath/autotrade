from gpt_runner.rag.faiss_firestore_adapter import add_firestore_record
from gpt_runner.rag.rag_utils import add_to_memory
from gpt_runner.rag.retriever import retrieve_similar_context


def test_add_and_retrieve():
    print("✅ Adding sample memory to RAG index...")
    samples = [
        {
            "text": "SGX Nifty flat, Dow down 100, VIX rising. Strategy used: ORB. SL hit.",
            "metadata": {
                "date": "2025-05-01",
                "summary": "ORB failed in uncertain market",
            },
        },
        {
            "text": "SGX Nifty up, Dow up, VIX stable. Strategy used: VWAP. Target hit.",
            "metadata": {
                "date": "2025-05-02",
                "summary": "VWAP success in strong uptrend",
            },
        },
        {
            "text": "SGX down, Dow flat, VIX high. Strategy: ORB. Result: Partial exit hit.",
            "metadata": {
                "date": "2025-05-03",
                "summary": "ORB partial win on volatile day",
            },
        },
    ]

    for sample in samples:
        add_to_memory(sample["text"], sample["metadata"], bot_name="test-bot")
        try:
            add_firestore_record(sample["text"], sample["metadata"])
        except Exception as e:
            print("Firestore add skipped (offline?):", e)

    print("✅ Retrieving similar context for a new scenario...")
    test_query = "SGX flat, Dow red, VIX spiking. What worked before?"
    results = retrieve_similar_context(test_query, limit=2)

    for i, (meta, score) in enumerate(results):
        print(
            f"{i + 1}. Score: {score:.4f} | Date: {meta.get('date')} | Summary: {meta.get('summary')}"
        )

    print("✅ Test complete.")


if __name__ == "__main__":
    test_add_and_retrieve()
