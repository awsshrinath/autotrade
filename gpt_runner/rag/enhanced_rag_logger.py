"""
Enhanced RAG Logger for TRON Trading System
===========================================

Comprehensive logging system for RAG operations including:
- Context retrieval and embeddings
- Query-response pairs with similarity scores
- Knowledge base updates and versioning
- Performance metrics and timing
- Error handling and debugging information

Writes to:
- Firestore: Real-time RAG operations, queries, and responses
- GCS: Historical RAG context archives, performance analytics
"""

import datetime
import json
import uuid
import time
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict

# Import enhanced logging system
try:
    from runner.enhanced_logging import TradingLogger, LogLevel, LogCategory, LogType
    from runner.enhanced_logging.log_types import LogEntry
    ENHANCED_LOGGING_AVAILABLE = True
except ImportError:
    ENHANCED_LOGGING_AVAILABLE = False

from runner.firestore_client import FirestoreClient


@dataclass
class RAGQueryLog:
    """RAG query log entry"""
    trace_id: str
    session_id: str
    bot_type: str
    query_text: str
    query_embedding: List[float]
    timestamp: datetime.datetime
    context_type: str  # 'trade_context', 'strategy_context', 'error_context'
    query_metadata: Dict[str, Any]


@dataclass
class RAGRetrievalLog:
    """RAG retrieval results log"""
    trace_id: str
    query_id: str
    retrieved_documents: List[Dict[str, Any]]
    similarity_scores: List[float]
    retrieval_time_ms: float
    total_documents_searched: int
    threshold_used: float
    retrieval_strategy: str  # 'semantic', 'hybrid', 'temporal'
    timestamp: datetime.datetime


@dataclass
class RAGContextLog:
    """Final RAG context sent to LLM"""
    trace_id: str
    query_id: str
    final_context: str
    context_sources: List[str]
    context_length: int
    compression_ratio: float
    llm_model: str
    temperature: float
    max_tokens: int
    timestamp: datetime.datetime


@dataclass
class RAGResponseLog:
    """LLM response using RAG context"""
    trace_id: str
    query_id: str
    llm_response: str
    response_length: int
    processing_time_ms: float
    tokens_used: int
    cost_estimate: float
    confidence_score: Optional[float]
    timestamp: datetime.datetime


@dataclass
class RAGEmbeddingLog:
    """Document embedding operations"""
    trace_id: str
    document_id: str
    document_type: str  # 'trade', 'log', 'reflection', 'error'
    source_bot: str
    embedding_model: str
    document_text: str
    document_metadata: Dict[str, Any]
    embedding_time_ms: float
    embedding_dimensions: int
    timestamp: datetime.datetime


