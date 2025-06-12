"""
Router for Google Cloud Storage (GCS) log retrieval endpoints.
"""

from fastapi import APIRouter, HTTPException, Query, Depends, Body, status
from typing import List, Optional, Dict, Any
from datetime import datetime
import structlog

from ..services.gcs_service import get_gcs_service, GCSLogService
from ..models.log_models import (
    GCSLogEntry, GCSLogFile, GCSLogFilterParams, LogSource, 
    PaginatedResponse, PaginationParams
)
# from ..utils.security import get_current_active_user # Placeholder for auth
from ..utils.security import get_current_active_user
from ..utils.config import get_config # For checking if auth is enabled

logger = structlog.get_logger(__name__)

app_config = get_config()
router_dependencies = []
if app_config.auth_enabled:
    router_dependencies.append(Depends(get_current_active_user))

router = APIRouter(dependencies=router_dependencies)

@router.get("/files", response_model=PaginatedResponse[GCSLogFile])
async def list_gcs_log_files(
    filters: GCSLogFilterParams = Depends(),
    pagination: PaginationParams = Depends(),
    gcs_service: GCSLogService = Depends(get_gcs_service)
    # current_user: Any = Depends(get_current_active_user) # Placeholder
):
    """List available log files in a GCS bucket with filtering and pagination."""
    try:
        logger.info("Listing GCS log files", filters=filters.model_dump_json(exclude_none=True), pagination=pagination.model_dump_json())
        
        all_files = await gcs_service.list_log_files(
            bucket_name=filters.bucket_name,
            prefix=filters.prefix,
            file_pattern=filters.file_pattern,
            start_time=filters.start_time,
            end_time=filters.end_time,
            min_size_bytes=filters.min_size_bytes,
            max_size_bytes=filters.max_size_bytes
        )
        
        total_files = len(all_files)
        start_idx = pagination.skip
        end_idx = pagination.skip + pagination.limit
        paginated_files = all_files[start_idx:end_idx]
        
        return PaginatedResponse[GCSLogFile](
            total=total_files,
            items=paginated_files,
            skip=pagination.skip,
            limit=pagination.limit
        )
    except Exception as e:
        logger.error("Error listing GCS log files", error=str(e), filters=filters.model_dump_json(exclude_none=True))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/file/content", response_model=GCSLogEntry) # Simplified: returns content of one file as one entry for now
async def get_gcs_log_file_content(
    bucket_name: str = Query(..., description="GCS bucket name."),
    file_path: str = Query(..., description="Full path to the log file in the bucket."),
    gcs_service: GCSLogService = Depends(get_gcs_service)
    # current_user: Any = Depends(get_current_active_user) # Placeholder
):
    """Get the content of a specific log file from GCS."""
    try:
        logger.info("Fetching GCS log file content", bucket_name=bucket_name, file_path=file_path)
        
        file_info = await gcs_service.get_file_info(bucket_name=bucket_name, file_path=file_path)
        if not file_info:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Log file not found")

        # Stream content - for simplicity in this model, we fetch all and put in raw_content
        # In a real scenario with very large files, streaming to client might be better or chunked response
        content_stream = await gcs_service.stream_log_content(bucket_name=bucket_name, file_path=file_path)
        
        raw_content = ""
        async for chunk in content_stream:
            raw_content += chunk
            if len(raw_content) > 1024 * 1024 * 5: # Limit to 5MB for safety in this example
                logger.warning("Log content truncated for GCSLogEntry due to size limit", file_path=file_path)
                raw_content += "\n... [TRUNCATED DUE TO SIZE] ..."
                break
        
        return GCSLogEntry(
            log_file=file_info,
            raw_content=raw_content,
            timestamp=datetime.utcnow(), # Timestamp of access, not log entry itself
            message=f"Content of {file_path}"
        )
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error("Error fetching GCS log file content", error=str(e), bucket_name=bucket_name, file_path=file_path)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/search", response_model=PaginatedResponse[GCSLogEntry])
async def search_gcs_logs(
    filters: GCSLogFilterParams = Body(...),
    pagination: PaginationParams = Depends(),
    gcs_service: GCSLogService = Depends(get_gcs_service)
    # current_user: Any = Depends(get_current_active_user) # Placeholder
):
    """Search for a keyword within GCS log files matching filter criteria."""
    if not filters.keyword:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Search keyword must be provided.")
    
    try:
        logger.info("Searching GCS logs", filters=filters.model_dump_json(exclude_none=True), pagination=pagination.model_dump_json())
        
        # Search results will be a list of dictionaries, each with 'file_info' and 'matches' (list of strings)
        search_results_raw = await gcs_service.search_logs(
            keyword=filters.keyword,
            bucket_name=filters.bucket_name,
            prefix=filters.prefix,
            file_pattern=filters.file_pattern,
            start_time=filters.start_time,
            end_time=filters.end_time
        )
        
        # Convert raw search results to GCSLogEntry model
        all_log_entries: List[GCSLogEntry] = []
        for res_item in search_results_raw:
            file_info = GCSLogFile(**res_item["file_info"].model_dump()) # Assuming service returns GCSLogFile Pydantic model
            for match_detail in res_item["matches"]:
                # match_detail could be a string or a dict like {"line_number": ..., "content": ..., "timestamp": ...}
                # Assuming it's {"content": str, "line_number": Optional[int], "timestamp": Optional[datetime]}
                raw_content = match_detail.get("content", "")
                line_number = match_detail.get("line_number")
                entry_timestamp = match_detail.get("timestamp") or datetime.utcnow()

                all_log_entries.append(GCSLogEntry(
                    log_file=file_info,
                    raw_content=raw_content,
                    line_number=line_number,
                    timestamp=entry_timestamp,
                    message=f"Match found in {file_info.path}"
                ))

        total_entries = len(all_log_entries)
        start_idx = pagination.skip
        end_idx = pagination.skip + pagination.limit
        paginated_entries = all_log_entries[start_idx:end_idx]
        
        return PaginatedResponse[GCSLogEntry](
            total=total_entries,
            items=paginated_entries,
            skip=pagination.skip,
            limit=pagination.limit
        )
    except Exception as e:
        logger.error("Error searching GCS logs", error=str(e), filters=filters.model_dump_json(exclude_none=True))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# Add more GCS-related endpoints here later (e.g., get_log_content, search_logs) 