from fastapi import APIRouter, Depends
from typing import Dict, Any, List

from services.cognitive_service import CognitiveService, get_cognitive_service

router = APIRouter()

@router.get("/summary")
async def get_cognitive_summary(
    cognitive_service: CognitiveService = Depends(get_cognitive_service)
) -> Dict[str, Any]:
    """
    Endpoint to get the cognitive system summary.
    """
    return await cognitive_service.get_cognitive_summary()

@router.get("/health")
async def get_cognitive_health(
    cognitive_service: CognitiveService = Depends(get_cognitive_service)
) -> Dict[str, Any]:
    """
    Endpoint to get the health of the cognitive system.
    """
    return await cognitive_service.get_cognitive_health()

@router.get("/insights/trade")
async def get_trade_insights(
    cognitive_service: CognitiveService = Depends(get_cognitive_service)
) -> List[Dict[str, Any]]:
    """
    Endpoint to get AI-powered trade insights.
    """
    return await cognitive_service.get_trade_insights() 