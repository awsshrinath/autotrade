"""
Retriever module for fetching similar context from the vector store.
Enhanced with comprehensive logging for tracking and analysis.
"""

import logging
import time
from typing import Any, Dict, List, Tuple

import numpy as np

from .embedder import embed_text
from .vector_store import load_from_vector_store

# Import enhanced RAG logging
try:
    from .enhanced_rag_logger import get_rag_logger, create_rag_logger
    ENHANCED_RAG_LOGGING = True
except ImportError:
    print("Warning: Enhanced RAG logging not available")
    ENHANCED_RAG_LOGGING = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def retrieve_similar_context(
    query: str,
    limit: int = 5,
    threshold: float = 0.7,
    bot_name: str = "default",
    session_id: str = None,
    context_type: str = "general"
) -> List[Tuple[Dict[str, Any], float]]:
    """
    Retrieve similar context from the vector store based on the query.
    Enhanced with comprehensive logging and performance tracking.

    Args:
        query: The query text or bot name to find similar context for
        limit: Maximum number of results to return
        threshold: Similarity threshold (0-1)
        bot_name: The name of the bot to retrieve context for
        session_id: Session ID for logging correlation
        context_type: Type of context being retrieved

    Returns:
        List of tuples containing (document, similarity_score)
    """
    start_time = time.time()
    
    # Initialize enhanced logging if available
    rag_logger = None
    trace_id = None
    if ENHANCED_RAG_LOGGING:
        rag_logger = get_rag_logger(session_id, bot_name)
    
    try:
        # Embed the query and log it
        query_embedding = embed_text(query)
        
        if rag_logger:
            trace_id = rag_logger.log_rag_query(
                query_text=query,
                query_embedding=query_embedding,
                context_type=context_type,
                metadata={
                    'bot_name': bot_name,
                    'limit': limit,
                    'threshold': threshold
                }
            )
        
        # Load vector store
        documents, embeddings = load_from_vector_store(bot_name)

        if not documents or len(documents) == 0:
            logger.warning(f"No documents found in vector store for {bot_name}")
            
            if rag_logger and trace_id:
                rag_logger.log_rag_retrieval(
                    trace_id=trace_id,
                    query_id=trace_id,
                    retrieved_docs=[],
                    similarity_scores=[],
                    retrieval_time_ms=(time.time() - start_time) * 1000,
                    total_searched=0,
                    threshold=threshold,
                    strategy="semantic"
                )
            
            return []

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
        result = [item for item in similarities if item[1] >= threshold][:limit]
        
        retrieval_time_ms = (time.time() - start_time) * 1000
        
        # Log retrieval results
        if rag_logger and trace_id:
            retrieved_docs = [item[0] for item in result]
            similarity_scores = [item[1] for item in result]
            
            rag_logger.log_rag_retrieval(
                trace_id=trace_id,
                query_id=trace_id,
                retrieved_docs=retrieved_docs,
                similarity_scores=similarity_scores,
                retrieval_time_ms=retrieval_time_ms,
                total_searched=len(documents),
                threshold=threshold,
                strategy="semantic"
            )
            
            # Build final context for LLM
            if result:
                context_sources = [doc.get('text', '') for doc, _ in result]
                final_context = "\n\n---\n\n".join(context_sources[:3])  # Top 3 results
                
                rag_logger.log_rag_context(
                    trace_id=trace_id,
                    query_id=trace_id,
                    final_context=final_context,
                    context_sources=context_sources,
                    llm_model="gpt-4",  # Default model
                    temperature=0.7,
                    max_tokens=2048
                )

        logger.info(
            f"Retrieved {len(result)} similar documents for query: {query[:50]}... "
            f"in {retrieval_time_ms:.1f}ms"
        )
        return result

    except Exception as e:
        logger.error(f"Error retrieving similar context: {e}")
        
        # Log error
        if rag_logger and trace_id:
            rag_logger.log_rag_retrieval(
                trace_id=trace_id,
                query_id=trace_id,
                retrieved_docs=[],
                similarity_scores=[],
                retrieval_time_ms=(time.time() - start_time) * 1000,
                total_searched=0,
                threshold=threshold,
                strategy="semantic_error"
            )
        
        return []


