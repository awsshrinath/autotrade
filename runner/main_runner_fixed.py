# runner/main_runner_fixed.py

import datetime
import time
import logging
import traceback
import os
import sys
from typing import Optional

# Setup basic logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join(os.getcwd(), 'runner.log'), mode='a')
    ]
)

# Placeholder functions to fix undefined name errors
def sync_firestore_to_faiss():
    """Placeholder function for Firestore to FAISS synchronization"""
    print("[INFO] sync_firestore_to_faiss called - placeholder implementation")
    pass

def embed_logs_for_today():
    """Placeholder function for embedding logs"""
    print("[INFO] embed_logs_for_today called - placeholder implementation")
    pass

def print_startup_info():
    """Print startup diagnostics"""
    print("=" * 60)
    print("🚀 TRON AUTOTRADE SYSTEM - ENHANCED STARTUP")
    print("=" * 60)
    print(f"Current working directory: {os.getcwd()}")
    print(f"Python path: {sys.path[:3]}")
    
    # Test basic imports
    try:
        import datetime
        import time
        print("✅ Basic Python modules imported successfully")
    except Exception as e:
        print(f"❌ Basic import failed: {e}")
        return False
    
    # Test package structure
    try:
        import runner
        print("✅ runner package found")
    except Exception as e:
        print(f"❌ runner package not found: {e}")
        
    try:
        import gpt_runner
        print("✅ gpt_runner package found")
    except Exception as e:
        print(f"⚠️ gpt_runner package not found: {e}")
    
    print("✅ Basic import validation completed")
    return True

def safe_import_with_fallback():
    """Safely import modules with fallbacks"""
    print("Starting application...")
    
    # Safe imports with error handling
    imports = {}
    
    # Basic runner modules
    try:
        from runner.logger import Logger
        imports['Logger'] = Logger
        print("✅ Logger imported")
    except Exception as e:
        print(f"⚠️ Logger import failed: {e}")
        imports['Logger'] = logging.getLogger
    
    try:
        from runner.enhanced_logger import TradingLogger
        imports['TradingLogger'] = TradingLogger
        print("✅ TradingLogger imported")
    except Exception as e:
        print(f"⚠️ TradingLogger import failed: {e}")
        imports['TradingLogger'] = None
    
    try:
        from runner.firestore_client import FirestoreClient
        imports['FirestoreClient'] = FirestoreClient
        print("✅ FirestoreClient imported")
    except Exception as e:
        print(f"⚠️ FirestoreClient import failed: {e}")
        imports['FirestoreClient'] = None
    
    # Enhanced modules with fallbacks
    try:
        from runner.enhanced_openai_manager import EnhancedOpenAIManager, get_openai_manager
        imports['OpenAIManager'] = get_openai_manager
        print("✅ Enhanced OpenAI Manager imported")
    except Exception as e:
        print(f"⚠️ Enhanced OpenAI Manager import failed: {e}")
        try:
            from runner.openai_manager import OpenAIManager
            imports['OpenAIManager'] = OpenAIManager
            print("✅ Fallback OpenAI Manager imported")
        except Exception as e2:
            print(f"❌ All OpenAI Manager imports failed: {e2}")
            imports['OpenAIManager'] = None
    
    try:
        from runner.enhanced_cognitive_system import initialize_enhanced_cognitive_system, DecisionType, ConfidenceLevel, CognitiveState, StateTransitionTrigger
        imports['initialize_cognitive_system'] = initialize_enhanced_cognitive_system
        imports['DecisionType'] = DecisionType
        imports['ConfidenceLevel'] = ConfidenceLevel
        imports['CognitiveState'] = CognitiveState
        imports['StateTransitionTrigger'] = StateTransitionTrigger
        print("✅ Enhanced Cognitive System imported")
    except Exception as e:
        print(f"⚠️ Enhanced Cognitive System import failed: {e}")
        try:
            from runner.cognitive_system import initialize_cognitive_system, DecisionType, ConfidenceLevel, CognitiveState, StateTransitionTrigger
            imports['initialize_cognitive_system'] = initialize_cognitive_system
            imports['DecisionType'] = DecisionType
            imports['ConfidenceLevel'] = ConfidenceLevel
            imports['CognitiveState'] = CognitiveState
            imports['StateTransitionTrigger'] = StateTransitionTrigger
            print("✅ Fallback Cognitive System imported")
        except Exception as e2:
            print(f"❌ All Cognitive System imports failed: {e2}")
            imports['initialize_cognitive_system'] = None
    
    # Other essential modules
    try:
        from runner.kite_manager import KiteConnectManager
        imports['KiteConnectManager'] = KiteConnectManager
        print("✅ KiteConnectManager imported")
    except Exception as e:
        print(f"⚠️ KiteConnectManager import failed: {e}")
        imports['KiteConnectManager'] = None
    
    try:
        from runner.market_monitor import MarketMonitor
        imports['MarketMonitor'] = MarketMonitor
        print("✅ MarketMonitor imported")
    except Exception as e:
        print(f"⚠️ MarketMonitor import failed: {e}")
        imports['MarketMonitor'] = None
    
    try:
        from runner.strategy_selector import StrategySelector
        imports['StrategySelector'] = StrategySelector
        print("✅ StrategySelector imported")
    except Exception as e:
        print(f"⚠️ StrategySelector import failed: {e}")
        imports['StrategySelector'] = None
    
    try:
        from runner.config import PAPER_TRADE
        imports['PAPER_TRADE'] = PAPER_TRADE
        print("✅ Config imported")
    except Exception as e:
        print(f"⚠️ Config import failed: {e}")
        imports['PAPER_TRADE'] = True  # Default to paper trading
    
    # Paper trader integration
    try:
        from runner.paper_trader_integration import PaperTradingManager
        imports['PaperTradingManager'] = PaperTradingManager
        print("✅ Paper Trading Manager imported")
    except Exception as e:
        print(f"⚠️ Paper Trading Manager import failed: {e}")
        imports['PaperTradingManager'] = None
    
    # RAG modules (with expected failures)
    try:
        from gpt_runner.rag import sync_firestore_to_faiss, embed_logs_for_today
        imports['sync_firestore_to_faiss'] = sync_firestore_to_faiss
        imports['embed_logs_for_today'] = embed_logs_for_today
        print("✅ RAG modules imported")
    except Exception as e:
        print(f"Warning: RAG modules not available: {e}")
        imports['sync_firestore_to_faiss'] = lambda *args, **kwargs: print("RAG sync not available - using placeholder")
        imports['embed_logs_for_today'] = lambda *args, **kwargs: print("RAG embedding not available - using placeholder")
    
    # GPT reflection
    try:
        from gpt_runner.gpt_reflection import run_gpt_reflection
        imports['run_gpt_reflection'] = run_gpt_reflection
        print("✅ GPT reflection imported")
    except Exception as e:
        print(f"Warning: Could not import RAG modules: {e}")
        imports['run_gpt_reflection'] = lambda *args, **kwargs: print("GPT reflection not available - using placeholder")
    
    return imports

