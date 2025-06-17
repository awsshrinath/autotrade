"""
System Data Provider
Provides system health and monitoring data for the dashboard by fetching it from the new FastAPI backend.
"""
import requests
from datetime import datetime
from typing import Dict, Any, List

class SystemDataProvider:
    """
    Provides system health data by making requests to the Tron Dashboard API backend.
    """
    
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        self.api_base_url = api_base_url

    def _get(self, endpoint: str) -> Dict[str, Any]:
        """Helper function to make a GET request to the backend."""
        try:
            response = requests.get(f"{self.api_base_url}{endpoint}", timeout=10)
            response.raise_for_status()  # Raise an exception for bad status codes
            return response.json()
        except requests.exceptions.RequestException as e:
            # Fallback to local log reading when API is not available
            return self._get_local_fallback_data(endpoint, str(e))

    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health summary from the backend."""
        return self._get("/api/system/health")

    def get_system_status(self) -> Dict[str, Any]:
        """Get detailed system status from the backend."""
        return self._get("/api/system/status")

    def get_health_checks(self) -> List[Dict[str, Any]]:
        """Get detailed health check results from the backend."""
        # Assuming the backend's /status endpoint returns a 'checks' list
        status_data = self._get("/api/system/status")
        return status_data.get('checks', [])

    def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system resource metrics from the backend."""
        return self._get("/api/system/metrics")

    def get_recent_system_logs(self, limit: int = 100):
        return self._get(f"system/logs/recent?limit={limit}")

    # The methods below are now either fetched from the backend or are no longer the
    # responsibility of the frontend data provider. They can be removed or adapted.
    # For now, we'll provide default/mock data to avoid breaking the UI.

    def get_market_overview(self) -> Dict[str, Any]:
        """Mock market overview data."""
        return {'status': 'unavailable', 'message': 'This is now handled by the backend.'}

    def get_service_status(self) -> Dict[str, Any]:
        """Mock service status."""
        return {'status': 'unavailable', 'message': 'This is now handled by the backend.'}

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Mock performance metrics."""
        return {'pnl': 0, 'trades': 0, 'win_rate': 0}

    def get_alerts(self) -> List[Dict[str, Any]]:
        """Mock alerts."""
        return []

    def get_log_summary(self) -> Dict[str, Any]:
        """Mock log summary."""
        return {'total_logs': 0, 'error_count': 0}
    
    def _get_local_fallback_data(self, endpoint: str, error_msg: str) -> Dict[str, Any]:
        """Fallback to local data sources when API is unavailable"""
        import os
        import json
        from datetime import datetime
        
        # Try to read from local log files when API is down
        if "/api/system/health" in endpoint:
            return self._get_local_system_health()
        elif "/api/system/status" in endpoint:
            return self._get_local_system_status()
        elif "/api/system/metrics" in endpoint:
            return self._get_local_system_metrics()
        else:
            return {
                'status': 'error', 
                'message': f"API connection error: {error_msg}",
                'fallback_mode': True,
                'data_source': 'local_files'
            }
    
    def _get_local_system_health(self) -> Dict[str, Any]:
        """Get system health from local sources when API is down"""
        try:
            # Check if local log files exist
            log_dir = "logs"
            today = datetime.now().strftime("%Y-%m-%d")
            
            health_status = "degraded"  # Default to degraded when API is down
            
            # Check for recent log files
            if os.path.exists(f"{log_dir}/{today}"):
                recent_logs = os.listdir(f"{log_dir}/{today}")
                if recent_logs:
                    health_status = "limited"  # Some functionality available
            
            return {
                'status': health_status,
                'message': 'Running in offline mode - API unavailable',
                'fallback_mode': True,
                'local_logs_available': os.path.exists(log_dir),
                'last_check': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Local fallback failed: {str(e)}',
                'fallback_mode': True
            }
    
    def _get_local_system_status(self) -> Dict[str, Any]:
        """Get system status from local sources"""
        try:
            return {
                'overall_status': 'degraded',
                'backend_service': 'offline',
                'database_connection': 'unknown',
                'api_endpoints': 'unavailable',
                'fallback_mode': True,
                'message': 'API service offline - using local data',
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'overall_status': 'error',
                'message': f'Local status check failed: {str(e)}',
                'fallback_mode': True
            }
    
    def _get_local_system_metrics(self) -> Dict[str, Any]:
        """Get basic system metrics locally"""
        try:
            import psutil
            memory = psutil.virtual_memory()
            return {
                'cpu_usage': psutil.cpu_percent(interval=None),
                'memory_usage': memory.percent,
                'memory_available_gb': round(memory.available / (1024**3), 2),
                'fallback_mode': True,
                'timestamp': datetime.now().isoformat(),
                'data_source': 'local_psutil'
            }
        except ImportError:
            return {
                'error': 'psutil not available for local metrics',
                'fallback_mode': True,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'error': f'Local metrics failed: {str(e)}',
                'fallback_mode': True
            } 