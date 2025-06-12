"""
Trade Data Provider
Provides trade and portfolio data for the dashboard by fetching it from the FastAPI backend.
"""
import requests
from typing import Dict, Any, List

class TradeDataProvider:
    """
    Provides trade and portfolio data by making requests to the Tron Dashboard API backend.
    """
    
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        self.api_base_url = api_base_url

    def _get(self, endpoint: str) -> Dict[str, Any]:
        """Helper function to make a GET request to the backend."""
        try:
            response = requests.get(f"{self.api_base_url}{endpoint}", timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {'data_status': f"API connection error: {e}"}

    def _get_list(self, endpoint: str) -> List[Dict[str, Any]]:
        """Helper function to make a GET request to the backend for a list response."""
        try:
            response = requests.get(f"{self.api_base_url}{endpoint}", timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return [{'error': f"API connection error: {e}"}]

    def get_daily_summary(self) -> Dict[str, Any]:
        """Get daily trading summary from the backend."""
        return self._get("/api/trade/summary/daily")
    
    def get_live_positions(self) -> List[Dict[str, Any]]:
        """Get current live positions from the backend."""
        return self._get_list("/api/trade/positions/live")

    def get_recent_trades(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent trades from the backend."""
        return self._get_list(f"/api/trade/trades/recent?limit={limit}")

    # The methods below can be removed or adapted as all logic is now backend-driven.
    # We provide default values to ensure the UI doesn't break during transition.
    
    def get_pnl_timeline(self) -> List[Dict[str, Any]]:
        return []

    def get_portfolio_allocation(self) -> List[Dict[str, Any]]:
        return []

    def get_strategy_performance_summary(self) -> List[Dict[str, Any]]:
        return []

    def get_active_strategies(self) -> List[str]:
        """Get list of active strategies"""
        # This method is no longer used in the new implementation
        return []

    def get_active_symbols(self) -> List[str]:
        """Get list of active symbols"""
        # This method is no longer used in the new implementation
        return []

    def get_positions_summary(self) -> Dict[str, Any]:
        """Get positions summary metrics"""
        # This method is no longer used in the new implementation
        return {}

    def get_active_trades(self, filters: Dict[str, str] = None) -> List[Dict[str, Any]]:
        """Get active trades with optional filters"""
        # This method is no longer used in the new implementation
        return []

    def _get_current_price(self, symbol: str) -> Dict[str, Any]:
        """Get current market price for a symbol"""
        # This method is no longer used in the new implementation
        return {}

    def _calculate_duration(self, entry_time: str) -> str:
        """Calculate duration since entry"""
        # This method is no longer used in the new implementation
        return ""

    def _calculate_pnl_change_pct(self, current_pnl: float) -> float:
        """Calculate P&L change percentage (would need historical data)"""
        # This method is no longer used in the new implementation
        return 0

    def _get_default_summary(self) -> Dict[str, Any]:
        """Get default summary when no data is available"""
        # This method is no longer used in the new implementation
        return {}

    # Additional methods for live trades page
    def get_position_pnl_timeline(self) -> List[Dict[str, Any]]:
        """Get real-time P&L timeline for positions"""
        # This method is no longer used in the new implementation
        return []

    def get_trade_events_timeline(self) -> List[Dict[str, Any]]:
        """Get timeline of trade events"""
        # This method is no longer used in the new implementation
        return []

    def get_real_time_risk_metrics(self) -> Dict[str, Any]:
        """Get real-time risk metrics"""
        # This method is no longer used in the new implementation
        return {}

    # Action methods
    def close_all_positions(self) -> Dict[str, Any]:
        """Close all active positions"""
        # This method is no longer used in the new implementation
        return {}

    def move_all_to_breakeven(self) -> Dict[str, Any]:
        """Move all positions to breakeven"""
        # This method is no longer used in the new implementation
        return {}

    def activate_trailing_stop(self) -> Dict[str, Any]:
        """Activate trailing stop for all positions"""
        # This method is no longer used in the new implementation
        return {}

    def partial_exit_all(self, exit_percentage: int) -> Dict[str, Any]:
        """Partial exit of all positions"""
        # This method is no longer used in the new implementation
        return {}

    def refresh_all_prices(self) -> Dict[str, Any]:
        """Refresh all position prices"""
        # This method is no longer used in the new implementation
        return {}

    # Mock data generation functions are now removed.
    # The system will rely on real data or show clear "No data" states.
    
    # Mock data removed - system now shows clear "No data" status when no real trading data is available 