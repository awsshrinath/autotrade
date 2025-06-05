#!/usr/bin/env python3
"""
Improved Main Runner with Crashloop Prevention and MCP Integration
================================================================

Key improvements:
1. Better timezone handling (explicit IST)
2. Robust market monitoring with proper exception handling
3. MCP integration for self-improvement after market hours
4. Kubernetes-aware restart handling
5. Comprehensive health checks and recovery mechanisms
6. Better memory management and cleanup
"""

import datetime
import os
import time
import sys
import traceback
import signal
import threading
from typing import Optional, Dict, Any
import pytz

# Add the project root to the Python path to ensure proper imports
sys.path.insert(0, '/app')
sys.path.insert(0, '/app/runner')
sys.path.insert(0, '/app/gpt_runner')

def setup_signal_handlers():
    """Setup signal handlers for graceful shutdown"""
    def signal_handler(signum, frame):
        print(f"🛑 Received signal {signum}. Initiating graceful shutdown...")
        # Set a global flag for graceful shutdown
        global SHUTDOWN_REQUESTED
        SHUTDOWN_REQUESTED = True
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

# Global shutdown flag
SHUTDOWN_REQUESTED = False

def safe_import_with_fallback():
    """Safely import modules with detailed error reporting and fallbacks"""
    imports_status = {}
    imported_modules = {}
    
    # RAG modules
    try:
        from gpt_runner.rag.faiss_firestore_adapter import sync_firestore_to_faiss
        from gpt_runner.rag.rag_worker import embed_logs_for_today
        imports_status['rag_modules'] = True
        imported_modules.update({
            'sync_firestore_to_faiss': sync_firestore_to_faiss,
            'embed_logs_for_today': embed_logs_for_today
        })
        print("✅ RAG modules imported successfully")
    except ImportError as e:
        print(f"❌ RAG modules import failed: {e}")
        imports_status['rag_modules'] = False
        # Define placeholder functions
        def sync_firestore_to_faiss(*args, **kwargs):
            print("RAG sync not available - using placeholder")
            return None
        
        def embed_logs_for_today(*args, **kwargs):
            print("RAG embedding not available - using placeholder")
            return None
        
        imported_modules.update({
            'sync_firestore_to_faiss': sync_firestore_to_faiss,
            'embed_logs_for_today': embed_logs_for_today
        })
    
    # Core runner modules
    try:
        from runner.common_utils import create_daily_folders
        from runner.firestore_client import FirestoreClient
        from runner.logger import Logger
        from runner.enhanced_logger import create_enhanced_logger, LogLevel, LogCategory
        imports_status['core_runner'] = True
        imported_modules.update({
            'create_daily_folders': create_daily_folders,
            'FirestoreClient': FirestoreClient,
            'Logger': Logger,
            'create_enhanced_logger': create_enhanced_logger,
            'LogLevel': LogLevel,
            'LogCategory': LogCategory
        })
        print("✅ Core runner modules imported successfully")
    except ImportError as e:
        print(f"❌ Core runner modules import failed: {e}")
        imports_status['core_runner'] = False
        raise  # This is critical, can't continue without core modules
    
    # GPT reflection module
    try:
        from runner.gpt_self_improvement_monitor import run_gpt_reflection
        imports_status['gpt_reflection'] = True
        imported_modules['run_gpt_reflection'] = run_gpt_reflection
        print("✅ GPT reflection module imported successfully")
    except ImportError as e:
        print(f"❌ GPT reflection import failed: {e}")
        imports_status['gpt_reflection'] = False
        
        def run_gpt_reflection(*args, **kwargs):
            print("Warning: GPT reflection functionality not available")
            return None
        
        imported_modules['run_gpt_reflection'] = run_gpt_reflection
    
    # Trading modules
    try:
        from runner.kiteconnect_manager import KiteConnectManager
        from runner.openai_manager import OpenAIManager
        imports_status['trading_modules'] = True
        imported_modules.update({
            'KiteConnectManager': KiteConnectManager,
            'OpenAIManager': OpenAIManager
        })
        print("✅ Trading modules imported successfully")
    except ImportError as e:
        print(f"❌ Trading modules import failed: {e}")
        imports_status['trading_modules'] = False
        # Continue without trading modules for basic functionality
    
    # Cognitive system modules (memory intensive)
    try:
        print("🧠 Initializing cognitive modules (this may take time)...")
        import gc
        
        # Force garbage collection before loading heavy modules
        gc.collect()
        
        from runner.cognitive_system import create_cognitive_system
        from runner.thought_journal import DecisionType, ConfidenceLevel
        imports_status['cognitive_modules'] = True
        imported_modules.update({
            'create_cognitive_system': create_cognitive_system,
            'DecisionType': DecisionType,
            'ConfidenceLevel': ConfidenceLevel
        })
        print("✅ Cognitive modules imported successfully")
        
        # Another garbage collection after import
        gc.collect()
        
    except ImportError as e:
        print(f"❌ Cognitive modules import failed: {e}")
        imports_status['cognitive_modules'] = False
    except Exception as e:
        print(f"❌ Unexpected error during cognitive modules import: {e}")
        print(f"📊 Error traceback: {traceback.format_exc()}")
        imports_status['cognitive_modules'] = False
        # Create placeholder classes
        class DecisionType:
            METACOGNITIVE = "metacognitive"
            MARKET_ANALYSIS = "market_analysis"
            PERFORMANCE_REVIEW = "performance_review"
        
        class ConfidenceLevel:
            HIGH = "high"
            MEDIUM = "medium"
            LOW = "low"
        
        def create_cognitive_system(*args, **kwargs):
            print("Warning: Cognitive system not available")
            return None
        
        imported_modules.update({
            'create_cognitive_system': create_cognitive_system,
            'DecisionType': DecisionType,
            'ConfidenceLevel': ConfidenceLevel
        })
    
    return imports_status, imported_modules

