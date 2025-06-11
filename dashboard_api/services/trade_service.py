"""
Service layer for handling trade and portfolio data.
"""
import asyncio
from datetime import datetime
from typing import Dict, List, Any

# Assuming necessary components are available in the python path
from runner.firestore_client import FirestoreClient
from runner.capital.portfolio_manager import create_portfolio_manager, PortfolioManager
from runner.kiteconnect_manager import KiteConnectManager
from runner.logger import Logger

class TradeService:
    """
    Service to provide trade and portfolio data.
    """
    def __init__(self, logger: Logger, firestore: FirestoreClient, portfolio_manager: PortfolioManager, kite_manager: KiteConnectManager):
        self.logger = logger
        self.firestore = firestore
        self.portfolio_manager = portfolio_manager
        self.kite_manager = kite_manager
        self.kite = self.kite_manager.get_kite_client() if self.kite_manager else None

    async def get_daily_summary(self) -> Dict[str, Any]:
        """Get daily trading summary."""
        # This is a simplified version of the original logic
        try:
            trades = await self.get_recent_trades(limit=100) # Fetch recent trades
            if not trades:
                return {"data_status": "No trading data found."}

            total_pnl = sum(trade.get('pnl', 0) for trade in trades if trade.get('status') != 'open')
            active_trades = len([t for t in trades if t.get('status') == 'open'])
            return {
                'total_pnl': total_pnl,
                'active_trades': active_trades,
                'total_trades': len(trades)
            }
        except Exception as e:
            self.logger.log_event(f"Error in get_daily_summary: {e}")
            return {"error": str(e)}

    async def get_live_positions(self) -> List[Dict[str, Any]]:
        """Get current live positions."""
        # Simplified logic
        if not self.kite:
            return []
        try:
            positions = self.kite.positions().get('net', [])
            return positions
        except Exception as e:
            self.logger.log_event(f"Error fetching live positions: {e}")
            return []

    async def get_recent_trades(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent trades from Firestore."""
        try:
            trades_collection = self.firestore.db.collection('gpt_runner_trades')
            docs = trades_collection.order_by('timestamp', direction='DESCENDING').limit(limit).stream()
            trades = []
            for doc in docs:
                trade_data = doc.to_dict()
                trade_data['id'] = doc.id
                trades.append(trade_data)
            return trades
        except Exception as e:
            self.logger.log_event(f"Error fetching recent trades: {e}")
            return []


# Dependency Injection
_trade_service_instance = None

def get_trade_service():
    global _trade_service_instance
    if _trade_service_instance is None:
        from .system_service import get_logger
        
        # This part is tricky because these clients have their own dependencies.
        # In a production system, a more robust DI framework would be used.
        logger = get_logger()
        try:
            firestore_client = FirestoreClient()
            portfolio_manager = create_portfolio_manager(paper_trade=True)
            kite_manager = KiteConnectManager(logger)
        except Exception as e:
            logger.log_event(f"FATAL: Failed to initialize clients for TradeService: {e}")
            # Return a non-functional service to avoid crashing the whole API
            return None

        _trade_service_instance = TradeService(
            logger=logger,
            firestore=firestore_client,
            portfolio_manager=portfolio_manager,
            kite_manager=kite_manager
        )
    return _trade_service_instance 