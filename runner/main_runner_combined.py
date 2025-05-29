import datetime
import os
import time

from gpt_runner.rag.faiss_firestore_adapter import sync_firestore_to_faiss
from gpt_runner.rag.rag_worker import embed_logs_for_today
from runner.common_utils import create_daily_folders
from runner.firestore_client import FirestoreClient
from runner.gpt_self_improvement_monitor import run_gpt_reflection
from runner.kiteconnect_manager import KiteConnectManager
from runner.logger import Logger
from runner.enhanced_logger import create_enhanced_logger, LogLevel, LogCategory
from runner.market_monitor import MarketMonitor
from runner.openai_manager import OpenAIManager
from runner.strategy_selector import StrategySelector
from runner.cognitive_system import create_cognitive_system, CognitiveSystem
from runner.cognitive_state_machine import CognitiveState, StateTransitionTrigger
from runner.thought_journal import DecisionType, ConfidenceLevel

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

    # Wait until market opens at 9:15 AM IST
    now = datetime.datetime.now()
    market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
    if now < market_open:
        wait_minutes = int((market_open - now).total_seconds() / 60)
        logger.log_event(
            f"⏳ Waiting {wait_minutes} minutes until market opens at 9:15 AM IST..."
        )
        
        # Record cognitive thought about waiting period
        if cognitive_system:
            cognitive_system.record_thought(
                decision=f"Waiting for market open ({wait_minutes} minutes)",
                reasoning="Market not yet open, cognitive system in standby mode",
                decision_type=DecisionType.METACOGNITIVE,
                confidence=ConfidenceLevel.HIGH,
                market_context={'wait_minutes': wait_minutes, 'market_open_time': '9:15'},
                tags=['market_wait', 'standby']
            )
            
            # Transition to observing state during wait
            cognitive_system.transition_state(
                CognitiveState.OBSERVING,
                StateTransitionTrigger.MARKET_OPEN,
                "Waiting for market open"
            )
        
        time.sleep((market_open - now).total_seconds())

    # Record market open event
    if cognitive_system:
        cognitive_system.record_thought(
            decision="Market opened - trading day begins",
            reasoning="Market opening detected, transitioning to active trading mode",
            decision_type=DecisionType.METACOGNITIVE,
            confidence=ConfidenceLevel.HIGH,
            market_context={'market_status': 'open', 'time': '9:15'},
            tags=['market_open', 'trading_start']
        )

    # Note: In Kubernetes, we don't need to start bots manually
    # The bots are deployed separately and will read the plan from Firestore
    logger.log_event(
        "🚀 Trading bots are running in separate pods and will read the plan from Firestore"
    )

    try:
        # Monitor the market until close
        while True:
            time.sleep(60)
            now = time.strftime("%H:%M")
            if now >= "15:30":
                logger.log_event("🔔 Market closed. Trading day complete.")

                # Record market close cognitive thought
                if cognitive_system:
                    cognitive_system.record_thought(
                        decision="Market closed - trading day ended",
                        reasoning="Market closing detected at 15:30, initiating end-of-day procedures",
                        decision_type=DecisionType.METACOGNITIVE,
                        confidence=ConfidenceLevel.HIGH,
                        market_context={'market_status': 'closed', 'time': '15:30'},
                        tags=['market_close', 'trading_end']
                    )
                    
                    # Transition to reflection state
                    cognitive_system.transition_state(
                        CognitiveState.REFLECTING,
                        StateTransitionTrigger.MARKET_CLOSE,
                        "Market closed, beginning daily reflection"
                    )

                # Run GPT self-improvement analysis
                logger.log_event("🧠 Starting GPT Self-Improvement Analysis...")
                run_gpt_reflection()  # Run reflection for all bots
                
                # Generate cognitive performance analysis
                if cognitive_system:
                    logger.log_event("🧠 Generating cognitive performance analysis...")
                    try:
                        analysis_id = cognitive_system.metacognition.generate_performance_attribution(period_days=1)
                        logger.log_event(f"✅ Cognitive analysis completed: {analysis_id}")
                        
                        # Get final cognitive summary
                        final_summary = cognitive_system.get_cognitive_summary()
                        logger.log_event(f"📊 Final cognitive summary: {final_summary}")
                        
                        # Record end-of-day reflection
                        cognitive_system.record_thought(
                            decision="Daily cognitive analysis completed",
                            reasoning=f"Performance analysis generated: {analysis_id}",
                            decision_type=DecisionType.PERFORMANCE_REVIEW,
                            confidence=ConfidenceLevel.HIGH,
                            market_context={'analysis_id': analysis_id},
                            tags=['daily_summary', 'performance_analysis']
                        )
                        
                    except Exception as e:
                        logger.log_event(f"❌ Cognitive analysis failed: {e}")
                
                break

    except KeyboardInterrupt:
        logger.log_event("🛑 Interrupted manually. Stopping monitoring.")
        
        # Record manual interruption
        if cognitive_system:
            cognitive_system.record_thought(
                decision="Manual interruption detected",
                reasoning="System interrupted by user, performing emergency shutdown procedures",
                decision_type=DecisionType.METACOGNITIVE,
                confidence=ConfidenceLevel.HIGH,
                market_context={'interruption_type': 'manual'},
                tags=['emergency_stop', 'manual_interrupt']
            )
        
        logger.log_event("🧠 Running GPT Reflection after manual stop...")
        run_gpt_reflection()
        
        # Emergency cognitive analysis if possible
        if cognitive_system:
            try:
                cognitive_system.metacognition.generate_performance_attribution(period_days=1)
            except:
                pass
    
    finally:
        # Graceful cognitive system shutdown
        if cognitive_system:
            try:
                logger.log_event("🧠 Shutting down cognitive system...")
                cognitive_system.shutdown()
                logger.log_event("✅ Cognitive system shutdown completed")
            except Exception as e:
                logger.log_event(f"❌ Cognitive system shutdown error: {e}")


if __name__ == "__main__":
    main()
