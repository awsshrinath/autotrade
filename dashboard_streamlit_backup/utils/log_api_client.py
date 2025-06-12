"""
API Client for interacting with the Log Aggregator FastAPI service.
"""

import requests
import streamlit as st # For error messages and session state
from typing import List, Optional, Dict, Any

# Assuming Pydantic models from FastAPI are similar or can be mapped to dicts for client
# For simplicity, this client will mostly return JSON/dicts.
# In a more complex scenario, you might share Pydantic models or have client-side models.

class LogAPIClient:
    def __init__(self, base_url: str, api_key: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {"Content-Type": "application/json"}
        if self.api_key:
            self.headers["X-API-Key"] = self.api_key

    def _handle_response(self, response: requests.Response):
        """Handles HTTP response, raising errors or returning JSON."""
        try:
            response.raise_for_status() # Raises HTTPError for bad responses (4XX or 5XX)
            if response.content:
                return response.json()
            return None # No content
        except requests.exceptions.HTTPError as e:
            error_detail = str(e)
            try:
                error_content = response.json()
                if isinstance(error_content, dict) and "detail" in error_content:
                    if isinstance(error_content["detail"], list) and error_content["detail"]:
                        # Pydantic validation error format
                        error_detail = f"{e}. Details: {error_content['detail'][0].get('msg', 'Validation error')}"
                    else:
                        error_detail = f"{e}. Details: {error_content['detail']}"
            except ValueError: # response.json() failed
                pass 
            st.error(f"API Error: {error_detail}")
            raise # Re-raise the exception to be caught by calling function if needed
        except requests.exceptions.RequestException as e:
            st.error(f"Request Error: {e}")
            raise

    # --- Health Check ---
    def health_check(self) -> Optional[Dict[str, Any]]:
        """Checks the health of the FastAPI service."""
        try:
            # Test the root endpoint first since /health is having issues
            response = requests.get(f"{self.base_url}/", headers=self.headers, timeout=5)
            result = self._handle_response(response)
            if result and "Welcome to the Log Aggregator API" in result.get("message", ""):
                return {
                    "status": "ok",
                    "message": "Log Aggregator API is running",
                    "dependencies": {
                        "gcs_service": "unknown",
                        "firestore_service": "unknown", 
                        "k8s_service": "unknown",
                        "gpt_service_openai": "unknown"
                    }
                }
            else:
                raise Exception("Unexpected response from root endpoint")
        except requests.exceptions.RequestException as e:
            st.warning(f"Log aggregator service unavailable: {e}")
            # Return offline status instead of None
            return {
                "status": "offline",
                "message": "Log aggregator service is not running. Dashboard running in offline mode.",
                "dependencies": {
                    "gcs_service": "offline",
                    "firestore_service": "offline", 
                    "k8s_service": "offline",
                    "gpt_service_openai": "offline"
                }
            }

    # --- GCS Endpoints ---
    def list_gcs_files(self, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        try:
            response = requests.get(f"{self.base_url}/gcs/files", headers=self.headers, params=params, timeout=30)
            return self._handle_response(response)
        except Exception as e:
            st.error(f"GCS service error: {e}")
            return None 

    def get_gcs_file_content(self, bucket_name: str, file_path: str) -> Optional[Dict[str, Any]]:
        params = {"bucket_name": bucket_name, "file_path": file_path}
        try:
            response = requests.get(f"{self.base_url}/gcs/file/content", headers=self.headers, params=params, timeout=60)
            return self._handle_response(response)
        except Exception as e:
            return None

    def search_gcs_logs(self, filters: Dict[str, Any], pagination: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        params = pagination or {}
        try:
            response = requests.post(f"{self.base_url}/gcs/search", headers=self.headers, json=filters, params=params, timeout=120)
            return self._handle_response(response)
        except Exception as e:
            return None

    # --- Firestore Endpoints ---
    def list_firestore_collections(self) -> Optional[List[Dict[str, Any]]]:
        try:
            response = requests.get(f"{self.base_url}/firestore/collections", headers=self.headers, timeout=30)
            return self._handle_response(response)
        except Exception as e:
            return None
    
    def query_firestore_logs(self, filter_params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            response = requests.post(f"{self.base_url}/firestore/query", headers=self.headers, json=filter_params, timeout=60)
            return self._handle_response(response)
        except Exception as e:
            st.error(f"Firestore service error: {e}")
            return None

    def get_firestore_document(self, collection_name: str, document_id: str) -> Optional[Dict[str, Any]]:
        try:
            response = requests.get(f"{self.base_url}/firestore/document/{collection_name}/{document_id}", headers=self.headers, timeout=30)
            return self._handle_response(response)
        except Exception as e:
            return None

    # --- Kubernetes Endpoints ---
    def list_k8s_pods(self, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        try:
            response = requests.get(f"{self.base_url}/k8s/pods", headers=self.headers, params=params, timeout=30)
            return self._handle_response(response)
        except Exception as e:
            st.error(f"Kubernetes service error: {e}")
            return None

    def get_k8s_pod_logs(self, pod_name: str, filter_params: Dict[str, Any], pagination: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        params = pagination or {}
        try:
            response = requests.post(f"{self.base_url}/k8s/{pod_name}/logs", headers=self.headers, json=filter_params, params=params, timeout=120)
            return self._handle_response(response)
        except Exception as e:
            return None

    def get_k8s_pod_events(self, pod_name: str, namespace: Optional[str] = None) -> Optional[List[Dict[str, Any]]]:
        params = {"namespace": namespace} if namespace else {}
        try:
            response = requests.get(f"{self.base_url}/k8s/{pod_name}/events", headers=self.headers, params=params, timeout=30)
            return self._handle_response(response)
        except Exception as e:
            return None

    def search_k8s_logs(self, search_query: str, filter_params: Dict[str, Any], pagination: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        params = pagination or {}
        params["search_query"] = search_query # Add search_query to query params for POST body
        try:
            response = requests.post(f"{self.base_url}/k8s/search-logs", headers=self.headers, json=filter_params, params=params, timeout=120)
            return self._handle_response(response)
        except Exception as e:
            return None

    # --- Summary Endpoints ---
    def summarize_logs(self, summary_request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            response = requests.post(f"{self.base_url}/summary/", headers=self.headers, json=summary_request, timeout=180) # Longer timeout for GPT
            return self._handle_response(response)
        except Exception as e:
            st.error(f"Log summarization service error: {e}")
            return None

    def analyze_log_patterns(self, summary_request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            response = requests.post(f"{self.base_url}/summary/analyze-patterns", headers=self.headers, json=summary_request, timeout=180)
            return self._handle_response(response)
        except Exception as e:
            return None



# Example Usage (for testing or direct use in Streamlit app):
# if __name__ == "__main__":
#     BASE_URL = "http://localhost:8000/api/v1" # Replace with your actual FastAPI base URL
#     API_KEY = "your_secret_api_key"  # Replace with your actual API key if auth is enabled
    
#     client = LogAPIClient(base_url=BASE_URL, api_key=API_KEY)
    
#     print("--- Health Check ---")
#     health = client.health_check()
#     print(json.dumps(health, indent=2) if health else "Health check failed or no content")

#     print("\n--- GCS: List Files ---")
#     gcs_files = client.list_gcs_files(params={"prefix": "trades/", "limit": 5})
#     print(json.dumps(gcs_files, indent=2) if gcs_files else "Failed to list GCS files")

#     # Add more example calls here for other endpoints as needed 