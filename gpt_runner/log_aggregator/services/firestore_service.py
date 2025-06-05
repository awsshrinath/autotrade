"""
Firestore service for log retrieval.
Handles connection, authentication, and document retrieval from Firestore collections.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union
from google.cloud import firestore
from google.cloud.exceptions import NotFound, Forbidden
from google.cloud.firestore_v1.base_query import FieldFilter
import structlog

from ..utils.config import get_config, get_firestore_project_id, get_firestore_collections

logger = structlog.get_logger(__name__)


class FirestoreLogService:
    """Service for retrieving logs from Firestore collections."""
    
    def __init__(self):
        self.config = get_config()
        self.client = None
        self.db = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the Firestore client with authentication."""
        try:
            # Initialize Firestore client
            # If GOOGLE_APPLICATION_CREDENTIALS is set, it will be used automatically
            project_id = get_firestore_project_id()
            self.client = firestore.Client(project=project_id)
            self.db = self.client
            
            logger.info(
                "Firestore client initialized successfully",
                project_id=project_id
            )
            
        except Exception as e:
            logger.error(
                "Failed to initialize Firestore client",
                error=str(e),
                project_id=get_firestore_project_id()
            )
            raise
    
    async def test_connection(self) -> bool:
        """Test the Firestore connection and permissions."""
        try:
            # Test connection by trying to list collections
            collections = list(self.db.collections())
            
            # Test read permissions by trying to read from a known collection
            test_collections = get_firestore_collections()
            for collection_name in test_collections:
                try:
                    collection_ref = self.db.collection(collection_name)
                    # Try to get one document to test read permissions
                    docs = collection_ref.limit(1).get()
                    logger.info(
                        "Firestore collection access test successful",
                        collection=collection_name,
                        doc_count=len(docs)
                    )
                except Exception as e:
                    logger.warning(
                        "Firestore collection access test failed",
                        collection=collection_name,
                        error=str(e)
                    )
            
            logger.info("Firestore connection test successful")
            return True
            
        except Forbidden as e:
            logger.error("Firestore access forbidden", error=str(e))
            return False
        except Exception as e:
            logger.error("Firestore connection test failed", error=str(e))
            return False
    
    async def get_documents(
        self,
        collection_name: str,
        limit: Optional[int] = None,
        order_by: Optional[str] = None,
        order_direction: str = "desc",
        filters: Optional[List[Dict[str, Any]]] = None,
        start_after: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve documents from a Firestore collection.
        
        Args:
            collection_name: Name of the Firestore collection
            limit: Maximum number of documents to return
            order_by: Field to order by
            order_direction: "asc" or "desc"
            filters: List of filter dictionaries with field, operator, value
            start_after: Document to start after for pagination
            
        Returns:
            List of document dictionaries
        """
        try:
            collection_ref = self.db.collection(collection_name)
            query = collection_ref
            
            # Apply filters
            if filters:
                for filter_dict in filters:
                    field = filter_dict.get("field")
                    operator = filter_dict.get("operator", "==")
                    value = filter_dict.get("value")
                    
                    if field and value is not None:
                        query = query.where(
                            filter=FieldFilter(field, operator, value)
                        )
            
            # Apply ordering
            if order_by:
                direction = firestore.Query.DESCENDING if order_direction == "desc" else firestore.Query.ASCENDING
                query = query.order_by(order_by, direction=direction)
            
            # Apply pagination
            if start_after:
                # Convert start_after dict to document snapshot for cursor
                # This is a simplified approach - in practice, you'd store the actual document snapshot
                query = query.start_after(start_after)
            
            # Apply limit
            if limit:
                query = query.limit(limit)
            
            # Execute query
            docs = query.get()
            
            # Convert to list of dictionaries
            results = []
            for doc in docs:
                doc_data = doc.to_dict()
                doc_data["_id"] = doc.id
                doc_data["_collection"] = collection_name
                
                # Add timestamp if available
                if hasattr(doc, "create_time") and doc.create_time:
                    doc_data["_created"] = doc.create_time.isoformat()
                if hasattr(doc, "update_time") and doc.update_time:
                    doc_data["_updated"] = doc.update_time.isoformat()
                
                results.append(doc_data)
            
            logger.info(
                "Retrieved documents from Firestore",
                collection=collection_name,
                count=len(results),
                limit=limit
            )
            
            return results
            
        except Exception as e:
            logger.error(
                "Failed to retrieve documents from Firestore",
                collection=collection_name,
                error=str(e)
            )
            raise
    
    async def get_recent_documents(
        self,
        collection_name: str,
        limit: int = 100,
        hours_back: int = 24,
        timestamp_field: str = "timestamp"
    ) -> List[Dict[str, Any]]:
        """
        Get recent documents from a collection based on timestamp.
        
        Args:
            collection_name: Name of the Firestore collection
            limit: Maximum number of documents to return
            hours_back: How many hours back to look for documents
            timestamp_field: Name of the timestamp field
            
        Returns:
            List of recent document dictionaries
        """
        try:
            # Calculate cutoff time
            cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)
            
            # Create filter for recent documents
            filters = [
                {
                    "field": timestamp_field,
                    "operator": ">=",
                    "value": cutoff_time
                }
            ]
            
            return await self.get_documents(
                collection_name=collection_name,
                limit=limit,
                order_by=timestamp_field,
                order_direction="desc",
                filters=filters
            )
            
        except Exception as e:
            logger.error(
                "Failed to get recent documents",
                collection=collection_name,
                error=str(e)
            )
            raise
    
    async def search_documents(
        self,
        collection_name: str,
        search_field: str,
        search_value: Any,
        limit: int = 100,
        additional_filters: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for documents containing specific values.
        
        Args:
            collection_name: Name of the Firestore collection
            search_field: Field to search in
            search_value: Value to search for
            limit: Maximum number of documents to return
            additional_filters: Additional filters to apply
            
        Returns:
            List of matching document dictionaries
        """
        try:
            filters = [
                {
                    "field": search_field,
                    "operator": "==",
                    "value": search_value
                }
            ]
            
            if additional_filters:
                filters.extend(additional_filters)
            
            return await self.get_documents(
                collection_name=collection_name,
                limit=limit,
                filters=filters,
                order_by="timestamp",
                order_direction="desc"
            )
            
        except Exception as e:
            logger.error(
                "Failed to search documents",
                collection=collection_name,
                search_field=search_field,
                error=str(e)
            )
            raise
    
    async def get_document_by_id(
        self,
        collection_name: str,
        document_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get a specific document by its ID.
        
        Args:
            collection_name: Name of the Firestore collection
            document_id: ID of the document to retrieve
            
        Returns:
            Document dictionary or None if not found
        """
        try:
            doc_ref = self.db.collection(collection_name).document(document_id)
            doc = doc_ref.get()
            
            if doc.exists:
                doc_data = doc.to_dict()
                doc_data["_id"] = doc.id
                doc_data["_collection"] = collection_name
                
                if hasattr(doc, "create_time") and doc.create_time:
                    doc_data["_created"] = doc.create_time.isoformat()
                if hasattr(doc, "update_time") and doc.update_time:
                    doc_data["_updated"] = doc.update_time.isoformat()
                
                logger.info(
                    "Retrieved document by ID",
                    collection=collection_name,
                    document_id=document_id
                )
                
                return doc_data
            else:
                logger.warning(
                    "Document not found",
                    collection=collection_name,
                    document_id=document_id
                )
                return None
                
        except Exception as e:
            logger.error(
                "Failed to get document by ID",
                collection=collection_name,
                document_id=document_id,
                error=str(e)
            )
            raise
    
    async def get_collection_statistics(
        self,
        collection_name: str
    ) -> Dict[str, Any]:
        """
        Get statistics about a Firestore collection.
        
        Args:
            collection_name: Name of the Firestore collection
            
        Returns:
            Dictionary with collection statistics
        """
        try:
            collection_ref = self.db.collection(collection_name)
            
            # Get total document count (this is expensive for large collections)
            # In production, you might want to maintain a counter document
            docs = collection_ref.get()
            total_docs = len(docs)
            
            # Get recent document count (last 24 hours)
            recent_cutoff = datetime.utcnow() - timedelta(hours=24)
            recent_docs = collection_ref.where(
                filter=FieldFilter("timestamp", ">=", recent_cutoff)
            ).get()
            recent_count = len(recent_docs)
            
            # Sample some documents to analyze structure
            sample_docs = collection_ref.limit(10).get()
            sample_fields = set()
            for doc in sample_docs:
                sample_fields.update(doc.to_dict().keys())
            
            stats = {
                "collection_name": collection_name,
                "total_documents": total_docs,
                "recent_documents_24h": recent_count,
                "sample_fields": list(sample_fields),
                "query_time": datetime.utcnow().isoformat()
            }
            
            logger.info(
                "Generated collection statistics",
                collection=collection_name,
                stats=stats
            )
            
            return stats
            
        except Exception as e:
            logger.error(
                "Failed to get collection statistics",
                collection=collection_name,
                error=str(e)
            )
            raise
    
    async def get_all_collections_data(
        self,
        limit_per_collection: int = 50
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get data from all configured Firestore collections.
        
        Args:
            limit_per_collection: Maximum documents to retrieve per collection
            
        Returns:
            Dictionary with collection names as keys and document lists as values
        """
        try:
            collections = get_firestore_collections()
            results = {}
            
            for collection_name in collections:
                try:
                    docs = await self.get_documents(
                        collection_name=collection_name,
                        limit=limit_per_collection,
                        order_by="timestamp",
                        order_direction="desc"
                    )
                    results[collection_name] = docs
                    
                except Exception as e:
                    logger.warning(
                        "Failed to get data from collection",
                        collection=collection_name,
                        error=str(e)
                    )
                    results[collection_name] = []
            
            logger.info(
                "Retrieved data from all collections",
                collections=list(results.keys()),
                total_docs=sum(len(docs) for docs in results.values())
            )
            
            return results
            
        except Exception as e:
            logger.error("Failed to get all collections data", error=str(e))
            raise


# Global service instance
_firestore_service = None


def get_firestore_service() -> FirestoreLogService:
    """Get the global Firestore service instance."""
    global _firestore_service
    if _firestore_service is None:
        _firestore_service = FirestoreLogService()
    return _firestore_service 