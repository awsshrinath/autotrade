"""
Cognitive Data Provider
Provides cognitive insights data for the dashboard by fetching it from the FastAPI backend.
"""
import requests
from typing import Dict, Any, List

class CognitiveDataProvider:
    """
    Provides cognitive insights data by making requests to the Tron Dashboard API backend.
    """
    
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        self.api_base_url = api_base_url

    def _get(self, endpoint: str) -> Dict[str, Any]:
        """Helper function to make a GET request to the backend."""
        try:
            response = requests.get(f"{self.api_base_url}{endpoint}", timeout=15)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {'status': 'error', 'message': f"API connection error: {e}"}

    def _get_list(self, endpoint: str) -> List[Dict[str, Any]]:
        """Helper function to make a GET request to the backend for a list response."""
        try:
            response = requests.get(f"{self.api_base_url}{endpoint}", timeout=15)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return [{'error': f"API connection error: {e}"}]

    def get_cognitive_summary(self) -> Dict[str, Any]:
        """Get comprehensive cognitive system summary from the backend."""
        return self._get("/api/cognitive/summary")
    
    def get_cognitive_health(self) -> Dict[str, Any]:
        """Get cognitive system health from the backend."""
        return self._get("/api/cognitive/health")

    def get_trade_insights(self) -> List[Dict[str, Any]]:
        """Get AI-powered trade insights from the backend."""
        return self._get_list("/api/cognitive/insights/trade")

    # The methods below can be removed or adapted as all logic is now backend-driven.
    # We provide default values to ensure the UI doesn't break during transition.
    
    def get_market_sentiment(self) -> Dict[str, Any]:
        return {'status': 'unavailable', 'message': 'Handled by backend.'}

    def get_strategy_recommendations(self) -> List[Dict[str, Any]]:
        return []

    def get_risk_predictions(self) -> List[Dict[str, Any]]:
        return []

    def get_performance_insights(self) -> Dict[str, Any]:
        return {'status': 'unavailable', 'message': 'Handled by backend.'}

    def get_recent_thoughts(self, limit: int = 50):
        return self._get(f"cognitive/thoughts/recent?limit={limit}") 