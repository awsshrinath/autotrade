"""
Router for GPT log summarization and analysis endpoints.
"""

from fastapi import APIRouter, HTTPException, Body, Depends, status
from typing import Dict, Any, Optional
import structlog
import json # For safely parsing source_params

from ..services.gpt_service import get_gpt_service, GPTLogService
from ..services.gcs_service import get_gcs_service, GCSLogService
from ..services.firestore_service import get_firestore_service, FirestoreLogService
from ..services.k8s_service import get_k8s_service, K8sLogService
from ..models.log_models import (
    SummaryRequest, SummaryResponse, LogSource,
    GCSLogFilterParams, FirestoreLogFilterParams, K8sLogFilterParams # For parsing source_params
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

MAX_LOG_CONTENT_LENGTH_FOR_SUMMARY = 500000 # 500KB limit for dynamic fetching to prevent abuse

async def _fetch_dynamic_logs(
    log_source: LogSource, 
    source_params: Dict[str, Any],
    gcs_service: GCSLogService,
    firestore_service: FirestoreLogService,
    k8s_service: K8sLogService
) -> str:
    """Helper to fetch logs dynamically based on source and params."""
    log_content_parts = []
    
    if log_source == LogSource.GCS:
        # Expects: bucket_name, file_path in source_params
        gcs_params = GCSLogFilterParams(**source_params) # Validate params
        if not gcs_params.bucket_name or not gcs_params.prefix: # prefix is used as file_path here
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="For GCS source, 'bucket_name' and 'prefix' (as file_path) are required in source_params.")
        
        content_stream = await gcs_service.stream_log_content(bucket_name=gcs_params.bucket_name, file_path=gcs_params.prefix)
        current_length = 0
        async for chunk in content_stream:
            log_content_parts.append(chunk)
            current_length += len(chunk)
            if current_length > MAX_LOG_CONTENT_LENGTH_FOR_SUMMARY:
                logger.warning("GCS log content truncated for summary due to size limit", file_path=gcs_params.prefix)
                log_content_parts.append("\n... [LOG TRUNCATED DUE TO SIZE LIMIT FOR SUMMARY] ...")
                break
    
    elif log_source == LogSource.FIRESTORE:
        # Expects: collection_name, and optional filters (e.g., document_id or simple query)
        # For simplicity, let's assume source_params contains collection_name and document_id for one doc
        # or a simple query that returns a few docs to concatenate.
        # More complex Firestore querying for summarization would need careful design.
        fs_params = FirestoreLogFilterParams(**source_params)
        if not fs_params.collection_name:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="For Firestore source, 'collection_name' is required in source_params.")
        
        # Example: fetch a single document if document_id is provided
        if fs_params.filters and len(fs_params.filters) == 1 and fs_params.filters[0].field == "document_id" and fs_params.filters[0].operator == "==":
            doc_id = fs_params.filters[0].value
            doc = await firestore_service.get_document_by_id(fs_params.collection_name, doc_id)
            if doc: log_content_parts.append(json.dumps(doc.data, indent=2))
        else:
            # Generic query - limit to a few docs for summarization to avoid huge content
            docs, _ = await firestore_service.query_documents(collection_name=fs_params.collection_name, filters=fs_params.filters, limit=5)
            for doc_obj in docs:
                log_content_parts.append(json.dumps(doc_obj.data, indent=2))
                if sum(len(p) for p in log_content_parts) > MAX_LOG_CONTENT_LENGTH_FOR_SUMMARY:
                    logger.warning("Firestore log content truncated for summary due to size limit")
                    log_content_parts.append("\n... [LOG TRUNCATED DUE TO SIZE LIMIT FOR SUMMARY] ...")
                    break
        if not log_content_parts:
            logger.warning("No documents found for Firestore summarization with given params", params=source_params)
            return "No matching Firestore documents found to summarize."
            
    elif log_source == LogSource.KUBERNETES:
        k8s_params = K8sLogFilterParams(**source_params)
        if not k8s_params.pod_name_pattern: # Assuming pod_name_pattern is used as pod_name here
             raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="For Kubernetes source, 'pod_name_pattern' (as pod_name) is required in source_params.")
        
        # Use a reasonable default for tail_lines if not specified for summary
        tail_lines = k8s_params.tail_lines or 1000 
        if tail_lines * 150 > MAX_LOG_CONTENT_LENGTH_FOR_SUMMARY: # Avg 150 chars/line
            tail_lines = MAX_LOG_CONTENT_LENGTH_FOR_SUMMARY // 150
            logger.warning("Kubernetes tail_lines adjusted for summary due to size limit", new_tail_lines=tail_lines)

        logs_str = await k8s_service.get_pod_logs(
            pod_name=k8s_params.pod_name_pattern, # pod_name_pattern used as pod_name
            namespace=k8s_params.namespace, 
            container=k8s_params.container_name,
            since_seconds=k8s_params.since_seconds,
            tail_lines=tail_lines,
            timestamps=True
        )
        log_content_parts.append(logs_str[:MAX_LOG_CONTENT_LENGTH_FOR_SUMMARY])
        if len(logs_str) > MAX_LOG_CONTENT_LENGTH_FOR_SUMMARY:
            log_content_parts.append("\n... [LOG TRUNCATED DUE TO SIZE LIMIT FOR SUMMARY] ...")
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported log_source for dynamic fetching: {log_source}")
    
    return "\n".join(log_content_parts)

