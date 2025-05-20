import os

# Toggle to switch between real trading and paper trading
PAPER_TRADE = os.getenv("PAPER_TRADE", "true").lower() == "true"

# Default capital per bot (optional, adjust as needed)
DEFAULT_CAPITAL = float(os.getenv("DEFAULT_CAPITAL", 100000))

# Logging level
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
