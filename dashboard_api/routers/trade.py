from fastapi import APIRouter, Depends
from typing import Dict, Any, List

from ..services.trade_service import TradeService, get_trade_service

router = APIRouter()

@router.get("/summary/daily")
async def get_daily_summary(
    trade_service: TradeService = Depends(get_trade_service)
) -> Dict[str, Any]:
    """
    Endpoint to get the daily trading summary.
    """
    return await trade_service.get_daily_summary()

@router.get("/positions/live")
async def get_live_positions(
    trade_service: TradeService = Depends(get_trade_service)
) -> List[Dict[str, Any]]:
    """
    Endpoint to get current live positions.
    """
    return await trade_service.get_live_positions()

@router.get("/trades/recent")
async def get_recent_trades(
    trade_service: TradeService = Depends(get_trade_service),
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Endpoint to get recent trades.
    """
    return await trade_service.get_recent_trades(limit=limit) 