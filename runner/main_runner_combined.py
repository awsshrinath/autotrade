import datetime
import os
import time
import sys

# Add the project root to the Python path to ensure proper imports
sys.path.insert(0, '/app')
sys.path.insert(0, '/app/runner')
sys.path.insert(0, '/app/gpt_runner')

# Import from absolute paths to avoid conflicts
try:
    from gpt_runner.rag.faiss_firestore_adapter import sync_firestore_to_faiss
    from gpt_runner.rag.rag_worker import embed_logs_for_today
except ImportError as e:
    print(f"Warning: Could not import RAG modules: {e}")
    # Define placeholder functions
    def sync_firestore_to_faiss(*args, **kwargs):
        print("RAG sync not available - using placeholder")
        return None
    
    def embed_logs_for_today(*args, **kwargs):
        print("RAG embedding not available - using placeholder")
        return None

from runner.common_utils import create_daily_folders
from runner.firestore_client import FirestoreClient

# Handle potential circular import with gpt_self_improvement_monitor
try:
    from runner.gpt_self_improvement_monitor import run_gpt_reflection
    GPT_REFLECTION_AVAILABLE = True
except ImportError as e:
    print(f"Warning: GPT reflection not available due to import issue: {e}")
    GPT_REFLECTION_AVAILABLE = False
    
    def run_gpt_reflection(*args, **kwargs):
        """Fallback function when GPT reflection is not available"""
        print("Warning: GPT reflection functionality not available")
        return None

from runner.kiteconnect_manager import KiteConnectManager
from runner.logger import Logger
from runner.enhanced_logger import create_enhanced_logger, LogLevel, LogCategory
from runner.market_data import MarketDataFetcher, TechnicalIndicators
from runner.market_monitor import MarketMonitor, CorrelationMonitor, MarketRegimeClassifier
from runner.openai_manager import OpenAIManager
from runner.strategy_selector import StrategySelector
from runner.cognitive_system import create_cognitive_system, CognitiveSystem
from runner.cognitive_state_machine import CognitiveState, StateTransitionTrigger
from runner.thought_journal import DecisionType, ConfidenceLevel
from runner.enhanced_trade_manager import create_enhanced_trade_manager, TradeRequest

# Load trading mode (PAPER or LIVE)
PAPER_TRADE = os.getenv("PAPER_TRADE", "true").lower() == "true"


def initialize_memory(logger):
    """Initialize RAG memory by syncing FAISS with Firestore and embedding today's logs"""
    logger.log_event("[RAG] Syncing FAISS with Firestore...")
    sync_firestore_to_faiss()
    logger.log_event("[RAG] Embedding today's logs...")
    embed_logs_for_today()


def initialize_cognitive_system(logger, enhanced_logger=None):
    """Initialize cognitive system with memory reconstruction"""
    try:
        logger.log_event("[COGNITIVE] Initializing cognitive system...")
        
        if enhanced_logger:
            enhanced_logger.log_event(
                "Cognitive system initialization started",
                LogLevel.INFO,
                LogCategory.SYSTEM,
                data={'component': 'cognitive_system'},
                source="cognitive_init"
            )
        
        # Create cognitive system with automatic memory loading
        cognitive_system = create_cognitive_system(
            project_id=os.getenv("GCP_PROJECT_ID"),
            enable_background_processing=True,
            logger=logger
        )
        
        # Record initial thought about system startup
        cognitive_system.record_thought(
            decision="System startup initiated",
            reasoning="Daily cluster recreation detected, cognitive system initializing with memory reconstruction",
            decision_type=DecisionType.METACOGNITIVE,
            confidence=ConfidenceLevel.HIGH,
            market_context={
                'startup_time': datetime.datetime.utcnow().isoformat(),
                'paper_trade_mode': PAPER_TRADE
            },
            tags=['system_startup', 'daily_initialization']
        )
        
        # Perform cognitive system health check
        health_status = cognitive_system._perform_health_checks()
        logger.log_event(f"[COGNITIVE] Health check results: {health_status}")
        
        if enhanced_logger:
            enhanced_logger.log_event(
                "Cognitive system health check completed",
                LogLevel.INFO,
                LogCategory.SYSTEM,
                data={
                    'health_status': health_status,
                    'all_healthy': all(health_status.values())
                },
                source="cognitive_health"
            )
        
        if not all(health_status.values()):
            logger.log_event(f"[COGNITIVE] Warning: Some health checks failed: {health_status}")
        else:
            logger.log_event("[COGNITIVE] All cognitive systems operational")
        
        # Get cognitive summary
        summary = cognitive_system.get_cognitive_summary()
        logger.log_event(f"[COGNITIVE] System summary: Working memory: {summary.get('memory_summary', {}).get('working_memory_count', 0)} items")
        
        return cognitive_system
        
    except Exception as e:
        logger.log_event(f"[COGNITIVE] Failed to initialize cognitive system: {e}")
        if enhanced_logger:
            enhanced_logger.log_event(
                "Cognitive system initialization failed",
                LogLevel.ERROR,
                LogCategory.SYSTEM,
                data={'error': str(e)},
                source="cognitive_init"
            )
        return None


