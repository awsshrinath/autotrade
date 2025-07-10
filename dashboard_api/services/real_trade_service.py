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
        """Get daily trading summary from Firestore in format expected by frontend."""
        try:
            today_str = datetime.now().strftime("%Y-%m-%d")
            summaries = self.db_logger.get_daily_summaries(date=today_str)
            
            # Aggregate data from all bots/strategies for frontend consumption
            total_pnl = 0
            total_trades = 0
            winning_trades = 0
            
            # Process summaries if they exist
            if summaries and isinstance(summaries, dict):
                for bot_data in summaries.values():
                    if isinstance(bot_data, dict):
                        total_pnl += bot_data.get('total_pnl', 0)
                        trades = bot_data.get('total_trades', 0)
                        total_trades += trades
                        winning_trades += bot_data.get('winning_trades', 0)
            
            # Calculate win rate
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            # Return structure expected by frontend
            return {
                "total_pnl": total_pnl,
                "win_rate": round(win_rate, 1),
                "total_trades": total_trades,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            # Return fallback data structure for frontend
            return {
                "total_pnl": 0,
                "win_rate": 0,
                "total_trades": 0,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

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
        Get position summary for risk analysis from Firestore in format expected by frontend.
        """
        try:
            positions = self.db_logger.get_live_trades(status="open")
            
            total_exposure = 0
            unrealized_pnl = 0
            total_margin_used = 0
            
            # Calculate aggregated metrics
            for position in positions:
                if isinstance(position, dict):
                    total_exposure += position.get('market_value', 0)
                    unrealized_pnl += position.get('pnl', 0)
                    # Estimate margin used (typically 20% of market value for equity)
                    total_margin_used += position.get('margin_used', position.get('market_value', 0) * 0.2)
            
            # Calculate margin usage percentage (assuming total margin available is 500k)
            total_margin_available = 500000  # TODO: Get from actual account data
            margin_usage_pct = (total_margin_used / total_margin_available * 100) if total_margin_available > 0 else 0
            
            # Return structure expected by frontend
            return {
                'total_exposure': round(total_exposure, 2),
                'margin_usage_pct': round(margin_usage_pct, 1),
                'unrealized_pnl': round(unrealized_pnl, 2),
                'open_positions_count': len(positions),
                'total_margin_used': round(total_margin_used, 2),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            # Return fallback data structure for frontend
            return {
                'total_exposure': 0,
                'margin_usage_pct': 0,
                'unrealized_pnl': 0,
                'open_positions_count': 0,
                'total_margin_used': 0,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    async def get_summary_strategy(self) -> Dict[str, Any]:
        """
        Get strategy performance summary from Firestore in format expected by frontend.
        """
        try:
            # Get today's summaries to analyze strategy performance
            today_str = datetime.now().strftime("%Y-%m-%d")
            summaries = self.db_logger.get_daily_summaries(date=today_str)
            
            strategy_stats = {}
            total_strategies = 0
            
            # Process summaries to extract strategy performance
            if summaries and isinstance(summaries, dict):
                for bot_id, bot_data in summaries.items():
                    if isinstance(bot_data, dict):
                        strategy_name = bot_data.get('strategy', bot_id)
                        if strategy_name not in strategy_stats:
                            strategy_stats[strategy_name] = {
                                'pnl': 0,
                                'trades': 0,
                                'wins': 0
                            }
                        
                        strategy_stats[strategy_name]['pnl'] += bot_data.get('total_pnl', 0)
                        strategy_stats[strategy_name]['trades'] += bot_data.get('total_trades', 0)
                        strategy_stats[strategy_name]['wins'] += bot_data.get('winning_trades', 0)
                        total_strategies += 1
            
            # Find top performing strategy
            top_strategy_name = "None"
            if strategy_stats:
                top_strategy_name = max(strategy_stats.keys(), 
                                      key=lambda k: strategy_stats[k]['pnl'])
            
            # Return structure expected by frontend
            return {
                'top_strategy': {
                    'name': top_strategy_name
                },
                'active_strategies': len(strategy_stats),
                'total_bots': total_strategies,
                'strategy_details': strategy_stats,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            # Return fallback data structure for frontend
            return {
                'top_strategy': {
                    'name': 'Error'
                },
                'active_strategies': 0,
                'total_bots': 0,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

# Dependency Injection
_trade_service_instance = None

def get_trade_service():
    global _trade_service_instance
    if _trade_service_instance is None:
        _trade_service_instance = RealTradeService()
    return _trade_service_instance 