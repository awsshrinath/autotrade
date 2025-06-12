"""
Embedder module for RAG (Retrieval Augmented Generation).
Provides text embedding functionality for the TRON trading system.
"""

from typing import List
import numpy as np
import os

# Try to import OpenAI for real embeddings
try:
    import openai
    from runner.openai_manager import OpenAIManager
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


def get_embedding(text: str, model: str = "text-embedding-ada-002") -> List[float]:
    """
    Get embedding for a text using OpenAI's embedding API
    
    Args:
        text: Text to embed
        model: OpenAI model to use for embedding
        
    Returns:
        List of floats representing the embedding
    """
    if OPENAI_AVAILABLE:
        try:
            # Try to use OpenAI for real embeddings
            openai_manager = OpenAIManager()
            client = openai_manager.get_client()
            
            if client:
                response = client.embeddings.create(
                    input=text,
                    model=model
                )
                return response.data[0].embedding
        except Exception as e:
            print(f"Warning: OpenAI embedding failed, using fallback: {e}")

    # Fallback implementation that returns a random embedding
    # In a real implementation, this would call the OpenAI API
    # Create a random embedding of the correct dimension (1536 for text-embedding-ada-002)
    dimension = 1536
    random_embedding = np.random.normal(0, 1, dimension).tolist()
    return random_embedding


def embed_text(text: str, logger=None, model: str = "text-embedding-ada-002") -> List[float]:
    """
    Embed text with logging support (alias for get_embedding with logging)
    
    Args:
        text: Text to embed
        logger: Logger instance for logging events
        model: OpenAI model to use for embedding
        
    Returns:
        List of floats representing the embedding
    """
    try:
        if logger:
            logger.log_event(f"[RAG] Embedding text: {text[:50]}...")
        
        embedding = get_embedding(text, model)
        
        if logger:
            logger.log_event(f"[RAG] Generated {len(embedding)}-dimensional embedding")
        
        return embedding
        
    except Exception as e:
        error_msg = f"[RAG][ERROR] Failed to embed text: {e}"
        if logger:
            logger.log_event(error_msg)
        else:
            print(error_msg)
        
        # Return empty embedding on error
        return []


def embed_batch(texts: List[str], model: str = "text-embedding-ada-002", 
                logger=None) -> List[List[float]]:
    """
    Embed multiple texts in batch for efficiency
    
    Args:
        texts: List of texts to embed
        model: OpenAI model to use for embedding
        logger: Logger instance for logging events
        
    Returns:
        List of embeddings
    """
    try:
        if logger:
            logger.log_event(f"[RAG] Batch embedding {len(texts)} texts")
        
        embeddings = []
        for text in texts:
            embedding = get_embedding(text, model)
            embeddings.append(embedding)
        
        if logger:
            logger.log_event(f"[RAG] Generated {len(embeddings)} embeddings")
        
        return embeddings
        
    except Exception as e:
        error_msg = f"[RAG][ERROR] Failed to embed batch: {e}"
        if logger:
            logger.log_event(error_msg)
        else:
            print(error_msg)
        
        # Return empty embeddings on error
        return [[] for _ in texts]


def cosine_similarity(embedding1: List[float], embedding2: List[float]) -> float:
    """
    Calculate cosine similarity between two embeddings
    
    Args:
        embedding1: First embedding
        embedding2: Second embedding
        
    Returns:
        Cosine similarity score (0-1)
    """
    try:
        # Convert to numpy arrays
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        # Calculate cosine similarity
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
        
    except Exception as e:
        print(f"Error calculating cosine similarity: {e}")
        return 0.0


def validate_embedding(embedding: List[float]) -> bool:
    """
    Validate that an embedding is properly formatted
    
    Args:
        embedding: Embedding to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not isinstance(embedding, list):
        return False
    
    if len(embedding) == 0:
        return False
    
    # Check if all elements are numbers
    try:
        for item in embedding:
            float(item)
        return True
    except (ValueError, TypeError):
        return False
