# runner / gcp_memory_client.py
# GCP Memory Client for Cloud Storage and Firestore operations
# Provides unified interface for cognitive system persistence across daily cluster recreations

import json
import pickle
import gzip
import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from google.cloud import storage
from google.cloud import firestore
import logging


@dataclass
class MemorySnapshot:
    """Snapshot of cognitive memory state for backup / restore"""
    timestamp: datetime.datetime
    working_memory: List[Dict]
    short_term_memory: List[Dict]
    cognitive_state: Dict
    recent_thoughts: List[Dict]
    performance_metrics: Dict


class GCPMemoryClient:
    """
    Unified client for cognitive memory persistence using GCP Firestore and Cloud Storage.
    Designed for bulletproof persistence across daily Kubernetes cluster recreations.
    """
    
    def __init__(self, project_id: str = None, logger: logging.Logger = None):
        self.project_id = project_id
        self.logger = logger or logging.getLogger(__name__)
        
        # Initialize clients
        self._init_clients()
        
        # Bucket names for different memory types
        self.memory_bucket = "tron - cognitive - memory"
        self.thought_bucket = "tron - thought - archives"
        self.reports_bucket = "tron - analysis - reports"
        self.backup_bucket = "tron - memory - backups"
        
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
            'learning_metrics': 'learning_metrics'
        }
        
        # Initialize storage buckets
        self._ensure_buckets_exist()
    
    def _init_clients(self):
        """Initialize GCP clients with error handling"""
        try:
            self.firestore_client = firestore.Client(project=self.project_id)
            self.storage_client = storage.Client(project=self.project_id)
            self.logger.info("GCP clients initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize GCP clients: {e}")
            raise
    
    def _ensure_buckets_exist(self):
        """Ensure all required Cloud Storage buckets exist"""
        buckets = [
                    self.memory_bucket,
                    self.thought_bucket, 
                self.reports_bucket,
            self.backup_bucket
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
    
    # === FIRESTORE OPERATIONS ===
    
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
    
    def cleanup_expired_memories(self):
        """Remove expired memory items from all collections"""
        for collection_name in self.collections.values():
            try:
                # Query expired items
                expired_docs = self.query_memory_collection(
                        collection_name,
                    filters=[('expires_at', '<', datetime.datetime.utcnow())]
                )
                
                # Delete expired items
                for doc in expired_docs:
                    self.delete_memory_item(collection_name, doc['id'])
                
                if expired_docs:
                    self.logger.info(f"Cleaned up {len(expired_docs)} expired items from {collection_name}")
            except Exception as e:
                self.logger.error(f"Failed to cleanup expired memories in {collection_name}: {e}")
    
    # === CLOUD STORAGE OPERATIONS ===
    
    def store_memory_snapshot(self, snapshot: MemorySnapshot) -> bool:
        """Store compressed memory snapshot to Cloud Storage"""
        try:
            timestamp_str = snapshot.timestamp.strftime("%Y%m%d_%H%M%S")
            blob_name = f"snapshots / memory_snapshot_{timestamp_str}.pkl.gz"
            
            # Serialize and compress snapshot
            serialized_data = pickle.dumps(asdict(snapshot))
            compressed_data = gzip.compress(serialized_data)
            
            # Upload to Cloud Storage
            bucket = self.storage_client.bucket(self.memory_bucket)
            blob = bucket.blob(blob_name)
            blob.upload_from_string(compressed_data)
            
            self.logger.info(f"Memory snapshot stored: {blob_name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to store memory snapshot: {e}")
            return False
    
    def load_latest_memory_snapshot(self) -> Optional[MemorySnapshot]:
        """Load the most recent memory snapshot from Cloud Storage"""
        try:
            bucket = self.storage_client.bucket(self.memory_bucket)
            blobs = list(bucket.list_blobs(prefix="snapshots / memory_snapshot_"))
            
            if not blobs:
                self.logger.info("No memory snapshots found")
                return None
            
            # Get the most recent snapshot
            latest_blob = max(blobs, key=lambda b: b.time_created)
            
            # Download and decompress
            compressed_data = latest_blob.download_as_bytes()
            serialized_data = gzip.decompress(compressed_data)
            snapshot_dict = pickle.loads(serialized_data)
            
            # Convert back to MemorySnapshot object
            snapshot_dict['timestamp'] = datetime.datetime.fromisoformat(snapshot_dict['timestamp'])
            snapshot = MemorySnapshot(**snapshot_dict)
            
            self.logger.info(f"Loaded memory snapshot from {latest_blob.name}")
            return snapshot
        except Exception as e:
            self.logger.error(f"Failed to load memory snapshot: {e}")
            return None
    
    def store_thought_archive(self, thoughts: List[Dict], date_str: str) -> bool:
        """Store compressed daily thought archive"""
        try:
            blob_name = f"daily_thoughts / thoughts_{date_str}.json.gz"
            
            # Serialize and compress thoughts
            json_data = json.dumps(thoughts, default=str, indent=2)
            compressed_data = gzip.compress(json_data.encode('utf - 8'))
            
            # Upload to Cloud Storage
            bucket = self.storage_client.bucket(self.thought_bucket)
            blob = bucket.blob(blob_name)
            blob.upload_from_string(compressed_data)
            
            self.logger.info(f"Thought archive stored: {blob_name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to store thought archive: {e}")
            return False
    
    def store_analysis_report(self, report: Dict, report_type: str, date_str: str) -> bool:
        """Store analysis report to Cloud Storage"""
        try:
            blob_name = f"{report_type}/{report_type}_{date_str}.json"
            
            # Upload report
            bucket = self.storage_client.bucket(self.reports_bucket)
            blob = bucket.blob(blob_name)
            blob.upload_from_string(json.dumps(report, default=str, indent=2))
            
            self.logger.info(f"Analysis report stored: {blob_name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to store analysis report: {e}")
            return False
    
    def create_disaster_recovery_backup(self) -> bool:
        """Create comprehensive backup of all cognitive data"""
        try:
            timestamp = datetime.datetime.utcnow()
            backup_name = f"disaster_recovery_{timestamp.strftime('%Y%m%d_%H%M%S')}"
            
            # Collect all cognitive data from Firestore
            backup_data = {
                    'timestamp': timestamp.isoformat(),
                'collections': {}
            }
            
            for collection_name in self.collections.values():
                docs = self.query_memory_collection(collection_name)
                backup_data['collections'][collection_name] = docs
            
            # Compress and store backup
            json_data = json.dumps(backup_data, default=str, indent=2)
            compressed_data = gzip.compress(json_data.encode('utf - 8'))
            
            bucket = self.storage_client.bucket(self.backup_bucket)
            blob = bucket.blob(f"{backup_name}.json.gz")
            blob.upload_from_string(compressed_data)
            
            self.logger.info(f"Disaster recovery backup created: {backup_name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to create disaster recovery backup: {e}")
            return False
    
    def restore_from_disaster_backup(self, backup_name: str = None) -> bool:
        """Restore cognitive data from disaster recovery backup"""
        try:
            bucket = self.storage_client.bucket(self.backup_bucket)
            
            if backup_name:
                blob = bucket.blob(f"{backup_name}.json.gz")
            else:
                # Get latest backup
                blobs = list(bucket.list_blobs(prefix="disaster_recovery_"))
                if not blobs:
                    self.logger.error("No disaster recovery backups found")
                    return False
                blob = max(blobs, key=lambda b: b.time_created)
            
            # Download and decompress backup
            compressed_data = blob.download_as_bytes()
            json_data = gzip.decompress(compressed_data).decode('utf - 8')
            backup_data = json.loads(json_data)
            
            # Restore data to Firestore
            for collection_name, docs in backup_data['collections'].items():
                for doc in docs:
                    doc_id = doc.pop('id', None)
                    if doc_id:
                        self.store_memory_item(collection_name, doc_id, doc)
            
            self.logger.info(f"Restored from disaster backup: {blob.name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to restore from disaster backup: {e}")
            return False
    
    # === HEALTH CHECKS ===
    
    def health_check(self) -> Dict[str, bool]:
        """Perform health check on all GCP services"""
        health_status = {
                    'firestore': False,
                'cloud_storage': False,
            'buckets': False
        }
        
        try:
            # Test Firestore
            test_doc = self.firestore_client.collection('health_check').document('test')
            test_doc.set({'timestamp': firestore.SERVER_TIMESTAMP})
            test_doc.delete()
            health_status['firestore'] = True
        except Exception as e:
            self.logger.error(f"Firestore health check failed: {e}")
        
        try:
            # Test Cloud Storage
            bucket = self.storage_client.bucket(self.memory_bucket)
            blob = bucket.blob('health_check.txt')
            blob.upload_from_string('health check')
            blob.delete()
            health_status['cloud_storage'] = True
            health_status['buckets'] = True
        except Exception as e:
            self.logger.error(f"Cloud Storage health check failed: {e}")
        
        return health_status
    
    def get_memory_stats(self) -> Dict[str, int]:
        """Get memory usage statistics across all collections"""
        stats = {}
        for collection_name in self.collections.values():
            try:
                docs = self.query_memory_collection(collection_name, limit=1000)
                stats[collection_name] = len(docs)
            except Exception as e:
                self.logger.error(f"Failed to get stats for {collection_name}: {e}")
                stats[collection_name] = -1
        
        return stats
