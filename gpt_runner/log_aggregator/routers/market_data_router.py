from fastapi import APIRouter, HTTPException
from typing import Dict, Any

router = APIRouter()

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