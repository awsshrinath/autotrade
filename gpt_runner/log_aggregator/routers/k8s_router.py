"""
Router for Kubernetes (K8s) pod log retrieval endpoints.
"""

from fastapi import APIRouter, HTTPException, Query, Depends, Body, status
from typing import List, Optional, Dict, Any
from datetime import datetime
import structlog

from ..services.k8s_service import get_k8s_service, K8sLogService
from ..models.log_models import (
    K8sLogEntry, K8sPodInfo, K8sLogFilterParams, K8sEventInfo,
    LogSource, PaginatedResponse, PaginationParams
)
# from ..utils.security import get_current_active_user # Placeholder
from ..utils.security import get_current_active_user
from ..utils.config import get_config # For checking if auth is enabled

logger = structlog.get_logger(__name__)

app_config = get_config()
router_dependencies = []
if app_config.auth_enabled:
    router_dependencies.append(Depends(get_current_active_user))

router = APIRouter(dependencies=router_dependencies)

@router.get("/pods", response_model=PaginatedResponse[K8sPodInfo])
async def list_kubernetes_pods(
    namespace: Optional[str] = Query(None, description="Kubernetes namespace. Uses default if not specified."),
    label_selector: Optional[str] = Query(None, description="Label selector to filter pods."),
    field_selector: Optional[str] = Query(None, description="Field selector to filter pods."),
    pagination: PaginationParams = Depends(),
    k8s_service: K8sLogService = Depends(get_k8s_service)
    # current_user: Any = Depends(get_current_active_user) # Placeholder
):
    """List pods in a Kubernetes namespace with filtering and pagination."""
    try:
        effective_namespace = namespace or k8s_service.config.kubernetes_namespace
        logger.info("Listing K8s pods", namespace=effective_namespace, label_selector=label_selector, field_selector=field_selector, pagination=pagination.model_dump_json())
        
        all_pods_raw = await k8s_service.get_pods(
            namespace=effective_namespace,
            label_selector=label_selector,
            field_selector=field_selector
        )
        # K8sPodInfo is already the Pydantic model from the service
        all_pods = [K8sPodInfo(**pod_data) for pod_data in all_pods_raw]

        total_pods = len(all_pods)
        start_idx = pagination.skip
        end_idx = pagination.skip + pagination.limit
        paginated_pods = all_pods[start_idx:end_idx]
        
        return PaginatedResponse[K8sPodInfo](
            total=total_pods,
            items=paginated_pods,
            skip=pagination.skip,
            limit=pagination.limit
        )
    except Exception as e:
        logger.error("Error listing K8s pods", error=str(e), namespace=namespace)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/{pod_name}/logs", response_model=PaginatedResponse[K8sLogEntry])
async def get_kubernetes_pod_logs(
    pod_name: str,
    filter_params: K8sLogFilterParams = Body(default_factory=K8sLogFilterParams),
    pagination: PaginationParams = Depends(), # For potential future use if service supports chunked streaming
    k8s_service: K8sLogService = Depends(get_k8s_service)
    # current_user: Any = Depends(get_current_active_user) # Placeholder
):
    """Get logs from a specific Kubernetes pod, with filtering.
    Note: True pagination for raw log streams is complex. This endpoint primarily uses K8s API's `tail_lines` and `since_seconds`/`since_time` for log slicing.
    The PaginatedResponse here will contain log lines as items.
    """
    effective_namespace = filter_params.namespace or k8s_service.config.kubernetes_namespace
    try:
        logger.info("Fetching K8s pod logs", pod_name=pod_name, namespace=effective_namespace, filters=filter_params.model_dump_json(exclude_none=True))
        
        raw_logs_str = await k8s_service.get_pod_logs(
            pod_name=pod_name,
            namespace=effective_namespace,
            container=filter_params.container_name,
            since_seconds=filter_params.since_seconds,
            since_time=filter_params.since_time,
            tail_lines=filter_params.tail_lines,
            timestamps=filter_params.timestamps
        )

        # Further client-side filtering if needed (e.g., log_level, keyword if not done by service)
        if filter_params.log_level:
            raw_logs_str = await k8s_service.filter_logs_by_level(raw_logs_str, [lvl.strip() for lvl in filter_params.log_level.split(",")])
        
        # Keyword search on the retrieved/filtered logs
        # This is client-side search on potentially large string. More efficient if service can do it.
        if filter_params.keyword:
            lines = raw_logs_str.splitlines()
            matched_lines = [line for line in lines if filter_params.keyword.lower() in line.lower()]
            raw_logs_str = "\n".join(matched_lines)

        log_lines = raw_logs_str.splitlines()
        
        # Create K8sLogEntry objects for each line
        log_entries: List[K8sLogEntry] = []
        for line_content in log_lines:
            entry_timestamp_str = k8s_service._extract_timestamp_from_line(line_content)
            entry_timestamp = None
            if entry_timestamp_str:
                try:
                    # Attempt to parse. This logic might need refinement based on actual timestamp formats.
                    entry_timestamp = datetime.fromisoformat(entry_timestamp_str.replace('Z', '+00:00'))
                except ValueError:
                    # Fallback or log warning if specific parsing fails
                    try: # Try common non-ISO format
                        entry_timestamp = datetime.strptime(entry_timestamp_str, '%Y-%m-%d %H:%M:%S') 
                    except ValueError:
                         logger.debug("Could not parse extracted timestamp", timestamp_str=entry_timestamp_str, log_line=line_content)
            
            log_entries.append(K8sLogEntry(
                pod_name=pod_name,
                namespace=effective_namespace,
                container_name=filter_params.container_name, # May need to get actual from pod if not specified
                raw_content=line_content,
                timestamp=entry_timestamp or datetime.utcnow(), # Fallback to now if no timestamp
                message=line_content[:200] # Truncated message for brevity
            ))
        
        # Paginate the processed log entries
        total_entries = len(log_entries)
        start_idx = pagination.skip
        end_idx = pagination.skip + pagination.limit
        paginated_entries = log_entries[start_idx:end_idx]

        return PaginatedResponse[K8sLogEntry](
            total=total_entries,
            items=paginated_entries,
            skip=pagination.skip,
            limit=pagination.limit
        )
    except ValueError as ve:
        logger.warning("Invalid input for K8s pod logs", error=str(ve), filters=filter_params.model_dump_json(exclude_none=True))
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(ve))
    except Exception as e:
        logger.error("Error fetching K8s pod logs", error=str(e), pod_name=pod_name, namespace=effective_namespace)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/{pod_name}/events", response_model=List[K8sEventInfo])
