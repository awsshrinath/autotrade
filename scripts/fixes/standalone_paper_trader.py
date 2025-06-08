#!/usr/bin/env python3
"""
Standalone Paper Trading System
Runs paper trading without Firestore dependencies for testing
"""

import os
import sys
import datetime
import time
import logging
from typing import Dict, Any

# Set paper trading environment
os.environ['PAPER_TRADE'] = 'true'

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('paper_trading.log', mode='a')
    ]
)

logger = logging.getLogger(__name__)

class MockFirestoreClient:
    """Mock Firestore client that logs to console instead of cloud"""
    
    def __init__(self, logger):
        self.logger = logger
        self.trades = []
        self.performance_data = []
    
    def log_trade(self, trader_type, date, trade_data):
        """Log trade to console and memory"""
        self.trades.append({
            'trader_type': trader_type,
            'date': date,
            'trade_data': trade_data,
            'timestamp': datetime.datetime.now().isoformat()
        })
        
        symbol = trade_data.get('symbol', 'Unknown')
        status = trade_data.get('status', 'unknown')
        entry_price = trade_data.get('entry_price', 0)
        
        self.logger.info(f"🔄 [MOCK FIRESTORE] Trade logged: {symbol} - {status} @ ₹{entry_price}")
    
    def log_performance(self, data):
        """Log performance to console and memory"""
        self.performance_data.append({
            'data': data,
            'timestamp': datetime.datetime.now().isoformat()
        })
        
        pnl = data.get('total_pnl', 0)
        trades = data.get('total_trades', 0)
        self.logger.info(f"📊 [MOCK FIRESTORE] Performance logged: {trades} trades, PnL: ₹{pnl:.2f}")
    
    def get_trades_summary(self):
        """Get summary of logged trades"""
        return {
            'total_trades': len(self.trades),
            'recent_trades': self.trades[-5:] if self.trades else [],
            'trade_symbols': [t['trade_data'].get('symbol') for t in self.trades]
        }

def create_sample_market_data():
    """Create realistic sample market data for paper trading"""
    import random
    
    # Sample stock data with realistic prices
    stocks_data = {
        "RELIANCE": {
            "ltp": random.uniform(2400, 2600),
            "high": 0, "low": 0, "volume": random.randint(50000, 200000)
        },
        "TCS": {
            "ltp": random.uniform(3100, 3300), 
            "high": 0, "low": 0, "volume": random.randint(30000, 150000)
        },
        "HDFCBANK": {
            "ltp": random.uniform(1500, 1700),
            "high": 0, "low": 0, "volume": random.randint(40000, 180000)
        },
        "INFY": {
            "ltp": random.uniform(1200, 1400),
            "high": 0, "low": 0, "volume": random.randint(35000, 160000)
        },
        "ICICIBANK": {
            "ltp": random.uniform(1000, 1200),
            "high": 0, "low": 0, "volume": random.randint(45000, 190000)
        }
    }
    
    # Add high/low based on LTP
    for symbol, data in stocks_data.items():
        ltp = data["ltp"]
        data["high"] = ltp * random.uniform(1.01, 1.03)
        data["low"] = ltp * random.uniform(0.97, 0.99)
    
    # Sample futures data
    futures_data = {
        "NIFTY24NOVFUT": {
            "ltp": random.uniform(23800, 24200),
            "high": 0, "low": 0, "volume": random.randint(20000, 100000)
        },
        "BANKNIFTY24NOVFUT": {
            "ltp": random.uniform(49500, 50500),
            "high": 0, "low": 0, "volume": random.randint(15000, 80000)
        }
    }
    
    # Add high/low for futures
    for symbol, data in futures_data.items():
        ltp = data["ltp"]
        data["high"] = ltp * random.uniform(1.005, 1.015)
        data["low"] = ltp * random.uniform(0.985, 0.995)
    
    # Combine all data
    market_data = {**stocks_data, **futures_data}
    
    return market_data

