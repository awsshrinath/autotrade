"""
RAG Worker module for embedding logs and other data for retrieval.
"""

import os
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from runner.logger import Logger
from runner.firestore_client import FirestoreClient, fetch_recent_trades
from .embedder import embed_text
from .vector_store import save_to_vector_store

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def embed_logs_for_today(bot_names: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Embed today's logs for the specified bots and save to vector store.

    Args:
        bot_names: List of bot names to embed logs for. If None, embeds for all bots.

    Returns:
        Dictionary with embedding statistics
    """
    today = datetime.now().strftime("%Y-%m-%d")
    logger_obj = Logger(today)

    if bot_names is None:
        bot_names = ["stock-trader", "options-trader", "futures-trader"]

    stats = {
        "date": today,
        "bots_processed": 0,
        "logs_embedded": 0,
        "trades_embedded": 0,
    }

    for bot_name in bot_names:
        try:
            # Embed trades
            trades = fetch_recent_trades(bot_name, limit=20)
            if trades:
                embed_trades(bot_name, trades)
                stats["trades_embedded"] += len(trades)

            # Embed logs from log files
            log_path = f"logs/{bot_name}_{today}.log"
            if os.path.exists(log_path):
                embed_log_file(bot_name, log_path)
                stats["logs_embedded"] += 1

            stats["bots_processed"] += 1
            logger_obj.log_event(f"[RAG] Embedded data for {bot_name}")

        except Exception as e:
            logger_obj.log_event(
                f"[RAG][ERROR] Failed to embed data for {bot_name}: {e}"
            )

    logger_obj.log_event(f"[RAG] Embedding complete: {stats}")
    return stats


def embed_trades(bot_name: str, trades: List[Dict[str, Any]]) -> None:
    """
    Embed trade data and save to vector store.

    Args:
        bot_name: Name of the bot
        trades: List of trade data to embed
    """
    vector_data = []

    for trade in trades:
        # Create a text representation of the trade
        trade_text = f"""
Bot: {bot_name}
Symbol: {trade.get('symbol', 'unknown')}
Strategy: {trade.get('strategy', 'unknown')}
Entry Time: {trade.get('entry_time', '')}
Entry Price: {trade.get('entry_price', 0)}
Exit Time: {trade.get('exit_time', '')}
Exit Price: {trade.get('exit_price', 0)}
PnL: {trade.get('pnl', 0)}
Status: {trade.get('status', 'unknown')}
Notes: {trade.get('notes', '')}
"""

        # Embed the text
        embedding = embed_text(trade_text)

        # Add to vector data
        vector_data.append(
            {
                "text": trade_text,
                "embedding": embedding,
                "metadata": {
                    "type": "trade",
                    "bot": bot_name,
                    "symbol": trade.get("symbol", "unknown"),
                    "timestamp": trade.get("entry_time", datetime.now().isoformat()),
                },
            }
        )

    # Save to vector store
    if vector_data:
        save_to_vector_store(bot_name, vector_data)


def embed_log_file(bot_name: str, log_path: str, chunk_size: int = 1000) -> None:
    """
    Embed log file content and save to vector store.

    Args:
        bot_name: Name of the bot
        log_path: Path to the log file
        chunk_size: Size of chunks to split the log file into
    """
    try:
        with open(log_path, "r") as f:
            log_content = f.read()

        # Split into chunks
        chunks = [
            log_content[i : i + chunk_size]
            for i in range(0, len(log_content), chunk_size)
        ]

        vector_data = []
        for i, chunk in enumerate(chunks):
            # Embed the chunk
            embedding = embed_text(chunk)

            # Add to vector data
            vector_data.append(
                {
                    "text": chunk,
                    "embedding": embedding,
                    "metadata": {
                        "type": "log",
                        "bot": bot_name,
                        "chunk": i,
                        "timestamp": datetime.now().isoformat(),
                    },
                }
            )

        # Save to vector store
        if vector_data:
            save_to_vector_store(bot_name, vector_data)

    except Exception as e:
        logger.error(f"Error embedding log file {log_path}: {e}")


def embed_reflection(bot_name: str, date_str: str) -> None:
    """
    Embed reflection data from Firestore and save to vector store.

    Args:
        bot_name: Name of the bot
        date_str: Date string for the reflection
    """
    try:
        firestore_client = FirestoreClient()
        reflection = firestore_client.fetch_reflection(bot_name, date_str)

        if not reflection:
            logger.warning(f"No reflection found for {bot_name} on {date_str}")
            return

        # Create a text representation of the reflection
        reflection_text = f"""
Bot: {bot_name}
Date: {date_str}
Reflection: {reflection}
"""

        # Embed the text
        embedding = embed_text(reflection_text)

        # Add to vector data
        vector_data = [
            {
                "text": reflection_text,
                "embedding": embedding,
                "metadata": {
                    "type": "reflection",
                    "bot": bot_name,
                    "date": date_str,
                    "timestamp": datetime.now().isoformat(),
                },
            }
        ]

        # Save to vector store
        save_to_vector_store(bot_name, vector_data)

    except Exception as e:
        logger.error(f"Error embedding reflection for {bot_name} on {date_str}: {e}")


if __name__ == "__main__":
    embed_logs_for_today()
