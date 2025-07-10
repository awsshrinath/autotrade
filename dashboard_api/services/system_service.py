"""
This file will contain the business logic for the system health endpoints.
We will migrate the logic from the old SystemDataProvider here.
"""
import asyncio
from datetime import datetime
from typing import Dict, Any, List
import psutil
import logging
from .log_service import get_log_service

# Simple logger for the backend service
class SimpleLogger:
    def __init__(self):
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def log_event(self, message: str):
        self.logger.info(message)

class SystemService:
    """
    Service layer for handling system health and monitoring logic.
    """
    def __init__(self):
        self.logger = SimpleLogger()
        self.log_service = get_log_service()

    async def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health summary with components array for frontend."""
        try:
            status_data = await self.get_system_status()
            
            # Get log service status to include in health check
            log_status = self.get_log_service_status()
            
            # Create components array that frontend expects
            components = [
                {
                    "name": "Backend Service",
                    "status": "active" if status_data.get('backend_service') == 'running' else "inactive"
                },
                {
                    "name": "Database Connection",
                    "status": "active" if status_data.get('database_connection') == 'connected' else "inactive"
                },
                {
                    "name": "API Endpoints",
                    "status": "active" if status_data.get('api_endpoints') == 'available' else "inactive"
                },
                {
                    "name": "Memory Manager",
                    "status": "active" if status_data.get('metrics', {}).get('memory_usage', 0) < 85 else "degraded"
                },
                {
                    "name": "Cognitive System",
                    "status": "active"  # TODO: Add real cognitive system check
                },
                {
                    "name": "GCS Logging",
                    "status": "active" if log_status.get('gcs_client') == 'initialized' else "degraded"
                },
                {
                    "name": "Firestore Logging",
                    "status": "active" if log_status.get('firestore_client') == 'initialized' else "degraded"
                },
                {
                    "name": "Kubernetes API",
                    "status": "active" if log_status.get('k8s_client') == 'initialized' else "degraded"
                }
            ]
            
            return {
                'status': status_data.get('overall_status', 'unknown'),
                'uptime_hours': self._get_uptime_hours(),
                'last_check': datetime.now().isoformat(),
                'components': components,
                'log_service_status': log_status,
                **status_data
            }
        except Exception as e:
            self.logger.log_event(f"Error getting system health: {e}")
            return {
                'status': 'error', 
                'message': str(e),
                'components': [
                    {"name": "System Check", "status": "error"}
                ]
            }

    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        try:
            # Simplified status check for backend service
            metrics = self.get_system_metrics()
            
            # Determine overall status based on resource usage
            overall_status = 'healthy'
            if metrics.get('cpu_usage', 0) > 80 or metrics.get('memory_usage', 0) > 80:
                overall_status = 'degraded'
            
            return {
                'overall_status': overall_status,
                'backend_service': 'running',
                'database_connection': 'connected',  # TODO: Add actual DB check
                'api_endpoints': 'available',
                'metrics': metrics,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.log_event(f"Error getting system status: {e}")
            return {'overall_status': 'unknown', 'message': str(e)}
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system resource metrics."""
        try:
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            cpu_usage = psutil.cpu_percent(interval=None)
            
            return {
                # Legacy field names for compatibility
                'cpu_usage': cpu_usage,
                'memory_usage': memory.percent,
                'disk_usage': disk.percent,
                'memory_available_gb': round(memory.available / (1024**3), 2),
                'network_connections': len(psutil.net_connections()),
                'timestamp': datetime.now().isoformat(),
                
                # Frontend expected field names
                'cpu_usage_pct': cpu_usage,
                'memory_usage_pct': memory.percent,
                'disk_usage_pct': disk.percent,
                'api_response_time_ms': 145  # Mock response time in milliseconds
            }
        except Exception as e:
            self.logger.log_event(f"Error getting system metrics: {e}")
            return {
                'error': str(e),
                'cpu_usage_pct': 0,
                'memory_usage_pct': 0,
                'disk_usage_pct': 0,
                'api_response_time_ms': 0
            }

    def _get_uptime_hours(self) -> float:
        """Calculate system uptime."""
        try:
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.now() - boot_time
            return round(uptime.total_seconds() / 3600, 2)
        except:
            return 0

    # New log service integration methods
    def get_log_service_status(self) -> Dict[str, Any]:
        """Get the status of log service connections."""
        try:
            status = self.log_service.get_status()
            return {
                **status,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.log_event(f"Error getting log service status: {e}")
            return {
                'error': str(e),
                'gcs_client': 'error',
                'firestore_client': 'error',
                'k8s_client': 'error',
                'timestamp': datetime.now().isoformat()
            }

    async def get_gcs_log_files(self, prefix: str = None, limit: int = 100,
                               date_from: str = None, date_to: str = None,
                               pattern: str = None) -> List[str]:
        """Get list of GCS log files with advanced filtering."""
        try:
            return await self.log_service.list_gcs_log_files(
                prefix=prefix, 
                limit=limit,
                date_from=date_from,
                date_to=date_to,
                pattern=pattern
            )
        except Exception as e:
            self.logger.log_event(f"Error retrieving GCS log files: {e}")
            return [f"Error: {e}"]

    async def get_gcs_file_content(self, file_path: str, search_term: str = None,
                                  log_level: str = None, lines_limit: int = None) -> Dict[str, Any]:
        """Get content of a specific GCS log file with filtering."""
        try:
            return await self.log_service.get_gcs_log_content(
                file_path=file_path,
                search_term=search_term,
                log_level=log_level,
                lines_limit=lines_limit
            )
        except Exception as e:
            self.logger.log_event(f"Error retrieving GCS file content: {e}")
            return {"error": str(e)}

    async def get_firestore_logs(self, limit: int = 100, component: str = None,
                                log_level: str = None, date_from: str = None,
                                date_to: str = None) -> List[Dict[str, Any]]:
        """Get recent Firestore logs with advanced filtering."""
        try:
            return await self.log_service.get_firestore_logs(
                limit=limit,
                component=component,
                log_level=log_level,
                date_from=date_from,
                date_to=date_to
            )
        except Exception as e:
            self.logger.log_event(f"Error retrieving Firestore logs: {e}")
            return [{"error": str(e)}]

    async def get_k8s_pods(self) -> Dict[str, Any]:
        """Get list of Kubernetes pods."""
        try:
            pods = await self.log_service.list_k8s_pods()
            return {
                'pods': pods,
                'count': len(pods),
                'namespace': self.log_service.get_status().get('k8s_namespace'),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.log_event(f"Error getting K8s pods: {e}")
            return {
                'error': str(e),
                'pods': [],
                'count': 0,
                'timestamp': datetime.now().isoformat()
            }

    async def get_k8s_pod_logs(self, pod_name: str, lines: int = 100,
                              since_seconds: int = None, follow: bool = False,
                              search_term: str = None, log_level: str = None) -> List[str]:
        """Get Kubernetes pod logs with filtering."""
        try:
            return await self.log_service.get_k8s_pod_logs(
                pod_name=pod_name,
                limit=lines,
                since_seconds=since_seconds,
                follow=follow,
                search_term=search_term,
                log_level=log_level
            )
        except Exception as e:
            self.logger.log_event(f"Error retrieving K8s pod logs: {e}")
            return [f"Error: {e}"]

    async def get_gcs_log_files_paginated(self, prefix: str = None, page_token: str = None,
                                         page_size: int = 50, date_from: str = None, 
                                         date_to: str = None, pattern: str = None) -> Dict[str, Any]:
        """Get paginated list of GCS log files with advanced filtering."""
        try:
            return await self.log_service.list_gcs_log_files_paginated(
                prefix=prefix,
                page_token=page_token,
                page_size=page_size,
                date_from=date_from,
                date_to=date_to,
                pattern=pattern
            )
        except Exception as e:
            self.logger.log_event(f"Error retrieving paginated GCS log files: {e}")
            return {"error": str(e), "files": [], "next_page_token": None}

    async def get_compressed_log_content(self, file_path: str, search_term: str = None,
                                        log_level: str = None, lines_limit: int = 1000) -> Dict[str, Any]:
        """Get compressed GCS log file content with filtering."""
        try:
            return await self.log_service.get_compressed_log_content(
                file_path=file_path,
                search_term=search_term,
                log_level=log_level,
                lines_limit=lines_limit
            )
        except Exception as e:
            self.logger.log_event(f"Error retrieving compressed GCS file content: {e}")
            return {"error": str(e)}

    async def stream_gcs_log_content(self, file_path: str, start_byte: int = 0, 
                                    chunk_size: int = None):
        """Stream GCS log file content in chunks."""
        try:
            async for chunk in self.log_service.stream_gcs_log_content(file_path, start_byte, chunk_size):
                yield chunk
        except Exception as e:
            self.logger.log_event(f"Error streaming GCS file content: {e}")
            yield f"Error: {e}".encode()

    async def get_firestore_logs_batch(self, limit: int = 100, component: str = None,
                                      log_level: str = None, date_from: str = None,
                                      date_to: str = None, cursor: str = None) -> Dict[str, Any]:
        """Get Firestore logs with batching and cursor-based pagination."""
        try:
            return await self.log_service.get_firestore_logs_batch(
                limit=limit,
                component=component,
                log_level=log_level,
                date_from=date_from,
                date_to=date_to,
                cursor=cursor
            )
        except Exception as e:
            self.logger.log_event(f"Error retrieving batched Firestore logs: {e}")
            return {"error": str(e), "logs": [], "next_cursor": None}

# Dependency Injection setup
_system_service_instance = None

def get_system_service():
    global _system_service_instance
    if _system_service_instance is None:
        _system_service_instance = SystemService()
    return _system_service_instance 