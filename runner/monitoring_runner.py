import os
import sys
import threading
import time
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from runner.market_monitor import MarketMonitor
from runner.kiteconnect_manager import KiteConnectManager
from runner.firestore_client import FirestoreClient
from runner.enhanced_logging import create_trading_logger
from runner.health_server import start_health_server, run_script_with_monitoring

def run_monitoring_service():
    """Initializes and runs the market monitoring service."""
    
    session_id = f"monitoring_service_{int(time.time())}"
    logger = create_trading_logger(session_id=session_id, bot_type="monitoring-service")
    
    logger.log_system_event("Monitoring Service Initializing...")

    try:
        kite_manager = KiteConnectManager(logger=logger)
        firestore_client = FirestoreClient(logger=logger)
        
        market_monitor = MarketMonitor(
            logger=logger,
            kite_client=kite_manager.get_kite_client(),
            firestore_client=firestore_client
        )
        
        logger.log_system_event("MarketMonitor initialized. Starting main loop.")
        
        # Main monitoring loop
        while True:
            try:
                # Example: Fetch and store enhanced market regime data periodically
                market_monitor.get_enhanced_market_regime()
                logger.log_system_event("Market regime data updated successfully.")
                
                # Sleep for a configurable interval (e.g., 15 minutes)
                time.sleep(900)
                
            except Exception as e:
                logger.log_error(e, context={"source": "monitoring_loop"}, source="monitoring-service")
                # Wait longer after an error before retrying
                time.sleep(300)

    except Exception as e:
        logger.log_error(e, context={"source": "monitoring_service_main"}, source="monitoring-service", urgent=True)

def main():
    """Main entry point for the monitoring service runner."""
    
    def monitoring_logic():
        run_monitoring_service()

    # Start health server in a separate thread
    health_port = int(os.environ.get('SERVICE_PORT', 8085))
    health_thread = threading.Thread(target=start_health_server, args=(health_port,), daemon=True)
    health_thread.start()
    
    # Run the monitoring logic with process monitoring
    run_script_with_monitoring(monitoring_logic)

if __name__ == "__main__":
    main() 