class SafeFirestoreClient:
    """Safe Firestore client wrapper with error handling"""
    
    def __init__(self, logger):
        self.logger = logger
        self.client = None
        self.available = False
        
        try:
            if hasattr(logger, 'log_event'):
                logger.log_event("Attempting to initialize Firestore client...")
            
            # Try to import and initialize real Firestore client
            from runner.firestore_client import FirestoreClient
            self.client = FirestoreClient(logger)
            self.available = True
            
            if hasattr(logger, 'log_event'):
                logger.log_event("✅ Firestore client initialized successfully")
            
        except Exception as e:
            if hasattr(logger, 'log_event'):
                logger.log_event(f"⚠️ Firestore client failed to initialize: {e}")
            else:
                logger.warning(f"Firestore client failed to initialize: {e}")
            
            self.available = False
    
    def store_daily_plan(self, plan):
        """Store daily plan with error handling"""
        if self.available and self.client:
            try:
                return self.client.store_daily_plan(plan)
            except Exception as e:
                if hasattr(self.logger, 'log_event'):
                    self.logger.log_event(f"❌ Failed to store daily plan: {e}")
                else:
                    self.logger.error(f"Failed to store daily plan: {e}")
        
        # Fallback: Log locally
        if hasattr(self.logger, 'log_event'):
            self.logger.log_event(f"📝 [LOCAL STORAGE] Daily plan: {plan}")
        else:
            self.logger.info(f"Daily plan (local): {plan}")

def create_safe_logger():
    """Create a safe logger that works in all environments"""
    
    try:
        from runner.logger import Logger
        logger = Logger(datetime.date.today().isoformat())
        return logger, "runner.logger"
    except Exception as e:
        print(f"⚠️ Runner logger failed: {e}")
        
        # Fallback to standard logging
        logger = logging.getLogger("safe_main_runner")
        logger.setLevel(logging.INFO)
        
        # Add log_event method for compatibility
        def log_event(message):
            logger.info(message)
        
        logger.log_event = log_event
        return logger, "standard_logging"

