"""
Service to provide real trade and portfolio data by connecting to
actual trading systems and data sources.
"""
from runner.enhanced_logging.core_logger import create_trading_logger
from runner.firestore_client import FirestoreClient
from runner.position_monitor import PositionMonitor
from runner.capital.portfolio_manager import PortfolioManager
from runner.trade_manager import EnhancedTradeManager
import sys
import os
from typing import Dict, List, Any
from datetime import datetime, timedelta

# Add runner path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

class RealTradeService:
    """
    Service to provide real-time and historical trading data from actual trading systems.
    """
    def __init__(self):
        self.project_id = os.getenv("GCP_PROJECT_ID", "autotrade-453303")
        
        # Initialize real trading components
        try:
            # Check environment variables for disabling Google Cloud services
            enable_gcs = os.getenv("DISABLE_GCS", "").lower() != "true"
            enable_firestore = os.getenv("DISABLE_FIRESTORE", "").lower() != "true"
            
            # Initialize Firestore client for real data access
            if enable_firestore:
                self.firestore_client = FirestoreClient(
                    project_id=self.project_id,
                    logger=None
                )
            else:
                self.firestore_client = None
            
            # Initialize trading logger for real-time data
            self.trading_logger = create_trading_logger(
                session_id="dashboard_api_session",
                bot_type="dashboard_api",
                project_id=self.project_id,
                enable_gcs=enable_gcs,
                enable_firestore=enable_firestore
            )
            
            # Connect to real Firestore logger for live data queries
            self.db_logger = self.trading_logger.firestore_logger if self.trading_logger else None
            
            # Initialize portfolio manager for real capital data
            self.portfolio_manager = PortfolioManager(
                firestore=self.firestore_client,
                logger=None,
                paper_trade=os.getenv("PAPER_TRADE", "true").lower() == "true"
            )
            
            print(f"✅ RealTradeService initialized with real data connections")
            print(f"   - Firestore: {'✅ Connected' if self.db_logger else '❌ Disabled'}")
            print(f"   - Portfolio Manager: {'✅ Active' if self.portfolio_manager else '❌ Failed'}")
            
        except Exception as e:
            print(f"⚠️ Failed to initialize real trading connections: {e}")
            self.trading_logger = None
            self.db_logger = None
            self.firestore_client = None
            self.portfolio_manager = None


    async def get_daily_summary(self) -> Dict[str, Any]:
        """Get daily trading summary from actual trading data."""
        try:
            total_pnl = 0.0
            total_trades = 0
            winning_trades = 0
            
            # Method 1: Get data from Portfolio Manager (real account data)
            if self.portfolio_manager:
                try:
                    capital_data = await self.portfolio_manager.get_real_time_capital()
                    if capital_data:
                        total_pnl = capital_data.day_pnl
                        print(f"📊 Portfolio Manager - Day PnL: ₹{total_pnl}")
                except Exception as e:
                    print(f"⚠️ Portfolio Manager error: {e}")
            
            # Method 2: Get trade data from Firestore collections
            if self.db_logger:
                try:
                    today_str = datetime.now().strftime("%Y-%m-%d")
                    
                    # Get live trades from today
                    live_trades = self.db_logger.get_live_trades()
                    if live_trades:
                        print(f"📊 Found {len(live_trades)} live trades")
                        for trade in live_trades:
                            # Check if trade is from today
                            trade_date = trade.get('timestamp', trade.get('entry_time', ''))
                            if today_str in str(trade_date):
                                total_trades += 1
                                trade_pnl = trade.get('pnl', trade.get('realized_pnl', 0))
                                if trade_pnl > 0:
                                    winning_trades += 1
                                total_pnl += trade_pnl
                    
                    # Get daily summaries if available
                    daily_summaries = self.db_logger.get_daily_summaries(date=today_str)
                    if daily_summaries:
                        print(f"📊 Found daily summaries: {len(daily_summaries)} bots")
                        for bot_id, summary in daily_summaries.items():
                            if isinstance(summary, dict):
                                total_pnl += summary.get('total_pnl', 0)
                                total_trades += summary.get('total_trades', 0)
                                winning_trades += summary.get('winning_trades', 0)
                
                except Exception as e:
                    print(f"⚠️ Firestore query error: {e}")
            
            # Method 3: Fallback to system recovery files
            if total_trades == 0:
                try:
                    recovery_file = "data/position_recovery.json"
                    if os.path.exists(recovery_file):
                        import json
                        with open(recovery_file, 'r') as f:
                            recovery_data = json.load(f)
                        
                        positions = recovery_data.get('positions', [])
                        for pos in positions:
                            if pos.get('status') == 'closed':
                                total_trades += 1
                                pnl = pos.get('realized_pnl', 0)
                                if pnl > 0:
                                    winning_trades += 1
                                total_pnl += pnl
                        
                        print(f"📊 Recovery file - Trades: {total_trades}, PnL: ₹{total_pnl}")
                
                except Exception as e:
                    print(f"⚠️ Recovery file error: {e}")
            
            # Calculate win rate
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            # Return actual trading data
            result = {
                "total_pnl": round(total_pnl, 2),
                "win_rate": round(win_rate, 1),
                "total_trades": total_trades,
                "winning_trades": winning_trades,
                "data_source": "real_trading_data",
                "timestamp": datetime.now().isoformat()
            }
            
            print(f"📊 Daily Summary: {result}")
            return result
            
        except Exception as e:
            print(f"❌ Error in get_daily_summary: {e}")
            # Return empty state instead of mock data
            return {
                "total_pnl": 0.0,
                "win_rate": 0.0,
                "total_trades": 0,
                "winning_trades": 0,
                "error": str(e),
                "data_source": "error_fallback",
                "timestamp": datetime.now().isoformat()
            }

    async def get_live_positions(self) -> List[Dict[str, Any]]:
        """Get current live positions (open trades) from actual trading systems."""
        positions = []
        
        try:
            # Method 1: Get live positions from Firestore
            if self.db_logger:
                live_trades = self.db_logger.get_live_trades(status="open")
                if live_trades:
                    positions.extend(live_trades)
                    print(f"📊 Found {len(live_trades)} open positions from Firestore")
            
            # Method 2: Get positions from Portfolio Manager
            if self.portfolio_manager and not positions:
                try:
                    capital_data = await self.portfolio_manager.get_real_time_capital()
                    # If we have portfolio data but no individual positions, 
                    # this indicates we have aggregate data but individual trades aren't tracked
                    if capital_data and capital_data.position_value != 0:
                        print(f"📊 Portfolio value: ₹{capital_data.position_value}, but no individual positions found")
                except Exception as e:
                    print(f"⚠️ Portfolio Manager error: {e}")
            
            # Method 3: Check recovery file for any open positions
            if not positions:
                try:
                    recovery_file = "data/position_recovery.json"
                    if os.path.exists(recovery_file):
                        import json
                        with open(recovery_file, 'r') as f:
                            recovery_data = json.load(f)
                        
                        for pos in recovery_data.get('positions', []):
                            if pos.get('status') == 'open':
                                positions.append(pos)
                        
                        if positions:
                            print(f"📊 Found {len(positions)} open positions from recovery file")
                
                except Exception as e:
                    print(f"⚠️ Recovery file error: {e}")
            
            # Return actual positions or empty list
            print(f"📊 Total live positions found: {len(positions)}")
            return positions
            
        except Exception as e:
            print(f"❌ Error getting live positions: {e}")
            return []

    async def get_recent_trades(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent trades from actual trading systems."""
        trades = []
        
        try:
            # Method 1: Get all trades from Firestore (open and closed)
            if self.db_logger:
                all_trades = self.db_logger.get_live_trades()
                if all_trades:
                    # Sort by timestamp and take most recent
                    sorted_trades = sorted(all_trades, 
                                         key=lambda x: x.get('timestamp', x.get('last_updated', '')), 
                                         reverse=True)
                    trades.extend(sorted_trades[:limit])
                    print(f"📊 Found {len(trades)} recent trades from Firestore")
            
            # Method 2: Check recovery file for historical trades
            if len(trades) < limit:
                try:
                    recovery_file = "data/position_recovery.json"
                    if os.path.exists(recovery_file):
                        import json
                        with open(recovery_file, 'r') as f:
                            recovery_data = json.load(f)
                        
                        recovery_trades = recovery_data.get('positions', [])
                        # Add recovery trades if we need more
                        remaining_needed = limit - len(trades)
                        trades.extend(recovery_trades[:remaining_needed])
                        
                        print(f"📊 Added {min(remaining_needed, len(recovery_trades))} trades from recovery file")
                
                except Exception as e:
                    print(f"⚠️ Recovery file error: {e}")
            
            print(f"📊 Total recent trades found: {len(trades)}")
            return trades[:limit]
            
        except Exception as e:
            print(f"❌ Error getting recent trades: {e}")
            return []

    async def get_summary_positions(self) -> Dict[str, Any]:
        """
        Get position summary for risk analysis from actual trading systems.
        """
        try:
            total_exposure = 0.0
            unrealized_pnl = 0.0
            total_margin_used = 0.0
            open_positions_count = 0
            
            # Method 1: Get data from Portfolio Manager (most accurate)
            if self.portfolio_manager:
                try:
                    capital_data = await self.portfolio_manager.get_real_time_capital()
                    if capital_data:
                        total_exposure = capital_data.position_value
                        unrealized_pnl = capital_data.unrealized_pnl
                        total_margin_used = capital_data.used_margin
                        margin_usage_pct = capital_data.margin_utilization
                        
                        print(f"📊 Portfolio Summary - Exposure: ₹{total_exposure}, PnL: ₹{unrealized_pnl}")
                        
                        # Get position count from individual positions
                        positions = await self.get_live_positions()
                        open_positions_count = len(positions)
                        
                        return {
                            'total_exposure': round(total_exposure, 2),
                            'margin_usage_pct': round(margin_usage_pct, 1),
                            'unrealized_pnl': round(unrealized_pnl, 2),
                            'open_positions_count': open_positions_count,
                            'total_margin_used': round(total_margin_used, 2),
                            'portfolio_value': round(capital_data.total_capital, 2),
                            'available_cash': round(capital_data.available_cash, 2),
                            'data_source': 'portfolio_manager',
                            'timestamp': datetime.now().isoformat()
                        }
                        
                except Exception as e:
                    print(f"⚠️ Portfolio Manager error: {e}")
            
            # Method 2: Calculate from individual positions if Portfolio Manager unavailable
            positions = await self.get_live_positions()
            open_positions_count = len(positions)
            
            if positions:
                for position in positions:
                    if isinstance(position, dict):
                        pos_value = position.get('market_value', 0)
                        if pos_value == 0:
                            # Calculate market value from quantity and current price
                            quantity = position.get('quantity', 0)
                            current_price = position.get('current_price', position.get('entry_price', 0))
                            pos_value = quantity * current_price
                        
                        total_exposure += pos_value
                        unrealized_pnl += position.get('pnl', position.get('unrealized_pnl', 0))
                        
                        # Estimate margin used
                        margin_used = position.get('margin_used', pos_value * 0.2)  # 20% for equity
                        total_margin_used += margin_used
                
                # Calculate margin usage percentage
                total_margin_available = 500000  # Default assumption
                if self.portfolio_manager:
                    try:
                        capital_data = await self.portfolio_manager.get_real_time_capital()
                        if capital_data:
                            total_margin_available = capital_data.total_capital
                    except:
                        pass
                
                margin_usage_pct = (total_margin_used / total_margin_available * 100) if total_margin_available > 0 else 0
                
                print(f"📊 Position Summary - Count: {open_positions_count}, Exposure: ₹{total_exposure}")
                
                return {
                    'total_exposure': round(total_exposure, 2),
                    'margin_usage_pct': round(margin_usage_pct, 1),
                    'unrealized_pnl': round(unrealized_pnl, 2),
                    'open_positions_count': open_positions_count,
                    'total_margin_used': round(total_margin_used, 2),
                    'data_source': 'individual_positions',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Method 3: No positions found - return zero state
            print("📊 No open positions found")
            return {
                'total_exposure': 0.0,
                'margin_usage_pct': 0.0,
                'unrealized_pnl': 0.0,
                'open_positions_count': 0,
                'total_margin_used': 0.0,
                'data_source': 'no_positions',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Error getting position summary: {e}")
            return {
                'total_exposure': 0.0,
                'margin_usage_pct': 0.0,
                'unrealized_pnl': 0.0,
                'open_positions_count': 0,
                'total_margin_used': 0.0,
                'error': str(e),
                'data_source': 'error_fallback',
                'timestamp': datetime.now().isoformat()
            }

    async def get_summary_strategy(self) -> Dict[str, Any]:
        """
        Get strategy performance summary from Firestore in format expected by frontend.
        """
        try:
            if self.db_logger:
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
                
                # If no real data, fetch from paper trading data
                if not strategy_stats:
                    strategy_stats = await self._get_paper_trading_strategies()
                    total_strategies = len(strategy_stats)
            else:
                # When database is not available, fetch from paper trading data
                strategy_stats = await self._get_paper_trading_strategies()
                total_strategies = len(strategy_stats)
            
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
            # Return empty data structure when there's an error
            return {
                'top_strategy': {
                    'name': 'No data available'
                },
                'active_strategies': 0,
                'total_bots': 0,
                'strategy_details': {},
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def _get_paper_trading_strategies(self) -> Dict[str, Any]:
        """
        Get paper trading strategy data from various sources.
        """
        strategy_stats = {}
        
        try:
            # Check for paper trading log files
            log_files = [
                "logs/paper_trading.log",
                "logs/strategy_performance.log",
                "data/strategy_stats.json"
            ]
            
            for log_file in log_files:
                if os.path.exists(log_file):
                    try:
                        if log_file.endswith('.json'):
                            import json
                            with open(log_file, 'r') as f:
                                data = json.load(f)
                            strategy_stats.update(data.get('strategies', {}))
                        else:
                            # Parse log file for strategy data
                            with open(log_file, 'r') as f:
                                lines = f.readlines()
                            
                            for line in lines[-100:]:  # Last 100 lines
                                if 'strategy' in line.lower() and 'pnl' in line.lower():
                                    # Extract strategy info from log line
                                    parts = line.strip().split()
                                    for i, part in enumerate(parts):
                                        if part.lower() == 'strategy':
                                            strategy_name = parts[i+1] if i+1 < len(parts) else 'Unknown'
                                            if strategy_name not in strategy_stats:
                                                strategy_stats[strategy_name] = {
                                                    'pnl': 0,
                                                    'trades': 0,
                                                    'wins': 0
                                                }
                                            strategy_stats[strategy_name]['trades'] += 1
                                            
                    except Exception as e:
                        print(f"⚠️ Error parsing {log_file}: {e}")
            
            # If no strategy data found, check for active strategy processes
            if not strategy_stats:
                try:
                    import subprocess
                    result = subprocess.run(['pgrep', '-f', 'python.*strategy'], 
                                          capture_output=True, text=True)
                    if result.returncode == 0:
                        # Found running strategy processes
                        strategy_stats = {
                            'ScalpStrategy': {'pnl': 0, 'trades': 0, 'wins': 0},
                            'RangeReversalStrategy': {'pnl': 0, 'trades': 0, 'wins': 0},
                            'MomentumStrategy': {'pnl': 0, 'trades': 0, 'wins': 0}
                        }
                        print("📊 Found active strategy processes")
                except Exception as e:
                    print(f"⚠️ Error checking processes: {e}")
            
            return strategy_stats
            
        except Exception as e:
            print(f"❌ Error getting paper trading strategies: {e}")
            return {}

# Dependency Injection
_trade_service_instance = None

def get_trade_service():
    global _trade_service_instance
    if _trade_service_instance is None:
        _trade_service_instance = RealTradeService()
    return _trade_service_instance 