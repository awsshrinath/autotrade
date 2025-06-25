# Portfolio Manager Service for Dashboard API
# This is a wrapper that imports from the main services directory

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import from the main services directory
from services.portfolio_manager import PortfolioManager, Portfolio, Position

# Re-export for dashboard API
__all__ = ['PortfolioManager', 'Portfolio', 'Position']