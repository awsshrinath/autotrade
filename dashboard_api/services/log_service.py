import os
import logging
from typing import List, Dict, Any, Optional
from google.cloud import storage, firestore
from kubernetes import client, config

# Configure logging
logger = logging.getLogger(__name__)

class LogService:
    def __init__(self):
        try:
            self.gcs_client = storage.Client()
            self.firestore_db = firestore.AsyncClient()
        except Exception as e:
            logger.error(f"Failed to initialize Google Cloud clients: {e}")
            self.gcs_client = None
            self.firestore_db = None

        self.gcs_bucket_name = os.getenv("GCS_LOG_BUCKET", "tron-trade-logs")

        try:
            # Load K8s config. In-cluster config for production, kubeconfig for local dev.
            if os.getenv("KUBERNETES_SERVICE_HOST"):
                config.load_incluster_config()
            else:
                config.load_kube_config()
            self.k8s_api = client.CoreV1Api()
        except config.ConfigException:
            logger.warning("Could not load Kubernetes configuration. K8s log features will be unavailable.")
            self.k8s_api = None

    async def list_gcs_log_files(self, prefix: Optional[str] = None, limit: int = 100) -> List[str]:
        """Lists log files from the GCS bucket."""
        if not self.gcs_client:
            return ["GCS client not initialized."]
        try:
            bucket = self.gcs_client.get_bucket(self.gcs_bucket_name)
            blobs = bucket.list_blobs(prefix=prefix, max_results=limit)
            return [blob.name for blob in blobs]
        except Exception as e:
            logger.error(f"Error listing GCS files: {e}")
            return [f"Error: {e}"]

    async def get_gcs_log_content(self, file_path: str) -> Dict[str, Any]:
        """Retrieves the content of a specific log file from GCS."""
        if not self.gcs_client:
            return {"error": "GCS client not initialized."}
        try:
            bucket = self.gcs_client.get_bucket(self.gcs_bucket_name)
            blob = bucket.blob(file_path)
            if not blob.exists():
                return {"error": "File not found."}
            content = blob.download_as_text()
            return {"file_path": file_path, "content": content}
        except Exception as e:
            logger.error(f"Error fetching GCS file content for {file_path}: {e}")
            return {"error": str(e)}

    async def get_firestore_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieves recent logs from the 'system_logs_realtime' collection in Firestore."""
        if not self.firestore_db:
            return [{"error": "Firestore client not initialized."}]
        try:
            logs_ref = self.firestore_db.collection('system_logs_realtime')
            query = logs_ref.order_by('timestamp', direction=firestore.Query.DESCENDING).limit(limit)
            docs = await query.get()
            return [doc.to_dict() for doc in docs]
        except Exception as e:
            logger.error(f"Error fetching Firestore logs: {e}")
            return [{"error": str(e)}]

    async def list_k8s_pods(self) -> List[str]:
        """Lists running pods in the configured Kubernetes namespace."""
        if not self.k8s_api:
            return ["Kubernetes API not available"]
        try:
            # Assuming we are running in a namespace, e.g., 'gpt'
            namespace = os.getenv("K8S_NAMESPACE", "gpt")
            pod_list = self.k8s_api.list_namespaced_pod(namespace=namespace, watch=False)
            return [pod.metadata.name for pod in pod_list.items]
        except Exception as e:
            logger.error(f"Error listing K8s pods: {e}")
            return [f"Error: {e}"]

    async def get_k8s_pod_logs(self, pod_name: str, limit: int = 100) -> List[str]:
        """Retrieves logs for a specific Kubernetes pod."""
        if not self.k8s_api:
            return ["Kubernetes API not available"]
        try:
            namespace = os.getenv("K8S_NAMESPACE", "gpt")
            logs = self.k8s_api.read_namespaced_pod_log(
                name=pod_name,
                namespace=namespace,
                tail_lines=limit
            )
            return logs.split('\n')
        except client.ApiException as e:
            logger.error(f"K8s API Error fetching logs for pod {pod_name}: {e}")
            return [f"K8s API Error: {e.reason}"]
        except Exception as e:
            logger.error(f"Error fetching logs for K8s pod {pod_name}: {e}")
            return [f"Error: {e}"]

# Dependency Injection setup
_log_service_instance = None

def get_log_service():
    global _log_service_instance
    if _log_service_instance is None:
        _log_service_instance = LogService()
    return _log_service_instance 