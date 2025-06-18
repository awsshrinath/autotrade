# main_runner.py

import os
import datetime
import time
import sys
import traceback
import logging
import argparse

from runner.market_monitor import MarketMonitor, CorrelationMonitor, MarketRegimeClassifier
from runner.strategy_selector import StrategySelector
from runner.trade_manager import EnhancedTradeManager
from runner.logger import TradingLogger
from runner.gpt_codefix_suggestor import GPTCodeFixSuggestor
from runner.daily_report_generator import DailyReportGenerator
from runner.gpt_self_improvement_monitor import GPTSelfImprovementMonitor
from runner.common_utils import create_daily_folders
from runner.openai_manager import OpenAIManager
from runner.kiteconnect_manager import KiteConnectManager
from runner.market_data import MarketDataFetcher, TechnicalIndicators
from runner.firestore_client import FirestoreClient
from runner.config import PAPER_TRADE, get_config, initialize_config
from runner.trade_manager import TradeManager

# Import paper trading components
try:
    from runner.paper_trader_integration import PaperTradingManager
    from runner.enhanced_logger import create_enhanced_logger
    PAPER_TRADING_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Paper trading components not available: {e}")
    PAPER_TRADING_AVAILABLE = False

# FIXED: Add RAG module imports with comprehensive fallback handling
try:
    # Try to import RAG modules
    from gpt_runner.rag.faiss_firestore_adapter import sync_firestore_to_faiss
    from gpt_runner.rag.rag_worker import embed_logs_for_today  
    from gpt_runner.rag.retriever import retrieve_similar_context
    RAG_MODULES_AVAILABLE = True
    print("✅ RAG modules loaded successfully")
except ImportError as e:
    print(f"Warning: RAG modules not available: {e}")
    RAG_MODULES_AVAILABLE = False
    
    # Define comprehensive fallback functions
    def sync_firestore_to_faiss(*args, **kwargs):
        """Fallback function when RAG sync is not available"""
        print("RAG: sync_firestore_to_faiss called - using placeholder implementation")
        return True
        
    def embed_logs_for_today(*args, **kwargs):
        """Fallback function when RAG embedding is not available"""
        print("RAG: embed_logs_for_today called - using placeholder implementation")
        return True
        
    def retrieve_similar_context(query, **kwargs):
        """Fallback function when RAG retrieval is not available"""
        print("Warning: RAG retrieval not available")
        return {"context": "RAG retrieval not available", "sources": []}

# FIXED: Add early validation and better error handling
def validate_environment():
    """Validate critical environment variables and configurations"""
    critical_vars = {
        'GOOGLE_APPLICATION_CREDENTIALS': 'Google Cloud credentials path',
        'GOOGLE_CLOUD_PROJECT': 'GCP Project ID'
    }
    
    missing_vars = []
    for var, description in critical_vars.items():
        if not os.getenv(var):
            missing_vars.append(f"{var} ({description})")
    
    if missing_vars:
        print(f"❌ Missing critical environment variables: {', '.join(missing_vars)}")
        print("💡 Set these variables before running the application")
        return False
    
    return True

# FIXED: Add safe imports with detailed error reporting
def safe_import_modules():
    """Safely import all required modules with detailed error reporting"""
    import_errors = []
    
    try:
        from runner.market_monitor import MarketMonitor, CorrelationMonitor, MarketRegimeClassifier
        from runner.strategy_selector import StrategySelector
        from runner.enhanced_trade_manager import EnhancedTradeManager
        from runner.logger import Logger
        from runner.gpt_codefix_suggestor import GPTCodeFixSuggestor
        from runner.daily_report_generator import DailyReportGenerator
        from runner.gpt_self_improvement_monitor import GPTSelfImprovementMonitor
        from runner.common_utils import create_daily_folders
        from runner.openai_manager import OpenAIManager
        from runner.kiteconnect_manager import KiteConnectManager
        from runner.market_data import MarketDataFetcher, TechnicalIndicators
        from runner.firestore_client import FirestoreClient
        from runner.config import PAPER_TRADE, get_config
        
        # Store successfully imported modules
        globals().update(locals())
        
    except ImportError as e:
        import_errors.append(f"Core modules: {e}")
    
    # FIXED: Safe import of optional paper trading components
    global PAPER_TRADING_AVAILABLE, PaperTradingManager, create_enhanced_logger
    PAPER_TRADING_AVAILABLE = False
    
    try:
        from runner.paper_trader_integration import PaperTradingManager
        from runner.enhanced_logger import create_enhanced_logger
        PAPER_TRADING_AVAILABLE = True
        print("✅ Paper trading components loaded successfully")
    except ImportError as e:
        print(f"⚠️  Warning: Paper trading components not available: {e}")
        # FIXED: Create fallback functions to prevent runtime errors
        def create_enhanced_logger(*args, **kwargs):
            print("ℹ️  Using fallback logger - enhanced logging not available")
            return None
    
    if import_errors:
        print(f"❌ Critical import errors: {', '.join(import_errors)}")
        return False
    
    return True

# FIXED: Add comprehensive logging setup
def setup_logging():
    """Setup comprehensive logging with rotation and error capture"""
    try:
        os.makedirs("logs", exist_ok=True)
        
        # Configure root logger
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'logs/main_{datetime.datetime.now().strftime("%Y%m%d")}.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        # Setup exception logging
        def log_exception(exc_type, exc_value, exc_traceback):
            if issubclass(exc_type, KeyboardInterrupt):
                sys.__excepthook__(exc_type, exc_value, exc_traceback)
                return
            
            logging.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
        
        sys.excepthook = log_exception
        
        return True
    except Exception as e:
        print(f"❌ Failed to setup logging: {e}")
        return False

def main():
    """
    Main function to run the trading bot.
    Initializes components and enters the main trading loop.
    """
    try:
        # Initialize configuration
        initialize_config('config/base.yaml', 'config/development.yaml')
        
        # Initialize necessary components
        logger = TradingLogger()
        config = get_config()
        kite_manager = KiteConnectManager(logger=logger, config=config)
        trade_manager = TradeManager(logger=logger, kite_manager=kite_manager, config=config)

        # Main loop
        while True:
            try:
                # Placeholder for trading logic
                # For example, check for signals and execute trades
                # trade_manager.execute_trade(...)
                time.sleep(60)  # Wait for a minute before the next iteration

            except KeyboardInterrupt:
                logger.log_info("Trading bot stopped by user.")
                break
            except Exception as e:
                logger.log_error(f"An error occurred in the main loop: {e}")
                logger.log_error(traceback.format_exc())
                time.sleep(60)  # Wait before retrying

    except Exception as e:
        # Log critical initialization errors
        # Using a fallback basic logger if TradingLogger fails
        print(f"A critical error occurred during initialization: {e}")
        print(traceback.format_exc())

    finally:
        # Clean up resources if they were initialized
        if 'kite_manager' in locals() and kite_manager:
            kite_manager.close_session()
        
        if 'logger' in locals() and logger:
            logger.log_info("Trading bot has finished its run.")

if __name__ == "__main__":
    main()
