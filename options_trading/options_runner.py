import os
import sys

# Add project root to path BEFORE any other imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import time
from datetime import datetime
from datetime import time as dtime

try:
    import pytz
    PYTZ_AVAILABLE = True
except ImportError:
    PYTZ_AVAILABLE = False
    print("Warning: pytz not available. Timezone functionality may be limited.")

from runner.config import PAPER_TRADE, initialize_config
from runner.firestore_client import FirestoreClient
from runner.kiteconnect_manager import KiteConnectManager
from runner.enhanced_logging import create_enhanced_logger, LogLevel, LogCategory
from runner.strategy_factory import load_strategy
from runner.trade_manager import create_enhanced_trade_manager
from runner.utils.trade_utils import is_market_open, get_today_date
from runner.health_server import start_health_server, run_script_with_monitoring
import threading

# Import market components with fallbacks
try:
    from runner.market_data import MarketDataFetcher
    from runner.market_monitor import MarketMonitor
except ImportError:
    class MarketDataFetcher:
        def __init__(self, *args): pass
    class MarketMonitor:
        def __init__(self, *args): pass
        def get_market_sentiment(self, kite):
            return {"INDIA VIX": 15}

IST = pytz.timezone("Asia/Kolkata") if PYTZ_AVAILABLE else None


def wait_until_market_opens(logger):
    logger.log_system_event("Waiting for market to open...")
    while True:
        now = datetime.now(IST).time() if IST else datetime.now().time()
        if dtime(9, 15) <= now <= dtime(15, 15):
            logger.log_system_event("Market is open. Continuing.")
            break
        time.sleep(30)


def wait_for_daily_plan(firestore_client, today_date, logger, max_wait_minutes=10):
    """
    Wait for the daily plan to be available, created by the main runner.
    Returns the plan if found, None if timeout reached.
    """
    wait_interval = 30
    max_attempts = (max_wait_minutes * 60) // wait_interval
    
    for attempt in range(max_attempts):
        daily_plan = firestore_client.fetch_daily_plan(today_date)
        if daily_plan:
            logger.info(f"Daily plan found after {attempt * wait_interval} seconds")
            return daily_plan
        
        if attempt == 0:
            logger.info("Daily plan not found, waiting for main runner to create it...")
        
        logger.info(f"Plan not available yet, retrying... (attempt {attempt + 1}/{max_attempts})")
        time.sleep(wait_interval)
    
    logger.warning(f"Daily plan not found after {max_wait_minutes} minutes, using fallback")
    return None


class OptionsTrader:
    def __init__(self, strategy_name: str, logger, paper_trade: bool = False):
        self.strategy_name = strategy_name
        self.paper_trade = paper_trade
        self.logger = logger
        self.strategy = None
        
        self.kite_manager = KiteConnectManager(logger=self.logger)
        self.trade_manager = create_enhanced_trade_manager(
            logger=self.logger, 
            kite_manager=self.kite_manager,
            paper_trade=self.paper_trade
        )
        self.logger.info(f"OptionsTrader for '{self.strategy_name}' initialized.")

    def load_strategy(self):
        self.strategy = load_strategy(
            self.strategy_name, 
            self.kite_manager.get_kite_client(), 
            self.logger, 
            paper_trade=self.paper_trade
        )

    def run(self):
        self.logger.info(f"Starting OptionsTrader with strategy: {self.strategy_name}")
        
        if not self.strategy:
            self.load_strategy()
        
        if not self.strategy:
            self.logger.critical(f"Failed to load strategy '{self.strategy_name}'. Exiting.")
            return

        while is_market_open() or self.paper_trade:
            try:
                signals = self.strategy.analyze()
                for signal in signals:
                    self.trade_manager.execute_trade(signal)
                
                if self.paper_trade:
                    self.logger.info("Paper trading mode: single run complete.")
                    break
                
                time.sleep(60)

            except KeyboardInterrupt:
                self.logger.info("OptionsTrader stopped by user.")
                break
            except Exception as e:
                self.logger.log_error(e, context={"source": "options_trader_run"}, source="options_trader")
                time.sleep(60)


def run_options_trader(strategy_name: str, paper_trade: bool = False):
    initialize_config()
    session_id = f"options_trader_{int(time.time())}"
    logger = create_enhanced_logger(session_id=session_id, bot_type="options-trader")
    
    logger.log_system_event(
        "Options Trading Bot Initializing",
        {"version": "1.1", "paper_trade": paper_trade, "strategy": strategy_name}
    )

    try:
        firestore_client = FirestoreClient(logger)
        today_date = get_today_date()
        daily_plan = wait_for_daily_plan(firestore_client, today_date, logger)
        
        if not daily_plan:
            logger.warning("No daily plan. Using default fallback strategy: scalp.")
            strategy_name = strategy_name or "scalp"
        else:
            strategy_tuple = daily_plan.get("options", (strategy_name or "scalp",))
            strategy_name = strategy_tuple[0] if isinstance(strategy_tuple, (list, tuple)) else strategy_tuple
            logger.info(f"Using strategy from daily plan: {strategy_name}")

        trader = OptionsTrader(strategy_name=strategy_name, logger=logger, paper_trade=paper_trade)
        
        if not paper_trade:
            wait_until_market_opens(logger)

        trader.run()

    except Exception as e:
        logger.log_error(e, context={"source": "options_trader_main", "critical": True}, source="options_trader", urgent=True)
        # sys.exit(1) # Removing this to allow health server to continue running
    finally:
        logger.log_system_event("Options trading bot shutting down.")
        # logger.shutdown() # Commenting out to keep logger active


def main():
    """Main entry point for options runner."""
    import argparse
    parser = argparse.ArgumentParser(description="Options Trading Bot")
    parser.add_argument("strategy", nargs='?', default="scalp", help="Name of the strategy to run (e.g., scalp)")
    parser.add_argument("--paper", action="store_true", help="Run in paper trading mode")
    args = parser.parse_args()

    paper_trade_mode = args.paper or PAPER_TRADE
    
    # Check if we're being run directly or through health server
    if os.environ.get('HEALTH_CHECK_ENABLED') == 'true':
        # We're being run through health server, just run trading logic once
        try:
            run_options_trader(strategy_name=args.strategy, paper_trade=paper_trade_mode)
        except Exception as e:
            print(f"ERROR: Options trading logic failed: {e}")
            import traceback
            traceback.print_exc()
    else:
        # Direct execution, start health server and run indefinitely
        health_port = int(os.environ.get('SERVICE_PORT', 8082))
        health_thread = threading.Thread(target=start_health_server, args=(health_port,), daemon=True)
        health_thread.start()
        
        # Run the trading logic directly
        try:
            run_options_trader(strategy_name=args.strategy, paper_trade=paper_trade_mode)
        except Exception as e:
            print(f"ERROR: Options trading logic failed: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
