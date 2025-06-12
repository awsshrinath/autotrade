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
import pytz

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
    ist = pytz.timezone('Asia/Kolkata')
    return datetime.datetime.now(ist)

def is_market_open():
    """Check if market is currently open"""
    now = get_ist_time()
    current_time = now.time()
    market_open_time = datetime.time(9, 15)
    market_close_time = datetime.time(15, 30)
    return market_open_time <= current_time <= market_close_time

def safe_initialize_loggers():
    """Initialize loggers with fallback"""
    global LogLevel, LogCategory
    
    try:
        from runner.common_utils import create_daily_folders
        from runner.logger import Logger
        from runner.enhanced_logger import create_enhanced_logger, LogLevel as LL, LogCategory as LC
        
        # Set global variables
        LogLevel = LL
        LogCategory = LC
        
        # Basic logger
        today_date = get_ist_time().strftime("%Y-%m-%d")
        create_daily_folders(today_date)
        logger = Logger(today_date)
        
        # Enhanced logger
        session_id = f"lightweight_runner_{int(time.time())}"
        enhanced_logger = create_enhanced_logger(
            session_id=session_id,
            enable_gcs=True,
            enable_firestore=True
        )
        
        print("✅ Loggers initialized successfully")
        return logger, enhanced_logger, session_id, today_date
        
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
                
                if enhanced_logger:
                    enhanced_logger.log_event(
                        "Lightweight monitoring heartbeat",
                        LogLevel.INFO,
                        LogCategory.MONITORING,
                        data={
                            'ist_time': now.strftime('%H:%M:%S'),
                            'market_open': is_market_open(),
                            'error_count': error_count,
                            'mode': 'lightweight'
                        },
                        source="lightweight_monitor"
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
    
    # Log startup
    if enhanced_logger:
        enhanced_logger.log_event(
            "Lightweight GPT Runner Started",
            LogLevel.INFO,
            LogCategory.SYSTEM,
            data={
                'session_id': session_id,
                'date': today_date,
                'startup_time': now.isoformat(),
                'market_open': is_market_open(),
                'lightweight_mode': True
            },
            source="lightweight_startup"
        )
    
    logger.log_event("✅ Lightweight GPT Runner Started")
    
    try:
        if is_market_open():
            print("🚀 Market is open - starting lightweight monitoring...")
            logger.log_event("🚀 Market is open - starting lightweight monitoring")
            
            # Start lightweight monitoring
            lightweight_market_monitor(logger, enhanced_logger)
            
        else:
            print("⏸️ Market is closed - waiting for next open")
            logger.log_event("⏸️ Market is closed - waiting for next open")
            
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
        
        print("✅ Lightweight execution completed successfully")
        
    except KeyboardInterrupt:
        print("🛑 Received interrupt signal - shutting down gracefully")
        logger.log_event("🛑 Interrupted manually. Shutting down gracefully.")
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        print("📋 Full traceback:")
        traceback.print_exc()
        logger.log_event(f"❌ Unexpected error: {e}")
    
    finally:
        # Graceful shutdown
        print("🔄 Starting graceful shutdown...")
        
        if enhanced_logger:
            try:
                enhanced_logger.flush_all()
                enhanced_logger.shutdown()
                print("✅ Enhanced logger shutdown completed")
            except Exception as e:
                print(f"❌ Enhanced logger shutdown error: {e}")
        
        print("👋 Lightweight Runner shutdown complete")

if __name__ == "__main__":
    main() 