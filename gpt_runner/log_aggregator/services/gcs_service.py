"""
Google Cloud Storage (GCS) service for log retrieval.
Handles connection, authentication, and log file retrieval from GCS buckets.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, AsyncGenerator
from google.cloud import storage
from google.cloud.exceptions import NotFound, Forbidden
import structlog

from ..utils.config import get_config, get_gcs_bucket_name, get_log_prefixes

logger = structlog.get_logger(__name__)


class GCSLogService:
    """Service for retrieving logs from Google Cloud Storage."""
    
    def __init__(self):
        self.config = get_config()
        self.client = None
        self.bucket = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the GCS client with authentication."""
        try:
            # Initialize GCS client
            # If GOOGLE_APPLICATION_CREDENTIALS is set, it will be used automatically
            self.client = storage.Client(project=self.config.firestore_project_id)
            
            # Get the bucket
            bucket_name = get_gcs_bucket_name()
            self.bucket = self.client.bucket(bucket_name)
            
            logger.info(
                "GCS client initialized successfully",
                bucket_name=bucket_name,
                project_id=self.config.firestore_project_id
            )
            
        except Exception as e:
            logger.error(
                "Failed to initialize GCS client",
                error=str(e),
                bucket_name=get_gcs_bucket_name()
            )
            raise
    
    async def test_connection(self) -> bool:
        """Test the GCS connection and permissions."""
        try:
            # Test bucket access
            if not self.bucket.exists():
                logger.error("GCS bucket does not exist", bucket_name=self.bucket.name)
                return False
            
            # Test list permissions by trying to list a few objects
            blobs = list(self.client.list_blobs(self.bucket, max_results=1))
            
            logger.info("GCS connection test successful", bucket_name=self.bucket.name)
            return True
            
        except Forbidden as e:
            logger.error("GCS access forbidden", error=str(e))
            return False
        except Exception as e:
            logger.error("GCS connection test failed", error=str(e))
            return False
    
    async def list_log_files(
        self,
        prefix: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        max_results: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        List log files in GCS bucket with optional filtering.
        
        Args:
            prefix: GCS object prefix to filter by
            start_time: Filter files modified after this time
            end_time: Filter files modified before this time
            max_results: Maximum number of files to return
            
        Returns:
            List of file metadata dictionaries
        """
        try:
            # Use default prefixes if none specified
            prefixes_to_search = [prefix] if prefix else get_log_prefixes()
            
            all_files = []
            
            for search_prefix in prefixes_to_search:
                logger.info("Listing files with prefix", prefix=search_prefix)
                
                # List blobs with prefix
                blobs = self.client.list_blobs(
                    self.bucket,
                    prefix=search_prefix,
                    max_results=max_results
                )
                
                for blob in blobs:
                    # Apply time filtering if specified
                    if start_time and blob.time_created < start_time:
                        continue
                    if end_time and blob.time_created > end_time:
                        continue
                    
                    file_info = {
                        "name": blob.name,
                        "size": blob.size,
                        "created": blob.time_created.isoformat() if blob.time_created else None,
                        "updated": blob.updated.isoformat() if blob.updated else None,
                        "content_type": blob.content_type,
                        "md5_hash": blob.md5_hash,
                        "prefix": search_prefix,
                        "bucket": self.bucket.name
                    }
                    all_files.append(file_info)
                    
                    # Break if we've reached max_results
                    if max_results and len(all_files) >= max_results:
                        break
                
                if max_results and len(all_files) >= max_results:
                    break
            
            # Sort by creation time (newest first)
            all_files.sort(key=lambda x: x["created"] or "", reverse=True)
            
            logger.info("Listed log files", count=len(all_files))
            return all_files
            
        except Exception as e:
            logger.error("Failed to list log files", error=str(e))
            raise
    
    async def get_log_content(
        self,
        file_path: str,
        max_size_mb: int = 10
    ) -> Optional[str]:
        """
        Retrieve the content of a specific log file.
        
        Args:
            file_path: Path to the file in GCS
            max_size_mb: Maximum file size to download in MB
            
        Returns:
            File content as string, or None if file not found/too large
        """
        try:
            blob = self.bucket.blob(file_path)
            
            if not blob.exists():
                logger.warning("Log file not found", file_path=file_path)
                return None
            
            # Check file size
            if blob.size and blob.size > max_size_mb * 1024 * 1024:
                logger.warning(
                    "Log file too large to download",
                    file_path=file_path,
                    size_mb=blob.size / (1024 * 1024),
                    max_size_mb=max_size_mb
                )
                return None
            
            # Download content
            content = blob.download_as_text()
            
            logger.info(
                "Downloaded log file content",
                file_path=file_path,
                size_bytes=len(content.encode('utf-8'))
            )
            
            return content
            
        except Exception as e:
            logger.error("Failed to get log content", file_path=file_path, error=str(e))
            raise
    
    async def stream_log_content(
        self,
        file_path: str,
        chunk_size: int = 1024 * 1024  # 1MB chunks
    ) -> AsyncGenerator[str, None]:
        """
        Stream log file content in chunks for large files.
        
        Args:
            file_path: Path to the file in GCS
            chunk_size: Size of each chunk in bytes
            
        Yields:
            Chunks of file content as strings
        """
        try:
            blob = self.bucket.blob(file_path)
            
            if not blob.exists():
                logger.warning("Log file not found for streaming", file_path=file_path)
                return
            
            # Stream content in chunks
            start_byte = 0
            while True:
                end_byte = start_byte + chunk_size - 1
                
                try:
                    chunk = blob.download_as_text(start=start_byte, end=end_byte)
                    if not chunk:
                        break
                    
                    yield chunk
                    start_byte = end_byte + 1
                    
                except Exception as e:
                    # End of file or other error
                    logger.info("End of file stream", file_path=file_path)
                    break
            
            logger.info("Completed streaming log file", file_path=file_path)
            
        except Exception as e:
            logger.error("Failed to stream log content", file_path=file_path, error=str(e))
            raise
    
    async def search_logs(
        self,
        query: str,
        prefix: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        max_files: int = 100,
        max_results: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Search for specific content within log files.
        
        Args:
            query: Search query string
            prefix: GCS object prefix to filter by
            start_time: Filter files modified after this time
            end_time: Filter files modified before this time
            max_files: Maximum number of files to search
            max_results: Maximum number of matching results to return
            
        Returns:
            List of search results with file info and matching lines
        """
        try:
            # Get list of files to search
            files = await self.list_log_files(
                prefix=prefix,
                start_time=start_time,
                end_time=end_time,
                max_results=max_files
            )
            
            results = []
            
            for file_info in files:
                if len(results) >= max_results:
                    break
                
                try:
                    # Get file content (limit to smaller files for search)
                    content = await self.get_log_content(file_info["name"], max_size_mb=5)
                    
                    if not content:
                        continue
                    
                    # Search for query in content
                    lines = content.split('\n')
                    matching_lines = []
                    
                    for line_num, line in enumerate(lines, 1):
                        if query.lower() in line.lower():
                            matching_lines.append({
                                "line_number": line_num,
                                "content": line.strip(),
                                "timestamp": self._extract_timestamp_from_line(line)
                            })
                            
                            if len(matching_lines) >= 10:  # Limit matches per file
                                break
                    
                    if matching_lines:
                        result = {
                            "file": file_info,
                            "matches": matching_lines,
                            "total_matches": len(matching_lines)
                        }
                        results.append(result)
                
                except Exception as e:
                    logger.warning(
                        "Failed to search in file",
                        file_path=file_info["name"],
                        error=str(e)
                    )
                    continue
            
            logger.info(
                "Log search completed",
                query=query,
                files_searched=len(files),
                results_found=len(results)
            )
            
            return results
            
        except Exception as e:
            logger.error("Failed to search logs", query=query, error=str(e))
            raise
    
    def _extract_timestamp_from_line(self, line: str) -> Optional[str]:
        """
        Extract timestamp from a log line.
        This is a simple implementation - can be enhanced based on log format.
        """
        try:
            # Look for common timestamp patterns
            import re
            
            # ISO format: 2023-12-01T10:30:00
            iso_pattern = r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}'
            match = re.search(iso_pattern, line)
            if match:
                return match.group()
            
            # Date format: 2023-12-01 10:30:00
            date_pattern = r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}'
            match = re.search(date_pattern, line)
            if match:
                return match.group()
            
            return None
            
        except Exception:
            return None
    
    async def get_log_statistics(
        self,
        prefix: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get statistics about log files in the bucket.
        
        Returns:
            Dictionary with statistics like file count, total size, etc.
        """
        try:
            files = await self.list_log_files(
                prefix=prefix,
                start_time=start_time,
                end_time=end_time
            )
            
            total_size = sum(f["size"] or 0 for f in files)
            
            # Group by prefix
            prefix_stats = {}
            for file_info in files:
                file_prefix = file_info["prefix"]
                if file_prefix not in prefix_stats:
                    prefix_stats[file_prefix] = {"count": 0, "size": 0}
                
                prefix_stats[file_prefix]["count"] += 1
                prefix_stats[file_prefix]["size"] += file_info["size"] or 0
            
            stats = {
                "total_files": len(files),
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "prefix_breakdown": prefix_stats,
                "bucket_name": self.bucket.name,
                "query_time": datetime.utcnow().isoformat()
            }
            
            logger.info("Generated log statistics", stats=stats)
            return stats
            
        except Exception as e:
            logger.error("Failed to get log statistics", error=str(e))
            raise


# Global service instance
_gcs_service = None


def get_gcs_service() -> GCSLogService:
    """Get the global GCS service instance."""
    global _gcs_service
    if _gcs_service is None:
        _gcs_service = GCSLogService()
    return _gcs_service 