@router.post("/", response_model=SummaryResponse)
async def summarize_logs_endpoint(
    request_body: SummaryRequest = Body(...),
    gpt_service: GPTLogService = Depends(get_gpt_service),
    gcs_service: GCSLogService = Depends(get_gcs_service),       # Inject other services
    firestore_service: FirestoreLogService = Depends(get_firestore_service),
    k8s_service: K8sLogService = Depends(get_k8s_service)
    # current_user: Any = Depends(get_current_active_user) # Placeholder
):
    """Summarize log content using GPT. 
    Provide either raw log_content or specify log_source and source_params to fetch logs.
    """
    log_content_to_summarize: Optional[str] = None
    try:
        logger.info("Received log summarization request", summary_type=request_body.summary_type, log_source=request_body.log_source)
        
        if request_body.log_content:
            log_content_to_summarize = request_body.log_content
        elif request_body.log_source and request_body.source_params:
            logger.info("Fetching logs dynamically for summarization", log_source=request_body.log_source, params=request_body.source_params)
            log_content_to_summarize = await _fetch_dynamic_logs(
                request_body.log_source, 
                request_body.source_params, 
                gcs_service, 
                firestore_service, 
                k8s_service
            )
        else:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Either log_content or (log_source and source_params) must be provided.")
        
        if not log_content_to_summarize or log_content_to_summarize.strip() == "":
             logger.warning("No log content available to summarize after fetching/processing.")
             # Return a specific response or raise error, for now, summarize empty content
             # which GPT service should handle (e.g. return "No content to summarize")
             pass # Let gpt_service handle empty string

        summary_data = await gpt_service.summarize_logs(
            log_content=log_content_to_summarize,
            summary_type=request_body.summary_type
        )
        return SummaryResponse(**summary_data)

    except HTTPException as http_exc:
        logger.error(f"HTTPException in summary endpoint: {http_exc.detail}", status_code=http_exc.status_code)
        raise http_exc
    except Exception as e:
        logger.error("Error during log summarization", error=str(e), request_body=request_body.model_dump_json(exclude_none=True))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}")

@router.post("/analyze-patterns", response_model=Dict[str, Any])
async def analyze_log_patterns_endpoint(
    request_body: SummaryRequest = Body(...), 
    gpt_service: GPTLogService = Depends(get_gpt_service),
    gcs_service: GCSLogService = Depends(get_gcs_service),
    firestore_service: FirestoreLogService = Depends(get_firestore_service),
    k8s_service: K8sLogService = Depends(get_k8s_service)
    # current_user: Any = Depends(get_current_active_user) # Placeholder
):
    """Analyze log content for patterns and insights using GPT.
    Provide either raw log_content or specify log_source and source_params to fetch logs.
    """
    log_content_to_analyze: Optional[str] = None
    try:
        logger.info("Received log pattern analysis request", log_source=request_body.log_source)
        if request_body.log_content:
            log_content_to_analyze = request_body.log_content
        elif request_body.log_source and request_body.source_params:
            logger.info("Fetching logs dynamically for pattern analysis", log_source=request_body.log_source, params=request_body.source_params)
            log_content_to_analyze = await _fetch_dynamic_logs(
                request_body.log_source, 
                request_body.source_params, 
                gcs_service, 
                firestore_service, 
                k8s_service
            )
        else:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Either log_content or (log_source and source_params) must be provided for pattern analysis.")
        
        if not log_content_to_analyze or log_content_to_analyze.strip() == "":
            logger.warning("No log content available to analyze after fetching/processing.")
            return {"analysis": "No log content provided or fetched for analysis.", "metadata": {}}

        analysis_data = await gpt_service.analyze_log_patterns(
            log_content=log_content_to_analyze
        )
        return analysis_data
    except HTTPException as http_exc:
        logger.error(f"HTTPException in pattern analysis endpoint: {http_exc.detail}", status_code=http_exc.status_code)
        raise http_exc
    except Exception as e:
        logger.error("Error during log pattern analysis", error=str(e), request_body=request_body.model_dump_json(exclude_none=True))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}")

# Add more summarization/analysis endpoints here later (e.g., get_cache_stats) 