class EnhancedRAGLogger:
    """Enhanced logger specifically for RAG operations"""
    
    def __init__(self, session_id: str = None, bot_type: str = "rag"):
        self.session_id = session_id or f"rag_{int(time.time())}"
        self.bot_type = bot_type
        
        # Initialize enhanced logging if available
        if ENHANCED_LOGGING_AVAILABLE:
            self.trading_logger = TradingLogger(
                session_id=self.session_id,
                bot_type=self.bot_type,
                project_id="autotrade-453303"
            )
            self.use_enhanced = True
        else:
            self.use_enhanced = False
            
        # Initialize Firestore client for RAG-specific collections
        try:
            self.firestore_client = FirestoreClient()
        except Exception as e:
            print(f"Warning: Could not initialize Firestore client: {e}")
            self.firestore_client = None
            
        # Performance tracking
        self.query_metrics = {
            'total_queries': 0,
            'total_retrievals': 0,
            'total_embeddings': 0,
            'avg_retrieval_time_ms': 0,
            'avg_embedding_time_ms': 0
        }
        
        print(f"Enhanced RAG Logger initialized - Session: {self.session_id}")
    
    def generate_trace_id(self) -> str:
        """Generate unique trace ID for correlation"""
        return f"rag_{uuid.uuid4().hex[:8]}_{int(time.time())}"
    
    def log_rag_query(self, query_text: str, query_embedding: List[float],
                      context_type: str = "general", metadata: Dict[str, Any] = None) -> str:
        """Log RAG query with trace ID"""
        trace_id = self.generate_trace_id()
        
        query_log = RAGQueryLog(
            trace_id=trace_id,
            session_id=self.session_id,
            bot_type=self.bot_type,
            query_text=query_text,
            query_embedding=query_embedding,
            timestamp=datetime.datetime.now(),
            context_type=context_type,
            query_metadata=metadata or {}
        )
        
        # Log to Firestore
        if self.firestore_client:
            try:
                self.firestore_client.log_document(
                    collection="rag_queries",
                    document_id=trace_id,
                    data=asdict(query_log)
                )
            except Exception as e:
                print(f"Error logging RAG query to Firestore: {e}")
        
        # Log to enhanced system if available
        if self.use_enhanced:
            self.trading_logger.log_event(
                f"RAG Query: {query_text[:100]}...",
                LogLevel.INFO,
                LogCategory.SYSTEM,
                data={
                    'trace_id': trace_id,
                    'context_type': context_type,
                    'query_length': len(query_text),
                    'embedding_dimensions': len(query_embedding),
                    'metadata': metadata
                },
                source="rag_query"
            )
        
        self.query_metrics['total_queries'] += 1
        return trace_id
    
    def log_rag_retrieval(self, trace_id: str, query_id: str, 
                         retrieved_docs: List[Dict[str, Any]], 
                         similarity_scores: List[float], retrieval_time_ms: float,
                         total_searched: int, threshold: float, 
                         strategy: str = "semantic"):
        """Log RAG retrieval results"""
        
        retrieval_log = RAGRetrievalLog(
            trace_id=trace_id,
            query_id=query_id,
            retrieved_documents=retrieved_docs,
            similarity_scores=similarity_scores,
            retrieval_time_ms=retrieval_time_ms,
            total_documents_searched=total_searched,
            threshold_used=threshold,
            retrieval_strategy=strategy,
            timestamp=datetime.datetime.now()
        )
        
        # Log to Firestore
        if self.firestore_client:
            try:
                self.firestore_client.log_document(
                    collection="rag_retrievals",
                    document_id=f"{trace_id}_retrieval",
                    data=asdict(retrieval_log)
                )
            except Exception as e:
                print(f"Error logging RAG retrieval to Firestore: {e}")
        
        # Log to enhanced system
        if self.use_enhanced:
            self.trading_logger.log_event(
                f"RAG Retrieval: {len(retrieved_docs)} docs in {retrieval_time_ms:.1f}ms",
                LogLevel.INFO,
                LogCategory.SYSTEM,
                data={
                    'trace_id': trace_id,
                    'documents_retrieved': len(retrieved_docs),
                    'avg_similarity': sum(similarity_scores) / len(similarity_scores) if similarity_scores else 0,
                    'retrieval_time_ms': retrieval_time_ms,
                    'strategy': strategy,
                    'threshold': threshold
                },
                source="rag_retrieval"
            )
        
        # Update metrics
        self.query_metrics['total_retrievals'] += 1
        self.query_metrics['avg_retrieval_time_ms'] = (
            (self.query_metrics['avg_retrieval_time_ms'] * (self.query_metrics['total_retrievals'] - 1) + 
             retrieval_time_ms) / self.query_metrics['total_retrievals']
        )
    
    def log_rag_context(self, trace_id: str, query_id: str, final_context: str,
                       context_sources: List[str], llm_model: str, 
                       temperature: float = 0.7, max_tokens: int = 2048):
        """Log final context sent to LLM"""
        
        context_log = RAGContextLog(
            trace_id=trace_id,
            query_id=query_id,
            final_context=final_context,
            context_sources=context_sources,
            context_length=len(final_context),
            compression_ratio=len(final_context) / sum(len(src) for src in context_sources) if context_sources else 1.0,
            llm_model=llm_model,
            temperature=temperature,
            max_tokens=max_tokens,
            timestamp=datetime.datetime.now()
        )
        
        # Log to Firestore
        if self.firestore_client:
            try:
                self.firestore_client.log_document(
                    collection="rag_contexts",
                    document_id=f"{trace_id}_context",
                    data=asdict(context_log)
                )
            except Exception as e:
                print(f"Error logging RAG context to Firestore: {e}")
        
        # Log to enhanced system
        if self.use_enhanced:
            self.trading_logger.log_event(
                f"RAG Context: {len(final_context)} chars from {len(context_sources)} sources",
                LogLevel.INFO,
                LogCategory.SYSTEM,
                data={
                    'trace_id': trace_id,
                    'context_length': len(final_context),
                    'sources_count': len(context_sources),
                    'compression_ratio': context_log.compression_ratio,
                    'llm_model': llm_model
                },
                source="rag_context"
            )
    
    def log_rag_response(self, trace_id: str, query_id: str, llm_response: str,
                        processing_time_ms: float, tokens_used: int = 0,
                        cost_estimate: float = 0.0, confidence_score: float = None):
        """Log LLM response using RAG context"""
        
        response_log = RAGResponseLog(
            trace_id=trace_id,
            query_id=query_id,
            llm_response=llm_response,
            response_length=len(llm_response),
            processing_time_ms=processing_time_ms,
            tokens_used=tokens_used,
            cost_estimate=cost_estimate,
            confidence_score=confidence_score,
            timestamp=datetime.datetime.now()
        )
        
        # Log to Firestore
        if self.firestore_client:
            try:
                self.firestore_client.log_document(
                    collection="rag_responses",
                    document_id=f"{trace_id}_response",
                    data=asdict(response_log)
                )
            except Exception as e:
                print(f"Error logging RAG response to Firestore: {e}")
        
        # Log to enhanced system
        if self.use_enhanced:
            self.trading_logger.log_event(
                f"RAG Response: {len(llm_response)} chars in {processing_time_ms:.1f}ms",
                LogLevel.INFO,
                LogCategory.SYSTEM,
                data={
                    'trace_id': trace_id,
                    'response_length': len(llm_response),
                    'processing_time_ms': processing_time_ms,
                    'tokens_used': tokens_used,
                    'cost_estimate': cost_estimate,
                    'confidence_score': confidence_score
                },
                source="rag_response"
            )
    
    def log_rag_embedding(self, document_id: str, document_type: str, 
                         source_bot: str, embedding_model: str,
                         document_text: str, metadata: Dict[str, Any],
                         embedding_time_ms: float, embedding_dimensions: int) -> str:
        """Log document embedding operation"""
        
        trace_id = self.generate_trace_id()
        
        embedding_log = RAGEmbeddingLog(
            trace_id=trace_id,
            document_id=document_id,
            document_type=document_type,
            source_bot=source_bot,
            embedding_model=embedding_model,
            document_text=document_text,
            document_metadata=metadata,
            embedding_time_ms=embedding_time_ms,
            embedding_dimensions=embedding_dimensions,
            timestamp=datetime.datetime.now()
        )
        
        # Log to Firestore
        if self.firestore_client:
            try:
                self.firestore_client.log_document(
                    collection="rag_embeddings",
                    document_id=trace_id,
                    data=asdict(embedding_log)
                )
            except Exception as e:
                print(f"Error logging RAG embedding to Firestore: {e}")
        
        # Log to enhanced system
        if self.use_enhanced:
            self.trading_logger.log_event(
                f"RAG Embedding: {document_type} from {source_bot}",
                LogLevel.INFO,
                LogCategory.SYSTEM,
                data={
                    'trace_id': trace_id,
                    'document_type': document_type,
                    'source_bot': source_bot,
                    'embedding_model': embedding_model,
                    'document_length': len(document_text),
                    'embedding_time_ms': embedding_time_ms,
                    'dimensions': embedding_dimensions
                },
                source="rag_embedding"
            )
        
        # Update metrics
        self.query_metrics['total_embeddings'] += 1
        self.query_metrics['avg_embedding_time_ms'] = (
            (self.query_metrics['avg_embedding_time_ms'] * (self.query_metrics['total_embeddings'] - 1) + 
             embedding_time_ms) / self.query_metrics['total_embeddings']
        )
        
        return trace_id
    
    def get_rag_performance_summary(self) -> Dict[str, Any]:
        """Get RAG performance metrics summary"""
        return {
            'session_id': self.session_id,
            'metrics': self.query_metrics,
            'timestamp': datetime.datetime.now().isoformat()
        }
    
    def archive_rag_session_logs(self) -> bool:
        """Archive current session's RAG logs to GCS"""
        if not self.use_enhanced:
            return False
            
        try:
            # Get session summary
            summary = self.get_rag_performance_summary()
            
            # Archive via enhanced logger
            self.trading_logger.log_event(
                "RAG Session Complete - Archiving Logs",
                LogLevel.INFO,
                LogCategory.SYSTEM,
                data=summary,
                source="rag_session_archive"
            )
            
            return True
        except Exception as e:
            print(f"Error archiving RAG session logs: {e}")
            return False


# Global RAG logger instance
_rag_logger = None

def get_rag_logger(session_id: str = None, bot_type: str = "rag") -> EnhancedRAGLogger:
    """Get or create global RAG logger instance"""
    global _rag_logger
    if _rag_logger is None:
        _rag_logger = EnhancedRAGLogger(session_id, bot_type)
    return _rag_logger

def create_rag_logger(session_id: str = None, bot_type: str = "rag") -> EnhancedRAGLogger:
    """Create new RAG logger instance"""
    return EnhancedRAGLogger(session_id, bot_type) 