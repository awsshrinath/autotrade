from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from runner.market_monitor import MarketMonitor

router = APIRouter()

# In a real application, you would use a dependency injection system
# to manage these instances. For simplicity, we'll create them here.
market_monitor = MarketMonitor()

@router.get(
    "/regime/{instrument_id}", 
    response_model=Dict[str, Any],
    summary="Get Market Regime",
    description="Fetches the current market regime (e.g., trending, ranging) for a given instrument ID."
)
async def get_market_regime(instrument_id: int):
    """
    Get the current market regime for a given instrument.
    
    - **instrument_id**: The ID of the instrument (e.g., 256265 for NIFTY 50).
    """
    try:
        return market_monitor.get_enhanced_market_regime(instrument_id=instrument_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get(
    "/latest_candle/{instrument_token}", 
    response_model=Dict[str, Any],
    summary="Get Latest Candle",
    description="Fetches the latest candle data for a given instrument token. This is a mock endpoint for load testing."
)
async def get_latest_candle(instrument_token: int):
    """
    Get the latest candle data for a given instrument.
    
    - **instrument_token**: The token of the instrument.
    """
    # This is a simplified implementation. A real one would use the MarketDataFetcher.
    # We'll return a mock response for now to get the load test running.
    return {
        "instrument_token": instrument_token,
        "timestamp": "2025-06-11T12:00:00Z",
        "open": 18000,
        "high": 18010,
        "low": 17990,
        "close": 18005,
        "volume": 100000
    }

@router.get(
    "/correlation", 
    response_model=Dict[str, Any],
    summary="Get Correlation Matrix",
    description="Calculates and returns the correlation matrix for major market indices."
)
async def get_correlation_matrix():
    """
    Get the market correlation matrix.
    """
    try:
        return market_monitor.correlation_monitor.calculate_correlation_matrix()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 