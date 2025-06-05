"""
Kubernetes (K8s) service for pod log retrieval.
Handles connection, authentication, and log retrieval from Kubernetes pods.
"""

import asyncio
import json
import logging
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union
from kubernetes import client, config
from kubernetes.client.rest import ApiException
import structlog

from ..utils.config import get_config

logger = structlog.get_logger(__name__)


class K8sLogService:
    """Service for retrieving logs from Kubernetes pods."""
    
    def __init__(self):
        self.config = get_config()
        self.core_v1_api = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the Kubernetes client with authentication."""
        try:
            # Try to load in-cluster config first (for when running inside a pod)
            try:
                config.load_incluster_config()
                logger.info("Kubernetes client initialized with in-cluster config")
            except config.ConfigException:
                # Fallback to kubeconfig file (for local development)
                config_file = self.config.kubernetes_config_path
                if config_file:
                    config.load_kube_config(config_file=config_file)
                    logger.info("Kubernetes client initialized with kubeconfig file", config_file=config_file)
                else:
                    config.load_kube_config()
                    logger.info("Kubernetes client initialized with default kubeconfig")
            
            # Initialize the Core V1 API client
            self.core_v1_api = client.CoreV1Api()
            
            logger.info("Kubernetes client initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize Kubernetes client", error=str(e))
            raise
    
    async def test_connection(self) -> bool:
        """Test the Kubernetes connection and permissions."""
        try:
            # Test connection by listing namespaces
            namespaces = self.core_v1_api.list_namespace()
            
            # Test pod listing in the configured namespace
            namespace = self.config.kubernetes_namespace
            pods = self.core_v1_api.list_namespaced_pod(namespace=namespace, limit=1)
            
            logger.info(
                "Kubernetes connection test successful",
                namespace_count=len(namespaces.items),
                test_namespace=namespace,
                pod_count=len(pods.items)
            )
            return True
            
        except ApiException as e:
            logger.error("Kubernetes API access forbidden", error=str(e), status=e.status)
            return False
        except Exception as e:
            logger.error("Kubernetes connection test failed", error=str(e))
            return False
    
    async def get_pods(
        self,
        namespace: Optional[str] = None,
        label_selector: Optional[str] = None,
        field_selector: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get list of pods in a namespace.
        
        Args:
            namespace: Kubernetes namespace (uses default if None)
            label_selector: Label selector to filter pods
            field_selector: Field selector to filter pods
            
        Returns:
            List of pod information dictionaries
        """
        try:
            namespace = namespace or self.config.kubernetes_namespace
            
            pods = self.core_v1_api.list_namespaced_pod(
                namespace=namespace,
                label_selector=label_selector,
                field_selector=field_selector
            )
            
            pod_list = []
            for pod in pods.items:
                pod_info = {
                    "name": pod.metadata.name,
                    "namespace": pod.metadata.namespace,
                    "status": pod.status.phase,
                    "created": pod.metadata.creation_timestamp.isoformat() if pod.metadata.creation_timestamp else None,
                    "labels": pod.metadata.labels or {},
                    "node_name": pod.spec.node_name,
                    "pod_ip": pod.status.pod_ip,
                    "containers": []
                }
                
                # Add container information
                if pod.spec.containers:
                    for container in pod.spec.containers:
                        container_info = {
                            "name": container.name,
                            "image": container.image,
                            "ready": False
                        }
                        
                        # Check container readiness
                        if pod.status.container_statuses:
                            for status in pod.status.container_statuses:
                                if status.name == container.name:
                                    container_info["ready"] = status.ready
                                    container_info["restart_count"] = status.restart_count
                                    break
                        
                        pod_info["containers"].append(container_info)
                
                pod_list.append(pod_info)
            
            logger.info(
                "Retrieved pod list",
                namespace=namespace,
                pod_count=len(pod_list)
            )
            
            return pod_list
            
        except Exception as e:
            logger.error("Failed to get pods", namespace=namespace, error=str(e))
            raise
    
    async def get_pod_logs(
        self,
        pod_name: str,
        namespace: Optional[str] = None,
        container: Optional[str] = None,
        since_seconds: Optional[int] = None,
        since_time: Optional[datetime] = None,
        tail_lines: Optional[int] = None,
        follow: bool = False,
        timestamps: bool = True
    ) -> str:
        """
        Get logs from a specific pod.
        
        Args:
            pod_name: Name of the pod
            namespace: Kubernetes namespace (uses default if None)
            container: Container name (uses first container if None)
            since_seconds: Logs from last N seconds
            since_time: Logs since specific datetime
            tail_lines: Number of lines from the end of the log
            follow: Whether to follow/stream logs
            timestamps: Whether to include timestamps
            
        Returns:
            Pod logs as string
        """
        try:
            namespace = namespace or self.config.kubernetes_namespace
            
            # Get pod info to determine container if not specified
            if not container:
                pod = self.core_v1_api.read_namespaced_pod(name=pod_name, namespace=namespace)
                if pod.spec.containers:
                    container = pod.spec.containers[0].name
                else:
                    raise ValueError(f"No containers found in pod {pod_name}")
            
            # Prepare parameters
            kwargs = {
                "name": pod_name,
                "namespace": namespace,
                "container": container,
                "timestamps": timestamps,
                "follow": follow
            }
            
            if since_seconds:
                kwargs["since_seconds"] = since_seconds
            elif since_time:
                kwargs["since_time"] = since_time
            
            if tail_lines:
                kwargs["tail_lines"] = tail_lines
            
            # Get logs
            logs = self.core_v1_api.read_namespaced_pod_log(**kwargs)
            
            logger.info(
                "Retrieved pod logs",
                pod_name=pod_name,
                namespace=namespace,
                container=container,
                log_length=len(logs)
            )
            
            return logs
            
        except Exception as e:
            logger.error(
                "Failed to get pod logs",
                pod_name=pod_name,
                namespace=namespace,
                container=container,
                error=str(e)
            )
            raise
    
    async def search_pod_logs(
        self,
        query: str,
        namespace: Optional[str] = None,
        pod_name_pattern: Optional[str] = None,
        since_hours: int = 24,
        max_pods: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for specific content within pod logs.
        
        Args:
            query: Search query string
            namespace: Kubernetes namespace (uses default if None)
            pod_name_pattern: Regex pattern to filter pod names
            since_hours: Hours back to search logs
            max_pods: Maximum number of pods to search
            
        Returns:
            List of search results with pod info and matching lines
        """
        try:
            namespace = namespace or self.config.kubernetes_namespace
            
            # Get pods
            pods = await self.get_pods(namespace=namespace)
            
            # Filter pods by name pattern if specified
            if pod_name_pattern:
                pattern = re.compile(pod_name_pattern)
                pods = [pod for pod in pods if pattern.search(pod["name"])]
            
            # Limit number of pods to search
            pods = pods[:max_pods]
            
            results = []
            since_time = datetime.utcnow() - timedelta(hours=since_hours)
            
            for pod in pods:
                try:
                    # Get logs for this pod
                    logs = await self.get_pod_logs(
                        pod_name=pod["name"],
                        namespace=namespace,
                        since_time=since_time
                    )
                    
                    # Search for query in logs
                    matching_lines = []
                    lines = logs.split('\n')
                    
                    for line_num, line in enumerate(lines, 1):
                        if query.lower() in line.lower():
                            matching_lines.append({
                                "line_number": line_num,
                                "content": line.strip(),
                                "timestamp": self._extract_timestamp_from_line(line)
                            })
                            
                            if len(matching_lines) >= 20:  # Limit matches per pod
                                break
                    
                    if matching_lines:
                        result = {
                            "pod": pod,
                            "matches": matching_lines,
                            "total_matches": len(matching_lines)
                        }
                        results.append(result)
                
                except Exception as e:
                    logger.warning(
                        "Failed to search logs in pod",
                        pod_name=pod["name"],
                        error=str(e)
                    )
                    continue
            
            logger.info(
                "Pod log search completed",
                query=query,
                pods_searched=len(pods),
                results_found=len(results)
            )
            
            return results
            
        except Exception as e:
            logger.error("Failed to search pod logs", query=query, error=str(e))
            raise
    
    async def filter_logs_by_level(
        self,
        logs: str,
        log_levels: List[str] = None
    ) -> str:
        """
        Filter logs by log level.
        
        Args:
            logs: Raw log content
            log_levels: List of log levels to include (ERROR, WARN, INFO, DEBUG)
            
        Returns:
            Filtered logs as string
        """
        if not log_levels:
            log_levels = ["ERROR", "WARN", "INFO"]
        
        # Convert to uppercase for comparison
        log_levels = [level.upper() for level in log_levels]
        
        filtered_lines = []
        lines = logs.split('\n')
        
        for line in lines:
            # Check if line contains any of the specified log levels
            line_upper = line.upper()
            for level in log_levels:
                if level in line_upper:
                    filtered_lines.append(line)
                    break
        
        filtered_logs = '\n'.join(filtered_lines)
        
        logger.info(
            "Filtered logs by level",
            original_lines=len(lines),
            filtered_lines=len(filtered_lines),
            levels=log_levels
        )
        
        return filtered_logs
    
    async def filter_logs_by_time_range(
        self,
        logs: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> str:
        """
        Filter logs by time range.
        
        Args:
            logs: Raw log content
            start_time: Start time for filtering
            end_time: End time for filtering
            
        Returns:
            Filtered logs as string
        """
        if not start_time and not end_time:
            return logs
        
        filtered_lines = []
        lines = logs.split('\n')
        
        for line in lines:
            timestamp = self._extract_timestamp_from_line(line)
            if not timestamp:
                # Include lines without timestamps
                filtered_lines.append(line)
                continue
            
            try:
                log_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                
                # Check time range
                if start_time and log_time < start_time:
                    continue
                if end_time and log_time > end_time:
                    continue
                
                filtered_lines.append(line)
                
            except ValueError:
                # Include lines with unparseable timestamps
                filtered_lines.append(line)
                continue
        
        filtered_logs = '\n'.join(filtered_lines)
        
        logger.info(
            "Filtered logs by time range",
            original_lines=len(lines),
            filtered_lines=len(filtered_lines),
            start_time=start_time.isoformat() if start_time else None,
            end_time=end_time.isoformat() if end_time else None
        )
        
        return filtered_logs
    
    def _extract_timestamp_from_line(self, line: str) -> Optional[str]:
        """
        Extract timestamp from a log line.
        Supports various timestamp formats commonly used in Kubernetes logs.
        """
        try:
            # Common timestamp patterns in Kubernetes logs
            patterns = [
                # ISO format with timezone: 2023-12-01T10:30:00.123Z
                r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{3})?Z',
                # ISO format: 2023-12-01T10:30:00
                r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}',
                # Date format: 2023-12-01 10:30:00
                r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}',
                # Syslog format: Dec 01 10:30:00
                r'[A-Za-z]{3} \d{2} \d{2}:\d{2}:\d{2}',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, line)
                if match:
                    return match.group()
            
            return None
            
        except Exception:
            return None
    
    async def get_pod_events(
        self,
        pod_name: str,
        namespace: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get events related to a specific pod.
        
        Args:
            pod_name: Name of the pod
            namespace: Kubernetes namespace (uses default if None)
            
        Returns:
            List of event dictionaries
        """
        try:
            namespace = namespace or self.config.kubernetes_namespace
            
            # Get events related to the pod
            events = self.core_v1_api.list_namespaced_event(
                namespace=namespace,
                field_selector=f"involvedObject.name={pod_name}"
            )
            
            event_list = []
            for event in events.items:
                event_info = {
                    "type": event.type,
                    "reason": event.reason,
                    "message": event.message,
                    "first_timestamp": event.first_timestamp.isoformat() if event.first_timestamp else None,
                    "last_timestamp": event.last_timestamp.isoformat() if event.last_timestamp else None,
                    "count": event.count,
                    "source": event.source.component if event.source else None
                }
                event_list.append(event_info)
            
            logger.info(
                "Retrieved pod events",
                pod_name=pod_name,
                namespace=namespace,
                event_count=len(event_list)
            )
            
            return event_list
            
        except Exception as e:
            logger.error(
                "Failed to get pod events",
                pod_name=pod_name,
                namespace=namespace,
                error=str(e)
            )
            raise
    
    async def get_cluster_statistics(self) -> Dict[str, Any]:
        """
        Get general statistics about the Kubernetes cluster.
        
        Returns:
            Dictionary with cluster statistics
        """
        try:
            # Get nodes
            nodes = self.core_v1_api.list_node()
            
            # Get all pods across all namespaces
            all_pods = self.core_v1_api.list_pod_for_all_namespaces()
            
            # Get namespaces
            namespaces = self.core_v1_api.list_namespace()
            
            # Calculate statistics
            running_pods = sum(1 for pod in all_pods.items if pod.status.phase == "Running")
            failed_pods = sum(1 for pod in all_pods.items if pod.status.phase == "Failed")
            pending_pods = sum(1 for pod in all_pods.items if pod.status.phase == "Pending")
            
            stats = {
                "nodes": {
                    "total": len(nodes.items),
                    "ready": sum(1 for node in nodes.items 
                               if any(condition.type == "Ready" and condition.status == "True" 
                                     for condition in node.status.conditions))
                },
                "pods": {
                    "total": len(all_pods.items),
                    "running": running_pods,
                    "failed": failed_pods,
                    "pending": pending_pods
                },
                "namespaces": {
                    "total": len(namespaces.items)
                },
                "query_time": datetime.utcnow().isoformat()
            }
            
            logger.info("Generated cluster statistics", stats=stats)
            return stats
            
        except Exception as e:
            logger.error("Failed to get cluster statistics", error=str(e))
            raise


# Global service instance
_k8s_service = None


def get_k8s_service() -> K8sLogService:
    """Get the global K8s service instance."""
    global _k8s_service
    if _k8s_service is None:
        _k8s_service = K8sLogService()
    return _k8s_service 