"""
Retriever module for fetching similar context from the vector store.
"""

import logging
from typing import Any, Dict, List, Tuple

import numpy as np

from .embedder import embed_text
from .vector_store import load_from_vector_store

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def retrieve_similar_context(
    query: str,
    limit: int = 5,
    threshold: float = 0.7,
    bot_name: str = "default",
) -> List[Tuple[Dict[str, Any], float]]:
    """
    Retrieve similar context from the vector store based on the query.

    Args:
        query: The query text or bot name to find similar context for
        limit: Maximum number of results to return
        threshold: Similarity threshold (0-1)
        bot_name: The name of the bot to retrieve context for

    Returns:
        List of tuples containing (document, similarity_score)
    """
    try:
        # Load vector store
        documents, embeddings = load_from_vector_store(bot_name)

        if not documents or len(documents) == 0:
            logger.warning(
                f"No documents found in vector store for {bot_name}"
            )
            return []

        # Embed the query
        query_embedding = embed_text(query)

        # Calculate similarities
        similarities = []
        for i, doc_embedding in enumerate(embeddings):
            # Calculate cosine similarity
            similarity = np.dot(query_embedding, doc_embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(doc_embedding)
            )
            similarities.append((documents[i], similarity))

        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)

        # Filter by threshold and limit
        result = [item for item in similarities if item[1] >= threshold][
            :limit
        ]

        logger.info(
            f"Retrieved {len(result)} similar documents for query: {query[:50]}..."
        )
        return result

    except Exception as e:
        logger.error(f"Error retrieving similar context: {e}")
        return []
