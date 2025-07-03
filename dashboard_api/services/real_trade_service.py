"""
Service to provide real trade and portfolio data by interacting
with the core TradingLogger and its underlying Firestore/GCS clients.
"""
from runner.enhanced_logging.core_logger import create_trading_logger
from typing import Dict, List, Any
import os
from datetime import datetime

class RealTradeService:
    """
    Service to provide real-time and historical trading data.
    """
    def __init__(self):
        self.project_id = os.getenv("GCP_PROJECT_ID")
        # The TradingLogger gives us access to the configured Firestore and GCS loggers
        self.trading_logger = create_trading_logger(
            session_id="dashboard_api_session",
            bot_type="dashboard_api",
            project_id=self.project_id,
            enable_gcs=False # No need for GCS in the dashboard API
        )
        # We will directly use the firestore_logger for queries
        self.db_logger = self.trading_logger.firestore_logger

    async def get_daily_summary(self) -> Dict[str, Any]:
        """Get daily trading summary from Firestore."""
        today_str = datetime.now().strftime("%Y-%m-%d")
        summaries = self.db_logger.get_daily_summaries(date=today_str)
        # This will return a dict of summaries per bot, we can aggregate them here if needed
        # For now, let's just return the raw dictionary.
        return summaries

    async def get_live_positions(self) -> List[Dict[str, Any]]:
        """Get current live positions (open trades) from Firestore."""
        return self.db_logger.get_live_trades(status="open")

    async def get_recent_trades(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent trades from Firestore."""
        # Note: The firestore_logger does not have a get_recent_trades method.
        # We are using get_live_trades as a substitute.
        # A more advanced implementation would query the trades_by_date collection.
        return self.db_logger.get_live_trades(limit=limit)

    async def get_summary_positions(self) -> Dict[str, Any]:
        """
        Get position summary for risk analysis from Firestore.
        This requires aggregating data from live positions.
        """
        positions = self.db_logger.get_live_trades(status="open")
        total_exposure = sum(p.get('market_value', 0) for p in positions)
        unrealized_pnl = sum(p.get('pnl', 0) for p in positions)
        # Other metrics like margin usage would need to be calculated
        # or fetched from another source.
        return {
            'total_exposure': total_exposure,
            'unrealized_pnl': unrealized_pnl,
            'open_positions_count': len(positions),
            'timestamp': datetime.now().isoformat()
        }

    async def get_summary_strategy(self) -> Dict[str, Any]:
        """
        Get strategy performance summary from Firestore.
        This is a complex query and would likely require aggregating
        all of today's trades from the 'trades_by_date' collection.
        This is a placeholder for that logic.
        """
        # Placeholder implementation
        return {
            'message': 'Strategy summary requires aggregation from historical trade data.',
            'strategy_performance': []
        }

# Dependency Injection
_trade_service_instance = None

def get_trade_service():
    global _trade_service_instance
    if _trade_service_instance is None:
        _trade_service_instance = RealTradeService()
    return _trade_service_instance 