def run_standalone_paper_trading():
    """Run standalone paper trading session"""
    
    logger.info("🚀 Starting Standalone Paper Trading System")
    logger.info("=" * 60)
    
    # Initialize mock Firestore client
    mock_firestore = MockFirestoreClient(logger)
    
    # Import paper trader with mock firestore
    try:
        from runner.paper_trader import PaperTrader
        from runner.paper_trader_integration import PaperTradingManager
        
        # Create paper trader with mock firestore
        paper_trader = PaperTrader(logger=logger, firestore_client=mock_firestore)
        trading_manager = PaperTradingManager(logger=logger, firestore_client=mock_firestore)
        
        logger.info(f"✅ Paper Trader initialized with ₹{paper_trader.capital.total_capital:,.2f} capital")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize paper trader: {e}")
        return
    
    # Track session statistics
    session_stats = {
        'start_time': datetime.datetime.now(),
        'iterations': 0,
        'trades_executed': 0,
        'total_pnl': 0
    }
    
    try:
        # Run trading session for 10 iterations (simulating market updates)
        logger.info("📈 Starting trading iterations...")
        
        for i in range(10):
            iteration_start = time.time()
            session_stats['iterations'] += 1
            
            logger.info(f"\n--- Iteration {i+1}/10 ---")
            
            # Generate sample market data
            market_data = create_sample_market_data()
            
            # Log some sample prices
            sample_symbols = list(market_data.keys())[:3]
            price_info = [f"{sym}: ₹{market_data[sym]['ltp']:.2f}" for sym in sample_symbols]
            logger.info(f"📊 Market Data: {', '.join(price_info)}")
            
            # Track trades before
            trades_before = len(paper_trader.active_trades) + len(paper_trader.completed_trades)
            
            # Run trading session
            trading_manager.run_trading_session(market_data)
            
            # Track trades after
            trades_after = len(paper_trader.active_trades) + len(paper_trader.completed_trades)
            new_trades = trades_after - trades_before
            session_stats['trades_executed'] += new_trades
            
            if new_trades > 0:
                logger.info(f"🎯 {new_trades} new trade(s) executed this iteration")
            
            # Get current performance
            dashboard_data = trading_manager.get_dashboard_data()
            current_pnl = dashboard_data.get('daily_pnl', 0)
            session_stats['total_pnl'] = current_pnl
            
            logger.info(f"💰 Current P&L: ₹{current_pnl:.2f}")
            logger.info(f"📊 Active Trades: {dashboard_data.get('active_trades', 0)}")
            
            # Wait 5 seconds between iterations
            iteration_time = time.time() - iteration_start
            logger.info(f"⏱️ Iteration completed in {iteration_time:.2f}s")
            
            time.sleep(5)
    
    except KeyboardInterrupt:
        logger.info("\n🛑 Trading session interrupted by user")
    
    except Exception as e:
        logger.error(f"❌ Error during trading session: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Final reporting
        session_duration = datetime.datetime.now() - session_stats['start_time']
        
        logger.info("\n" + "=" * 60)
        logger.info("📊 FINAL SESSION REPORT")
        logger.info("=" * 60)
        
        # Get final performance data
        final_performance = trading_manager.get_performance_report("daily")
        final_dashboard = trading_manager.get_dashboard_data()
        
        logger.info(f"⏱️ Session Duration: {session_duration}")
        logger.info(f"🔄 Iterations Completed: {session_stats['iterations']}")
        logger.info(f"📈 Total Trades Executed: {session_stats['trades_executed']}")
        logger.info(f"💰 Final P&L: ₹{session_stats['total_pnl']:.2f}")
        logger.info(f"📊 Active Trades: {final_dashboard.get('active_trades', 0)}")
        logger.info(f"✅ Completed Trades Today: {final_dashboard.get('completed_trades_today', 0)}")
        
        # Show trade summary from mock firestore
        trades_summary = mock_firestore.get_trades_summary()
        logger.info(f"🗂️ Total Logged Trades: {trades_summary['total_trades']}")
        
        if trades_summary['trade_symbols']:
            logger.info(f"📋 Trade Symbols: {', '.join(set(trades_summary['trade_symbols']))}")
        
        # Show capital utilization
        capital_info = final_dashboard.get('capital_allocation', {})
        logger.info(f"💵 Stocks Available: ₹{capital_info.get('stocks_available', 0):,.2f}")
        logger.info(f"💵 Options Available: ₹{capital_info.get('options_available', 0):,.2f}")
        logger.info(f"💵 Futures Available: ₹{capital_info.get('futures_available', 0):,.2f}")
        
        logger.info("=" * 60)
        logger.info("🎉 Paper Trading Session Completed!")

if __name__ == "__main__":
    run_standalone_paper_trading() 