async def get_kubernetes_pod_events(
    pod_name: str,
    namespace: Optional[str] = Query(None, description="Kubernetes namespace of the pod."),
    k8s_service: K8sLogService = Depends(get_k8s_service)
    # current_user: Any = Depends(get_current_active_user) # Placeholder
):
    """Get events related to a specific Kubernetes pod."""
    effective_namespace = namespace or k8s_service.config.kubernetes_namespace
    try:
        logger.info("Fetching K8s pod events", pod_name=pod_name, namespace=effective_namespace)
        events_raw = await k8s_service.get_pod_events(pod_name=pod_name, namespace=effective_namespace)
        # K8sEventInfo is already the Pydantic model from the service
        events = [K8sEventInfo(**event_data) for event_data in events_raw]
        return events
    except Exception as e:
        logger.error("Error fetching K8s pod events", error=str(e), pod_name=pod_name, namespace=effective_namespace)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/search-logs", response_model=PaginatedResponse[K8sLogEntry])
async def search_kubernetes_pod_logs(
    search_query: str = Query(..., description="Keyword or regex to search in logs."),
    filter_params: K8sLogFilterParams = Body(default_factory=K8sLogFilterParams),
    pagination: PaginationParams = Depends(),
    k8s_service: K8sLogService = Depends(get_k8s_service)
    # current_user: Any = Depends(get_current_active_user) # Placeholder
):
    """Search logs across multiple Kubernetes pods based on criteria."""
    effective_namespace = filter_params.namespace or k8s_service.config.kubernetes_namespace
    try:
        logger.info("Searching K8s pod logs", query=search_query, namespace=effective_namespace, filters=filter_params.model_dump_json(exclude_none=True))
        
        # The service's search_pod_logs returns List[Dict[str, Any]] where each dict has 'pod' and 'matches'
        # We need to convert this into a flat list of K8sLogEntry items for PaginatedResponse
        raw_search_results = await k8s_service.search_pod_logs(
            query=search_query,
            namespace=effective_namespace,
            pod_name_pattern=filter_params.pod_name_pattern,
            since_hours=filter_params.since_seconds // 3600 if filter_params.since_seconds else 24 # Rough conversion
        )
        
        all_log_entries: List[K8sLogEntry] = []
        for result_item in raw_search_results:
            pod_info = K8sPodInfo(**result_item["pod"]) # Assuming service returns K8sPodInfo compatible dict
            for match in result_item["matches"]:
                # Assuming match is a dict like {"line_number": int, "content": str, "timestamp": str}
                entry_timestamp = None
                if match.get("timestamp"):
                    try:
                        entry_timestamp = datetime.fromisoformat(match["timestamp"].replace('Z', '+00:00'))
                    except ValueError:
                        logger.debug("Could not parse timestamp from search match", timestamp_str=match["timestamp"])
                
                all_log_entries.append(K8sLogEntry(
                    pod_name=pod_info.name,
                    namespace=pod_info.namespace,
                    container_name=pod_info.containers[0].name if pod_info.containers else None, # Best guess
                    raw_content=match["content"],
                    timestamp=entry_timestamp or datetime.utcnow(),
                    message=f"Match found in {pod_info.name}: {match['content'][:100]}...",
                    metadata={"line_number": match.get("line_number")}
                ))
        
        total_entries = len(all_log_entries)
        start_idx = pagination.skip
        end_idx = pagination.skip + pagination.limit
        paginated_entries = all_log_entries[start_idx:end_idx]
        
        return PaginatedResponse[K8sLogEntry](
            total=total_entries,
            items=paginated_entries,
            skip=pagination.skip,
            limit=pagination.limit
        )
    except Exception as e:
        logger.error("Error searching K8s pod logs", error=str(e), query=search_query, namespace=effective_namespace)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) 