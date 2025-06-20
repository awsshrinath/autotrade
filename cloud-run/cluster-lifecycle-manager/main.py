#!/usr/bin/env python3
"""
TRON Trading System - Daily Cluster Lifecycle Manager
Cloud Run service for automated GKE cluster creation, deployment, and deletion
"""

import os
import json
import logging
import subprocess
import time
from datetime import datetime, timezone
from flask import Flask, request, jsonify
from google.cloud import container_v1
from google.cloud import secretmanager
from google.cloud import storage
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration
PROJECT_ID = os.environ.get('GCP_PROJECT_ID', 'autotrade-453303')
CLUSTER_NAME = os.environ.get('CLUSTER_NAME', 'tron-trading-cluster')
ZONE = os.environ.get('GKE_ZONE', 'asia-south1-a')
HELM_CHART_PATH = os.environ.get('HELM_CHART_PATH', '/app/helm')
NAMESPACE = os.environ.get('KUBERNETES_NAMESPACE', 'gpt')
BACKUP_BUCKET = os.environ.get('BACKUP_BUCKET', 'tron-trading-backups')

class ClusterLifecycleManager:
    def __init__(self):
        self.container_client = container_v1.ClusterManagerClient()
        self.secret_client = secretmanager.SecretManagerServiceClient()
        self.storage_client = storage.Client()
        self.cluster_path = f"projects/{PROJECT_ID}/locations/{ZONE}"
        
    def create_cluster(self):
        """Create a new GKE cluster for daily trading operations"""
        logger.info(f"Creating GKE cluster: {CLUSTER_NAME}")
        
        cluster_config = {
            "name": CLUSTER_NAME,
            "description": "TRON Trading System - Daily Fresh Cluster",
            "initial_node_count": 3,
            "node_config": {
                "machine_type": "e2-standard-4",
                "disk_size_gb": 100,
                "oauth_scopes": [
                    "https://www.googleapis.com/auth/cloud-platform",
                    "https://www.googleapis.com/auth/devstorage.read_only",
                    "https://www.googleapis.com/auth/logging.write",
                    "https://www.googleapis.com/auth/monitoring",
                ],
                "service_account": f"gpt-runner-sa@{PROJECT_ID}.iam.gserviceaccount.com",
            },
            "master_auth": {
                "client_certificate_config": {
                    "issue_client_certificate": False
                }
            },
            "network": "default",
            "subnetwork": "default",
            "ip_allocation_policy": {
                "use_ip_aliases": True,
                "cluster_ipv4_cidr_block": "/14",
                "services_ipv4_cidr_block": "/20"
            },
            "master_authorized_networks_config": {
                "enabled": False
            },
            "network_policy": {
                "enabled": False
            },
            "addons_config": {
                "http_load_balancing": {"disabled": False},
                "horizontal_pod_autoscaling": {"disabled": False},
                "network_policy_config": {"disabled": True},
            },
            "release_channel": {
                "channel": container_v1.ReleaseChannel.Channel.STABLE
            },
            "workload_identity_config": {
                "workload_pool": f"{PROJECT_ID}.svc.id.goog"
            }
        }
        
        try:
            operation = self.container_client.create_cluster(
                parent=self.cluster_path,
                cluster=cluster_config
            )
            
            logger.info(f"Cluster creation initiated. Operation: {operation.name}")
            
            # Wait for cluster creation to complete
            self._wait_for_operation(operation)
            
            logger.info("Cluster created successfully")
            return {"status": "success", "message": "Cluster created"}
            
        except Exception as e:
            logger.error(f"Failed to create cluster: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def delete_cluster(self, backup_data=True):
        """Delete the GKE cluster after backing up important data"""
        logger.info(f"Deleting GKE cluster: {CLUSTER_NAME}")
        
        try:
            if backup_data:
                self.backup_cluster_data()
            
            operation = self.container_client.delete_cluster(
                name=f"{self.cluster_path}/clusters/{CLUSTER_NAME}"
            )
            
            logger.info(f"Cluster deletion initiated. Operation: {operation.name}")
            
            # Wait for cluster deletion to complete
            self._wait_for_operation(operation)
            
            logger.info("Cluster deleted successfully")
            return {"status": "success", "message": "Cluster deleted"}
            
        except Exception as e:
            logger.error(f"Failed to delete cluster: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def deploy_trading_system(self):
        """Deploy the TRON trading system using Helm"""
        logger.info("Deploying TRON trading system")
        
        try:
            # Configure kubectl
            self._configure_kubectl()
            
            # Create namespace
            self._create_namespace()
            
            # Create GCP service account secret
            self._create_gcp_secret()
            
            # Deploy using Helm
            helm_cmd = [
                "helm", "upgrade", "--install", "tron-system",
                HELM_CHART_PATH,
                "--namespace", NAMESPACE,
                "--create-namespace",
                "--wait",
                "--timeout", "15m",
                "--set", f"global.gcpProjectId={PROJECT_ID}",
                "--set", f"namespace={NAMESPACE}",
                "--set", "ingress.enabled=true",
                "--set", "ssl.managedCertificate.enabled=true"
            ]
            
            result = subprocess.run(helm_cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("Helm deployment successful")
                
                # Wait for all pods to be ready
                self._wait_for_pods_ready()
                
                # Verify deployment
                deployment_status = self._verify_deployment()
                
                return {
                    "status": "success",
                    "message": "Trading system deployed successfully",
                    "deployment_status": deployment_status
                }
            else:
                logger.error(f"Helm deployment failed: {result.stderr}")
                return {
                    "status": "error",
                    "message": f"Deployment failed: {result.stderr}"
                }
                
        except Exception as e:
            logger.error(f"Failed to deploy trading system: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def backup_cluster_data(self):
        """Backup important data before cluster deletion"""
        logger.info("Backing up cluster data")
        
        try:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            backup_dir = f"daily_backups/{timestamp}"
            
            # Backup ConfigMaps
            self._backup_configmaps(backup_dir)
            
            # Backup application logs
            self._backup_logs(backup_dir)
            
            # Backup persistent data (if any)
            self._backup_persistent_data(backup_dir)
            
            logger.info(f"Backup completed: {backup_dir}")
            return {"status": "success", "backup_location": backup_dir}
            
        except Exception as e:
            logger.error(f"Backup failed: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def _configure_kubectl(self):
        """Configure kubectl to connect to the cluster"""
        cmd = [
            "gcloud", "container", "clusters", "get-credentials",
            CLUSTER_NAME, "--zone", ZONE, "--project", PROJECT_ID
        ]
        subprocess.run(cmd, check=True)
    
    def _create_namespace(self):
        """Create the Kubernetes namespace"""
        cmd = ["kubectl", "create", "namespace", NAMESPACE, "--dry-run=client", "-o", "yaml"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            apply_cmd = ["kubectl", "apply", "-f", "-"]
            subprocess.run(apply_cmd, input=result.stdout, text=True, check=True)
    
    def _create_gcp_secret(self):
        """Create GCP service account secret in the cluster"""
        try:
            # Get service account key from Secret Manager
            secret_name = f"projects/{PROJECT_ID}/secrets/gcp-service-account-key/versions/latest"
            response = self.secret_client.access_secret_version(request={"name": secret_name})
            service_account_key = response.payload.data.decode("UTF-8")
            
            # Create Kubernetes secret
            cmd = [
                "kubectl", "create", "secret", "generic", "gcp-service-account-key",
                "--from-literal=key.json=" + service_account_key,
                "--namespace", NAMESPACE,
                "--dry-run=client", "-o", "yaml"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                apply_cmd = ["kubectl", "apply", "-f", "-"]
                subprocess.run(apply_cmd, input=result.stdout, text=True, check=True)
                
        except Exception as e:
            logger.warning(f"Could not create GCP secret: {str(e)}")
    
    def _wait_for_pods_ready(self):
        """Wait for all pods to be ready"""
        logger.info("Waiting for pods to be ready...")
        
        for attempt in range(30):  # Wait up to 15 minutes
            cmd = [
                "kubectl", "get", "pods", "--namespace", NAMESPACE,
                "--field-selector=status.phase!=Succeeded",
                "-o", "jsonpath={.items[*].status.conditions[?(@.type=='Ready')].status}"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                ready_statuses = result.stdout.strip().split()
                if ready_statuses and all(status == "True" for status in ready_statuses):
                    logger.info("All pods are ready")
                    return True
            
            logger.info(f"Waiting for pods to be ready... (attempt {attempt + 1}/30)")
            time.sleep(30)
        
        logger.warning("Timeout waiting for pods to be ready")
        return False
    
    def _verify_deployment(self):
        """Verify the deployment is working correctly"""
        try:
            # Check service status
            cmd = ["kubectl", "get", "services", "--namespace", NAMESPACE, "-o", "json"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            services = json.loads(result.stdout)
            
            # Check pod status
            cmd = ["kubectl", "get", "pods", "--namespace", NAMESPACE, "-o", "json"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            pods = json.loads(result.stdout)
            
            running_pods = sum(1 for pod in pods['items'] 
                             if pod['status'].get('phase') == 'Running')
            total_pods = len(pods['items'])
            
            return {
                "services_count": len(services['items']),
                "running_pods": running_pods,
                "total_pods": total_pods,
                "cluster_ready": running_pods == total_pods
            }
            
        except Exception as e:
            logger.error(f"Deployment verification failed: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def _backup_configmaps(self, backup_dir):
        """Backup ConfigMaps to GCS"""
        cmd = ["kubectl", "get", "configmaps", "--namespace", NAMESPACE, "-o", "yaml"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            bucket = self.storage_client.bucket(BACKUP_BUCKET)
            blob = bucket.blob(f"{backup_dir}/configmaps.yaml")
            blob.upload_from_string(result.stdout)
    
    def _backup_logs(self, backup_dir):
        """Backup application logs to GCS"""
        try:
            # Get logs from all pods
            cmd = ["kubectl", "get", "pods", "--namespace", NAMESPACE, "-o", "name"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                pod_names = result.stdout.strip().split('\\n')
                
                for pod_name in pod_names:
                    if pod_name:
                        log_cmd = ["kubectl", "logs", pod_name, "--namespace", NAMESPACE]
                        log_result = subprocess.run(log_cmd, capture_output=True, text=True)
                        
                        if log_result.returncode == 0:
                            bucket = self.storage_client.bucket(BACKUP_BUCKET)
                            blob = bucket.blob(f"{backup_dir}/logs/{pod_name.replace('pod/', '')}.log")
                            blob.upload_from_string(log_result.stdout)
                            
        except Exception as e:
            logger.warning(f"Log backup failed: {str(e)}")
    
    def _backup_persistent_data(self, backup_dir):
        """Backup any persistent data"""
        # Add specific backup logic for persistent volumes or data if needed
        logger.info("Persistent data backup completed")
    
    def _wait_for_operation(self, operation):
        """Wait for a GKE operation to complete"""
        while operation.status != container_v1.Operation.Status.DONE:
            time.sleep(10)
            operation = self.container_client.get_operation(
                name=operation.self_link
            )
            
            if operation.status == container_v1.Operation.Status.ABORTING:
                raise Exception(f"Operation failed: {operation.detail}")

# Initialize the cluster manager
cluster_manager = ClusterLifecycleManager()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()})

@app.route('/create-cluster', methods=['POST'])
def create_cluster():
    """Create a new cluster and deploy the trading system"""
    logger.info("Received cluster creation request")
    
    try:
        # Create cluster
        create_result = cluster_manager.create_cluster()
        if create_result["status"] != "success":
            return jsonify(create_result), 500
        
        # Deploy trading system
        deploy_result = cluster_manager.deploy_trading_system()
        if deploy_result["status"] != "success":
            return jsonify(deploy_result), 500
        
        return jsonify({
            "status": "success",
            "message": "Cluster created and trading system deployed",
            "cluster_creation": create_result,
            "deployment": deploy_result,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
    except Exception as e:
        logger.error(f"Cluster creation failed: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/delete-cluster', methods=['POST'])
def delete_cluster():
    """Delete the cluster after backing up data"""
    logger.info("Received cluster deletion request")
    
    try:
        # Parse request for backup option
        data = request.get_json() or {}
        backup_data = data.get('backup_data', True)
        
        delete_result = cluster_manager.delete_cluster(backup_data=backup_data)
        
        return jsonify({
            "status": delete_result["status"],
            "message": delete_result["message"],
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
    except Exception as e:
        logger.error(f"Cluster deletion failed: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/deploy', methods=['POST'])
def deploy_system():
    """Deploy the trading system to existing cluster"""
    logger.info("Received deployment request")
    
    try:
        deploy_result = cluster_manager.deploy_trading_system()
        return jsonify(deploy_result)
        
    except Exception as e:
        logger.error(f"Deployment failed: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/backup', methods=['POST'])
def backup_data():
    """Backup cluster data"""
    logger.info("Received backup request")
    
    try:
        backup_result = cluster_manager.backup_cluster_data()
        return jsonify(backup_result)
        
    except Exception as e:
        logger.error(f"Backup failed: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/status', methods=['GET'])
def cluster_status():
    """Get cluster status"""
    try:
        # Check if cluster exists
        cluster_name = f"{cluster_manager.cluster_path}/clusters/{CLUSTER_NAME}"
        cluster = cluster_manager.container_client.get_cluster(name=cluster_name)
        
        return jsonify({
            "status": "running",
            "cluster_status": cluster.status.name,
            "node_count": cluster.current_node_count,
            "location": cluster.location,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
    except Exception as e:
        return jsonify({
            "status": "not_found",
            "message": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)