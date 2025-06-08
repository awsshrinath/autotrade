"""
Pydantic models for log entries, filtering parameters, and API responses.
"""

from enum import Enum
from typing import List, Optional, Dict, Any, Union, Generic, TypeVar
from pydantic import BaseModel, Field, HttpUrl, validator
from datetime import datetime

# Generic type for paginated responses
T = TypeVar('T')

class LogSource(str, Enum):
    GCS = "GCS"
    FIRESTORE = "Firestore"
    KUBERNETES = "Kubernetes"
    SYSTEM = "System"

class BaseLog(BaseModel):
    timestamp: Optional[datetime] = Field(None, description="Timestamp of the log entry or event.")
    source: LogSource = Field(..., description="The source of the log.")
    message: Optional[str] = Field(None, description="The main log message or event description.")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Any additional structured metadata.")

# --- GCS Models ---
class GCSLogFile(BaseModel):
    name: str = Field(..., description="Name of the log file.")
    path: str = Field(..., description="Full path to the log file in the bucket.")
    size: Optional[int] = Field(None, description="Size of the log file in bytes.")
    updated: Optional[datetime] = Field(None, description="Last modified timestamp of the file.")
    source: LogSource = Field(default=LogSource.GCS, description="Log source type.")
    bucket_name: Optional[str] = Field(None, description="Name of the GCS bucket.")

class GCSLogEntry(BaseLog):
    log_file: GCSLogFile = Field(..., description="Information about the GCS log file this entry belongs to.")
    line_number: Optional[int] = Field(None, description="Line number within the log file, if applicable.")
    raw_content: str = Field(..., description="The raw log line content.")
    source: LogSource = Field(default=LogSource.GCS)

class GCSLogFilterParams(BaseModel):
    bucket_name: Optional[str] = Field(None, description="GCS bucket name. Uses default if not provided.")
    prefix: Optional[str] = Field(None, description="Filter log files by prefix (e.g., 'trades/').")
    file_pattern: Optional[str] = Field(None, description="Regex pattern to filter file names.")
    start_time: Optional[datetime] = Field(None, description="Include logs modified after this time.")
    end_time: Optional[datetime] = Field(None, description="Include logs modified before this time.")
    min_size_bytes: Optional[int] = Field(None, description="Minimum file size in bytes.")
    max_size_bytes: Optional[int] = Field(None, description="Maximum file size in bytes.")
    keyword: Optional[str] = Field(None, description="Keyword to search within log content.")

# --- Firestore Models ---
class FirestoreCollectionInfo(BaseModel):
    name: str = Field(..., description="Name of the Firestore collection.")
    document_count: Optional[int] = Field(None, description="Estimated number of documents in the collection.")
    source: LogSource = Field(default=LogSource.FIRESTORE)

class FirestoreLogEntry(BaseLog):
    collection_name: str = Field(..., description="Name of the Firestore collection.")
    document_id: str = Field(..., description="ID of the Firestore document.")
    data: Dict[str, Any] = Field(..., description="The full document data.")
    source: LogSource = Field(default=LogSource.FIRESTORE)

class FirestoreFilter(BaseModel):
    field: str = Field(..., description="Document field to filter on.")
    operator: str = Field(..., description="Filter operator (e.g., '==', '>', '<=', 'in').")
    value: Any = Field(..., description="Value to compare against.")

class FirestoreLogFilterParams(BaseModel):
    collection_name: str = Field(..., description="Name of the Firestore collection to query.")
    filters: Optional[List[FirestoreFilter]] = Field(None, description="List of filters to apply.")
    order_by: Optional[str] = Field(None, description="Field to order results by.")
    limit: Optional[int] = Field(default=100, description="Maximum number of documents to return.")
    start_after: Optional[Union[List[Any], Dict[str, Any]]] = Field(None, description="Document fields to start after for pagination.") # Firestore cursors can be complex

# --- Kubernetes Models ---
class K8sContainerInfo(BaseModel):
    name: str = Field(..., description="Name of the container.")
    image: str = Field(..., description="Image used by the container.")
    ready: bool = Field(..., description="Indicates if the container is ready.")
    restart_count: int = Field(..., description="Number of times the container has been restarted.")