def retrieve_with_hybrid_strategy(
    query: str,
    limit: int = 5,
    threshold: float = 0.7,
    bot_name: str = "default",
    temporal_weight: float = 0.3,
    session_id: str = None
) -> List[Tuple[Dict[str, Any], float]]:
    """
    Retrieve using hybrid strategy combining semantic similarity and temporal relevance.
    
    Args:
        query: The query text
        limit: Maximum number of results
        threshold: Similarity threshold
        bot_name: Bot name for context
        temporal_weight: Weight for temporal relevance (0-1)
        session_id: Session ID for logging
        
    Returns:
        List of tuples containing (document, hybrid_score)
    """
    start_time = time.time()
    
    # Initialize enhanced logging
    rag_logger = None
    trace_id = None
    if ENHANCED_RAG_LOGGING:
        rag_logger = get_rag_logger(session_id, bot_name)
    
    try:
        # Embed query
        query_embedding = embed_text(query)
        
        if rag_logger:
            trace_id = rag_logger.log_rag_query(
                query_text=query,
                query_embedding=query_embedding,
                context_type="hybrid_retrieval",
                metadata={
                    'bot_name': bot_name,
                    'limit': limit,
                    'threshold': threshold,
                    'temporal_weight': temporal_weight,
                    'strategy': 'hybrid'
                }
            )
        
        # Load documents
        documents, embeddings = load_from_vector_store(bot_name)
        
        if not documents or len(documents) == 0:
            logger.warning(f"No documents found for hybrid retrieval: {bot_name}")
            return []
        
        current_time = time.time()
        hybrid_scores = []
        
        for i, (doc, doc_embedding) in enumerate(zip(documents, embeddings)):
            # Semantic similarity
            semantic_sim = np.dot(query_embedding, doc_embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(doc_embedding)
            )
            
            # Temporal relevance (more recent = higher score)
            doc_timestamp = doc.get('metadata', {}).get('timestamp', 0)
            if isinstance(doc_timestamp, str):
                try:
                    from datetime import datetime
                    doc_time = datetime.fromisoformat(doc_timestamp.replace('Z', '+00:00')).timestamp()
                except:
                    doc_time = 0
            else:
                doc_time = doc_timestamp
            
            time_diff_hours = (current_time - doc_time) / 3600
            temporal_score = max(0, 1 - (time_diff_hours / 168))  # Decay over 1 week
            
            # Hybrid score
            hybrid_score = (1 - temporal_weight) * semantic_sim + temporal_weight * temporal_score
            hybrid_scores.append((doc, hybrid_score))
        
        # Sort and filter
        hybrid_scores.sort(key=lambda x: x[1], reverse=True)
        result = [item for item in hybrid_scores if item[1] >= threshold][:limit]
        
        retrieval_time_ms = (time.time() - start_time) * 1000
        
        # Log hybrid retrieval
        if rag_logger and trace_id:
            retrieved_docs = [item[0] for item in result]
            scores = [item[1] for item in result]
            
            rag_logger.log_rag_retrieval(
                trace_id=trace_id,
                query_id=trace_id,
                retrieved_docs=retrieved_docs,
                similarity_scores=scores,
                retrieval_time_ms=retrieval_time_ms,
                total_searched=len(documents),
                threshold=threshold,
                strategy="hybrid"
            )
        
        logger.info(f"Hybrid retrieval: {len(result)} docs in {retrieval_time_ms:.1f}ms")
        return result
        
    except Exception as e:
        logger.error(f"Error in hybrid retrieval: {e}")
        return []


def retrieve_by_category(
    category: str,
    limit: int = 10,
    bot_name: str = "default",
    session_id: str = None
) -> List[Dict[str, Any]]:
    """
    Retrieve documents by category (trade, log, reflection, error).
    
    Args:
        category: Document category to retrieve
        limit: Maximum number of results
        bot_name: Bot name for context
        session_id: Session ID for logging
        
    Returns:
        List of documents matching the category
    """
    start_time = time.time()
    
    # Initialize logging
    rag_logger = None
    if ENHANCED_RAG_LOGGING:
        rag_logger = get_rag_logger(session_id, bot_name)
    
    try:
        documents, _ = load_from_vector_store(bot_name)
        
        if not documents:
            return []
        
        # Filter by category
        category_docs = [
            doc for doc in documents 
            if doc.get('metadata', {}).get('type') == category
        ]
        
        # Sort by timestamp (most recent first)
        category_docs.sort(
            key=lambda x: x.get('metadata', {}).get('timestamp', ''),
            reverse=True
        )
        
        result = category_docs[:limit]
        
        # Log category retrieval
        if rag_logger:
            trace_id = rag_logger.generate_trace_id()
            rag_logger.log_rag_retrieval(
                trace_id=trace_id,
                query_id=trace_id,
                retrieved_docs=result,
                similarity_scores=[1.0] * len(result),  # Category match = 100%
                retrieval_time_ms=(time.time() - start_time) * 1000,
                total_searched=len(documents),
                threshold=1.0,
                strategy="category_filter"
            )
        
        logger.info(f"Category retrieval ({category}): {len(result)} documents")
        return result
        
    except Exception as e:
        logger.error(f"Error in category retrieval: {e}")
        return []
