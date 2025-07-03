import os
import sys

# Add project root to path BEFORE any other imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import time
from datetime import datetime
from datetime import time as dtime
from runner.enhanced_logging.log_types import LogLevel, LogCategory
from runner.enhanced_logging import create_trading_logger
try:
    import pytz
    PYTZ_AVAILABLE = True
except ImportError:
    PYTZ_AVAILABLE = False
    print("Warning: pytz not available. Timezone functionality may be limited.")
from runner.config import PAPER_TRADE
from runner.firestore_client import FirestoreClient
from runner.kiteconnect_manager import KiteConnectManager
from runner.strategy_factory import load_strategy
from runner.trade_manager import EnhancedTradeManager, create_enhanced_trade_manager
from runner.risk_governor import RiskGovernor
from runner.position_monitor import PositionMonitor
from runner.utils.paper_trade_utils import simulate_exit

# Import market components with fallbacks
try:
    from runner.market_data import MarketDataFetcher, TechnicalIndicators
    from runner.market_monitor import MarketMonitor, CorrelationMonitor, MarketRegimeClassifier
except ImportError:
    class MarketDataFetcher:
        def __init__(self, *args): pass
    class TechnicalIndicators:
        def __init__(self, *args): pass
    class MarketMonitor:
        def __init__(self, *args): pass
        def get_market_sentiment(self, kite):
            return {"INDIA VIX": 15}
    class CorrelationMonitor:
        def __init__(self, *args): pass
    class MarketRegimeClassifier:
        def __init__(self, *args): pass

IST = pytz.timezone("Asia/Kolkata")


def wait_until_market_opens(logger):
    logger.log_system_event("Waiting for market to open...")
    while True:
        now = datetime.now().astimezone(IST).time()
        if dtime(9, 15) <= now <= dtime(15, 15):
            logger.log_system_event("Market is open. Continuing.")
            break
        time.sleep(30)


# Strategy Map
STRATEGY_MAP = {"orb": "futures_trading.strategies.orb_strategy"}


def is_market_open():
    now = datetime.now(IST)
    weekday = now.weekday()
    if weekday >= 5:
        print("[INFO] Weekend detected. Market is closed.")
        return False
    start_time = dtime(9, 15)
    end_time = dtime(15, 15)
    return start_time <= now.time() <= end_time


def graceful_exit_if_off_hours(kite):
    if is_market_open():
        return
    print("[INFO] Market closed. Attempting to exit open futures trades...")
    firestore = FirestoreClient()
    today = datetime.now().strftime("%Y-%m-%d")
    trades = firestore.fetch_trades(bot_name="futures-trader", date_str=today)

    for trade in trades:
        if trade["status"] != "open":
            continue
        try:
            if PAPER_TRADE:
                print(f"[EXIT-PAPER] Simulating exit for {trade['symbol']}")
                exit_candles = kite.historical_data(
                    trade["symbol"],
                    trade["entry_time"],
                    datetime.now(),
                    interval="5minute",
                )
                simulate_exit(trade, exit_candles)
            else:
                print(f"[FORCED-EXIT] Closing real trade for {trade['symbol']}")
                trade["status"] = "forced_exit"
                trade["exit_price"] = trade["entry_price"]
                trade["exit_time"] = datetime.now().isoformat()
                trade["pnl"] = 0
                firestore.log_trade(trade)
        except Exception as e:
            print(f"[ERROR] Exit failed for {trade['symbol']}: {e}")
    print("[INFO] All open trades handled. Exiting bot.")
    exit(0)


def get_realtime_futures_data(kite):
    instruments = kite.instruments(exchange="NFO")
    for ins in instruments:
        if ins["name"] == "NIFTY" and ins["instrument_type"] == "FUT":
            return {
                "symbol": ins["tradingsymbol"],
                "token": ins["instrument_token"],
            }
    return None


def wait_for_daily_plan(firestore_client, today_date, logger, max_wait_minutes=10):
    """
    Wait for the daily plan to be available, created by the main runner.
    Returns the plan if found, None if timeout reached.
    """
    wait_interval = 30  # seconds
    max_attempts = (max_wait_minutes * 60) // wait_interval
    
    for attempt in range(max_attempts):
        daily_plan = firestore_client.fetch_daily_plan(today_date)
        if daily_plan:
            logger.info(f"Daily plan found after {attempt * wait_interval} seconds")
            return daily_plan
        
        if attempt == 0:
            logger.info(f"Daily plan not found, waiting for main runner to create it...")
        
        logger.info(f"Plan not available yet, retrying in {wait_interval}s... (attempt {attempt + 1}/{max_attempts})")
        time.sleep(wait_interval)
    
    logger.warning(f"Daily plan not found after {max_wait_minutes} minutes, using fallback")
    return None


