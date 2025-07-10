import os
import logging
import asyncio
import gzip
import json
from typing import List, Dict, Any, Optional, Generator, AsyncGenerator
from datetime import datetime, timedelta
from google.cloud import storage, firestore
from google.oauth2 import service_account
from kubernetes import client, config
import google.auth.exceptions

# Configure logging
logger = logging.getLogger(__name__)

class LogCache:
    """Simple in-memory cache for frequently accessed log data."""
    def __init__(self, max_size: int = 100, ttl_seconds: int = 300):
        self.cache = {}
        self.access_times = {}
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached item if still valid."""
        if key not in self.cache:
            return None
        
        # Check TTL
        if datetime.now().timestamp() - self.access_times[key] > self.ttl_seconds:
            del self.cache[key]
            del self.access_times[key]
            return None
        
        self.access_times[key] = datetime.now().timestamp()
        return self.cache[key]
    
    def set(self, key: str, value: Any):
        """Set cached item with cleanup if needed."""
        # Clean up expired items
        self._cleanup_expired()
        
        # Remove oldest items if cache is full
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
            del self.cache[oldest_key]
            del self.access_times[oldest_key]
        
        self.cache[key] = value
        self.access_times[key] = datetime.now().timestamp()
    
    def _cleanup_expired(self):
        """Remove expired cache entries."""
        current_time = datetime.now().timestamp()
        expired_keys = [
            key for key, access_time in self.access_times.items() 
            if current_time - access_time > self.ttl_seconds
        ]
        for key in expired_keys:
            del self.cache[key]
            del self.access_times[key]

class LogService:
    def __init__(self):
        self.project_id = os.getenv("GCP_PROJECT_ID", "autotrade-453303")
        self.gcs_bucket_name = os.getenv("GCS_LOG_BUCKET", "tron-trade-logs")
        
        # Initialize clients with proper authentication
        self.gcs_client = None
        self.firestore_db = None
        self.k8s_api = None
        
        # Performance optimizations
        self.cache = LogCache(max_size=200, ttl_seconds=300)  # 5-minute cache
        self.max_file_size = int(os.getenv("MAX_LOG_FILE_SIZE", "100")) * 1024 * 1024  # 100MB default
        self.chunk_size = int(os.getenv("LOG_CHUNK_SIZE", "1")) * 1024 * 1024  # 1MB chunks
        
        self._initialize_gcp_clients()
        self._initialize_k8s_client()

    def _initialize_gcp_clients(self):
        """Initialize GCP clients with comprehensive authentication methods."""
        try:
            # Method 1: Try service account key file
            service_account_key = os.getenv("GCP_SERVICE_ACCOUNT_KEY")
            if service_account_key:
                if os.path.isfile(service_account_key):
                    credentials = service_account.Credentials.from_service_account_file(service_account_key)
                    self.gcs_client = storage.Client(credentials=credentials, project=self.project_id)
                    self.firestore_db = firestore.Client(credentials=credentials, project=self.project_id)
                    logger.info("GCP clients initialized using service account key file")
                    return
                else:
                    # Try as JSON string
                    import json
                    try:
                        key_data = json.loads(service_account_key)
                        credentials = service_account.Credentials.from_service_account_info(key_data)
                        self.gcs_client = storage.Client(credentials=credentials, project=self.project_id)
                        self.firestore_db = firestore.Client(credentials=credentials, project=self.project_id)
                        logger.info("GCP clients initialized using service account key JSON")
                        return
                    except json.JSONDecodeError:
                        logger.warning("Invalid JSON in GCP_SERVICE_ACCOUNT_KEY")
            
            # Method 2: Try environment credentials
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
            if os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
                self.gcs_client = storage.Client(project=self.project_id)
                self.firestore_db = firestore.Client(project=self.project_id)
                logger.info("GCP clients initialized using environment credentials")
                return
            
            # Method 3: Try default credentials (Cloud Run, GCE, local gcloud)
            try:
                self.gcs_client = storage.Client(project=self.project_id)
                self.firestore_db = firestore.Client(project=self.project_id)
                logger.info("GCP clients initialized using default credentials")
                return
            except Exception as e:
                logger.error(f"Failed to initialize with default credentials: {e}")
            
        except Exception as e:
            logger.error(f"Failed to initialize GCP clients: {e}")
            self.gcs_client = None
            self.firestore_db = None

    def _initialize_k8s_client(self):
        """Initialize Kubernetes client with fallback options."""
        try:
            # Try in-cluster config first (for pods running in K8s)
            config.load_incluster_config()
            self.k8s_api = client.CoreV1Api()
            logger.info("Kubernetes client initialized with in-cluster config")
        except config.ConfigException:
            try:
                # Try local kubeconfig
                config.load_kube_config()
                self.k8s_api = client.CoreV1Api()
                logger.info("Kubernetes client initialized with local kubeconfig")
            except Exception as e:
                logger.warning(f"Could not initialize Kubernetes client: {e}")
                self.k8s_api = None

    async def list_gcs_log_files_paginated(self, prefix: str = None, page_token: str = None,
                                          page_size: int = 50, date_from: str = None, 
                                          date_to: str = None, pattern: str = None) -> Dict[str, Any]:
        """Lists log files from GCS bucket with pagination for large volumes."""
        if not self.gcs_client:
            return {"error": "GCS client not initialized", "files": [], "next_page_token": None}
        
        cache_key = f"gcs_files_{prefix}_{page_token}_{page_size}_{date_from}_{date_to}_{pattern}"
        cached_result = self.cache.get(cache_key)
        if cached_result:
            logger.info("Returning cached GCS file list")
            return cached_result
        
        try:
            bucket = self.gcs_client.get_bucket(self.gcs_bucket_name)
            
            # Use page_token for pagination
            blobs = bucket.list_blobs(
                prefix=prefix, 
                max_results=page_size,
                page_token=page_token
            )
            
            files = []
            next_page_token = None
            
            # Process blobs and apply filters
            for page in blobs.pages:
                for blob in page:
                    # Apply filtering
                    if date_from or date_to:
                        if not self._is_file_in_date_range(blob.name, date_from, date_to):
                            continue
                    
                    if pattern and pattern.lower() not in blob.name.lower():
                        continue
                    
                    files.append({
                        "name": blob.name,
                        "size": blob.size,
                        "size_mb": round(blob.size / (1024 * 1024), 2) if blob.size else 0,
                        "created": blob.time_created.isoformat() if blob.time_created else None,
                        "updated": blob.updated.isoformat() if blob.updated else None,
                        "content_type": blob.content_type,
                        "is_large": blob.size > self.max_file_size if blob.size else False
                    })
                
                # Get next page token
                next_page_token = page.next_page_token
                break  # Only process first page
            
            result = {
                "files": files,
                "count": len(files),
                "next_page_token": next_page_token,
                "page_size": page_size,
                "bucket": self.gcs_bucket_name,
                "filters": {
                    "prefix": prefix,
                    "date_from": date_from,
                    "date_to": date_to,
                    "pattern": pattern
                }
            }
            
            # Cache result
            self.cache.set(cache_key, result)
            logger.info(f"Listed {len(files)} paginated files from GCS")
            return result
            
        except Exception as e:
            logger.error(f"Error listing paginated GCS files: {e}")
            return {"error": str(e), "files": [], "next_page_token": None}

    async def stream_gcs_log_content(self, file_path: str, start_byte: int = 0, 
                                   chunk_size: int = None) -> AsyncGenerator[bytes, None]:
        """Stream large log file content in chunks to handle big files efficiently."""
        if not self.gcs_client:
            yield b"Error: GCS client not initialized"
            return
        
        chunk_size = chunk_size or self.chunk_size
        
        try:
            bucket = self.gcs_client.get_bucket(self.gcs_bucket_name)
            blob = bucket.blob(file_path)
            
            if not blob.exists():
                yield b"Error: File not found"
                return
            
            # Get file size for progress tracking
            blob.reload()
            file_size = blob.size
            
            current_pos = start_byte
            while current_pos < file_size:
                end_pos = min(current_pos + chunk_size - 1, file_size - 1)
                
                # Download chunk
                chunk = blob.download_as_bytes(start=current_pos, end=end_pos)
                yield chunk
                
                current_pos += len(chunk)
                
                # Prevent infinite loops
                if len(chunk) == 0:
                    break
            
            logger.info(f"Streamed {file_size} bytes from GCS file: {file_path}")
            
        except Exception as e:
            logger.error(f"Error streaming GCS file {file_path}: {e}")
            yield f"Error: {e}".encode()

    async def get_compressed_log_content(self, file_path: str, search_term: str = None,
                                       log_level: str = None, lines_limit: int = 1000) -> Dict[str, Any]:
        """Get log content with compression support for better transfer efficiency."""
        if not self.gcs_client:
            return {"error": "GCS client not initialized"}
        
        cache_key = f"compressed_log_{file_path}_{search_term}_{log_level}_{lines_limit}"
        cached_result = self.cache.get(cache_key)
        if cached_result:
            logger.info("Returning cached compressed log content")
            return cached_result
        
        try:
            bucket = self.gcs_client.get_bucket(self.gcs_bucket_name)
            blob = bucket.blob(file_path)
            
            if not blob.exists():
                return {"error": f"File not found: {file_path}"}
            
            blob.reload()
            file_size = blob.size
            
            # Handle large files differently
            if file_size > self.max_file_size:
                # For very large files, stream and process in chunks
                content_chunks = []
                async for chunk in self.stream_gcs_log_content(file_path, chunk_size=self.chunk_size):
                    if chunk.startswith(b"Error:"):
                        return {"error": chunk.decode()}
                    content_chunks.append(chunk.decode('utf-8', errors='ignore'))
                
                content = ''.join(content_chunks)
            else:
                # For smaller files, download directly
                content = blob.download_as_text()
            
            lines = content.split('\n')
            
            # Apply filtering efficiently
            filtered_lines = self._filter_log_lines_optimized(lines, search_term, log_level, lines_limit)
            
            # Compress content for transfer
            filtered_content = '\n'.join(filtered_lines)
            compressed_content = gzip.compress(filtered_content.encode('utf-8'))
            
            result = {
                "file_path": file_path,
                "content": filtered_content,
                "compressed_content": compressed_content.hex(),  # hex encoded for JSON
                "compression_ratio": round(len(compressed_content) / len(filtered_content.encode('utf-8')), 3),
                "total_lines": len(lines),
                "filtered_lines": len(filtered_lines),
                "original_size_mb": round(file_size / (1024 * 1024), 2),
                "filtered_size_kb": round(len(filtered_content.encode('utf-8')) / 1024, 2),
                "compressed_size_kb": round(len(compressed_content) / 1024, 2),
                "updated": blob.updated.isoformat() if blob.updated else None,
                "filters_applied": {
                    "search_term": search_term,
                    "log_level": log_level,
                    "lines_limit": lines_limit
                }
            }
            
            # Cache result (without compressed content to save memory)
            cache_result = {**result}
            del cache_result["compressed_content"]
            self.cache.set(cache_key, cache_result)
            
            logger.info(f"Processed and compressed log file: {file_path}")
            return result
            
        except Exception as e:
            logger.error(f"Error getting compressed log content for {file_path}: {e}")
            return {"error": str(e)}

    async def get_firestore_logs_batch(self, limit: int = 100, component: str = None,
                                     log_level: str = None, date_from: str = None,
                                     date_to: str = None, cursor: str = None) -> Dict[str, Any]:
        """Get Firestore logs with batching and cursor-based pagination."""
        if not self.firestore_db:
            return {"error": "Firestore client not initialized", "logs": [], "next_cursor": None}
        
        cache_key = f"firestore_logs_{limit}_{component}_{log_level}_{date_from}_{date_to}_{cursor}"
        cached_result = self.cache.get(cache_key)
        if cached_result:
            logger.info("Returning cached Firestore logs")
            return cached_result
        
        try:
            logs_ref = self.firestore_db.collection('system_logs_realtime')
            query = logs_ref.order_by('timestamp', direction=firestore.Query.DESCENDING)
            
            # Apply filters with optimized queries
            if date_from:
                date_from_dt = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
                query = query.where('timestamp', '>=', date_from_dt)
            
            if date_to:
                date_to_dt = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
                query = query.where('timestamp', '<=', date_to_dt)
            
            if component:
                query = query.where('component', '==', component)
            
            if log_level:
                query = query.where('level', '==', log_level.upper())
            
            # Apply cursor for pagination
            if cursor:
                cursor_doc = logs_ref.document(cursor).get()
                if cursor_doc.exists:
                    query = query.start_after(cursor_doc)
            
            query = query.limit(limit)
            
            # Execute query with timeout
            docs = await asyncio.wait_for(query.get(), timeout=30.0)
            
            logs = []
            last_doc = None
            
            for doc in docs:
                log_data = doc.to_dict()
                logs.append({
                    **log_data,
                    'id': doc.id,
                    'timestamp': log_data.get('timestamp').isoformat() if log_data.get('timestamp') else None
                })
                last_doc = doc
            
            result = {
                "logs": logs,
                "count": len(logs),
                "next_cursor": last_doc.id if last_doc else None,
                "limit": limit,
                "filters": {
                    "component": component,
                    "log_level": log_level,
                    "date_from": date_from,
                    "date_to": date_to
                }
            }
            
            # Cache result
            self.cache.set(cache_key, result)
            logger.info(f"Retrieved {len(logs)} batched logs from Firestore")
            return result
            
        except asyncio.TimeoutError:
            logger.error("Firestore query timeout")
            return {"error": "Query timeout", "logs": [], "next_cursor": None}
        except Exception as e:
            logger.error(f"Error fetching batched Firestore logs: {e}")
            return {"error": str(e), "logs": [], "next_cursor": None}

    async def list_k8s_pods(self) -> List[str]:
        """Lists running pods in the configured Kubernetes namespace."""
        if not self.k8s_api:
            logger.warning("Kubernetes API not available - cannot list pods")
            return ["Kubernetes API not available"]
        
        try:
            # Assuming we are running in a namespace, e.g., 'gpt'
            namespace = os.getenv("K8S_NAMESPACE", "gpt")
            pod_list = self.k8s_api.list_namespaced_pod(namespace=namespace, watch=False)
            pods = [pod.metadata.name for pod in pod_list.items]
            logger.info(f"Successfully listed {len(pods)} pods from namespace: {namespace}")
            return pods
        except Exception as e:
            logger.error(f"Error listing K8s pods: {e}")
            return [f"Error: {e}"]

    async def get_k8s_pod_logs(self, pod_name: str, limit: int = 100,
                              since_seconds: int = None,
                              follow: bool = False,
                              search_term: str = None,
                              log_level: str = None) -> List[str]:
        """Retrieves logs for a specific Kubernetes pod with filtering."""
        if not self.k8s_api:
            logger.warning("Kubernetes API not available - cannot retrieve pod logs")
            return ["Kubernetes API not available"]
        
        try:
            namespace = os.getenv("K8S_NAMESPACE", "gpt")
            
            # Build log retrieval parameters
            log_params = {
                'name': pod_name,
                'namespace': namespace,
                'tail_lines': limit
            }
            
            if since_seconds:
                log_params['since_seconds'] = since_seconds
                
            if follow:
                log_params['follow'] = follow
            
            logs = self.k8s_api.read_namespaced_pod_log(**log_params)
            log_lines = logs.split('\n')
            
            # Apply filtering
            filtered_lines = self._filter_log_lines(log_lines, search_term, log_level)
            
            logger.info(f"Successfully retrieved {len(filtered_lines)} filtered log lines for pod: {pod_name}")
            return filtered_lines
        except client.ApiException as e:
            logger.error(f"K8s API Error fetching logs for pod {pod_name}: {e}")
            return [f"K8s API Error: {e.reason}"]
        except Exception as e:
            logger.error(f"Error fetching logs for K8s pod {pod_name}: {e}")
            return [f"Error: {e}"]

    def get_status(self) -> Dict[str, Any]:
        """Get the status of all clients and connections."""
        return {
            "gcs_client": "initialized" if self.gcs_client else "failed",
            "firestore_client": "initialized" if self.firestore_db else "failed", 
            "k8s_client": "initialized" if self.k8s_api else "failed",
            "project_id": self.project_id,
            "gcs_bucket": self.gcs_bucket_name,
            "k8s_namespace": os.getenv("K8S_NAMESPACE", "gpt")
        }

    def _filter_log_lines(self, lines: List[str], search_term: str = None, 
                         log_level: str = None) -> List[str]:
        """Apply filtering to log lines based on search term and log level."""
        filtered_lines = lines
        
        # Filter by search term
        if search_term:
            search_lower = search_term.lower()
            filtered_lines = [line for line in filtered_lines if search_lower in line.lower()]
        
        # Filter by log level
        if log_level:
            level_upper = log_level.upper()
            level_patterns = {
                'ERROR': ['ERROR', 'FATAL', 'CRITICAL'],
                'WARN': ['WARN', 'WARNING'],
                'INFO': ['INFO'],
                'DEBUG': ['DEBUG', 'TRACE']
            }
            
            patterns = level_patterns.get(level_upper, [level_upper])
            filtered_lines = [
                line for line in filtered_lines 
                if any(pattern in line.upper() for pattern in patterns)
            ]
        
        return filtered_lines

    def _filter_log_lines_optimized(self, lines: List[str], search_term: str = None,
                                   log_level: str = None, lines_limit: int = None) -> List[str]:
        """Optimized filtering for large log volumes with early termination."""
        filtered_lines = []
        search_lower = search_term.lower() if search_term else None
        
        # Optimize log level patterns
        level_patterns = None
        if log_level:
            level_upper = log_level.upper()
            level_map = {
                'ERROR': ['ERROR', 'FATAL', 'CRITICAL'],
                'WARN': ['WARN', 'WARNING'],
                'INFO': ['INFO'],
                'DEBUG': ['DEBUG', 'TRACE']
            }
            level_patterns = level_map.get(level_upper, [level_upper])
        
        # Process lines with early termination for performance
        for line in lines:
            # Apply search term filter first (usually most selective)
            if search_lower and search_lower not in line.lower():
                continue
            
            # Apply log level filter
            if level_patterns:
                line_upper = line.upper()
                if not any(pattern in line_upper for pattern in level_patterns):
                    continue
            
            filtered_lines.append(line)
            
            # Early termination for performance
            if lines_limit and len(filtered_lines) >= lines_limit:
                break
        
        return filtered_lines

    def _is_file_in_date_range(self, filename: str, date_from: str = None, 
                              date_to: str = None) -> bool:
        """Check if a log file falls within the specified date range based on filename."""
        if not date_from and not date_to:
            return True
        
        # Extract date from filename (common patterns: YYYY-MM-DD, YYYYMMDD)
        import re
        from datetime import datetime
        
        date_patterns = [
            r'(\d{4}-\d{2}-\d{2})',  # YYYY-MM-DD
            r'(\d{4}\d{2}\d{2})',    # YYYYMMDD
            r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})'  # ISO datetime
        ]
        
        file_date = None
        for pattern in date_patterns:
            match = re.search(pattern, filename)
            if match:
                try:
                    date_str = match.group(1)
                    if 'T' in date_str:
                        file_date = datetime.fromisoformat(date_str)
                    elif '-' in date_str:
                        file_date = datetime.strptime(date_str, '%Y-%m-%d')
                    else:
                        file_date = datetime.strptime(date_str, '%Y%m%d')
                    break
                except ValueError:
                    continue
        
        if not file_date:
            return True  # Include files without date in filename
        
        # Check date range
        if date_from:
            try:
                date_from_dt = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
                if file_date < date_from_dt.replace(tzinfo=None):
                    return False
            except ValueError:
                pass
        
        if date_to:
            try:
                date_to_dt = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
                if file_date > date_to_dt.replace(tzinfo=None):
                    return False
            except ValueError:
                pass
        
        return True

# Dependency Injection setup
_log_service_instance = None

def get_log_service():
    global _log_service_instance
    if _log_service_instance is None:
        _log_service_instance = LogService()
    return _log_service_instance 