from runner.openai_manager import OpenAIManager
from gpt_runner.rag.vector_store import save_to_vector_store
from datetime import datetime


def embed_logs_for_today(bot_name, logger):
    try:
        logger.log_event(f"[EMBED] Embedding logs for bot: {bot_name}")

        # Simulated logs for today (replace this with actual log loader)
        logs = [
            f"{bot_name} entered a bullish trade at 9:20",
            f"{bot_name} stopped out at 10:05",
            f"{bot_name} hit target at 12:30",
        ]

        openai = OpenAIManager(logger)
        embedded_logs = []

        for log_text in logs:
            embedding = openai.get_embedding(log_text)
            embedded_logs.append({
                "text": log_text,
                "embedding": embedding
            })

        # Save to vector store
        save_to_vector_store(bot_name, embedded_logs, logger)
        logger.log_event(f"[EMBED] {len(embedded_logs)} logs embedded and saved.")

    except Exception as e:
        logger.log_event(f"[EMBED][ERROR] Failed to embed logs: {e}")
