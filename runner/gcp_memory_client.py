# runner / gcp_memory_client.py
# GCP Memory Client for Cloud Storage and Firestore operations
# Provides unified interface for cognitive system persistence across daily cluster recreations
# 🚀 ENHANCED: Now includes FAISS integration for dynamic embedding storage and retrieval

import json
import pickle
import gzip
import datetime
import numpy as np
import faiss
import os
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from google.cloud import storage
from google.cloud import firestore
import logging

# Try importing OpenAI for embeddings, fallback to sentence-transformers
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False


@dataclass
class MemorySnapshot:
    """Snapshot of cognitive memory state for backup / restore"""
    timestamp: datetime.datetime
    working_memory: List[Dict]
    short_term_memory: List[Dict]
    cognitive_state: Dict
    recent_thoughts: List[Dict]
    performance_metrics: Dict


@dataclass
class EmbeddingDocument:
    """Document structure for embedding storage"""
    doc_id: str
    content: str
    embedding: List[float]
    metadata: Dict[str, Any]
    timestamp: datetime.datetime
    document_type: str  # 'trade_log', 'market_sentiment', 'decision', etc.


class GCPMemoryClient:
    """
    🚀 ENHANCED: Unified client for cognitive memory persistence using GCP Firestore, Cloud Storage, and FAISS.
    Now includes dynamic embedding storage and retrieval for GPT-based context enrichment.
    Designed for bulletproof persistence across daily Kubernetes cluster recreations.
    """
    
    def __init__(self, project_id: str = None, logger: logging.Logger = None, 
                 openai_api_key: str = None, embedding_dimension: int = 1536):
        self.project_id = project_id
        self.logger = logger or logging.getLogger(__name__)
        self.embedding_dimension = embedding_dimension
        
        # Initialize clients
        self._init_clients()
        self._init_embedding_system(openai_api_key)
        
        # Bucket names for different memory types
        self.memory_bucket = "tron-cognitive-memory"
        self.thought_bucket = "tron-thought-archives"
        self.reports_bucket = "tron-analysis-reports"
        self.backup_bucket = "tron-memory-backups"
        self.embeddings_bucket = "tron-embeddings-store"  # 🆕 New bucket for FAISS indices
        
        # Firestore collection names
        self.collections = {
            'working_memory': 'working_memory',
            'short_term_memory': 'short_term_memory', 
            'long_term_memory': 'long_term_memory',
            'episodic_memory': 'episodic_memory',
            'thought_journal': 'thought_journal',
            'state_transitions': 'state_transitions',
            'decision_analysis': 'decision_analysis',
            'performance_attribution': 'performance_attribution',
            'bias_tracking': 'bias_tracking',
            'learning_metrics': 'learning_metrics',
            # 🆕 New collections for embeddings
            'embedding_metadata': 'embedding_metadata',
            'trade_embeddings': 'trade_embeddings',
            'sentiment_embeddings': 'sentiment_embeddings',
            'context_embeddings': 'context_embeddings'
        }
        
        # 🆕 FAISS indices for different document types
        self.faiss_indices = {}
        self.embedding_metadata = {}  # Maps doc_id to metadata
        
        # Initialize storage buckets and FAISS system
        self._ensure_buckets_exist()
        self._init_faiss_indices()
    
    def _init_clients(self):
        """Initialize GCP clients with error handling"""
        try:
            self.firestore_client = firestore.Client(project=self.project_id)
            self.storage_client = storage.Client(project=self.project_id)
            self.logger.info("GCP clients initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize GCP clients: {e}")
            raise
    
    def _init_embedding_system(self, openai_api_key: str = None):
        """🆕 Initialize embedding system (OpenAI or SentenceTransformers)"""
        try:
            if OPENAI_AVAILABLE and openai_api_key:
                openai.api_key = openai_api_key
                self.embedding_model = "openai"
                self.logger.info("Initialized OpenAI embeddings")
            elif SENTENCE_TRANSFORMERS_AVAILABLE:
                self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
                self.embedding_model = "sentence_transformers"
                self.embedding_dimension = 384  # all-MiniLM-L6-v2 dimension
                self.logger.info("Initialized SentenceTransformers embeddings")
            else:
                self.embedding_model = None
                self.logger.warning("No embedding model available. Install openai or sentence-transformers")
        except Exception as e:
            self.logger.error(f"Failed to initialize embedding system: {e}")
            self.embedding_model = None
    
    def _init_faiss_indices(self):
        """🆕 Initialize FAISS indices for different document types"""
        try:
            document_types = ['trade_log', 'market_sentiment', 'decision', 'context', 'general']
            
            for doc_type in document_types:
                # Create FAISS index with inner product similarity
                index = faiss.IndexFlatIP(self.embedding_dimension)
                self.faiss_indices[doc_type] = index
                self.embedding_metadata[doc_type] = {}
                
                # Try to load existing index from GCS
                self._load_faiss_index(doc_type)
            
            self.logger.info(f"Initialized FAISS indices for {len(document_types)} document types")
        except Exception as e:
            self.logger.error(f"Failed to initialize FAISS indices: {e}")
    
    def _generate_embedding(self, text: str) -> Optional[List[float]]:
        """🆕 Generate embedding for text using available model"""
        try:
            if self.embedding_model == "openai":
                response = openai.Embedding.create(
                    input=text,
                    model="text-embedding-ada-002"
                )
                return response['data'][0]['embedding']
            elif self.embedding_model == "sentence_transformers":
                embedding = self.sentence_model.encode(text)
                return embedding.tolist()
            else:
                self.logger.warning("No embedding model available")
                return None
        except Exception as e:
            self.logger.error(f"Failed to generate embedding: {e}")
            return None
    
    def _ensure_buckets_exist(self):
        """Ensure all required Cloud Storage buckets exist"""
        buckets = [
            self.memory_bucket,
            self.thought_bucket, 
            self.reports_bucket,
            self.backup_bucket,
            self.embeddings_bucket  # 🆕 New embeddings bucket
        ]
        
        for bucket_name in buckets:
            try:
                bucket = self.storage_client.bucket(bucket_name)
                if not bucket.exists():
                    # Create bucket in asia-south1 region with proper labels
                    bucket = self.storage_client.create_bucket(
                        bucket_name,
                        location='asia-south1',  # Force asia-south1 region
                        labels={
                            'environment': 'production',
                            'system': 'tron-trading',
                            'purpose': 'memory-management',
                            'region': 'asia-south1'
                        }
                    )
                    self.logger.info(f"Created bucket: {bucket_name} in asia-south1")
                    
                # Ensure bucket is in correct region
                bucket.reload()
                if bucket.location != 'asia-south1':
                    self.logger.warning(f"Bucket {bucket_name} is in {bucket.location}, not asia-south1")
                    
            except Exception as e:
                self.logger.error(f"Failed to ensure bucket {bucket_name}: {e}")
    
    # === ENHANCED FIRESTORE OPERATIONS ===
    
    def store_memory_item(self, collection_name: str, doc_id: str, data: Dict[str, Any], 
                         ttl_hours: Optional[int] = None) -> bool:
        """Store memory item in Firestore with optional TTL"""
        try:
            doc_ref = self.firestore_client.collection(collection_name).document(doc_id)
            
            # Add timestamp and TTL if specified
            data_with_meta = {
                **data,
                'created_at': firestore.SERVER_TIMESTAMP,
                'last_accessed': firestore.SERVER_TIMESTAMP
            }
            
            if ttl_hours:
                expiry_time = datetime.datetime.utcnow() + datetime.timedelta(hours=ttl_hours)
                data_with_meta['expires_at'] = expiry_time
            
            doc_ref.set(data_with_meta)
            return True
        except Exception as e:
            self.logger.error(f"Failed to store memory item in {collection_name}: {e}")
            return False
    
    def get_memory_item(self, collection_name: str, doc_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve memory item from Firestore"""
        try:
            doc_ref = self.firestore_client.collection(collection_name).document(doc_id)
            doc = doc_ref.get()
            
            if doc.exists:
                data = doc.to_dict()
                # Update last accessed time
                doc_ref.update({'last_accessed': firestore.SERVER_TIMESTAMP})
                return data
            return None
        except Exception as e:
            self.logger.error(f"Failed to get memory item from {collection_name}: {e}")
            return None
    
    def query_memory_collection(self, collection_name: str, filters: List[tuple] = None,
                               order_by: str = None, limit: int = None) -> List[Dict[str, Any]]:
        """Query memory collection with filters"""
        try:
            collection_ref = self.firestore_client.collection(collection_name)
            query = collection_ref
            
            # Apply filters
            if filters:
                for field, operator, value in filters:
                    query = query.where(field, operator, value)
            
            # Apply ordering
            if order_by:
                query = query.order_by(order_by, direction=firestore.Query.DESCENDING)
            
            # Apply limit
            if limit:
                query = query.limit(limit)
            
            docs = query.stream()
            return [{'id': doc.id, **doc.to_dict()} for doc in docs]
        except Exception as e:
            self.logger.error(f"Failed to query collection {collection_name}: {e}")
            return []
    
    def update_memory_item(self, collection_name: str, doc_id: str, 
                          updates: Dict[str, Any]) -> bool:
        """Update memory item in Firestore"""
        try:
            doc_ref = self.firestore_client.collection(collection_name).document(doc_id)
            updates_with_meta = {
                **updates,
                'last_accessed': firestore.SERVER_TIMESTAMP
            }
            doc_ref.update(updates_with_meta)
            return True
        except Exception as e:
            self.logger.error(f"Failed to update memory item in {collection_name}: {e}")
            return False
    
    def delete_memory_item(self, collection_name: str, doc_id: str) -> bool:
        """Delete memory item from Firestore"""
        try:
            doc_ref = self.firestore_client.collection(collection_name).document(doc_id)
            doc_ref.delete()
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete memory item from {collection_name}: {e}")
            return False
    
    # === 🆕 ENHANCED EMBEDDING OPERATIONS ===
    
    def store_embedding_document(self, content: str, doc_type: str, metadata: Dict[str, Any] = None) -> Optional[str]:
        """
        🆕 Store document with embedding in FAISS and metadata in Firestore
        
        Args:
            content: Text content to embed and store
            doc_type: Type of document ('trade_log', 'market_sentiment', 'decision', etc.)
            metadata: Additional metadata to store with the document
            
        Returns:
            Document ID if successful, None otherwise
        """
        try:
            # Generate embedding
            embedding = self._generate_embedding(content)
            if not embedding:
                self.logger.error("Failed to generate embedding")
                return None
            
            # Generate unique document ID
            doc_id = f"{doc_type}_{datetime.datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}"
            
            # Create embedding document
            embed_doc = EmbeddingDocument(
                doc_id=doc_id,
                content=content,
                embedding=embedding,
                metadata=metadata or {},
                timestamp=datetime.datetime.utcnow(),
                document_type=doc_type
            )
            
            # Add to FAISS index
            if doc_type not in self.faiss_indices:
                self.faiss_indices[doc_type] = faiss.IndexFlatIP(self.embedding_dimension)
                self.embedding_metadata[doc_type] = {}
            
            # Add embedding to FAISS
            embedding_array = np.array([embedding], dtype=np.float32)
            # Normalize for cosine similarity
            faiss.normalize_L2(embedding_array)
            self.faiss_indices[doc_type].add(embedding_array)
            
            # Store metadata
            self.embedding_metadata[doc_type][doc_id] = {
                'content': content,
                'metadata': metadata or {},
                'timestamp': embed_doc.timestamp,
                'index_position': self.faiss_indices[doc_type].ntotal - 1
            }
            
            # Store in Firestore
            firestore_data = {
                'doc_id': doc_id,
                'content': content,
                'document_type': doc_type,
                'metadata': metadata or {},
                'timestamp': embed_doc.timestamp,
                'embedding_dimension': len(embedding)
            }
            
            collection_name = f"{doc_type}_embeddings"
            self.store_memory_item(collection_name, doc_id, firestore_data)
            
            # Periodically save FAISS index to GCS
            if self.faiss_indices[doc_type].ntotal % 100 == 0:  # Save every 100 documents
                self._save_faiss_index(doc_type)
            
            self.logger.info(f"Stored embedding document: {doc_id} of type {doc_type}")
            return doc_id
            
        except Exception as e:
            self.logger.error(f"Failed to store embedding document: {e}")
            return None
    
    def search_similar_documents(self, query_text: str, doc_type: str = None, 
                               top_k: int = 5, similarity_threshold: float = 0.7) -> List[Dict[str, Any]]:
        """
        🆕 Search for similar documents using FAISS semantic similarity
        
        Args:
            query_text: Text to search for
            doc_type: Type of documents to search in (None for all types)
            top_k: Number of top results to return
            similarity_threshold: Minimum similarity score (0-1)
            
        Returns:
            List of similar documents with scores
        """
        try:
            # Generate query embedding
            query_embedding = self._generate_embedding(query_text)
            if not query_embedding:
                self.logger.error("Failed to generate query embedding")
                return []
            
            query_array = np.array([query_embedding], dtype=np.float32)
            faiss.normalize_L2(query_array)
            
            results = []
            search_types = [doc_type] if doc_type else list(self.faiss_indices.keys())
            
            for search_type in search_types:
                if search_type not in self.faiss_indices or self.faiss_indices[search_type].ntotal == 0:
                    continue
                
                # Search in FAISS index
                scores, indices = self.faiss_indices[search_type].search(query_array, top_k)
                
                for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
                    if score < similarity_threshold:
                        continue
                    
                    # Find document by index position
                    doc_data = None
                    for doc_id, meta in self.embedding_metadata[search_type].items():
                        if meta['index_position'] == idx:
                            doc_data = {
                                'doc_id': doc_id,
                                'content': meta['content'],
                                'metadata': meta['metadata'],
                                'timestamp': meta['timestamp'],
                                'document_type': search_type,
                                'similarity_score': float(score),
                                'rank': i + 1
                            }
                            break
                    
                    if doc_data:
                        results.append(doc_data)
            
            # Sort by similarity score
            results.sort(key=lambda x: x['similarity_score'], reverse=True)
            
            self.logger.info(f"Found {len(results)} similar documents for query: {query_text[:50]}...")
            return results[:top_k]
            
        except Exception as e:
            self.logger.error(f"Failed to search similar documents: {e}")
            return []
    
    def store_trade_log_embedding(self, trade_data: Dict[str, Any]) -> Optional[str]:
        """
        🆕 Store trade log with semantic embedding for future analysis
        
        Args:
            trade_data: Trade information dictionary
            
        Returns:
            Document ID if successful
        """
        try:
            # Create meaningful text content from trade data
            content_parts = [
                f"Trade: {trade_data.get('action', 'unknown')} {trade_data.get('quantity', 0)} shares of {trade_data.get('symbol', 'unknown')}",
                f"Price: ₹{trade_data.get('price', 0):.2f}",
                f"Strategy: {trade_data.get('strategy', 'unknown')}",
                f"Sentiment: {trade_data.get('market_sentiment', 'neutral')}",
                f"Reason: {trade_data.get('reasoning', 'No reasoning provided')}"
            ]
            
            if 'pnl' in trade_data:
                content_parts.append(f"PnL: ₹{trade_data['pnl']:.2f}")
            
            content = " | ".join(content_parts)
            
            # Enhanced metadata
            metadata = {
                **trade_data,
                'trade_date': trade_data.get('timestamp', datetime.datetime.utcnow().isoformat()),
                'trade_category': 'live_trade'
            }
            
            return self.store_embedding_document(content, 'trade_log', metadata)
            
        except Exception as e:
            self.logger.error(f"Failed to store trade log embedding: {e}")
            return None
    
    def store_market_sentiment_embedding(self, sentiment_data: Dict[str, Any]) -> Optional[str]:
        """
        🆕 Store market sentiment analysis with embedding
        
        Args:
            sentiment_data: Market sentiment information
            
        Returns:
            Document ID if successful
        """
        try:
            # Create meaningful content from sentiment data
            content_parts = [
                f"Market Sentiment: {sentiment_data.get('overall_sentiment', 'neutral')}",
                f"VIX: {sentiment_data.get('vix', 'unknown')}",
                f"NIFTY Trend: {sentiment_data.get('nifty_trend', 'neutral')}",
                f"SGX Nifty: {sentiment_data.get('sgx_nifty', 'neutral')}",
                f"Dow Futures: {sentiment_data.get('dow', 'neutral')}"
            ]
            
            if 'regime_analysis' in sentiment_data:
                regime = sentiment_data['regime_analysis'].get('overall_regime', {})
                content_parts.append(f"Market Regime: {regime.get('regime', 'unknown')}")
                content_parts.append(f"Volatility: {regime.get('factors', {}).get('volatility', 'unknown')}")
            
            content = " | ".join(content_parts)
            
            # Enhanced metadata
            metadata = {
                **sentiment_data,
                'analysis_timestamp': datetime.datetime.utcnow().isoformat(),
                'sentiment_category': 'market_analysis'
            }
            
            return self.store_embedding_document(content, 'market_sentiment', metadata)
            
        except Exception as e:
            self.logger.error(f"Failed to store market sentiment embedding: {e}")
            return None
    
    def get_contextual_trade_history(self, query: str, days_back: int = 30, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        🆕 Get relevant trade history based on current market context using semantic search
        
        Args:
            query: Current context or question
            days_back: How many days back to search
            top_k: Number of relevant trades to return
            
        Returns:
            List of relevant trade records with similarity scores
        """
        try:
            # Search for similar trade logs
            trade_results = self.search_similar_documents(query, 'trade_log', top_k * 2, 0.6)
            
            # Filter by date range
            cutoff_date = datetime.datetime.utcnow() - datetime.timedelta(days=days_back)
            
            filtered_results = []
            for result in trade_results:
                trade_date_str = result['metadata'].get('trade_date', result['metadata'].get('timestamp', ''))
                try:
                    trade_date = datetime.datetime.fromisoformat(trade_date_str.replace('Z', '+00:00'))
                    if trade_date >= cutoff_date:
                        filtered_results.append(result)
                except (ValueError, TypeError):
                    # Include if we can't parse the date
                    filtered_results.append(result)
            
            self.logger.info(f"Retrieved {len(filtered_results)} relevant trades for context: {query[:50]}...")
            return filtered_results[:top_k]
            
        except Exception as e:
            self.logger.error(f"Failed to get contextual trade history: {e}")
            return []
    
    def get_similar_market_conditions(self, current_conditions: Dict[str, Any], top_k: int = 5) -> List[Dict[str, Any]]:
        """
        🆕 Find historical market conditions similar to current state
        
        Args:
            current_conditions: Current market conditions dictionary
            top_k: Number of similar conditions to return
            
        Returns:
            List of similar market condition records
        """
        try:
            # Create query from current conditions
            query_parts = [
                f"Market Sentiment: {current_conditions.get('sentiment', 'neutral')}",
                f"VIX: {current_conditions.get('vix', 'moderate')}",
                f"Volatility: {current_conditions.get('volatility', 'medium')}"
            ]
            
            if 'regime' in current_conditions:
                query_parts.append(f"Regime: {current_conditions['regime']}")
            
            query = " | ".join(query_parts)
            
            # Search for similar market sentiment records
            results = self.search_similar_documents(query, 'market_sentiment', top_k, 0.7)
            
            self.logger.info(f"Found {len(results)} similar market conditions")
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to get similar market conditions: {e}")
            return []
    
    def _save_faiss_index(self, doc_type: str) -> bool:
        """🆕 Save FAISS index to Google Cloud Storage"""
        try:
            if doc_type not in self.faiss_indices:
                return False
            
            # Create temporary files
            index_file = f"/tmp/faiss_index_{doc_type}.bin"
            metadata_file = f"/tmp/metadata_{doc_type}.pkl"
            
            # Save FAISS index
            faiss.write_index(self.faiss_indices[doc_type], index_file)
            
            # Save metadata
            with open(metadata_file, 'wb') as f:
                pickle.dump(self.embedding_metadata[doc_type], f)
            
            # Upload to GCS
            bucket = self.storage_client.bucket(self.embeddings_bucket)
            
            # Upload index file
            index_blob = bucket.blob(f"faiss_indices/{doc_type}_index.bin")
            index_blob.upload_from_filename(index_file)
            
            # Upload metadata file
            metadata_blob = bucket.blob(f"faiss_indices/{doc_type}_metadata.pkl")
            metadata_blob.upload_from_filename(metadata_file)
            
            # Cleanup temp files
            os.remove(index_file)
            os.remove(metadata_file)
            
            self.logger.info(f"Saved FAISS index for {doc_type} to GCS")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save FAISS index for {doc_type}: {e}")
            return False
    
    def _load_faiss_index(self, doc_type: str) -> bool:
        """🆕 Load FAISS index from Google Cloud Storage"""
        try:
            bucket = self.storage_client.bucket(self.embeddings_bucket)
            
            # Download index file
            index_blob = bucket.blob(f"faiss_indices/{doc_type}_index.bin")
            if not index_blob.exists():
                return False
            
            index_file = f"/tmp/faiss_index_{doc_type}.bin"
            index_blob.download_to_filename(index_file)
            
            # Download metadata file
            metadata_blob = bucket.blob(f"faiss_indices/{doc_type}_metadata.pkl")
            metadata_file = f"/tmp/metadata_{doc_type}.pkl"
            metadata_blob.download_to_filename(metadata_file)
            
            # Load FAISS index
            self.faiss_indices[doc_type] = faiss.read_index(index_file)
            
            # Load metadata
            with open(metadata_file, 'rb') as f:
                self.embedding_metadata[doc_type] = pickle.load(f)
            
            # Cleanup temp files
            os.remove(index_file)
            os.remove(metadata_file)
            
            self.logger.info(f"Loaded FAISS index for {doc_type} from GCS ({self.faiss_indices[doc_type].ntotal} documents)")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load FAISS index for {doc_type}: {e}")
            return False
    
    def get_embedding_statistics(self) -> Dict[str, Any]:
        """🆕 Get statistics about stored embeddings"""
        try:
            stats = {
                'total_documents': 0,
                'by_type': {},
                'embedding_dimension': self.embedding_dimension,
                'embedding_model': self.embedding_model
            }
            
            for doc_type, index in self.faiss_indices.items():
                count = index.ntotal
                stats['by_type'][doc_type] = count
                stats['total_documents'] += count
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to get embedding statistics: {e}")
            return {}
    
    def cleanup_expired_memories(self):
        """Remove expired memory items from all collections"""
        try:
            current_time = datetime.datetime.utcnow()
            cleanup_count = 0
            
            for collection_name in self.collections.values():
                # Query for expired documents
                expired_docs = self.query_memory_collection(
                    collection_name,
                    filters=[('expires_at', '<', current_time)]
                )
                
                # Delete expired documents
                for doc in expired_docs:
                    if self.delete_memory_item(collection_name, doc['id']):
                        cleanup_count += 1
            
            self.logger.info(f"Cleaned up {cleanup_count} expired memory items")
            return cleanup_count
        except Exception as e:
            self.logger.error(f"Failed to cleanup expired memories: {e}")
            return 0

    # === EXISTING CLOUD STORAGE OPERATIONS ===
    
    def store_memory_snapshot(self, snapshot: MemorySnapshot) -> bool:
        """Store complete memory snapshot to Cloud Storage"""
        try:
            bucket = self.storage_client.bucket(self.memory_bucket)
            
            # Create unique filename with timestamp
            timestamp = snapshot.timestamp.strftime('%Y%m%d_%H%M%S')
            filename = f"memory_snapshots/snapshot_{timestamp}.pkl.gz"
            
            # Serialize and compress snapshot
            snapshot_data = pickle.dumps(asdict(snapshot))
            compressed_data = gzip.compress(snapshot_data)
            
            # Upload to Cloud Storage
            blob = bucket.blob(filename)
            blob.upload_from_string(compressed_data, content_type='application/gzip')
            
            self.logger.info(f"Stored memory snapshot: {filename}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to store memory snapshot: {e}")
            return False
    
    def load_latest_memory_snapshot(self) -> Optional[MemorySnapshot]:
        """Load the most recent memory snapshot from Cloud Storage"""
        try:
            bucket = self.storage_client.bucket(self.memory_bucket)
            
            # List all snapshot files
            blobs = list(bucket.list_blobs(prefix="memory_snapshots/"))
            if not blobs:
                self.logger.warning("No memory snapshots found")
                return None
            
            # Sort by name to get the latest (timestamp-based naming)
            latest_blob = sorted(blobs, key=lambda x: x.name)[-1]
            
            # Download and decompress
            compressed_data = latest_blob.download_as_bytes()
            snapshot_data = gzip.decompress(compressed_data)
            snapshot_dict = pickle.loads(snapshot_data)
            
            # Convert back to MemorySnapshot
            snapshot_dict['timestamp'] = datetime.datetime.fromisoformat(snapshot_dict['timestamp'])
            snapshot = MemorySnapshot(**snapshot_dict)
            
            self.logger.info(f"Loaded memory snapshot: {latest_blob.name}")
            return snapshot
        except Exception as e:
            self.logger.error(f"Failed to load memory snapshot: {e}")
            return None
    
    def store_thought_archive(self, thoughts: List[Dict], date_str: str) -> bool:
        """Store daily thought archives to Cloud Storage"""
        try:
            bucket = self.storage_client.bucket(self.thought_bucket)
            filename = f"daily_thoughts/{date_str}_thoughts.json.gz"
            
            # Compress and store
            json_data = json.dumps(thoughts, indent=2, default=str)
            compressed_data = gzip.compress(json_data.encode('utf-8'))
            
            blob = bucket.blob(filename)
            blob.upload_from_string(compressed_data, content_type='application/gzip')
            
            self.logger.info(f"Stored thought archive: {filename}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to store thought archive: {e}")
            return False
    
    def store_analysis_report(self, report: Dict, report_type: str, date_str: str) -> bool:
        """Store analysis reports to Cloud Storage"""
        try:
            bucket = self.storage_client.bucket(self.reports_bucket)
            filename = f"reports/{report_type}/{date_str}_{report_type}_report.json"
            
            blob = bucket.blob(filename)
            blob.upload_from_string(
                json.dumps(report, indent=2, default=str),
                content_type='application/json'
            )
            
            self.logger.info(f"Stored analysis report: {filename}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to store analysis report: {e}")
            return False
    
    def create_disaster_recovery_backup(self) -> bool:
        """Create comprehensive disaster recovery backup"""
        try:
            timestamp = datetime.datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            
            # Backup all Firestore collections
            backup_data = {}
            for collection_name in self.collections.values():
                docs = self.query_memory_collection(collection_name, limit=10000)
                backup_data[collection_name] = docs
            
            # Include FAISS indices and embeddings
            backup_data['faiss_statistics'] = self.get_embedding_statistics()
            
            # Store backup
            bucket = self.storage_client.bucket(self.backup_bucket)
            filename = f"disaster_recovery/backup_{timestamp}.json.gz"
            
            json_data = json.dumps(backup_data, indent=2, default=str)
            compressed_data = gzip.compress(json_data.encode('utf-8'))
            
            blob = bucket.blob(filename)
            blob.upload_from_string(compressed_data, content_type='application/gzip')
            
            # Save all FAISS indices
            for doc_type in self.faiss_indices.keys():
                self._save_faiss_index(doc_type)
            
            self.logger.info(f"Created disaster recovery backup: {filename}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to create disaster recovery backup: {e}")
            return False
    
    def restore_from_disaster_backup(self, backup_name: str = None) -> bool:
        """Restore from disaster recovery backup"""
        try:
            bucket = self.storage_client.bucket(self.backup_bucket)
            
            if backup_name:
                blob = bucket.blob(backup_name)
            else:
                # Get latest backup
                blobs = list(bucket.list_blobs(prefix="disaster_recovery/"))
                if not blobs:
                    self.logger.error("No disaster recovery backups found")
                    return False
                blob = sorted(blobs, key=lambda x: x.name)[-1]
            
            # Download and restore
            compressed_data = blob.download_as_bytes()
            backup_data = json.loads(gzip.decompress(compressed_data).decode('utf-8'))
            
            # Restore collections
            for collection_name, docs in backup_data.items():
                if collection_name == 'faiss_statistics':
                    continue
                
                for doc in docs:
                    doc_id = doc.pop('id')
                    self.store_memory_item(collection_name, doc_id, doc)
            
            # Restore FAISS indices
            for doc_type in self.faiss_indices.keys():
                self._load_faiss_index(doc_type)
            
            self.logger.info(f"Restored from disaster recovery backup: {blob.name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to restore from disaster backup: {e}")
            return False
    
    def health_check(self) -> Dict[str, bool]:
        """Perform health check on all systems"""
        health = {
            'firestore': False,
            'cloud_storage': False,
            'memory_bucket': False,
            'thought_bucket': False,
            'reports_bucket': False,
            'backup_bucket': False,
            'embeddings_bucket': False,  # 🆕
            'embedding_system': False,   # 🆕
            'faiss_indices': False       # 🆕
        }
        
        try:
            # Test Firestore
            test_doc = self.firestore_client.collection('health_check').document('test')
            test_doc.set({'timestamp': firestore.SERVER_TIMESTAMP})
            test_doc.delete()
            health['firestore'] = True
        except Exception as e:
            self.logger.error(f"Firestore health check failed: {e}")
        
        try:
            # Test Cloud Storage buckets
            buckets_to_test = [
                ('memory_bucket', self.memory_bucket),
                ('thought_bucket', self.thought_bucket),
                ('reports_bucket', self.reports_bucket),
                ('backup_bucket', self.backup_bucket),
                ('embeddings_bucket', self.embeddings_bucket)
            ]
            
            for bucket_key, bucket_name in buckets_to_test:
                bucket = self.storage_client.bucket(bucket_name)
                if bucket.exists():
                    health[bucket_key] = True
                    if bucket_key == 'memory_bucket':
                        health['cloud_storage'] = True
        except Exception as e:
            self.logger.error(f"Cloud Storage health check failed: {e}")
        
        # 🆕 Test embedding system
        try:
            if self.embedding_model:
                test_embedding = self._generate_embedding("test query")
                health['embedding_system'] = test_embedding is not None
        except Exception as e:
            self.logger.error(f"Embedding system health check failed: {e}")
        
        # 🆕 Test FAISS indices
        try:
            total_docs = sum(index.ntotal for index in self.faiss_indices.values())
            health['faiss_indices'] = len(self.faiss_indices) > 0
        except Exception as e:
            self.logger.error(f"FAISS indices health check failed: {e}")
        
        return health
    
    def get_memory_stats(self) -> Dict[str, int]:
        """Get statistics about stored memories and embeddings"""
        stats = {}
        
        for collection_name in self.collections.values():
            try:
                docs = self.query_memory_collection(collection_name, limit=1)
                # Get approximate count (Firestore doesn't have efficient count)
                count = len(self.query_memory_collection(collection_name, limit=1000))
                stats[collection_name] = count
            except Exception as e:
                self.logger.error(f"Failed to get stats for {collection_name}: {e}")
                stats[collection_name] = 0
        
        # 🆕 Add embedding statistics
        embedding_stats = self.get_embedding_statistics()
        stats.update(embedding_stats)
        
        return stats
