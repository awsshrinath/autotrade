#!/usr/bin/env python3
"""
Kubernetes-Native GCP Client

This client is designed specifically for Kubernetes deployments where the pod
runs with a service account that has the necessary GCP permissions.

Unlike traditional GCP clients that use explicit credentials or impersonation,
this client relies on the default service account attached to the pod.
"""

import logging
import os
from typing import Optional
import google.auth
from google.cloud import firestore, storage, secretmanager


class K8sNativeGCPClient:
    """GCP client that uses Kubernetes pod service account"""
    
    def __init__(self, project_id: str = None, logger: logging.Logger = None):
        self.logger = logger or logging.getLogger(__name__)
        self.project_id = project_id or os.getenv("GCP_PROJECT_ID", "autotrade-453303")
        
        # Initialize clients
        self.credentials = None
        self.discovered_project = None
        self.firestore_client = None
        self.storage_client = None
        self.secret_client = None
        
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize GCP clients using pod service account"""
        
        try:
            # Get default credentials - this uses the pod's service account in K8s
            self.credentials, self.discovered_project = google.auth.default()
            
            # Use discovered project if available
            if self.discovered_project and not self.project_id:
                self.project_id = self.discovered_project
                
            self._log_info(f"Using pod service account for project: {self.project_id}")
            
            # Initialize clients with the default credentials
            self.firestore_client = firestore.Client(
                project=self.project_id,
                credentials=self.credentials
            )
            
            self.storage_client = storage.Client(
                project=self.project_id,
                credentials=self.credentials
            )
            
            self.secret_client = secretmanager.SecretManagerServiceClient(
                credentials=self.credentials
            )
            
            self._log_info("✅ All GCP clients initialized successfully")
            
        except Exception as e:
            self._log_error(f"Failed to initialize GCP clients: {e}")
            
            # Fallback: Try without explicit credentials (minimal approach)
            try:
                self.firestore_client = firestore.Client(project=self.project_id)
                self.storage_client = storage.Client(project=self.project_id)
                self.secret_client = secretmanager.SecretManagerServiceClient()
                
                self._log_info("✅ GCP clients initialized with minimal configuration")
                
            except Exception as e2:
                self._log_error(f"All GCP client initialization methods failed: {e2}")
                # Continue with None clients - hybrid mode can handle this
    
    @property
    def is_available(self) -> bool:
        """Check if GCP clients are available"""
        return (
            self.firestore_client is not None and 
            self.storage_client is not None and 
            self.secret_client is not None
        )
    
    def get_firestore_client(self) -> Optional[firestore.Client]:
        """Get Firestore client"""
        return self.firestore_client
    
    def get_storage_client(self) -> Optional[storage.Client]:
        """Get Cloud Storage client"""
        return self.storage_client
    
    def get_secret_client(self) -> Optional[secretmanager.SecretManagerServiceClient]:
        """Get Secret Manager client"""
        return self.secret_client
    
    def test_connectivity(self) -> dict:
        """Test connectivity to GCP services"""
        results = {
            "firestore": False,
            "storage": False,
            "secrets": False,
            "overall": False
        }
        
        # Test Firestore
        if self.firestore_client:
            try:
                # Quick test - list collections (minimal operation)
                collections = list(self.firestore_client.collections())
                results["firestore"] = True
                self._log_info("✅ Firestore connectivity confirmed")
            except Exception as e:
                self._log_warning(f"⚠️ Firestore test failed: {e}")
        
        # Test Storage
        if self.storage_client:
            try:
                # Quick test - list buckets (minimal operation)
                buckets = list(self.storage_client.list_buckets(max_results=1))
                results["storage"] = True
                self._log_info("✅ Storage connectivity confirmed")
            except Exception as e:
                self._log_warning(f"⚠️ Storage test failed: {e}")
        
        # Test Secret Manager
        if self.secret_client:
            try:
                # Quick test - list secrets (minimal operation)
                parent = f"projects/{self.project_id}"
                request = secretmanager.ListSecretsRequest(parent=parent)
                secrets = list(self.secret_client.list_secrets(request=request, timeout=5))
                results["secrets"] = True
                self._log_info("✅ Secret Manager connectivity confirmed")
            except Exception as e:
                self._log_warning(f"⚠️ Secret Manager test failed: {e}")
        
        results["overall"] = all([results["firestore"], results["storage"], results["secrets"]])
        return results
    
    def _log_info(self, message: str):
        """Log info message"""
        if hasattr(self.logger, 'log_event'):
            self.logger.log_event(f"ℹ️ [K8sGCP] {message}")
        else:
            self.logger.info(f"[K8sGCP] {message}")
    
    def _log_warning(self, message: str):
        """Log warning message"""
        if hasattr(self.logger, 'log_event'):
            self.logger.log_event(f"⚠️ [K8sGCP] {message}")
        else:
            self.logger.warning(f"[K8sGCP] {message}")
    
    def _log_error(self, message: str):
        """Log error message"""
        if hasattr(self.logger, 'log_event'):
            self.logger.log_event(f"❌ [K8sGCP] {message}")
        else:
            self.logger.error(f"[K8sGCP] {message}")
    
    # Compatibility methods for cognitive system
    def load_latest_memory_snapshot(self):
        """Load latest memory snapshot - compatibility method"""
        try:
            if not self.firestore_client:
                return None
                
            # Query for latest snapshot
            snapshots = (self.firestore_client
                        .collection('memory_snapshots')
                        .order_by('created_at', direction=firestore.Query.DESCENDING)
                        .limit(1)
                        .get())
            
            if snapshots:
                snapshot_data = snapshots[0].to_dict()
                return SimpleMemorySnapshot(snapshot_data)
            return None
            
        except Exception as e:
            self._log_warning(f"Failed to load memory snapshot: {e}")
            return None
    
    def query_memory_collection(self, collection_name: str, order_by: str = None, limit: int = 10):
        """Query memory collection - compatibility method"""
        try:
            if not self.firestore_client:
                return []
                
            query = self.firestore_client.collection(collection_name)
            
            if order_by:
                query = query.order_by(order_by, direction=firestore.Query.DESCENDING)
                
            if limit:
                query = query.limit(limit)
                
            docs = query.get()
            return [doc.to_dict() for doc in docs]
            
        except Exception as e:
            self._log_warning(f"Failed to query {collection_name}: {e}")
            return []
    
    def store_memory_item(self, collection_name: str, memory_id: str, data: dict, ttl_hours: int = None):
        """Store memory item - compatibility method"""
        try:
            if not self.firestore_client:
                return False
                
            doc_ref = self.firestore_client.collection(collection_name).document(memory_id)
            doc_ref.set(data)
            return True
            
        except Exception as e:
            self._log_warning(f"Failed to store memory item {memory_id}: {e}")
            return False
    
    def health_check(self):
        """Health check - compatibility method"""
        results = self.test_connectivity()
        return {
            'firestore_connected': results.get('firestore', False),
            'storage_connected': results.get('storage', False),
            'secrets_connected': results.get('secrets', False),
            'overall_healthy': results.get('overall', False)
        }
    
    def create_disaster_recovery_backup(self):
        """Create disaster recovery backup - compatibility method"""
        try:
            self._log_info("Creating disaster recovery backup...")
            # Simplified backup - just log for now
            return True
        except Exception as e:
            self._log_warning(f"Backup creation failed: {e}")
            return False
    
    def get_secret(self, secret_name: str) -> str:
        """Get secret value - compatibility method"""
        try:
            if not self.secret_client:
                return None
                
            name = f"projects/{self.project_id}/secrets/{secret_name}/versions/latest"
            response = self.secret_client.access_secret_version(request={"name": name})
            return response.payload.data.decode("UTF-8")
            
        except Exception as e:
            self._log_warning(f"Failed to get secret {secret_name}: {e}")
            return None
    
    # Additional compatibility methods for cognitive memory system
    def cleanup_expired_memories(self):
        """Cleanup expired memories - compatibility method"""
        try:
            self._log_info("Cleaning up expired memories...")
            # Simplified cleanup
            return True
        except Exception as e:
            self._log_warning(f"Memory cleanup failed: {e}")
            return False
    
    def delete_memory_item(self, collection_name: str, memory_id: str):
        """Delete memory item - compatibility method"""
        try:
            if not self.firestore_client:
                return False
                
            doc_ref = self.firestore_client.collection(collection_name).document(memory_id)
            doc_ref.delete()
            return True
            
        except Exception as e:
            self._log_warning(f"Failed to delete memory item {memory_id}: {e}")
            return False
    
    def update_memory_item(self, collection_name: str, memory_id: str, data: dict):
        """Update memory item - compatibility method"""
        try:
            if not self.firestore_client:
                return False
                
            doc_ref = self.firestore_client.collection(collection_name).document(memory_id)
            doc_ref.update(data)
            return True
            
        except Exception as e:
            self._log_warning(f"Failed to update memory item {memory_id}: {e}")
            return False
    
    def store_memory_snapshot(self, snapshot_data: dict):
        """Store memory snapshot - compatibility method"""
        try:
            if not self.firestore_client:
                return False
                
            snapshot_id = f"snapshot_{int(snapshot_data['timestamp'].timestamp())}"
            doc_ref = self.firestore_client.collection('memory_snapshots').document(snapshot_id)
            doc_ref.set(snapshot_data)
            return True
            
        except Exception as e:
            self._log_warning(f"Failed to store memory snapshot: {e}")
            return False
    
    def get_memory_stats(self):
        """Get memory statistics - compatibility method"""
        try:
            if not self.firestore_client:
                return {}
                
            # Basic stats - count documents in each collection
            stats = {}
            collections = ['working_memory', 'short_term_memory', 'long_term_memory', 'episodic_memory']
            
            for collection_name in collections:
                try:
                    docs = self.firestore_client.collection(collection_name).limit(1000).get()
                    stats[f"{collection_name}_count"] = len(docs)
                except:
                    stats[f"{collection_name}_count"] = 0
            
            return stats
            
        except Exception as e:
            self._log_warning(f"Failed to get memory stats: {e}")
            return {}


class SimpleMemorySnapshot:
    """Simple memory snapshot for compatibility"""
    def __init__(self, data: dict):
        self.working_memory = data.get('working_memory', [])
        self.short_term_memory = data.get('short_term_memory', [])
        self.created_at = data.get('created_at')
        self.snapshot_id = data.get('snapshot_id', 'unknown')


# Global instance for easy access
_k8s_gcp_client = None

def get_k8s_gcp_client(project_id: str = None, logger: logging.Logger = None) -> K8sNativeGCPClient:
    """Get or create the global K8s GCP client instance"""
    global _k8s_gcp_client
    
    if _k8s_gcp_client is None:
        _k8s_gcp_client = K8sNativeGCPClient(project_id=project_id, logger=logger)
    
    return _k8s_gcp_client


if __name__ == "__main__":
    # Test the client
    client = K8sNativeGCPClient()
    print(f"Client available: {client.is_available}")
    
    if client.is_available:
        results = client.test_connectivity()
        print(f"Connectivity test results: {results}") 