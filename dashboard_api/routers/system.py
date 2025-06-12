from fastapi import APIRouter, Depends
from typing import Dict, Any

from ..services.system_service import SystemService, get_system_service

router = APIRouter()

@router.get("/health")
async def get_system_health(
    system_service: SystemService = Depends(get_system_service)
) -> Dict[str, Any]:
    """
    Endpoint to get the overall system health.
    """
    return await system_service.get_system_health()

@router.get("/status")
async def get_system_status(
    system_service: SystemService = Depends(get_system_service)
) -> Dict[str, Any]:
    """
    Endpoint to get a detailed status of all system components.
    """
    return await system_service.get_system_status()

@router.get("/metrics")
async def get_system_metrics(
    system_service: SystemService = Depends(get_system_service)
) -> Dict[str, Any]:
    """
    Endpoint to get system resource metrics (CPU, memory, etc.).
    """
    return system_service.get_system_metrics() 