class FuturesTrader:
    def __init__(self, strategy_name: str, logger, paper_trade: bool = False):
        self.strategy_name = strategy_name
        self.paper_trade = paper_trade
        
        # Initialize logger
        self.logger = logger
        self.strategy = None # Initialize strategy attribute
        
        self.kite_manager = KiteConnectManager(logger=self.logger)
        self.risk_governor = RiskGovernor(self.logger)
        self.trade_manager = create_enhanced_trade_manager(
            logger=self.logger, 
            kite_manager=self.kite_manager
        )
        self.position_monitor = PositionMonitor(
            logger=self.logger,
            kite_manager=self.kite_manager
        )
        
        self.logger.info(f"FuturesTrader for '{self.strategy_name}' initialized.")

    def _get_market_data_fetcher(self):
        # This can be customized based on needs
        return MarketDataFetcher(self.logger, self.kite_manager)

    def _get_strategy(self, strategy_name: str):
        if strategy_name not in STRATEGY_MAP:
            self.logger.error(f"Unknown strategy: {strategy_name}")
            return None
        self.strategy = load_strategy(strategy_name, self.kite_manager.get_kite_client(), self.logger)
        return self.strategy

    def run(self):
        """Main loop for the futures trader."""
        self.logger.info(f"Starting FuturesTrader with strategy: {self.strategy_name}")
        
        # Ensure strategy is loaded
        if not self.strategy:
            self._get_strategy(self.strategy_name)

        if not self.strategy:
            self.logger.critical(f"Failed to load strategy '{self.strategy_name}'. Exiting.")
            return

        while is_market_open() or self.paper_trade:
            try:
                trade_signals = self.strategy.analyze()
                if trade_signals:
                    for trade_signal in trade_signals:
                        self.logger.info(f"Executing trade: {trade_signal}")
                        try:
                            result = self.trade_manager.execute_trade(trade_signal)
                            if result:
                                self.logger.info(f"Futures trade executed successfully: {result}")
                            else:
                                self.logger.warning(f"Futures trade execution failed.")
                        except Exception as trade_error:
                            self.logger.log_error(trade_error, context={"source": "futures_trade_execution"}, source="futures_trader")
                else:
                    self.logger.debug("No valid trade signal from strategy.")
                
                if self.paper_trade:
                    self.logger.info("Paper trading mode: single run complete.")
                    break
                
                time.sleep(60)

            except KeyboardInterrupt:
                self.logger.info("FuturesTrader stopped by user.")
                break
            except Exception as e:
                self.logger.log_error(e, context={"source": "futures_trader_run"}, source="futures_trader")
                time.sleep(60) # Wait longer after an error


def run_futures_trader(strategy_name: str, paper_trade: bool = False):
    today_date = datetime.now().strftime("%Y-%m-%d")
    
    session_id = f"futures_trader_{int(time.time())}"
    logger = create_trading_logger(session_id=session_id, bot_type="futures-trader")
    
    logger.log_system_event(
        "Futures Trading Bot Initializing",
        {"version": "1.1", "paper_trade": paper_trade, "strategy": strategy_name}
    )

    try:
    firestore_client = FirestoreClient(logger)
    daily_plan = wait_for_daily_plan(firestore_client, today_date, logger)
    
    if not daily_plan:
            logger.warning("No daily plan. Using default fallback strategy: ORB.")
            # Use provided strategy name as fallback or default to ORB
            strategy_name = strategy_name or "ORB"
            else:
            # Extract the futures strategy from the plan, with fallback
            strategy_tuple = daily_plan.get("futures", (strategy_name or "ORB",))
        strategy_name = strategy_tuple[0] if isinstance(strategy_tuple, (list, tuple)) else strategy_tuple
            logger.info(f"Using strategy from daily plan: {strategy_name}")
        sentiment = daily_plan.get("market_sentiment", {})
        if sentiment:
                logger.info(f"Market sentiment from plan: {sentiment}")

        trader = FuturesTrader(strategy_name=strategy_name, logger=logger, paper_trade=paper_trade)

        if not paper_trade:
    wait_until_market_opens(logger)

        trader.run()

    except Exception as e:
        logger.log_error(e, context={"source": "futures_trader_main", "critical": True}, source="futures_trader", urgent=True)
        # Optional: send a notification on critical failure
        # send_slack_notification(f"CRITICAL: Futures trading bot crashed: {e}")
    finally:
        if logger:
            logger.log_system_event("Futures trading bot shutting down.")
            logger.shutdown()


def main():
    """Entry point for the script."""
    # Example usage, can be driven by args
    run_futures_trader(strategy_name="orb", paper_trade=PAPER_TRADE)


if __name__ == "__main__":
    main()
