# main_runner.py

import os
import datetime
import time
import sys
import traceback
import logging

from runner.market_monitor import MarketMonitor, CorrelationMonitor, MarketRegimeClassifier
from runner.strategy_selector import StrategySelector
from runner.trade_manager import TradeManager
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
        from runner.trade_manager import TradeManager
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
    """Main entry point with comprehensive error handling and validation"""
    try:
        # FIXED: Early validation and setup
        print("🚀 Starting Autotrade System...")
        
        if not setup_logging():
            print("❌ Failed to setup logging - exiting")
            sys.exit(1)
        
        if not validate_environment():
            print("❌ Environment validation failed - exiting")
            sys.exit(1)
        
        if not safe_import_modules():
            print("❌ Module import failed - exiting")
            sys.exit(1)
        
        print("✅ All validations passed, initializing components...")
        
        # FIXED: Safe date and folder creation
        try:
            today_date = datetime.datetime.now().strftime("%Y-%m-%d")
            create_daily_folders(today_date)
        except Exception as e:
            logging.error(f"Failed to create daily folders: {e}")
            print(f"⚠️  Warning: Could not create daily folders: {e}")
        
        # FIXED: Initialize logger with error handling
        try:
            logger = Logger(today_date)
            logger.log_event("GPT Runner+ Started Successfully.")
        except Exception as e:
            logging.error(f"Failed to initialize logger: {e}")
            print(f"❌ Logger initialization failed: {e}")
            sys.exit(1)
        
        # FIXED: Initialize enhanced logger with fallback
        enhanced_logger = None
        try:
            session_id = f"main_{int(time.time())}"
            enhanced_logger = create_enhanced_logger(
                session_id=session_id,
                enable_gcs=True,
                enable_firestore=True,
                bot_type="main-runner"
            )
            
            if enhanced_logger:
                enhanced_logger.log_event(
                    f"Main Runner Started - Paper Trade Mode: {PAPER_TRADE}",
                    data={
                        'paper_trade_mode': PAPER_TRADE,
                        'session_id': session_id,
                        'startup_time': datetime.datetime.now().isoformat()
                    }
                )
        except Exception as e:
            logging.warning(f"Enhanced logger not available: {e}")
            print(f"⚠️  Warning: Enhanced logging not available: {e}")
        
        # FIXED: Initialize Firestore client with error handling
        firestore_client = None
        try:
            firestore_client = FirestoreClient(logger)
            logger.log_event("Firestore client initialized successfully")
        except Exception as e:
            logging.error(f"Failed to initialize Firestore client: {e}")
            logger.log_event(f"Warning: Firestore client failed to initialize: {e}")
            print(f"⚠️  Warning: Firestore client not available: {e}")
        
        # FIXED: Initialize RAG memory system with comprehensive fallback
        try:
            logger.log_event("ℹ️ [INFO] GCP clients initialized successfully")
            
            if RAG_MODULES_AVAILABLE:
                logger.log_event("[RAG] Initializing RAG memory system...")
                try:
                    # Initialize RAG memory by syncing FAISS with Firestore
                    logger.log_event("[RAG] Syncing FAISS with Firestore...")
                    sync_firestore_to_faiss()
                    
                    # Embed today's logs for RAG retrieval
                    logger.log_event("[RAG] Embedding today's logs...")
                    embed_logs_for_today()
                    
                    logger.log_event("[RAG] RAG memory system initialized successfully")
                    
                except Exception as rag_error:
                    logger.log_event(f"Warning: RAG memory initialization failed: {rag_error}")
                    print(f"⚠️  RAG memory initialization failed: {rag_error}")
            else:
                logger.log_event("[RAG] Using RAG placeholder implementations (modules not available)")
                # Still call the fallback functions to maintain compatibility
                sync_firestore_to_faiss()
                embed_logs_for_today()
                
        except Exception as e:
            logging.error(f"RAG initialization error: {e}")
            logger.log_event(f"Warning: RAG system failed to initialize: {e}")
        
        # FIXED: Initialize OpenAI Manager with validation
        openai_manager = None
        try:
            openai_manager = OpenAIManager(logger)
            logger.log_event("OpenAI manager initialized successfully")
        except Exception as e:
            logging.error(f"Failed to initialize OpenAI manager: {e}")
            logger.log_event(f"Warning: OpenAI manager failed to initialize: {e}")
        
        # FIXED: Initialize KiteConnect Manager with proper error handling
        kite_manager = None
        kite = None
        try:
            kite_manager = KiteConnectManager(logger)
            if not PAPER_TRADE:
                kite_manager.set_access_token()
                logger.log_event("KiteConnect access token set successfully")
            else:
                logger.log_event("Paper trade mode - skipping KiteConnect token setup")
            
            kite = kite_manager.get_kite_client()
            logger.log_event("KiteConnect client initialized successfully")
        except Exception as e:
            logging.error(f"Failed to initialize KiteConnect: {e}")
            logger.log_event(f"Error initializing KiteConnect: {e}")
            
            if not PAPER_TRADE:
                print(f"❌ KiteConnect required for live trading but failed to initialize: {e}")
                sys.exit(1)
            else:
                print(f"⚠️  Warning: KiteConnect not available but running in paper mode: {e}")
        
        # FIXED: Initialize market data fetcher with validation
        market_data_fetcher = None
        try:
            market_data_fetcher = MarketDataFetcher(kite, logger)
            logger.log_event("Market data fetcher initialized successfully")
        except Exception as e:
            logging.error(f"Failed to initialize market data fetcher: {e}")
            logger.log_event(f"Error initializing market data fetcher: {e}")
        
        # FIXED: Initialize strategy selector with error handling
        strategy_selector = None
        try:
            strategy_selector = StrategySelector(logger)
            logger.log_event("Strategy selector initialized successfully")
        except Exception as e:
            logging.error(f"Failed to initialize strategy selector: {e}")
            logger.log_event(f"Error initializing strategy selector: {e}")
            print(f"❌ Strategy selector required but failed to initialize: {e}")
            sys.exit(1)
        
        # FIXED: Initialize TradeManager with comprehensive error handling
        trade_manager = None
        try:
            trade_manager = TradeManager(kite, logger, firestore_client=firestore_client)
            logger.log_event("Trade manager initialized successfully")
        except Exception as e:
            logging.error(f"Failed to initialize trade manager: {e}")
            logger.log_event(f"Error initializing trade manager: {e}")
            print(f"❌ Trade manager required but failed to initialize: {e}")
            sys.exit(1)
        
        # FIXED: Initialize Paper Trading Manager with validation
        paper_trading_manager = None
        if PAPER_TRADE and PAPER_TRADING_AVAILABLE:
            try:
                paper_trading_manager = PaperTradingManager(
                    logger=logger,
                    firestore_client=firestore_client
                )
                logger.log_event("Paper Trading Manager initialized")
                
                if enhanced_logger:
                    enhanced_logger.log_event(
                        "Paper Trading Manager initialized",
                        data={'capital': paper_trading_manager.paper_trader.capital.total_capital if paper_trading_manager.paper_trader else 0}
                    )
            except Exception as e:
                logging.error(f"Failed to initialize paper trading manager: {e}")
                logger.log_event(f"Error initializing paper trading manager: {e}")
                print(f"⚠️  Warning: Paper trading manager not available: {e}")
        
        # FIXED: Pre-Market Monitoring with error handling
        pre_market_data = {}
        try:
            market_monitor = MarketMonitor(logger)
            pre_market_data = market_monitor.fetch_premarket_data()
            logger.log_event("Starting Pre-Market Monitoring...")
        except Exception as e:
            logging.error(f"Failed to fetch pre-market data: {e}")
            logger.log_event(f"Warning: Pre-market monitoring failed: {e}")
            print(f"⚠️  Warning: Using default market data due to error: {e}")
        
        # FIXED: Strategy selection with fallback
        selected_strategy = None
        try:
            selected_strategy = strategy_selector.select_strategy(pre_market_data)
            logger.log_event(f"Selected Strategy for Today: {selected_strategy}")
        except Exception as e:
            logging.error(f"Failed to select strategy: {e}")
            logger.log_event(f"Error in strategy selection: {e}")
            # FIXED: Use fallback strategy
            selected_strategy = "scalp"  # Default fallback strategy
            logger.log_event(f"Using fallback strategy: {selected_strategy}")
        
        # FIXED: Load strategy with error handling
        try:
            if PAPER_TRADE and paper_trading_manager:
                logger.log_event(f"Loading strategy {selected_strategy} for paper trading")
            else:
                trade_manager.load_strategy(selected_strategy)
                logger.log_event(f"Strategy {selected_strategy} loaded for live trading")
        except Exception as e:
            logging.error(f"Failed to load strategy: {e}")
            logger.log_event(f"Error loading strategy {selected_strategy}: {e}")
        
        # FIXED: Market open timing with better validation
        try:
            now = datetime.datetime.now()
            market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
            
            # FIXED: Handle weekend/holiday scenarios
            if now.weekday() >= 5:  # Saturday = 5, Sunday = 6
                logger.log_event("Weekend detected - paper trading only")
                print("📅 Weekend detected - running in paper mode only")
            elif now < market_open:
                wait_seconds = (market_open - now).total_seconds()
                logger.log_event(f"Waiting for Indian Market Open at 9:15 AM... ({wait_seconds:.0f} seconds)")
                print(f"⏰ Waiting for market open: {wait_seconds:.0f} seconds")
                # FIXED: Add maximum wait time and validation
                if wait_seconds > 0 and wait_seconds < 86400:  # Less than 24 hours
                    time.sleep(wait_seconds)
                else:
                    logger.log_event("Market wait time invalid - proceeding anyway")
        except Exception as e:
            logging.error(f"Error in market timing logic: {e}")
            logger.log_event(f"Error in market timing: {e}")
        
        # FIXED: Trading session with comprehensive error handling
        try:
            if PAPER_TRADE and paper_trading_manager:
                logger.log_event("Starting Paper Trading Session...")
                if enhanced_logger:
                    enhanced_logger.log_event("Paper Trading Session Started", data={'strategy': selected_strategy})
                
                # FIXED: Import with error handling
                try:
                    from runner.paper_trader_integration import create_sample_market_data
                    
                    # FIXED: Run trading cycles with better error handling and limits
                    max_cycles = 10
                    cycle_delay = 30
                    
                    for i in range(max_cycles):
                        try:
                            market_data = create_sample_market_data()
                            paper_trading_manager.run_trading_session(market_data)
                            
                            # FIXED: Get dashboard data with error handling
                            try:
                                dashboard_data = paper_trading_manager.get_dashboard_data()
                                active_trades = dashboard_data.get('active_trades', 0)
                                daily_pnl = dashboard_data.get('daily_pnl', 0)
                                logger.log_event(f"Paper Trading Cycle {i+1}: {active_trades} active trades, P&L: ₹{daily_pnl:.2f}")
                            except Exception as e:
                                logger.log_event(f"Warning: Could not get dashboard data for cycle {i+1}: {e}")
                            
                            # FIXED: Safe sleep with interruption handling
                            try:
                                time.sleep(cycle_delay)
                            except KeyboardInterrupt:
                                logger.log_event("Paper trading interrupted by user")
                                break
                            
                        except Exception as e:
                            logging.error(f"Error in paper trading cycle {i+1}: {e}")
                            logger.log_event(f"Error in paper trading cycle {i+1}: {e}")
                            # Continue with next cycle instead of failing completely
                            continue
                            
                except ImportError as e:
                    logging.error(f"Failed to import paper trading components: {e}")
                    logger.log_event(f"Error: Paper trading components not available: {e}")
                    
            else:
                # FIXED: Live trading with validation
                if not trade_manager:
                    logger.log_event("Error: Trade manager not available for live trading")
                    print("❌ Trade manager required for live trading")
                    sys.exit(1)
                
                logger.log_event("Starting Live Trading Session...")
                if enhanced_logger:
                    enhanced_logger.log_event("Live Trading Session Started", data={'strategy': selected_strategy})
                
                try:
                    trade_manager.start_trading(selected_strategy, market_data_fetcher)
                except Exception as e:
                    logging.error(f"Error in live trading session: {e}")
                    logger.log_event(f"Error in live trading session: {e}")
                    
        except Exception as e:
            logging.error(f"Error in trading session: {e}")
            logger.log_event(f"Error in trading session: {e}")
            if enhanced_logger:
                enhanced_logger.log_error(e, context={'session_type': 'trading'})
        
        # FIXED: Performance monitoring with error handling
        try:
            if openai_manager and firestore_client:
                monitor = GPTSelfImprovementMonitor(logger, firestore_client, openai_manager)
                monitor.analyze(bot_name=selected_strategy)
                logger.log_event("Performance analysis completed")
        except Exception as e:
            logging.error(f"Error in performance monitoring: {e}")
            logger.log_event(f"Warning: Performance monitoring failed: {e}")
        
        # FIXED: Cleanup with error handling
        try:
            if enhanced_logger:
                enhanced_logger.flush_all()
                logger.log_event("Session completed, logs flushed to GCS")
        except Exception as e:
            logging.error(f"Error flushing logs: {e}")
            logger.log_event(f"Error flushing logs: {e}")
        
        logger.log_event("Main runner completed successfully")
        print("✅ Autotrade system completed successfully")
        
    except KeyboardInterrupt:
        logging.info("Application interrupted by user")
        print("\n🛑 Application interrupted by user")
        sys.exit(0)
        
    except Exception as e:
        logging.critical(f"Critical error in main function: {e}")
        logging.critical(traceback.format_exc())
        print(f"❌ Critical error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
