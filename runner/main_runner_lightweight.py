#!/usr/bin/env python3
"""
Lightweight Main Runner with Basic Functionality
===============================================

This is a simplified version of the main runner designed for low-memory environments.
It focuses on core functionality without memory-intensive features like:
- Cognitive system
- RAG/FAISS operations
- Sentence transformers

Key features:
- IST timezone handling
- Basic market monitoring
- Enhanced logging
- Crashloop prevention
"""

import datetime
import os
import time
import sys
import traceback
import signal

try:
    import pytz
    PYTZ_AVAILABLE = True
except ImportError:
    PYTZ_AVAILABLE = False
    print("Warning: pytz not available. Using UTC time.")

# Add project paths
sys.path.insert(0, '/app')
sys.path.insert(0, '/app/runner')

# Global variables for imports
LogLevel = None
LogCategory = None

def setup_signal_handlers():
    """Setup signal handlers for graceful shutdown"""
    def signal_handler(signum, frame):
        print(f"🛑 Received signal {signum}. Initiating graceful shutdown...")
        global SHUTDOWN_REQUESTED
        SHUTDOWN_REQUESTED = True
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

# Global shutdown flag
SHUTDOWN_REQUESTED = False

def get_ist_time():
    """Get current time in IST timezone"""
    if PYTZ_AVAILABLE:
        ist = pytz.timezone('Asia/Kolkata')
        return datetime.datetime.now(ist)
    else:
        # Fallback to UTC if pytz not available
        return datetime.datetime.utcnow()

def is_market_open():
    """Check if market is currently open"""
    now = get_ist_time()
    current_time = now.time()
    market_open_time = datetime.time(9, 15)
    market_close_time = datetime.time(15, 30)
    return market_open_time <= current_time <= market_close_time

def safe_initialize_loggers():
    """Initialize loggers with minimal memory footprint"""
    global LogLevel, LogCategory
    
    # Set up fallback classes first
    class FallbackLogLevel:
        DEBUG = "DEBUG"
        INFO = "INFO" 
        WARNING = "WARNING"
        ERROR = "ERROR"
        CRITICAL = "CRITICAL"
    
    class FallbackLogCategory:
        TRADE = "TRADE"
        SYSTEM = "SYSTEM"
        ERROR = "ERROR"
        COGNITIVE = "COGNITIVE"
    
    LogLevel = FallbackLogLevel
    LogCategory = FallbackLogCategory
    
    try:
        # Use basic logger only to minimize memory usage
        from runner.logger import Logger
        
        today_date = get_ist_time().strftime("%Y-%m-%d")
        
        # Skip creating daily folders to save memory
        logger = Logger(today_date)
        
        # Skip enhanced logging to save memory - use basic logging only
        enhanced_logger = None
        print("✅ Basic logger initialized (memory-optimized mode)")
        return logger, enhanced_logger, f"lightweight_runner_{int(time.time())}", today_date
        
    except Exception as e:
        print(f"❌ Logger initialization failed: {e}")
        return None, None, None, None

def lightweight_market_monitor(logger, enhanced_logger):
    """Lightweight market monitoring without heavy dependencies"""
    print("📊 Starting lightweight market monitoring...")
    
    last_log_time = None
    error_count = 0
    max_errors = 5
    
    while not SHUTDOWN_REQUESTED and is_market_open():
        try:
            now = get_ist_time()
            
            # Log status every 10 minutes
            if last_log_time is None or (now - last_log_time).total_seconds() >= 600:
                print(f"⏰ Lightweight monitoring active - IST time: {now.strftime('%H:%M:%S')}")
                logger.log_event(f"📊 Lightweight monitoring heartbeat - IST: {now.strftime('%H:%M:%S')}")
                
                # Only use enhanced logger if available
                if enhanced_logger:
                    enhanced_logger.log_system_event(
                        "Lightweight monitoring heartbeat",
                        data={
                            'ist_time': now.strftime('%H:%M:%S'),
                            'market_open': is_market_open(),
                            'error_count': error_count,
                            'mode': 'lightweight'
                        }
                    )
                
                last_log_time = now
                error_count = 0
            
            # Sleep for 30 seconds
            time.sleep(30)
            
        except KeyboardInterrupt:
            print("🛑 Received keyboard interrupt during monitoring")
            break
            
        except Exception as e:
            error_count += 1
            print(f"❌ Error in monitoring (#{error_count}): {e}")
            
            if error_count >= max_errors:
                print(f"❌ Too many consecutive errors ({max_errors}), stopping monitoring")
                break
            
            # Wait before retrying
            wait_time = min(30, 5 * error_count)
            print(f"⏳ Waiting {wait_time} seconds before retry...")
            time.sleep(wait_time)
    
    print("🔔 Market closed or monitoring stopped.")

def main():
    """Lightweight main function"""
    print("🚀 Lightweight GPT Runner Starting")
    print("=" * 50)
    
    # Setup signal handlers
    setup_signal_handlers()
    
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
    
    # Log startup - only use enhanced logger if available
    if enhanced_logger:
        enhanced_logger.log_system_event(
            "Lightweight GPT Runner Started",
            data={
                'session_id': session_id,
                'date': today_date,
                'startup_time': now.isoformat(),
                'market_open': is_market_open(),
                'lightweight_mode': True
            }
        )
    
    logger.log_event("✅ Lightweight GPT Runner Started")
    
    try:
        while not SHUTDOWN_REQUESTED:
            if is_market_open():
                print("🚀 Market is open - starting lightweight monitoring...")
                logger.log_event("🚀 Market is open - starting lightweight monitoring")
                
                try:
                    # Start lightweight monitoring
                    lightweight_market_monitor(logger, enhanced_logger)
                except Exception as e:
                    print(f"❌ Monitoring function failed: {e}")
                    print(f"🔄 Will retry in 60 seconds...")
                
                # After monitoring, wait a bit before checking again if market is open
                print("💤 Market monitoring finished. Waiting before next check...")
                time.sleep(60)
            else:
                print("Market is closed. Sleeping for 5 minutes...")
                # Sleep for 5 minutes if market is closed
                for _ in range(300):
                    if SHUTDOWN_REQUESTED:
                        break
                    time.sleep(1)

    except KeyboardInterrupt:
        print("\n🛑 Keyboard interrupt detected. Shutting down...")
    
    finally:
        print("✅ Lightweight execution completed successfully")
        
        # Shutdown loggers
        if enhanced_logger:
            enhanced_logger.shutdown()
        
        print("🔄 Starting graceful shutdown...")
        # Add any other cleanup logic here
        print("👋 Lightweight Runner shutdown complete")

if __name__ == "__main__":
    main() 