"""
Paper Trader Integration Module
Shows how to integrate the paper trader with the main trading system
"""

import datetime
import time
import logging
from typing import Dict, Any, Optional

from runner.paper_trader import PaperTrader, create_paper_trader, is_paper_trading_enabled
from runner.firestore_client import FirestoreClient
from runner.enhanced_logger import TradingLogger
from runner.market_data_fetcher import MarketDataFetcher


class PaperTradingManager:
    """Manages paper trading integration with the main trading system"""
    
    def __init__(self, logger=None, firestore_client=None):
        self.logger = logger or logging.getLogger(__name__)
        self.firestore_client = firestore_client or FirestoreClient(logger=self.logger)
        
        # Initialize paper trader if enabled
        self.paper_trader = create_paper_trader(
            logger=self.logger,
            firestore_client=self.firestore_client
        )
        
        self.is_enabled = is_paper_trading_enabled()
        
        if self.is_enabled and self.paper_trader:
            self.logger.info("Paper trading mode enabled")
        else:
            self.logger.info("Paper trading mode disabled - real trading active")
    
    def execute_trade(self, trade_signal: Dict[str, Any], strategy: str) -> Optional[Any]:
        """
        Execute a trade - either paper or real based on configuration
        
        Args:
            trade_signal: Dictionary containing trade parameters
            strategy: Strategy name that generated the signal
            
        Returns:
            Trade object if successful, None otherwise
        """
        
        if self.is_enabled and self.paper_trader:
            # Execute paper trade
            return self.paper_trader.execute_paper_trade(trade_signal, strategy)
        else:
            # Execute real trade (would call actual broker API)
            self.logger.info("Real trading not implemented in this example")
            return None
    
    def monitor_positions(self, market_data: Dict[str, float]):
        """Monitor and manage positions"""
        
        if self.is_enabled and self.paper_trader:
            # Monitor paper trades
            self.paper_trader.monitor_and_exit_trades(market_data)
    
    def run_trading_session(self, market_data: Dict[str, Any]):
        """Run a complete trading session"""
        
        try:
            if self.is_enabled and self.paper_trader:
                # Run strategies and execute paper trades
                self.paper_trader.run_strategies_and_execute(market_data)
                
                # Monitor existing positions
                price_data = {}
                for symbol, data in market_data.items():
                    if isinstance(data, dict) and "ltp" in data:
                        price_data[symbol] = data["ltp"]
                
                self.paper_trader.monitor_and_exit_trades(price_data)
                
                # Log daily performance if end of day
                current_time = datetime.datetime.now().time()
                if current_time >= datetime.time(15, 30):  # After market close
                    self.paper_trader.log_performance_summary("daily")
            
        except Exception as e:
            self.logger.error(f"Error in trading session: {e}")
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get data for dashboard display"""
        
        if self.is_enabled and self.paper_trader:
            return self.paper_trader.get_dashboard_data()
        else:
            return {
                "trading_mode": "real",
                "message": "Real trading active - no paper trade data"
            }
    
    def get_performance_report(self, period: str = "daily") -> Dict[str, Any]:
        """Get performance report for specified period"""
        
        if self.is_enabled and self.paper_trader:
            summary = self.paper_trader.calculate_performance_summary(period)
            return {
                "period": period,
                "summary": summary,
                "trading_mode": "paper"
            }
        else:
            return {
                "period": period,
                "trading_mode": "real",
                "message": "Real trading performance not available in this module"
            }
    
    def weekly_update(self):
        """Weekly performance update and logging"""
        
        if self.is_enabled and self.paper_trader:
            self.paper_trader.weekly_performance_update()
            self.logger.info("Weekly paper trading performance updated")
    
    def monthly_update(self):
        """Monthly performance update and logging"""
        
        if self.is_enabled and self.paper_trader:
            self.paper_trader.monthly_performance_update()
            self.logger.info("Monthly paper trading performance updated")
    
    def cleanup_old_data(self, days_to_keep: int = 30):
        """Cleanup old trade data"""
        
        if self.is_enabled and self.paper_trader:
            self.paper_trader.cleanup_old_trades(days_to_keep)


def create_sample_market_data() -> Dict[str, Any]:
    """Create sample market data for testing"""
    
    import random
    
    # Sample stock data
    stocks = ["RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK"]
    stock_data = {}
    
    for stock in stocks:
        base_price = random.uniform(100, 3000)
        stock_data[stock] = {
            "ltp": base_price,
            "high": base_price * 1.02,
            "low": base_price * 0.98,
            "volume": random.randint(10000, 100000)
        }
    
    # Sample futures data
    futures = ["NIFTY24NOVFUT", "BANKNIFTY24NOVFUT"]
    for future in futures:
        if "NIFTY" in future and "BANK" not in future:
            base_price = random.uniform(23000, 25000)
        else:
            base_price = random.uniform(48000, 52000)
        
        stock_data[future] = {
            "ltp": base_price,
            "high": base_price * 1.01,
            "low": base_price * 0.99,
            "volume": random.randint(5000, 50000)
        }
    
    return stock_data


def main_trading_loop():
    """Main trading loop example"""
    
    # Initialize logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Initialize paper trading manager
    trading_manager = PaperTradingManager(logger=logger)
    
    # Run trading session
    logger.info("Starting trading session...")
    
    # Simulate market data updates every 30 seconds
    for i in range(10):  # Run for 10 iterations as example
        try:
            # Get sample market data
            market_data = create_sample_market_data()
            
            # Run trading session
            trading_manager.run_trading_session(market_data)
            
            # Get and log dashboard data
            dashboard_data = trading_manager.get_dashboard_data()
            logger.info(f"Dashboard update: Active trades: {dashboard_data.get('active_trades', 0)}, "
                       f"Daily P&L: ₹{dashboard_data.get('daily_pnl', 0):.2f}")
            
            # Wait before next iteration
            time.sleep(30)
            
        except KeyboardInterrupt:
            logger.info("Trading session interrupted by user")
            break
        except Exception as e:
            logger.error(f"Error in main trading loop: {e}")
    
    # End of day cleanup
    logger.info("End of trading session")
    
    # Get final performance report
    performance = trading_manager.get_performance_report("daily")
    logger.info(f"Daily performance: {performance}")


def test_paper_trading():
    """Test function for paper trading functionality"""
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Create paper trading manager
    manager = PaperTradingManager(logger=logger)
    
    if not manager.is_enabled:
        logger.info("Paper trading is disabled - enable it in config to test")
        return
    
    # Test trade execution
    test_signal = {
        "symbol": "RELIANCE",
        "entry_price": 2500.0,
        "quantity": 10,
        "stop_loss": 2450.0,
        "target": 2600.0,
        "direction": "bullish"
    }
    
    trade = manager.execute_trade(test_signal, "test_strategy")
    if trade:
        logger.info(f"Test trade executed successfully: {trade.symbol}")
        
        # Test position monitoring
        market_data = {"RELIANCE": 2550.0}  # Price moved up
        manager.monitor_positions(market_data)
        
        # Get dashboard data
        dashboard_data = manager.get_dashboard_data()
        logger.info(f"Dashboard data: {dashboard_data}")
        
        # Get performance report
        performance = manager.get_performance_report()
        logger.info(f"Performance: {performance}")
    
    logger.info("Paper trading test completed")


if __name__ == "__main__":
    # Choose which function to run
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_paper_trading()
    else:
        main_trading_loop() 