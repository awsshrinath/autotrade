from .embedder import embed_text
from .vector_store import save_to_vector_store


def add_to_memory(text: str, metadata: dict, bot_name="default", logger=None):
    """
    Add a document to the vector store memory.

    Args:
        text (str): The text to add to memory
        metadata (dict): Additional metadata for the document
        bot_name (str): The name of the bot to associate with this memory
        logger (Logger): Logger instance for logging events
    """
    try:
        # Create a combined text with metadata
        combined_text = f"{text} {' '.join([f'{k}:{v}' for k, v in metadata.items()])}"

        # Embed the text
        vec = embed_text(text, logger)

        # Create vector data
        vector_data = [{"text": combined_text, "embedding": vec}]

        # Save to vector store
        if logger:
            save_to_vector_store(bot_name, vector_data, logger)
        else:
            # Create a simple logger for this operation
            import datetime

            from runner.logger import Logger

            temp_logger = Logger(
                today_date=datetime.datetime.now().strftime("%Y-%m-%d")
            )
            save_to_vector_store(bot_name, vector_data, temp_logger)
    except Exception as e:
        if logger:
            logger.log_event(f"[RAG][ERROR] Failed to add to memory: {e}")
        else:
            print(f"[RAG][ERROR] Failed to add to memory: {e}")
