"""
Router for Firestore log retrieval endpoints.
"""

from fastapi import APIRouter, HTTPException, Query, Body, Depends, status
from typing import List, Optional, Dict, Any
from datetime import datetime
import structlog

from ..services.firestore_service import get_firestore_service, FirestoreLogService
from ..models.log_models import (
    FirestoreLogEntry, FirestoreCollectionInfo, FirestoreLogFilterParams, 
    LogSource, PaginatedResponse, PaginationParams, FirestoreFilter
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

@router.get("/collections", response_model=List[FirestoreCollectionInfo])
async def list_firestore_collections(
    firestore_service: FirestoreLogService = Depends(get_firestore_service)
    # current_user: Any = Depends(get_current_active_user) # Placeholder
):
    """List available collections in Firestore (or specific ones configured)."""
    try:
        logger.info("Listing Firestore collections")
        collections_info = await firestore_service.get_collections_info()
        return collections_info
    except Exception as e:
        logger.error("Error listing Firestore collections", error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/query", response_model=PaginatedResponse[FirestoreLogEntry])
async def query_firestore_logs(
    filter_params: FirestoreLogFilterParams = Body(...),
    # PaginationParams are implicitly part of FirestoreLogFilterParams (limit, start_after)
    firestore_service: FirestoreLogService = Depends(get_firestore_service)
    # current_user: Any = Depends(get_current_active_user) # Placeholder
):
    """Query logs from a Firestore collection based on filter criteria."""
    try:
        logger.info("Querying Firestore logs", collection_name=filter_params.collection_name, filters=filter_params.filters)
        
        # The service method is expected to handle conversion from raw docs to FirestoreLogEntry models
        # and to return a structure compatible with PaginatedResponse if possible, or we adapt here.
        # For now, assuming service returns a list of FirestoreLogEntry and total count.

        # Convert Pydantic FirestoreFilter to the format expected by the service if necessary
        service_filters = []
        if filter_params.filters:
            for f_filter in filter_params.filters:
                service_filters.append({"field": f_filter.field, "operator": f_filter.operator, "value": f_filter.value})

        # The Firestore service itself might handle pagination differently (cursor-based)
        # So, the PaginatedResponse structure might need careful adaptation or the service needs to return total.
        
        # Let's assume the service returns a tuple: (items, total_count_or_next_cursor)
        # For true cursor-based pagination, 'total' might be unknown or very expensive.
        # We will use 'limit' from filter_params for this endpoint's pagination concept.

        documents, total_items_estimate = await firestore_service.query_documents(
            collection_name=filter_params.collection_name,
            filters=service_filters,
            order_by=filter_params.order_by,
            limit=filter_params.limit,
            start_after=filter_params.start_after
        )

        # We'll use the number of returned documents for 'items' and 'limit' for this page.
        # 'total' will be an estimate or potentially the count if small enough.
        # If total_items_estimate is a cursor, this model needs adjustment or further info.
        # For simplicity, if it's not an int, we'll assume it's just the items we got.
        
        total_count = total_items_estimate if isinstance(total_items_estimate, int) else len(documents)
        if not isinstance(total_items_estimate, int) and total_items_estimate is not None:
             logger.info("Firestore query returned a cursor for next page", next_cursor=str(total_items_estimate))

        # The skip parameter is not directly used with cursor-based pagination like Firestore's start_after.
        # The 'skip' in PaginatedResponse would represent the conceptual skip if we were page-numbering.
        # Here, it will be 0 as we are directly using start_after.

        return PaginatedResponse[FirestoreLogEntry](
            total=total_count, # This might be an estimate or just len(documents) if true total is unavailable
            items=documents,
            skip=0, # Not directly applicable with start_after, represents current page's offset
            limit=filter_params.limit
        )
    except ValueError as ve:
        logger.warning("Invalid input for Firestore query", error=str(ve), filters=filter_params.model_dump_json(exclude_none=True))
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(ve))
    except Exception as e:
        logger.error("Error querying Firestore logs", error=str(e), collection_name=filter_params.collection_name)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/document/{collection_name}/{document_id}", response_model=FirestoreLogEntry)
async def get_firestore_document(
    collection_name: str,
    document_id: str,
    firestore_service: FirestoreLogService = Depends(get_firestore_service)
    # current_user: Any = Depends(get_current_active_user) # Placeholder
):
    """Get a specific document from a Firestore collection."""
    try:
        logger.info("Fetching Firestore document", collection_name=collection_name, document_id=document_id)
        document = await firestore_service.get_document_by_id(collection_name, document_id)
        if not document:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
        return document
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error("Error fetching Firestore document", error=str(e), collection_name=collection_name, document_id=document_id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# Add more Firestore-related endpoints here later (e.g., list_collections) 