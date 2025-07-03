from fastapi import APIRouter, Depends
from typing import Dict, Any, List

from dashboard_api.services.simple_trade_service import SimpleTradeService, get_trade_service

router = APIRouter()

@router.get("/summary/daily")
async def get_daily_summary(
    trade_service: SimpleTradeService = Depends(get_trade_service)
) -> Dict[str, Any]:
    """
    Endpoint to get the daily trading summary.
    """
    return await trade_service.get_daily_summary()

@router.get("/summary/positions")
async def get_summary_positions(
    trade_service: SimpleTradeService = Depends(get_trade_service)
) -> Dict[str, Any]:
    """
    Endpoint to get position summary for risk analysis.
    """
    return await trade_service.get_summary_positions()

@router.get("/summary/strategy")
async def get_summary_strategy(
    trade_service: SimpleTradeService = Depends(get_trade_service)
) -> Dict[str, Any]:
    """
    Endpoint to get strategy performance summary.
    """
    return await trade_service.get_summary_strategy()

@router.get("/positions/live")
async def get_live_positions(
    trade_service: SimpleTradeService = Depends(get_trade_service)
) -> List[Dict[str, Any]]:
    """
    Endpoint to get current live positions.
    """
    return await trade_service.get_live_positions()

@router.get("/trades/recent")
async def get_recent_trades(
    trade_service: SimpleTradeService = Depends(get_trade_service),
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Endpoint to get recent trades.
    """
    return await trade_service.get_recent_trades(limit=limit) 