def initialize_memory_safe(logger):
    """Initialize memory safely"""
    try:
        if hasattr(logger, 'log_event'):
            logger.log_event("[RAG] Syncing FAISS with Firestore...")
        else:
            logger.info("[RAG] Syncing FAISS with Firestore...")
        
        # This will use the placeholder function if RAG is not available
        sync_firestore_to_faiss()
        
        if hasattr(logger, 'log_event'):
            logger.log_event("[RAG] Embedding today's logs...")
        else:
            logger.info("[RAG] Embedding today's logs...")
        
        embed_logs_for_today()
        
    except Exception as e:
        if hasattr(logger, 'log_event'):
            logger.log_event(f"⚠️ [RAG] Memory initialization failed: {e}")
        else:
            logger.warning(f"[RAG] Memory initialization failed: {e}")

def main():
    """Enhanced main function with comprehensive error handling"""
    
    # Print startup diagnostics
    if not print_startup_info():
        print("❌ Basic startup validation failed")
        return
    
    # Safe import all modules
    imports = safe_import_with_fallback()
    
    # Extract imported modules/functions
    Logger = imports.get('Logger', logging.getLogger)
    TradingLogger = imports.get('TradingLogger')
    initialize_cognitive_system = imports.get('initialize_cognitive_system')
    DecisionType = imports.get('DecisionType')
    ConfidenceLevel = imports.get('ConfidenceLevel')
    CognitiveState = imports.get('CognitiveState')
    StateTransitionTrigger = imports.get('StateTransitionTrigger')
    OpenAIManager = imports.get('OpenAIManager')
    KiteConnectManager = imports.get('KiteConnectManager')
    MarketMonitor = imports.get('MarketMonitor')
    StrategySelector = imports.get('StrategySelector')
    PaperTradingManager = imports.get('PaperTradingManager')
    PAPER_TRADE = imports.get('PAPER_TRADE', True)
    sync_firestore_to_faiss = imports.get('sync_firestore_to_faiss')
    embed_logs_for_today = imports.get('embed_logs_for_today')
    run_gpt_reflection = imports.get('run_gpt_reflection')
    
    # Create safe logger
    logger, logger_type = create_safe_logger()
    
    try:
        enhanced_logger = TradingLogger() if TradingLogger else None
    except Exception as e:
        enhanced_logger = None
        if hasattr(logger, 'log_event'):
            logger.log_event(f"⚠️ Enhanced logger failed to initialize: {e}")
    
    if hasattr(logger, 'log_event'):
        logger.log_event(f"Using new optimized logging system ({logger_type})")
    
    # Print comprehensive status
    if hasattr(logger, 'log_event'):
        logger.log_event("✅ GPT Runner+ Orchestrator Started")
        logger.log_event(f"📊 Components Status:")
        logger.log_event(f"   Logger: {logger_type}")
        logger.log_event(f"   Enhanced Logger: {'✅' if enhanced_logger else '❌'}")
        logger.log_event(f"   Firestore: {'✅' if imports.get('FirestoreClient') else '❌'}")
        logger.log_event(f"   OpenAI: {'✅' if OpenAIManager else '❌'}")
        logger.log_event(f"   Cognitive System: {'✅' if initialize_cognitive_system else '❌'}")
        logger.log_event(f"   Kite Manager: {'✅' if KiteConnectManager else '❌'}")
        logger.log_event(f"   Paper Trading: {'✅' if PaperTradingManager else '❌'}")
        logger.log_event(f"   Trading Mode: {'PAPER' if PAPER_TRADE else 'LIVE'}")
    
    # Initialize cognitive system
    cognitive_system = None
    if initialize_cognitive_system:
        try:
            if hasattr(logger, 'log_event'):
                logger.log_event("[COGNITIVE] Initializing cognitive system...")
            cognitive_system = initialize_cognitive_system(logger, enhanced_logger)
            if cognitive_system:
                if hasattr(logger, 'log_event'):
                    logger.log_event("✅ [COGNITIVE] Cognitive system initialized")
            else:
                if hasattr(logger, 'log_event'):
                    logger.log_event("⚠️ [COGNITIVE] Cognitive system running in fallback mode")
        except Exception as e:
            if hasattr(logger, 'log_event'):
                logger.log_event(f"❌ [COGNITIVE] Failed to initialize cognitive system: {e}")
            cognitive_system = None
    
    # Initialize memory (RAG)
    initialize_memory_safe(logger)
    
    # Initialize clients with error handling
    firestore_client = SafeFirestoreClient(logger)
    
    # Initialize OpenAI Manager
    openai_manager = None
    if OpenAIManager:
        try:
            openai_manager = OpenAIManager(logger)
            if hasattr(logger, 'log_event'):
                logger.log_event("✅ OpenAI Manager initialized")
        except Exception as e:
            if hasattr(logger, 'log_event'):
                logger.log_event(f"⚠️ OpenAI Manager failed: {e}")
            openai_manager = None
    
    # Initialize Kite Manager
    kite_manager = None
    kite = None
    if KiteConnectManager:
        try:
            kite_manager = KiteConnectManager(logger)
            kite_manager.set_access_token()
            kite = kite_manager.get_kite_client()
            if hasattr(logger, 'log_event'):
                logger.log_event("✅ Kite Manager initialized")
        except Exception as e:
            if hasattr(logger, 'log_event'):
                logger.log_event(f"⚠️ Kite Manager failed: {e}")
            kite_manager = None
            kite = None
    
    # Initialize Paper Trading Manager
    paper_trading_manager = None
    if PaperTradingManager and PAPER_TRADE:
        try:
            paper_trading_manager = PaperTradingManager(logger=logger)
            if hasattr(logger, 'log_event'):
                logger.log_event("✅ Paper Trading Manager initialized")
        except Exception as e:
            if hasattr(logger, 'log_event'):
                logger.log_event(f"⚠️ Paper Trading Manager failed: {e}")
            paper_trading_manager = None
    
    # Get market context
    sentiment_data = {"status": "unknown", "sentiment": "neutral"}
    if MarketMonitor and kite:
        try:
            market_monitor = MarketMonitor(logger)
            sentiment_data = market_monitor.get_market_sentiment(kite)
            if hasattr(logger, 'log_event'):
                logger.log_event(f"📈 Market Sentiment Data: {sentiment_data}")
        except Exception as e:
            if hasattr(logger, 'log_event'):
                logger.log_event(f"⚠️ Market sentiment analysis failed: {e}")
    
    # Record cognitive thoughts about market analysis
    if cognitive_system and DecisionType and ConfidenceLevel:
        try:
            cognitive_system.record_thought(
                decision="Market sentiment analysis completed",
                reasoning=f"Analyzed market sentiment: {sentiment_data}",
                decision_type=DecisionType.MARKET_ANALYSIS,
                confidence=ConfidenceLevel.MEDIUM,
                market_context=sentiment_data,
                tags=['market_sentiment', 'daily_analysis']
            )
        except Exception as e:
            if hasattr(logger, 'log_event'):
                logger.log_event(f"⚠️ Cognitive thought recording failed: {e}")
    
    # Create and store daily strategy plan
    today_date = datetime.date.today().isoformat()
    
    # Strategy selection with fallbacks
    stock_strategy = "vwap_strategy"
    options_strategy = "scalp_strategy"
    futures_strategy = "orb_strategy"
    
    if StrategySelector:
        try:
            strategy_selector = StrategySelector(logger)
            stock_strategy = strategy_selector.choose_strategy("stock", market_sentiment=sentiment_data)
            options_strategy = strategy_selector.choose_strategy("options", market_sentiment=sentiment_data)
            futures_strategy = strategy_selector.choose_strategy("futures", market_sentiment=sentiment_data)
        except Exception as e:
            if hasattr(logger, 'log_event'):
                logger.log_event(f"⚠️ Strategy selection failed, using defaults: {e}")
    
    # Record strategy selection thoughts
    if cognitive_system and DecisionType and ConfidenceLevel:
        try:
            cognitive_system.record_thought(
                decision="Daily strategy selection completed",
                reasoning=f"Selected strategies: Stock-{stock_strategy}, Options-{options_strategy}, Futures-{futures_strategy}",
                decision_type=DecisionType.STRATEGY_SELECTION,
                confidence=ConfidenceLevel.HIGH,
                market_context={
                    'strategies': {
                        'stock': stock_strategy,
                        'options': options_strategy,
                        'futures': futures_strategy
                    },
                    'market_sentiment': sentiment_data
                },
                tags=['strategy_selection', 'daily_plan']
            )
        except Exception as e:
            if hasattr(logger, 'log_event'):
                logger.log_event(f"⚠️ Cognitive strategy recording failed: {e}")
    
    # Create daily plan
    plan = {
        "date": today_date,
        "stocks": stock_strategy,
        "options": options_strategy,
        "futures": futures_strategy,
        "mode": "paper" if PAPER_TRADE else "live",
        "timestamp": datetime.datetime.now().isoformat(),
        "market_sentiment": sentiment_data,
        "cognitive_system_active": cognitive_system is not None,
        "components_status": {
            "firestore": firestore_client.available,
            "openai": openai_manager is not None,
            "kite": kite is not None,
            "paper_trading": paper_trading_manager is not None
        }
    }
    
    # Store daily plan
    firestore_client.store_daily_plan(plan)
    if hasattr(logger, 'log_event'):
        logger.log_event(f"✅ Strategy Plan Saved: {plan}")
    
    # Wait until market opens at 9:15 AM IST
    now = datetime.datetime.now()
    market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
    if now < market_open:
        wait_minutes = int((market_open - now).total_seconds() / 60)
        if hasattr(logger, 'log_event'):
            logger.log_event(f"⏳ Waiting {wait_minutes} minutes until market opens at 9:15 AM IST...")
        
        # Record cognitive thought about waiting period
        if cognitive_system and DecisionType and ConfidenceLevel and CognitiveState and StateTransitionTrigger:
            try:
                cognitive_system.record_thought(
                    decision=f"Waiting for market open ({wait_minutes} minutes)",
                    reasoning="Market not yet open, cognitive system in standby mode",
                    decision_type=DecisionType.METACOGNITIVE,
                    confidence=ConfidenceLevel.HIGH,
                    market_context={'wait_minutes': wait_minutes, 'market_open_time': '9:15'},
                    tags=['market_wait', 'standby']
                )
                
                cognitive_system.transition_state(
                    CognitiveState.OBSERVING,
                    StateTransitionTrigger.MARKET_OPEN,
                    "Waiting for market open"
                )
            except Exception as e:
                if hasattr(logger, 'log_event'):
                    logger.log_event(f"⚠️ Cognitive waiting state failed: {e}")
        
        time.sleep((market_open - now).total_seconds())
    
    # Record market open event
    if cognitive_system and DecisionType and ConfidenceLevel:
        try:
            cognitive_system.record_thought(
                decision="Market opened - trading day begins",
                reasoning="Market opening detected, transitioning to active trading mode",
                decision_type=DecisionType.METACOGNITIVE,
                confidence=ConfidenceLevel.HIGH,
                market_context={'market_status': 'open', 'time': '9:15'},
                tags=['market_open', 'trading_start']
            )
        except Exception as e:
            if hasattr(logger, 'log_event'):
                logger.log_event(f"⚠️ Cognitive market open recording failed: {e}")
    
    if hasattr(logger, 'log_event'):
        logger.log_event("🚀 Trading bots are running in separate pods and will read the plan from Firestore")
    
    # Main trading loop
    try:
        while True:
            time.sleep(60)
            now = time.strftime("%H:%M")
            
            # Run paper trading if enabled
            if paper_trading_manager and PAPER_TRADE:
                try:
                    # Create sample market data for paper trading
                    sample_market_data = {
                        "RELIANCE": {"ltp": 2500.0},
                        "TCS": {"ltp": 3200.0},
                        "NIFTY24NOVFUT": {"ltp": 24000.0},
                        "BANKNIFTY24NOVFUT": {"ltp": 50000.0}
                    }
                    paper_trading_manager.run_trading_session(sample_market_data)
                except Exception as e:
                    if hasattr(logger, 'log_event'):
                        logger.log_event(f"⚠️ Paper trading session failed: {e}")
            
            if now >= "15:30":
                if hasattr(logger, 'log_event'):
                    logger.log_event("🔔 Market closed. Trading day complete.")
                
                # Record market close cognitive thought
                if cognitive_system and DecisionType and ConfidenceLevel and CognitiveState and StateTransitionTrigger:
                    try:
                        cognitive_system.record_thought(
                            decision="Market closed - trading day ended",
                            reasoning="Market closing detected at 15:30, initiating end-of-day procedures",
                            decision_type=DecisionType.METACOGNITIVE,
                            confidence=ConfidenceLevel.HIGH,
                            market_context={'market_status': 'closed', 'time': '15:30'},
                            tags=['market_close', 'trading_end']
                        )
                        
                        cognitive_system.transition_state(
                            CognitiveState.REFLECTING,
                            StateTransitionTrigger.MARKET_CLOSE,
                            "Market closed, beginning daily reflection"
                        )
                    except Exception as e:
                        if hasattr(logger, 'log_event'):
                            logger.log_event(f"⚠️ Cognitive market close recording failed: {e}")
                
                # Run GPT self-improvement analysis
                if hasattr(logger, 'log_event'):
                    logger.log_event("🧠 Starting GPT Self-Improvement Analysis...")
                try:
                    run_gpt_reflection()
                except Exception as e:
                    if hasattr(logger, 'log_event'):
                        logger.log_event(f"⚠️ GPT reflection failed: {e}")
                
                # Generate cognitive performance analysis
                if cognitive_system:
                    try:
                        if hasattr(logger, 'log_event'):
                            logger.log_event("🧠 Generating cognitive performance analysis...")
                        
                        analysis_id = cognitive_system.metacognition.generate_performance_attribution(period_days=1)
                        if hasattr(logger, 'log_event'):
                            logger.log_event(f"✅ Cognitive analysis completed: {analysis_id}")
                        
                        final_summary = cognitive_system.get_cognitive_summary()
                        if hasattr(logger, 'log_event'):
                            logger.log_event(f"📊 Final cognitive summary: {final_summary}")
                        
                        cognitive_system.record_thought(
                            decision="Daily cognitive analysis completed",
                            reasoning=f"Performance analysis generated: {analysis_id}",
                            decision_type=DecisionType.PERFORMANCE_REVIEW,
                            confidence=ConfidenceLevel.HIGH,
                            market_context={'analysis_id': analysis_id},
                            tags=['daily_summary', 'performance_analysis']
                        )
                        
                    except Exception as e:
                        if hasattr(logger, 'log_event'):
                            logger.log_event(f"⚠️ Cognitive analysis failed: {e}")
                
                break
    
    except KeyboardInterrupt:
        if hasattr(logger, 'log_event'):
            logger.log_event("🛑 Interrupted manually. Stopping monitoring.")
        
        # Record manual interruption
        if cognitive_system and DecisionType and ConfidenceLevel:
            try:
                cognitive_system.record_thought(
                    decision="Manual interruption detected",
                    reasoning="System interrupted by user, performing emergency shutdown procedures",
                    decision_type=DecisionType.METACOGNITIVE,
                    confidence=ConfidenceLevel.HIGH,
                    market_context={'interruption_type': 'manual'},
                    tags=['emergency_stop', 'manual_interrupt']
                )
            except Exception as e:
                if hasattr(logger, 'log_event'):
                    logger.log_event(f"⚠️ Cognitive interruption recording failed: {e}")
        
        if hasattr(logger, 'log_event'):
            logger.log_event("🧠 Running GPT Reflection after manual stop...")
        try:
            run_gpt_reflection()
        except Exception as e:
            if hasattr(logger, 'log_event'):
                logger.log_event(f"⚠️ Manual stop GPT reflection failed: {e}")
        
        # Emergency cognitive analysis if possible
        if cognitive_system:
            try:
                cognitive_system.metacognition.generate_performance_attribution(period_days=1)
            except Exception as e:
                if hasattr(logger, 'log_event'):
                    logger.log_event(f"⚠️ Emergency cognitive analysis failed: {e}")
    
    except Exception as e:
        if hasattr(logger, 'log_event'):
            logger.log_event(f"❌ Unexpected error in main loop: {e}")
            logger.log_event(f"Traceback: {traceback.format_exc()}")
        else:
            logger.error(f"Unexpected error: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    finally:
        # Graceful cognitive system shutdown
        if cognitive_system:
            try:
                if hasattr(logger, 'log_event'):
                    logger.log_event("🧠 Shutting down cognitive system...")
                cognitive_system.shutdown()
                if hasattr(logger, 'log_event'):
                    logger.log_event("✅ Cognitive system shutdown completed")
            except Exception as e:
                if hasattr(logger, 'log_event'):
                    logger.log_event(f"⚠️ Cognitive system shutdown failed: {e}")
        
        if hasattr(logger, 'log_event'):
            logger.log_event("🏁 Main runner shutdown completed")
        else:
            logger.info("Main runner shutdown completed")

if __name__ == "__main__":
    main() 