class K8sPodInfo(BaseModel):
    name: str = Field(..., description="Name of the pod.")
    namespace: str = Field(..., description="Namespace of the pod.")
    status: str = Field(..., description="Current status of the pod (e.g., Running, Pending, Failed).")
    created_at: Optional[datetime] = Field(None, alias="created", description="Timestamp when the pod was created.")
    labels: Optional[Dict[str, str]] = Field(default_factory=dict, description="Labels associated with the pod.")
    node_name: Optional[str] = Field(None, description="Name of the node the pod is running on.")
    pod_ip: Optional[str] = Field(None, description="IP address of the pod.")
    containers: List[K8sContainerInfo] = Field(default_factory=list, description="List of containers in the pod.")
    source: LogSource = Field(default=LogSource.KUBERNETES)

class K8sLogEntry(BaseLog):
    pod_name: str = Field(..., description="Name of the pod this log entry is from.")
    namespace: str = Field(..., description="Namespace of the pod.")
    container_name: Optional[str] = Field(None, description="Name of the container this log entry is from.")
    raw_content: str = Field(..., description="The raw log line content.")
    source: LogSource = Field(default=LogSource.KUBERNETES)

class K8sEventInfo(BaseLog):
    event_type: str = Field(..., alias="type", description="Type of the event (e.g., Normal, Warning).")
    reason: Optional[str] = Field(None, description="Reason for the event.")
    involved_object_name: Optional[str] = Field(None, description="Name of the object involved in the event.")
    involved_object_kind: Optional[str] = Field(None, description="Kind of the object involved (e.g., Pod, Node).")
    first_timestamp: Optional[datetime] = Field(None, description="Timestamp of the first occurrence of the event.")
    last_timestamp: Optional[datetime] = Field(None, description="Timestamp of the most recent occurrence of the event.")
    count: Optional[int] = Field(None, description="Number of times the event has occurred.")
    source_component: Optional[str] = Field(None, alias="source_component_name", description="Component that reported the event (e.g., kubelet, scheduler).")
    source: LogSource = Field(default=LogSource.KUBERNETES)

class K8sLogFilterParams(BaseModel):
    namespace: Optional[str] = Field(None, description="Kubernetes namespace. Uses default if not specified.")
    pod_name_pattern: Optional[str] = Field(None, description="Regex pattern to filter pod names.")
    container_name: Optional[str] = Field(None, description="Specific container name to get logs from.")
    since_seconds: Optional[int] = Field(None, description="Return logs newer than N seconds.")
    since_time: Optional[datetime] = Field(None, description="Return logs newer than this specific time.")
    tail_lines: Optional[int] = Field(None, description="Number of lines from the end of the logs to return.")
    timestamps: bool = Field(default=True, description="Include timestamps in log lines.")
    log_level: Optional[str] = Field(None, description="Filter logs by level (e.g., ERROR, INFO). Requires log format support.")
    keyword: Optional[str] = Field(None, description="Keyword to search within log content.")

# --- Summary Models ---
class SummaryRequest(BaseModel):
    log_content: Optional[str] = Field(None, description="Raw log content to summarize.")
    log_source: Optional[LogSource] = Field(None, description="Source of the logs if providing IDs/params instead of raw content.")
    source_params: Optional[Dict[str, Any]] = Field(None, description="Parameters to fetch logs if not providing raw content (e.g., GCS bucket/prefix, pod name).")
    summary_type: str = Field(default="general", description="Type of summary (general, errors, performance, security, trends).")

class SummaryResponse(BaseModel):
    summary: str = Field(..., description="The generated summary.")
    summary_type: str = Field(..., description="Type of summary performed.")
    metadata: Dict[str, Any] = Field(..., description="Metadata about the summarization process.")

# --- General API Models ---
class PaginationParams(BaseModel):
    skip: int = Field(0, ge=0, description="Number of items to skip.")
    limit: int = Field(100, ge=1, le=500, description="Maximum number of items to return.")

class PaginatedResponse(BaseModel, Generic[T]):
    total: int = Field(..., description="Total number of items available.")
    items: List[T] = Field(..., description="List of items for the current page.")
    skip: int = Field(..., description="Number of items skipped.")
    limit: int = Field(..., description="Number of items per page.")

class HealthStatus(BaseModel):
    status: str = Field(..., description="Overall service status (e.g., 'ok', 'degraded').")
    message: Optional[str] = Field(None, description="Optional message providing more details.")
    services: Optional[Dict[str, str]] = Field(None, description="Status of dependent services (e.g., GCS, Firestore, OpenAI, Redis).")

class AuthenticatedUser(BaseModel):
    username: str
    # Add other relevant user fields like roles, permissions etc. 