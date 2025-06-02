# config/emergency_config.py

"""
Emergency configuration for when GCP services are not available
This provides fallback settings to keep the system running
"""

import os
import logging

# Emergency mode flag
EMERGENCY_MODE = True

# Paper trading (always True in emergency mode)
PAPER_TRADE = True

# Logging configuration
LOG_LEVEL = logging.INFO
LOG_TO_FILE = True
LOG_FILE_PATH = "/tmp/autotrade_emergency.log"

# Fallback settings
DEFAULT_STRATEGIES = {
    "stock": "vwap_strategy",
    "options": "scalp_strategy", 
    "futures": "orb_strategy"
}

DEFAULT_MARKET_SENTIMENT = {
    "status": "emergency_mode",
    "sentiment": "neutral",
    "confidence": 0.5,
    "source": "fallback"
}

# Component availability
COMPONENTS_AVAILABLE = {
    "firestore": False,
    "openai": False,
    "kite": False,
    "secret_manager": False,
    "gcs": False,
    "cognitive_system": False,
    "paper_trading": True  # Always available in emergency mode
}

# Environment variable fallbacks
def setup_emergency_env():
    """Setup emergency environment variables"""
    
    # Set paper trading mode
    os.environ["PAPER_TRADE"] = "true"
    
    # Disable GCP services
    os.environ["DISABLE_FIRESTORE"] = "true"
    os.environ["DISABLE_SECRET_MANAGER"] = "true"
    os.environ["DISABLE_GCS"] = "true"
    
    # Set emergency OpenAI key placeholder
    if not os.environ.get("OPENAI_API_KEY"):
        os.environ["OPENAI_API_KEY"] = "emergency_mode_no_key"
    
    print("🚨 Emergency configuration activated")
    print("📋 Settings:")
    print(f"   Paper Trading: {PAPER_TRADE}")
    print(f"   Emergency Mode: {EMERGENCY_MODE}")
    print(f"   Components Available: {sum(COMPONENTS_AVAILABLE.values())}/{len(COMPONENTS_AVAILABLE)}")

# Safe configuration loading
def get_safe_config():
    """Get safe configuration that works without external dependencies"""
    
    config = {
        "emergency_mode": EMERGENCY_MODE,
        "paper_trade": PAPER_TRADE,
        "log_level": LOG_LEVEL,
        "log_to_file": LOG_TO_FILE,
        "log_file_path": LOG_FILE_PATH,
        "default_strategies": DEFAULT_STRATEGIES,
        "default_market_sentiment": DEFAULT_MARKET_SENTIMENT,
        "components_available": COMPONENTS_AVAILABLE,
        "project_id": "autotrade-453303",  # For reference only
        "trading_hours": {
            "market_open": "09:15",
            "market_close": "15:30"
        },
        "capital_allocation": {
            "total": 100000.0,
            "stocks": 40000.0,
            "options": 30000.0,
            "futures": 30000.0
        }
    }
    
    return config

if __name__ == "__main__":
    setup_emergency_env()
    config = get_safe_config()
    print("Emergency configuration loaded successfully")
    print(f"Config: {config}") 