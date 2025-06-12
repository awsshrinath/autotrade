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
            # Return a structured error that the UI can understand
            return {'status': 'error', 'message': f"API connection error: {e}"}

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