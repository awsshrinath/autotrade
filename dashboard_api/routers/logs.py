from fastapi import APIRouter, Depends, Query
from typing import List, Dict, Any, Optional

from services.log_service import LogService, get_log_service

router = APIRouter()

@router.get("/gcs")
async def get_gcs_logs(
    log_service: LogService = Depends(get_log_service),
    prefix: Optional[str] = None,
    limit: int = 100
) -> List[str]:
    """Retrieve a list of log files from Google Cloud Storage."""
    return await log_service.list_gcs_log_files(prefix=prefix, limit=limit)

@router.get("/gcs/content")
async def get_gcs_log_content(
    file_path: str,
    log_service: LogService = Depends(get_log_service)
) -> Dict[str, Any]:
    """Get the content of a specific log file from GCS."""
    return await log_service.get_gcs_log_content(file_path=file_path)

@router.get("/firestore")
async def get_firestore_logs(
    log_service: LogService = Depends(get_log_service),
    limit: int = 100
) -> List[Dict[str, Any]]:
    """Retrieve recent logs from Firestore."""
    return await log_service.get_firestore_logs(limit=limit)

@router.get("/k8s")
async def get_k8s_pod_logs(
    pod_name: str,
    log_service: LogService = Depends(get_log_service),
    limit: int = 100
) -> List[str]:
    """Get logs for a specific Kubernetes pod."""
    return await log_service.get_k8s_pod_logs(pod_name=pod_name, limit=limit)

@router.get("/k8s/pods")
async def list_k8s_pods(
    log_service: LogService = Depends(get_log_service)
) -> List[str]:
    """List running pods in the Kubernetes cluster."""
    return await log_service.list_k8s_pods() 