"""
API Client for interacting with the Log Aggregator FastAPI service.
"""

import requests
import streamlit as st # For error messages and session state
from typing import List, Optional, Dict, Any
import os

# Assuming Pydantic models from FastAPI are similar or can be mapped to dicts for client
# For simplicity, this client will mostly return JSON/dicts.
# In a more complex scenario, you might share Pydantic models or have client-side models.

class LogAPIClient:
    def __init__(self, api_key: Optional[str] = None):
        # Base URL now points to the service and will be prefixed with /api/v1
        self.base_url = os.getenv("DASHBOARD_API_URL", "http://localhost:8001") + "/api/v1"
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
        """Checks the health of the FastAPI service with multiple fallback strategies."""
        # Try multiple endpoints to test connectivity
        test_endpoints = ["/", "/health", "/api/v1/", "/status"]
        
        for endpoint in test_endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", headers=self.headers, timeout=5)
                if response.status_code == 200:
                    result = response.json() if response.content else {"status": "ok"}
                    return {
                        "status": "ok",
                        "message": f"Log Aggregator API is running (endpoint: {endpoint})",
                        "response_time_ms": response.elapsed.total_seconds() * 1000,
                        "endpoint_used": endpoint,
                        "dependencies": {
                            "gcs_service": "unknown",
                            "firestore_service": "unknown", 
                            "k8s_service": "unknown",
                            "gpt_service_openai": "unknown"
                        }
                    }
            except requests.exceptions.RequestException:
                continue  # Try next endpoint
        
        # If all endpoints fail, return offline status
        st.warning("Log aggregator service completely unavailable - all endpoints failed")
        return {
            "status": "offline",
            "message": "Log aggregator service is not running. Dashboard running in offline mode.",
            "attempted_endpoints": test_endpoints,
            "dependencies": {
                "gcs_service": "offline",
                "firestore_service": "offline", 
                "k8s_service": "offline",
                "gpt_service_openai": "offline"
            }
        }

    # --- System Endpoints ---
    def get_system_health(self) -> Optional[Dict[str, Any]]:
        """Checks the health of the FastAPI service."""
        try:
            response = requests.get(f"{self.base_url}/system/health", headers=self.headers, timeout=5)
            return self._handle_response(response)
        except Exception:
            return {"status": "offline", "message": "Log aggregator service is not running."}

    # --- Log Retrieval Endpoints ---
    def list_gcs_log_files(self, prefix: Optional[str] = None, limit: int = 100) -> List[str]:
        params = {"prefix": prefix, "limit": limit}
        try:
            response = requests.get(f"{self.base_url}/logs/gcs", headers=self.headers, params=params, timeout=30)
            return self._handle_response(response)
        except Exception as e:
            st.error(f"Failed to list GCS files: {e}")
            return []

    def get_gcs_log_content(self, file_path: str) -> Optional[Dict[str, Any]]:
        params = {"file_path": file_path}
        try:
            response = requests.get(f"{self.base_url}/logs/gcs/content", headers=self.headers, params=params, timeout=60)
            return self._handle_response(response)
        except Exception as e:
            st.error(f"Failed to get GCS log content: {e}")
            return None

    def get_firestore_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        params = {"limit": limit}
        try:
            response = requests.get(f"{self.base_url}/logs/firestore", headers=self.headers, params=params, timeout=60)
            return self._handle_response(response)
        except Exception as e:
            st.error(f"Failed to get Firestore logs: {e}")
            return []

    def list_k8s_pods(self) -> List[str]:
        try:
            response = requests.get(f"{self.base_url}/logs/k8s/pods", headers=self.headers, timeout=30)
            return self._handle_response(response)
        except Exception as e:
            st.error(f"Failed to list Kubernetes pods: {e}")
            return []

    def get_k8s_pod_logs(self, pod_name: str, limit: int = 100) -> List[str]:
        params = {"pod_name": pod_name, "limit": limit}
        try:
            # Note: pod_name is now a query parameter
            response = requests.get(f"{self.base_url}/logs/k8s", headers=self.headers, params=params, timeout=120)
            return self._handle_response(response)
        except Exception as e:
            st.error(f"Failed to get Kubernetes pod logs: {e}")
            return []

    # --- Cognitive (AI) Endpoints ---
    def get_log_summary(self, source: str, identifier: str) -> Optional[Dict[str, Any]]:
        """Gets an AI-powered summary for a specific log."""
        params = {"source": source, "identifier": identifier}
        try:
            response = requests.get(f"{self.base_url}/cognitive/summary/logs", headers=self.headers, params=params, timeout=180) # Longer timeout for GPT
            return self._handle_response(response)
        except Exception as e:
            st.error(f"Log summarization service error: {e}")
            return None

    def get_portfolio_overview(self):
        """Fetches the portfolio overview data from the API."""
        response = requests.get(f"{self.base_url}/portfolio/overview")
        response.raise_for_status()
        return response.json()

    def login(self, username, password):
        """Logs the user in and returns an access token."""
        login_data = {
            'username': username,
            'password': password
        }
        response = requests.post(f"{self.base_url}/auth/token", data=login_data)
        response.raise_for_status()
        return response.json()

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