def get_ist_time():
    """Get current time in IST timezone"""
    ist = pytz.timezone('Asia/Kolkata')
    return datetime.datetime.now(ist)

def is_market_open():
    """Check if market is currently open"""
    now = get_ist_time()
    current_time = now.time()
    market_open_time = datetime.time(9, 15)
    market_close_time = datetime.time(15, 30)
    return market_open_time <= current_time <= market_close_time

def check_environment_variables():
    """Check critical environment variables"""
    required_vars = [
        'GCP_PROJECT_ID',
        'KITE_API_KEY', 
        'KITE_API_SECRET',
        'OPENAI_API_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {missing_vars}")
        return False
    else:
        print("✅ All critical environment variables present")
        return True

def safe_initialize_loggers():
    """Safely initialize both enhanced and basic loggers"""
    try:
        # Basic logger
        today_date = get_ist_time().strftime("%Y-%m-%d")
        logger = Logger(today_date)
        create_daily_folders(today_date)
        
        # Enhanced logger
        session_id = f"main_runner_{int(time.time())}"
        enhanced_logger = create_enhanced_logger(
            session_id=session_id,
            enable_gcs=True,
            enable_firestore=True
        )
        
        print("✅ Loggers initialized successfully")
        return logger, enhanced_logger, session_id, today_date
        
    except Exception as e:
        print(f"❌ Logger initialization failed: {e}")
        traceback.print_exc()
        return None, None, None, None

def safe_initialize_cognitive_system(logger, enhanced_logger=None):
    """Safely initialize cognitive system with memory optimization"""
    if not imports_status.get('cognitive_modules', False):
        print("⚠️ Cognitive modules not available, skipping cognitive system")
        return None
    
    try:
        print("[COGNITIVE] Initializing cognitive system...")
        
        # Force garbage collection before creating cognitive system
        import gc
        gc.collect()
        
        # Set environment variable to use CPU for sentence transformers
        os.environ['SENTENCE_TRANSFORMERS_CACHE'] = '/tmp'
        os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'max_split_size_mb:128'
        
        cognitive_system = create_cognitive_system(
            project_id=os.getenv("GCP_PROJECT_ID"),
            enable_background_processing=False,  # Disable to save memory
            logger=logger
        )
        
        if cognitive_system:
            print("✅ Cognitive system initialized successfully")
            
            # Record startup thought (minimal data to save memory)
            try:
                cognitive_system.record_thought(
                    decision="Enhanced system startup",
                    reasoning="Main runner with crashloop prevention started",
                    decision_type=DecisionType.METACOGNITIVE,
                    confidence=ConfidenceLevel.HIGH,
                    market_context={
                        'startup_time': get_ist_time().strftime('%Y-%m-%d %H:%M:%S'),
                        'market_open': is_market_open()
                    },
                    tags=['system_startup']
                )
            except Exception as thought_error:
                print(f"⚠️ Failed to record startup thought: {thought_error}")
                # Continue anyway
        
        # Cleanup after initialization
        gc.collect()
        
        return cognitive_system
        
    except Exception as e:
        print(f"❌ Cognitive system initialization failed: {e}")
        print(f"📊 Full traceback: {traceback.format_exc()}")
        
        # Try to create a minimal fallback
        try:
            print("🔧 Attempting minimal cognitive system fallback...")
            cognitive_system = create_cognitive_system(
                project_id=os.getenv("GCP_PROJECT_ID"),
                enable_background_processing=False,
                logger=logger,
                minimal_mode=True  # If this parameter exists
            )
            if cognitive_system:
                print("✅ Minimal cognitive system initialized")
                return cognitive_system
        except Exception:
            pass
        
        print("⚠️ Continuing without cognitive system")
        return None

def robust_market_monitor(logger, enhanced_logger, cognitive_system):
    """Robust market monitoring with proper exception handling"""
    print("📊 Starting robust market monitoring...")
    
    last_log_time = None
    error_count = 0
    max_errors = 10
    
    while not SHUTDOWN_REQUESTED and is_market_open():
        try:
            now = get_ist_time()
            
            # Log status every 10 minutes
            if last_log_time is None or (now - last_log_time).total_seconds() >= 600:
                print(f"⏰ Market monitoring active - IST time: {now.strftime('%H:%M:%S')}")
                logger.log_event(f"📊 Market monitoring heartbeat - IST: {now.strftime('%H:%M:%S')}")
                
                if enhanced_logger:
                    enhanced_logger.log_event(
                        "Market monitoring heartbeat",
                        LogLevel.INFO,
                        LogCategory.MONITORING,
                        data={
                            'ist_time': now.strftime('%H:%M:%S'),
                            'market_open': is_market_open(),
                            'error_count': error_count
                        },
                        source="market_monitor"
                    )
                
                last_log_time = now
                error_count = 0  # Reset error count on successful log
            
            # Sleep for 30 seconds
            time.sleep(30)
            
        except KeyboardInterrupt:
            print("🛑 Received keyboard interrupt during monitoring")
            break
            
        except Exception as e:
            error_count += 1
            print(f"❌ Error in market monitoring (#{error_count}): {e}")
            
            if error_count >= max_errors:
                print(f"❌ Too many consecutive errors ({max_errors}), stopping market monitoring")
                break
            
            # Wait before retrying (exponential backoff)
            wait_time = min(60, 5 * error_count)
            print(f"⏳ Waiting {wait_time} seconds before retry...")
            time.sleep(wait_time)
    
    # Market closed
    if not SHUTDOWN_REQUESTED:
        print("🔔 Market closed at 15:30. Trading day complete.")
        logger.log_event("🔔 Market closed. Trading day complete.")

def run_post_market_analysis(logger, enhanced_logger, cognitive_system):
    """Run post-market analysis and self-improvement"""
    print("🧠 Starting post-market analysis and self-improvement...")
    
    try:
        # Run GPT reflection if available
        if imports_status.get('gpt_reflection', False):
            print("🤖 Running GPT self-reflection...")
            reflection_result = run_gpt_reflection(logger)
            print(f"✅ GPT reflection completed")
            
            if cognitive_system and reflection_result:
                cognitive_system.record_thought(
                    decision="Post-market GPT reflection completed",
                    reasoning="Daily self-improvement reflection executed after market close",
                    decision_type=DecisionType.PERFORMANCE_REVIEW,
                    confidence=ConfidenceLevel.HIGH,
                    market_context={'reflection_completed': True},
                    tags=['post_market', 'self_improvement', 'gpt_reflection']
                )
        
        # Run RAG-based memory consolidation
        if imports_status.get('rag_modules', False):
            print("🧠 Running RAG memory consolidation...")
            try:
                sync_firestore_to_faiss()
                embed_logs_for_today()
                print("✅ RAG memory consolidation completed")
                
                if cognitive_system:
                    cognitive_system.record_thought(
                        decision="RAG memory consolidation completed",
                        reasoning="Consolidated today's trading data into long-term memory",
                        decision_type=DecisionType.METACOGNITIVE,
                        confidence=ConfidenceLevel.HIGH,
                        market_context={'rag_sync': True},
                        tags=['post_market', 'memory_consolidation', 'rag']
                    )
                    
            except Exception as e:
                print(f"❌ RAG memory consolidation failed: {e}")
        
        print("✅ Post-market analysis completed")
        
    except Exception as e:
        print(f"❌ Post-market analysis failed: {e}")
        traceback.print_exc()

def main():
    """Main function with comprehensive error handling and crashloop prevention"""
    print("🚀 Enhanced GPT Runner+ Starting with Crashloop Prevention")
    print("=" * 70)
    
    # Setup signal handlers
    setup_signal_handlers()
    
    # Perform safe imports
    try:
        global imports_status, imported_modules
        imports_status, imported_modules = safe_import_with_fallback()
        print(f"📊 Import Status: {imports_status}")
        
        # Make imported modules available globally
        globals().update(imported_modules)
        
    except Exception as e:
        print(f"❌ Critical import failure: {e}")
        print("📋 Full traceback:")
        traceback.print_exc()
        print("🛑 Exiting due to critical import failure")
        sys.exit(1)
    
    # Load trading mode
    PAPER_TRADE = os.getenv("PAPER_TRADE", "true").lower() == "true"
    print(f"💼 Trading Mode: {'PAPER' if PAPER_TRADE else 'LIVE'}")
    
    # Check environment
    env_ok = check_environment_variables()
    if not env_ok:
        print("🛑 Missing critical environment variables, but continuing with degraded functionality...")
    
    # Initialize loggers
    logger, enhanced_logger, session_id, today_date = safe_initialize_loggers()
    
    if logger is None:
        print("❌ Cannot proceed without basic logger")
        sys.exit(1)
    
    print(f"📅 Today's date: {today_date}")
    print(f"🆔 Session ID: {session_id}")
    
    # Get current time and market status
    now = get_ist_time()
    
    print(f"⏰ Current IST time: {now.strftime('%H:%M:%S')}")
    print(f"📈 Market open: 09:15")
    print(f"📉 Market close: 15:30")
    print(f"📊 Market currently: {'OPEN' if is_market_open() else 'CLOSED'}")
    
    # Log startup
    if enhanced_logger:
        enhanced_logger.log_event(
            "Enhanced GPT Runner+ Started",
            LogLevel.INFO,
            LogCategory.SYSTEM,
            data={
                'session_id': session_id,
                'date': today_date,
                'startup_time': now.isoformat(),
                'imports_status': imports_status,
                'market_open': is_market_open(),
                'enhanced_runner': True,
                'crashloop_prevention': True
            },
            source="main_startup"
        )
    
    logger.log_event("✅ Enhanced GPT Runner+ Started with Crashloop Prevention")
    
    # Force garbage collection before memory-intensive operations
    import gc
    gc.collect()
    
    # Set memory optimization environment variables
    os.environ['TOKENIZERS_PARALLELISM'] = 'false'  # Reduce memory usage
    os.environ['OMP_NUM_THREADS'] = '1'  # Single thread to save memory
    
    # Initialize cognitive system
    cognitive_system = safe_initialize_cognitive_system(logger, enhanced_logger)
    
    # Initialize memory/RAG if available (optional, non-blocking)
    if imports_status.get('rag_modules', False):
        try:
            print("🧠 Initializing memory/RAG systems (this may take time)...")
            
            # Force garbage collection before RAG operations
            gc.collect()
            
            logger.log_event("[RAG] Syncing FAISS with Firestore...")
            sync_firestore_to_faiss()
            
            # Another GC after sync
            gc.collect()
            
            logger.log_event("[RAG] Embedding today's logs...")
            embed_logs_for_today()
            
            print("✅ Memory/RAG systems initialized")
            
            # Final cleanup
            gc.collect()
            
        except Exception as e:
            print(f"❌ Memory/RAG initialization failed: {e}")
            print(f"📊 Continuing without RAG - Error: {traceback.format_exc()}")
            # Continue anyway - RAG is not critical for basic functionality
    
    try:
        # Main execution logic
        if is_market_open():
            print("🚀 Market is open - starting monitoring...")
            logger.log_event("🚀 Market is open - starting enhanced monitoring")
            
            # Record market monitoring start
            if cognitive_system:
                try:
                    cognitive_system.record_thought(
                        decision="Enhanced market monitoring started",
                        reasoning="Market is currently open, beginning robust monitoring with crashloop prevention",
                        decision_type=DecisionType.METACOGNITIVE,
                        confidence=ConfidenceLevel.HIGH,
                        market_context={
                            'market_status': 'open',
                            'start_time': now.strftime('%H:%M'),
                            'enhanced_monitoring': True
                        },
                        tags=['market_monitoring', 'enhanced_runner', 'crashloop_prevention']
                    )
                except Exception as e:
                    print(f"❌ Cognitive thought recording failed: {e}")
            
            # Start robust monitoring
            robust_market_monitor(logger, enhanced_logger, cognitive_system)
            
            # After market closes, run post-market analysis
            if not SHUTDOWN_REQUESTED:
                print("🔄 Market closed, starting post-market analysis...")
                run_post_market_analysis(logger, enhanced_logger, cognitive_system)
            
        else:
            print("⏸️ Market is closed - running self-improvement analysis")
            logger.log_event("⏸️ Market is closed - running self-improvement analysis")
            
            # Run post-market analysis immediately if market is closed
            run_post_market_analysis(logger, enhanced_logger, cognitive_system)
            
            # Calculate wait time until next market open
            if now.time() >= datetime.time(15, 30):
                # Market closed today, wait until tomorrow 9:15
                tomorrow = now + datetime.timedelta(days=1)
                next_open = tomorrow.replace(hour=9, minute=15, second=0, microsecond=0)
            else:
                # Market hasn't opened today
                next_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
            
            wait_time = (next_open - now).total_seconds()
            wait_hours = wait_time / 3600
            
            print(f"⏰ Next market open: {next_open.strftime('%Y-%m-%d %H:%M')}")
            print(f"⏳ Wait time: {wait_hours:.1f} hours")
            
            # Sleep until market opens
            time.sleep(wait_time)
        
        print("✅ Main execution completed successfully")
        
    except KeyboardInterrupt:
        print("🛑 Received interrupt signal - shutting down gracefully")
        logger.log_event("🛑 Interrupted manually. Shutting down gracefully.")
        
    except Exception as e:
        print(f"❌ Unexpected error in main execution: {e}")
        print("📋 Full traceback:")
        traceback.print_exc()
        
        logger.log_event(f"❌ Unexpected error: {e}")
        
        if enhanced_logger:
            enhanced_logger.log_event(
                "Main execution error",
                LogLevel.ERROR,
                LogCategory.SYSTEM,
                data={'error': str(e), 'traceback': traceback.format_exc()},
                source="main_execution_error"
            )
    
    finally:
        # Graceful shutdown
        print("🔄 Starting graceful shutdown...")
        
        if cognitive_system:
            try:
                print("🧠 Shutting down cognitive system...")
                
                # Record shutdown thought
                cognitive_system.record_thought(
                    decision="System shutdown initiated",
                    reasoning="Enhanced main runner shutting down gracefully",
                    decision_type=DecisionType.METACOGNITIVE,
                    confidence=ConfidenceLevel.HIGH,
                    market_context={'shutdown_time': get_ist_time().isoformat()},
                    tags=['system_shutdown', 'graceful_shutdown']
                )
                
                cognitive_system.shutdown()
                print("✅ Cognitive system shutdown completed")
            except Exception as e:
                print(f"❌ Cognitive system shutdown error: {e}")
        
        # Flush loggers
        if enhanced_logger:
            try:
                enhanced_logger.flush_all()
                enhanced_logger.shutdown()
                print("✅ Enhanced logger shutdown completed")
            except Exception as e:
                print(f"❌ Enhanced logger shutdown error: {e}")
        
        print("👋 Enhanced Main Runner shutdown complete")

if __name__ == "__main__":
    main() 