def main():
    """Main orchestrator function that coordinates all trading activities"""
    today_date = datetime.datetime.now().strftime("%Y-%m-%d")
    
    # Initialize enhanced logger for Firestore and GCS logging
    session_id = f"main_runner_{int(time.time())}"
    enhanced_logger = create_enhanced_logger(
        session_id=session_id,
        enable_gcs=True,
        enable_firestore=True
    )
    
    # Initialize basic logger for backward compatibility
    logger = Logger(today_date)
    create_daily_folders(today_date)
    
    # Log startup with enhanced logger
    enhanced_logger.log_event(
        "GPT Runner+ Orchestrator Started",
        LogLevel.INFO,
        LogCategory.SYSTEM,
        data={
            'session_id': session_id,
            'date': today_date,
            'startup_time': datetime.datetime.now().isoformat()
        },
        source="main_orchestrator"
    )
    
    logger.log_event("✅ GPT Runner+ Orchestrator Started")

    # Initialize cognitive system first for memory reconstruction
    cognitive_system = initialize_cognitive_system(logger, enhanced_logger)

    # Init memory + RAG sync
    initialize_memory(logger)

    # Initialize clients
    firestore_client = FirestoreClient(logger)
    OpenAIManager(logger)
    kite_manager = KiteConnectManager(logger)
    kite_manager.set_access_token()
    kite = kite_manager.get_kite_client()

    # Initialize the Enhanced Trade Manager
    trade_manager = create_enhanced_trade_manager(
        logger=logger, 
        kite_manager=kite_manager, 
        firestore_client=firestore_client,
        cognitive_system=cognitive_system
    )
    trade_manager.start_trading_session()

    # Get market context
    market_monitor = MarketMonitor(logger)
    sentiment_data = market_monitor.get_market_sentiment(kite)
    logger.log_event(f"📈 Market Sentiment Data: {sentiment_data}")

    # Record cognitive thoughts about market analysis
    if cognitive_system:
        cognitive_system.record_thought(
            decision="Market sentiment analysis completed",
            reasoning=f"Analyzed market sentiment: {sentiment_data}",
            decision_type=DecisionType.MARKET_ANALYSIS,
            confidence=ConfidenceLevel.MEDIUM,
            market_context=sentiment_data,
            tags=['market_sentiment', 'daily_analysis']
        )

    # Create and store daily strategy plan with cognitive input
    strategy_selector = StrategySelector(logger)
    
    # Record strategy selection thoughts
    stock_strategy = strategy_selector.choose_strategy("stock", market_sentiment=sentiment_data)
    options_strategy = strategy_selector.choose_strategy("options", market_sentiment=sentiment_data)
    futures_strategy = strategy_selector.choose_strategy("futures", market_sentiment=sentiment_data)
    
    if cognitive_system:
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

    plan = {
        "date": today_date,
        "stocks": stock_strategy,
        "options": options_strategy,
        "futures": futures_strategy,
        "mode": "paper" if PAPER_TRADE else "live",
        "timestamp": datetime.datetime.now().isoformat(),
        "market_sentiment": sentiment_data,
        "cognitive_system_active": cognitive_system is not None
    }
    firestore_client.store_daily_plan(plan)
    logger.log_event(f"✅ Strategy Plan Saved: {plan}")

    # Main trading loop
    while True:
        now = datetime.datetime.now()
        if now.hour >= 15 and now.minute >= 25:
            logger.log_event("🛑 Market closed. Exiting main loop.")
            break

        if now.hour >= 9 and now.minute >= 15:
            try:
                # Example of running a strategy. This would be driven by signals.
                trade_manager.run_strategy_once(stock_strategy, "bullish", "stock")
            except Exception as e:
                logger.log_event(f"Error during trading loop: {e}")

        time.sleep(60) # Wait for 1 minute before next cycle

    # End of day processes
    trade_manager.stop_trading_session()
    
    # Run GPT Self-Improvement Monitor after market hours
    if GPT_REFLECTION_AVAILABLE:
        run_gpt_reflection(today_date)

    # Log shutdown
    logger.log_event("✅ GPT Runner+ Orchestrator Shutdown")
    enhanced_logger.log_event("GPT Runner+ Orchestrator Shutdown", LogLevel.INFO, LogCategory.SYSTEM)


if __name__ == "__main__":
    main()
