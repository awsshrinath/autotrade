"""
Streamlit page for Unified Log Monitoring.

This page will provide a UI to view and interact with logs from GCS,
Firestore, and Kubernetes, and to get GPT-based summaries.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import re

# Import the API client using absolute import
# This fixes the "attempted relative import with no known parent package" error
from dashboard.utils.log_api_client import LogAPIClient

# Placeholder: Initialize API client
# Make sure the FastAPI service is running and accessible.
# BASE_URL = "http://localhost:8000/api/v1" # Or from config
# API_KEY = "YOUR_API_KEY" # Or from config/secrets
# client = LogAPIClient(base_url=BASE_URL, api_key=API_KEY)

# Configuration for the API client (could be moved to a config file or Streamlit secrets)
# Ensure your FastAPI service is running at this address.
# The API_PREFIX from your FastAPI config should be part of this base_url.
# Try to get from environment variables first, then use default for GKE deployment
import os
FASTAPI_BASE_URL = os.environ.get("FASTAPI_BASE_URL", "http://log-monitor-service:8001/api/v1") 

# Initialize API client in session state to persist across reruns
if 'log_api_client' not in st.session_state:
    st.session_state.log_api_client = None

st.set_page_config(
    page_title="Log Monitor",
    page_icon="🔍",
    layout="wide"
)

st.title("🔍 Unified Log Monitor")
st.caption(f"Displaying logs and insights. Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# Function to initialize or update client, potentially after API key is entered
def initialize_api_client(api_key_to_use: Optional[str] = None):
    if api_key_to_use:
        st.session_state.log_api_client = LogAPIClient(base_url=FASTAPI_BASE_URL, api_key=api_key_to_use)
        st.session_state.user_authenticated = True
        st.session_state.api_key = api_key_to_use
        st.success("API Client initialized with new key.")
    elif st.session_state.get("api_key"):
        st.session_state.log_api_client = LogAPIClient(base_url=FASTAPI_BASE_URL, api_key=st.session_state.api_key)
        st.session_state.user_authenticated = True # Assuming stored key is valid
        st.info("API Client initialized with stored key.")
    else:
        st.session_state.log_api_client = LogAPIClient(base_url=FASTAPI_BASE_URL) # No API key (for unsecured dev or if auth is off)
        st.session_state.user_authenticated = False # Or True if auth is disabled on backend
        st.warning("API Client initialized without API key. Endpoints requiring auth may fail if auth is enabled on backend.")

# --- Authentication Check and Client Initialization ---
if 'user_authenticated' not in st.session_state:
    st.session_state.user_authenticated = False
if 'api_key' not in st.session_state:
    st.session_state.api_key = None

# Attempt to initialize client on first load if key already in session_state (e.g. from previous session)
if st.session_state.log_api_client is None and st.session_state.api_key:
    initialize_api_client(st.session_state.api_key)

with st.sidebar:
    st.header("API Configuration")
    # Allow users to update API key if needed
    new_api_key_input = st.text_input(
        "Enter API Key", 
        type="password", 
        value=st.session_state.get("api_key", ""),
        key="api_key_input_sidebar"
    )
    if st.button("Update API Key & Re-initialize Client"):
        if new_api_key_input:
            initialize_api_client(new_api_key_input)
            st.rerun()
        else:
            st.warning("Please enter an API key to update.")
    
    if st.session_state.log_api_client and st.session_state.user_authenticated:
        st.success("API Client is active.")
        # Perform a health check
        if st.button("Test API Connection (Health Check)"):
            with st.spinner("Checking API health..."):
                health_status = st.session_state.log_api_client.health_check()
                if health_status and health_status.get("status") == "ok":
                    st.success(f"API Connection Successful: {health_status.get('message')}")
                    st.json(health_status.get("dependencies", {}))
                elif health_status:
                    st.warning(f"API Status: {health_status.get('status')} - {health_status.get('message')}")
                    st.json(health_status.get("dependencies", {}))
                else:
                    st.error("Failed to connect to API or get health status.")
    elif not st.session_state.api_key:
        st.info("Enter an API key to activate client and features.")

# Stop page execution if client not properly initialized for authenticated access (if needed)
# This logic depends on whether your backend *requires* an API key for all/most operations.
# If AUTH_ENABLED is false on backend, client can operate without api_key.
# For this example, we allow page to load, and individual API calls will fail if key is missing & required.
if not st.session_state.log_api_client and st.session_state.user_authenticated: # Edge case: user_auth true but client not set
    initialize_api_client(st.session_state.api_key) # Try to re-init

if not st.session_state.user_authenticated and os.environ.get("REQUIRE_AUTH_GLOBALLY", "True").lower() == "true":
     st.warning("Please provide a valid API Key in the sidebar to use the log monitoring features.")
     st.stop()


# --- Main Page Layout ---
# Tabs for different log sources and summary
tab_gcs, tab_firestore, tab_k8s, tab_summary, tab_search = st.tabs([
    "📄 GCS Logs", "🔥 Firestore Logs", "☸️ Kubernetes Logs", "💡 Summaries", "🔎 Universal Search"
])

with tab_gcs:
    st.header("Google Cloud Storage (GCS) Logs")
    st.write("View logs from GCS buckets (trades/, reflections/, strategies/).")
    # Placeholder for GCS log display and filtering
    # st.info("GCS log viewing functionality will be implemented here.")

    client = st.session_state.get("log_api_client")
    if not client:
        st.warning("API client not initialized. Please configure API Key in the sidebar.")
        st.stop()

    # Section 1: List GCS Log Files
    st.subheader("List Log Files")
    if st.button("🔄 Refresh File List", key="gcs_refresh_list"):
        if "gcs_list_files_form_submitted_params" in st.session_state:
            pass # Placeholder for more robust refresh logic
        st.rerun()

    with st.form(key="gcs_list_files_form"):
        list_col1, list_col2 = st.columns(2)
        with list_col1:
            gcs_list_bucket_name = st.text_input("Bucket Name (optional, uses default if empty)", key="gcs_list_bucket")
            gcs_list_prefix = st.text_input("File Prefix (e.g., 'trades/')", key="gcs_list_prefix")
            gcs_list_file_pattern = st.text_input("File Name Pattern (regex, optional)", key="gcs_list_pattern")
        with list_col2:
            gcs_list_start_time_date = st.date_input("Start Date (optional)", value=None, key="gcs_list_start_date")
            gcs_list_start_time_time = st.time_input("Start Time (optional)", value=None, key="gcs_list_start_time")
            gcs_list_end_time_date = st.date_input("End Date (optional)", value=None, key="gcs_list_end_date")
            gcs_list_end_time_time = st.time_input("End Time (optional)", value=None, key="gcs_list_end_time")
        
        list_page = st.number_input("Page", min_value=1, value=st.session_state.get("gcs_list_page", 1), key="gcs_list_page_num")
        list_limit = st.selectbox("Files per page", options=[10, 25, 50, 100], index=1, key="gcs_list_limit_num")

        submitted_list_files = st.form_submit_button("Fetch GCS Files")

    if submitted_list_files:
        st.session_state.gcs_list_page = list_page 
        current_params = {
            "bucket_name": gcs_list_bucket_name if gcs_list_bucket_name else None,
            "prefix": gcs_list_prefix if gcs_list_prefix else None,
            "file_pattern": gcs_list_file_pattern if gcs_list_file_pattern else None,
            "skip": (list_page - 1) * list_limit,
            "limit": list_limit
        }
        if gcs_list_start_time_date and gcs_list_start_time_time:
            current_params["start_time"] = datetime.combine(gcs_list_start_time_date, gcs_list_start_time_time).isoformat()
        if gcs_list_end_time_date and gcs_list_end_time_time:
            current_params["end_time"] = datetime.combine(gcs_list_end_time_date, gcs_list_end_time_time).isoformat()
        st.session_state.gcs_list_files_form_submitted_params = current_params
        
        with st.spinner("Fetching GCS log files..."):
            response = client.list_gcs_files(params=current_params)
            if response and "items" in response:
                st.session_state.gcs_files_response = response
            else:
                st.session_state.gcs_files_response = None
                st.error("Failed to fetch GCS files or empty response.")
    
    if "gcs_files_response" in st.session_state and st.session_state.gcs_files_response:
        response_data = st.session_state.gcs_files_response
        files_df = pd.DataFrame(response_data["items"])
        st.write(f"Found {response_data['total']} files. Displaying page {list_page} ({len(files_df)} files)." )
        if not files_df.empty:
            st.dataframe(files_df, use_container_width=True)
        else:
            st.info("No files found matching your criteria for this page.")
        # Simple pagination display (actual page change handled by re-submission of form)
        total_pages = (response_data['total'] + list_limit - 1) // list_limit
        st.caption(f"Total pages: {total_pages if total_pages > 0 else 1}")

    st.markdown("---")
    # Section 2: Get GCS File Content
    st.subheader("Get File Content")
    with st.form(key="gcs_get_content_form"):
        gcs_content_bucket_name = st.text_input("Bucket Name", key="gcs_content_bucket")
        gcs_content_file_path = st.text_input("Full File Path (e.g., trades/log.txt)", key="gcs_content_path")
        submitted_get_content = st.form_submit_button("Fetch File Content")

    if submitted_get_content:
        if not gcs_content_bucket_name or not gcs_content_file_path:
            st.warning("Please provide both Bucket Name and File Path.")
        else:
            with st.spinner(f"Fetching content for {gcs_content_file_path}..."):
                response = client.get_gcs_file_content(bucket_name=gcs_content_bucket_name, file_path=gcs_content_file_path)
                if response and "raw_content" in response:
                    st.text_area("File Content", value=response["raw_content"], height=300, key="gcs_content_area")
                    with st.expander("File Info"):
                        st.json(response.get("log_file", {}))
                else:
                    st.error("Failed to fetch file content or file not found.")
    
    st.markdown("---")
    # Section 3: Search GCS Logs
    st.subheader("Search Within Logs")
    with st.form(key="gcs_search_logs_form"):
        search_col1, search_col2 = st.columns(2)
        with search_col1:
            gcs_search_keyword = st.text_input("Keyword to Search", key="gcs_search_keyword")
            gcs_search_bucket_name = st.text_input("Bucket Name (optional)", key="gcs_search_bucket")
        with search_col2:
            gcs_search_prefix = st.text_input("File Prefix (optional)", key="gcs_search_prefix")
            gcs_search_file_pattern = st.text_input("File Name Pattern (regex, optional)", key="gcs_search_fpattern")
        
        search_page = st.number_input("Page", min_value=1, value=st.session_state.get("gcs_search_page", 1), key="gcs_search_page_num")
        search_limit = st.selectbox("Results per page", options=[10, 25, 50, 100], index=1, key="gcs_search_limit_num")
        submitted_search_logs = st.form_submit_button("Search GCS Logs")

    if submitted_search_logs:
        if not gcs_search_keyword:
            st.warning("Please provide a keyword to search.")
        else:
            st.session_state.gcs_search_page = search_page
            filters = {
                "keyword": gcs_search_keyword,
                "bucket_name": gcs_search_bucket_name if gcs_search_bucket_name else None,
                "prefix": gcs_search_prefix if gcs_search_prefix else None,
                "file_pattern": gcs_search_file_pattern if gcs_search_file_pattern else None
            }
            pagination = {"skip": (search_page - 1) * search_limit, "limit": search_limit}
            
            with st.spinner("Searching GCS logs..."):
                response = client.search_gcs_logs(filters=filters, pagination=pagination)
                if response and "items" in response:
                    st.session_state.gcs_search_response = response
                else:
                    st.session_state.gcs_search_response = None
                    st.error("Search failed or no results found.")

    if "gcs_search_response" in st.session_state and st.session_state.gcs_search_response:
        response_data = st.session_state.gcs_search_response
        search_results_df = pd.DataFrame(response_data["items"])
        st.write(f"Found {response_data['total']} matching log entries. Displaying page {search_page} ({len(search_results_df)} entries)." )
        if not search_results_df.empty:
            # Display relevant fields from GCSLogEntry
            display_df = search_results_df[["timestamp", "message", "raw_content", "log_file"]].copy()
            display_df["log_file"] = display_df["log_file"].apply(lambda x: x.get('path', 'N/A') if isinstance(x, dict) else 'N/A')
            st.dataframe(display_df, use_container_width=True)
        else:
            st.info("No matching log entries found for your criteria on this page.")
        total_search_pages = (response_data['total'] + search_limit - 1) // search_limit
        st.caption(f"Total pages: {total_search_pages if total_search_pages > 0 else 1}")

with tab_firestore:
    st.header("Firestore Logs")
    st.write("View logs from Firestore collections (gpt_runner_trades, gpt_runner_reflections).")
    # Placeholder for Firestore log display and filtering
    # st.info("Firestore log viewing functionality will be implemented here.")

    client = st.session_state.get("log_api_client")
    if not client:
        st.warning("API client not initialized. Please configure API Key in the sidebar.")
        st.stop()

    # Section 1: Query Firestore Logs
    st.subheader("Query Collection")
    if st.button("🔄 Refresh Query Results", key="fs_refresh_query"):
        if "firestore_query_form_submitted_params" in st.session_state:
            pass # Placeholder for more robust refresh logic
        st.rerun()

    # Initialize filters in session state if not present
    if 'firestore_filters' not in st.session_state:
        st.session_state.firestore_filters = [] # List of dicts {field, operator, value}

    with st.form(key="firestore_query_form"):
        fs_query_col1, fs_query_col2 = st.columns(2)
        with fs_query_col1:
            fs_collection_name = st.text_input("Collection Name", value="gpt_runner_trades", key="fs_collection")
            fs_order_by = st.text_input("Order By Field (optional)", key="fs_order_by")
        with fs_query_col2:
            fs_order_direction = st.selectbox("Order Direction", options=["ASCENDING", "DESCENDING"], index=1, key="fs_order_dir")
            fs_limit_query = st.number_input("Limit Results", min_value=1, max_value=1000, value=25, key="fs_limit_q")

        st.markdown("**Filters**")
        # Display existing filters
        for i, f_filter in enumerate(st.session_state.firestore_filters):
            cols = st.columns([3,2,3,1])
            cols[0].text_input(f"Field##{i}", value=f_filter["field"], key=f"fs_f_field_{i}", disabled=True)
            cols[1].text_input(f"Operator##{i}", value=f_filter["operator"], key=f"fs_f_op_{i}", disabled=True)
            cols[2].text_input(f"Value##{i}", value=str(f_filter["value"]), key=f"fs_f_val_{i}", disabled=True)
            if cols[3].button(f"🗑️##{i}", key=f"fs_f_del_{i}"):
                st.session_state.firestore_filters.pop(i)
                st.rerun() # Rerun to update the displayed filters
        
        # Inputs to add a new filter
        st.markdown("Add New Filter:")
        new_filter_cols = st.columns([3,2,3])
        new_filter_field = new_filter_cols[0].text_input("Field", key="fs_new_f_field")
        new_filter_operator = new_filter_cols[1].selectbox("Operator", 
            options=["==", "!=", "<", "<=", ">", ">=", "array_contains", "array_contains_any", "in", "not_in"],
            key="fs_new_f_op"
        )
        new_filter_value = new_filter_cols[2].text_input("Value (auto-types, e.g., 123 for int, true for bool)", key="fs_new_f_val")
        # Add filter button is outside the form to allow adding filters without submitting query
        
        fs_start_after_doc_id = st.text_input("Start After Document ID (for pagination, optional)", key="fs_start_after")
        submitted_query_firestore = st.form_submit_button("Query Firestore")

    if st.button("Add Filter", key="fs_add_filter_btn"):
        if new_filter_field and new_filter_operator and new_filter_value:
            # Attempt to convert value to appropriate type
            try:
                typed_value = int(new_filter_value)
            except ValueError:
                try:
                    typed_value = float(new_filter_value)
                except ValueError:
                    if new_filter_value.lower() == 'true':
                        typed_value = True
                    elif new_filter_value.lower() == 'false':
                        typed_value = False
                    else:
                        typed_value = new_filter_value # Keep as string
            
            st.session_state.firestore_filters.append({
                "field": new_filter_field,
                "operator": new_filter_operator,
                "value": typed_value
            })
            # Clear input fields after adding
            # This requires a rerun and careful key management, or use st.empty()
            st.rerun()
        else:
            st.warning("Please fill all fields for the new filter.")

    if submitted_query_firestore:
        query_payload = {
            "collection_name": fs_collection_name,
            "filters": st.session_state.firestore_filters,
            "order_by": fs_order_by if fs_order_by else None,
            "order_direction": fs_order_direction if fs_order_by else None,
            "limit": fs_limit_query,
            "start_after": fs_start_after_doc_id if fs_start_after_doc_id else None
        }
        st.session_state.firestore_query_form_submitted_params = query_payload
        with st.spinner("Querying Firestore..."):
            response = client.query_firestore_logs(filter_params=query_payload)
            if response and "items" in response:
                st.session_state.firestore_query_response = response
            else:
                st.session_state.firestore_query_response = None
                st.error("Failed to query Firestore or no results.")

    if "firestore_query_response" in st.session_state and st.session_state.firestore_query_response:
        response_data = st.session_state.firestore_query_response
        if response_data["items"]:
            items_df = pd.DataFrame(response_data["items"])
            st.write(f"Found {len(items_df)} documents (limit was {fs_limit_query}).")
            st.dataframe(items_df, use_container_width=True)
            # For pagination, users can copy the last doc ID to "Start After Document ID"
            last_doc_id_query = items_df.iloc[-1]["id"] if not items_df.empty and "id" in items_df.columns else None
            if last_doc_id_query:
                st.info(f"To get next page, use Start After Document ID: {last_doc_id_query}")
        else:
            st.info("No documents found matching your criteria.")

    st.markdown("---")
    # Section 2: Get Firestore Document by ID
    st.subheader("Get Document by ID")
    with st.form(key="firestore_get_doc_form"):
        fs_get_doc_collection = st.text_input("Collection Name", value="gpt_runner_trades", key="fs_get_doc_coll")
        fs_get_doc_id = st.text_input("Document ID", key="fs_get_doc_id_val")
        submitted_get_document = st.form_submit_button("Fetch Document")

    if submitted_get_document:
        if not fs_get_doc_collection or not fs_get_doc_id:
            st.warning("Please provide Collection Name and Document ID.")
        else:
            with st.spinner(f"Fetching document {fs_get_doc_id} from {fs_get_doc_collection}..."):
                response = client.get_firestore_document(collection_name=fs_get_doc_collection, document_id=fs_get_doc_id)
                if response:
                    st.json(response) # Display full document as JSON
                else:
                    st.error("Failed to fetch document or document not found.")

with tab_k8s:
    st.header("Kubernetes Pod Logs")
    st.write("View logs from GKE pods.")
    # Placeholder for K8s log display and filtering
    # st.info("Kubernetes log viewing functionality will be implemented here.")

    client = st.session_state.get("log_api_client")
    if not client:
        st.warning("API client not initialized. Please configure API Key in the sidebar.")
        st.stop()

    # Section 1: List K8s Pods
    st.subheader("List Pods")
    if st.button("🔄 Refresh Pod List", key="k8s_refresh_pods"):
        if "k8s_list_pods_form_submitted_params" in st.session_state:
            pass # Placeholder for robust refresh
        st.rerun()

    with st.form(key="k8s_list_pods_form"):
        k8s_list_namespace = st.text_input("Namespace (optional, default from config)", key="k8s_list_ns")
        k8s_list_label_selector = st.text_input("Label Selector (e.g., app=my-app)", key="k8s_list_label")
        k8s_list_field_selector = st.text_input("Field Selector (e.g., status.phase=Running)", key="k8s_list_field")
        
        k8s_list_page = st.number_input("Page", min_value=1, value=st.session_state.get("k8s_list_pods_page", 1), key="k8s_list_pods_page_num")
        k8s_list_limit = st.selectbox("Pods per page", options=[10, 25, 50, 100], index=1, key="k8s_list_pods_limit_num")
        submitted_list_pods = st.form_submit_button("List K8s Pods")

    if submitted_list_pods:
        st.session_state.k8s_list_pods_page = k8s_list_page
        current_k8s_list_params = {
            "namespace": k8s_list_namespace if k8s_list_namespace else None,
            "label_selector": k8s_list_label_selector if k8s_list_label_selector else None,
            "field_selector": k8s_list_field_selector if k8s_list_field_selector else None,
            "skip": (k8s_list_page - 1) * k8s_list_limit,
            "limit": k8s_list_limit
        }
        st.session_state.k8s_list_pods_form_submitted_params = current_k8s_list_params
        with st.spinner("Listing K8s pods..."):
            response = client.list_k8s_pods(params=current_k8s_list_params)
            if response and "items" in response:
                st.session_state.k8s_pods_response = response
            else:
                st.session_state.k8s_pods_response = None
                st.error("Failed to list K8s pods or empty response.")
    
    if "k8s_pods_response" in st.session_state and st.session_state.k8s_pods_response:
        response_data = st.session_state.k8s_pods_response
        pods_df = pd.DataFrame(response_data["items"])
        st.write(f"Found {response_data['total']} pods. Displaying page {k8s_list_page} ({len(pods_df)} pods)." )
        if not pods_df.empty:
            st.dataframe(pods_df, use_container_width=True)
        else:
            st.info("No pods found matching your criteria for this page.")
        total_pods_pages = (response_data['total'] + k8s_list_limit - 1) // k8s_list_limit
        st.caption(f"Total pages: {total_pods_pages if total_pods_pages > 0 else 1}")

    st.markdown("---")
    # Section 2: Get K8s Pod Logs
    st.subheader("Get Pod Logs")
    if st.button("🔄 Refresh Pod Logs", key="k8s_refresh_pod_logs"):
         if "k8s_get_pod_logs_form_submitted_params" in st.session_state:
            pass # Placeholder for robust refresh
         st.rerun()

    with st.form(key="k8s_get_pod_logs_form"):
        log_col1, log_col2 = st.columns(2)
        with log_col1:
            k8s_log_pod_name = st.text_input("Pod Name", key="k8s_log_podname")
            k8s_log_namespace = st.text_input("Namespace (optional)", key="k8s_log_ns")
            k8s_log_container = st.text_input("Container Name (optional)", key="k8s_log_container")
            k8s_log_timestamps = st.checkbox("Include Timestamps?", value=True, key="k8s_log_timestamps")
        with log_col2:
            k8s_log_since_seconds = st.number_input("Since Seconds Ago (optional)", min_value=0, value=0, key="k8s_log_since")
            k8s_log_tail_lines = st.number_input("Tail Lines (optional, 0 for all)", min_value=0, value=100, key="k8s_log_tail")
            k8s_log_previous = st.checkbox("Fetch Previous Terminated Container's Logs?", value=False, key="k8s_log_previous")
        
        k8s_log_page = st.number_input("Page (for paginated logs from API)", min_value=1, value=st.session_state.get("k8s_log_page", 1), key="k8s_log_page_num")
        k8s_log_limit = st.selectbox("Lines per page (API pagination)", options=[100, 500, 1000, 5000], index=1, key="k8s_log_limit_num")
        submitted_get_pod_logs = st.form_submit_button("Fetch Pod Logs")
    
    # Log level filter for K8s logs
    if "k8s_pod_logs_original_text" in st.session_state and st.session_state.k8s_pod_logs_original_text:
        log_levels = ["INFO", "WARNING", "ERROR", "DEBUG", "CRITICAL", "FATAL"]
        selected_levels = st.multiselect("Filter by Log Level (client-side)", options=log_levels, default=st.session_state.get("k8s_log_levels_selected", []))
        st.session_state.k8s_log_levels_selected = selected_levels

    if submitted_get_pod_logs:
        if not k8s_log_pod_name:
            st.warning("Please provide Pod Name.")
        else:
            st.session_state.k8s_log_page = k8s_log_page
            filter_params = {
                "namespace": k8s_log_namespace if k8s_log_namespace else None,
                "container_name": k8s_log_container if k8s_log_container else None,
                "since_seconds": k8s_log_since_seconds if k8s_log_since_seconds > 0 else None,
                "tail_lines": k8s_log_tail_lines if k8s_log_tail_lines > 0 else None,
                "timestamps": k8s_log_timestamps,
                "previous": k8s_log_previous
            }
            pagination = {"skip": (k8s_log_page - 1) * k8s_log_limit, "limit": k8s_log_limit}
            st.session_state.k8s_get_pod_logs_form_submitted_params = {
                "pod_name": k8s_log_pod_name, 
                "filter_params": filter_params, 
                "pagination": pagination
            }
            with st.spinner(f"Fetching logs for pod {k8s_log_pod_name}..."):
                response = client.get_k8s_pod_logs(pod_name=k8s_log_pod_name, filter_params=filter_params, pagination=pagination)
                if response and "items" in response:
                    # Store the original, unfiltered logs from API
                    original_log_text = "\n".join(item.get("raw_content","") for item in response["items"])
                    st.session_state.k8s_pod_logs_original_text = original_log_text
                    st.session_state.k8s_pod_logs_api_response = response # Store full API response for pagination info
                else:
                    st.session_state.k8s_pod_logs_original_text = ""
                    st.session_state.k8s_pod_logs_api_response = None
                    st.error("Failed to fetch pod logs or no logs returned.")
                st.session_state.k8s_log_levels_selected = [] # Reset log level filter on new fetch

    # Display K8s Pod Logs (potentially filtered)
    if "k8s_pod_logs_original_text" in st.session_state and st.session_state.k8s_pod_logs_original_text:
        original_logs = st.session_state.k8s_pod_logs_original_text
        api_response_data = st.session_state.k8s_pod_logs_api_response
        current_log_page = st.session_state.get("k8s_get_pod_logs_form_submitted_params", {}).get("pagination",{}).get("skip",0)//st.session_state.get("k8s_get_pod_logs_form_submitted_params", {}).get("pagination",{}).get("limit",100)+1
        limit_per_page = st.session_state.get("k8s_get_pod_logs_form_submitted_params", {}).get("pagination",{}).get("limit",100)

        displayed_logs = original_logs
        if st.session_state.get("k8s_log_levels_selected"):
            filtered_lines = []
            for line in original_logs.split('\n'):
                if any(level.lower() in line.lower() for level in st.session_state.k8s_log_levels_selected):
                    filtered_lines.append(line)
            displayed_logs = "\n".join(filtered_lines)
        
        st.text_area("Pod Logs", value=displayed_logs, height=400, key="k8s_pod_log_area_display")
        
        if api_response_data:
            st.write(f"Displaying page {current_log_page} of logs ({len(api_response_data.get('items',[]))} lines from API response). Total lines available: {api_response_data.get('total', 'N/A')}")
            total_log_pages = (api_response_data.get('total', 0) + limit_per_page -1) // limit_per_page if api_response_data.get('total', 0) > 0 else 1
            st.caption(f"Total pages (API pagination): {total_log_pages if total_log_pages > 0 else 1}")
        else:
             st.info("No logs currently displayed or API response missing.")
    elif "k8s_get_pod_logs_form_submitted_params" in st.session_state: # If form was submitted but no logs
        st.info("No logs found for this pod with the given criteria.")

    st.markdown("---")
    # Section 3: Get K8s Pod Events
    st.subheader("Get Pod Events")
    with st.form(key="k8s_get_pod_events_form"):
        k8s_event_pod_name = st.text_input("Pod Name", key="k8s_event_podname")
        k8s_event_namespace = st.text_input("Namespace (optional)", key="k8s_event_ns")
        submitted_get_pod_events = st.form_submit_button("Fetch Pod Events")

    if submitted_get_pod_events:
        if not k8s_event_pod_name:
            st.warning("Please provide Pod Name.")
        else:
            with st.spinner(f"Fetching events for pod {k8s_event_pod_name}..."):
                response = client.get_k8s_pod_events(pod_name=k8s_event_pod_name, namespace=k8s_event_namespace if k8s_event_namespace else None)
                if response:
                    st.session_state.k8s_pod_events_response = response
                else:
                    st.session_state.k8s_pod_events_response = None
                    st.error("Failed to fetch pod events or no events found.")

    if "k8s_pod_events_response" in st.session_state and st.session_state.k8s_pod_events_response:
        events_df = pd.DataFrame(st.session_state.k8s_pod_events_response)
        if not events_df.empty:
            st.dataframe(events_df, use_container_width=True)
        else:
            st.info("No events found for this pod.")

    st.markdown("---")
    # Section 4: Search K8s Pod Logs
    st.subheader("Search Across Pod Logs")
    with st.form(key="k8s_search_logs_form"):
        k8s_search_col1, k8s_search_col2 = st.columns(2)
        with k8s_search_col1:
            k8s_search_query = st.text_input("Search Query (keyword or regex)", key="k8s_search_query")
            k8s_search_namespace = st.text_input("Namespace (optional)", key="k8s_search_ns")
        with k8s_search_col2:
            k8s_search_label_selector = st.text_input("Label Selector (optional)", key="k8s_search_label")
            k8s_search_field_selector = st.text_input("Field Selector (optional)", key="k8s_search_field")
        
        k8s_search_page = st.number_input("Page", min_value=1, value=st.session_state.get("k8s_search_page", 1), key="k8s_search_page_num")
        k8s_search_limit = st.selectbox("Results per page", options=[10, 25, 50, 100], index=1, key="k8s_search_limit_num")
        submitted_search_k8s_logs = st.form_submit_button("Search K8s Logs")
    
    if submitted_search_k8s_logs:
        if not k8s_search_query:
            st.warning("Please provide a search query.")
        else:
            st.session_state.k8s_search_page = k8s_search_page
            filter_params = {
                "namespace": k8s_search_namespace if k8s_search_namespace else None,
                "label_selector": k8s_search_label_selector if k8s_search_label_selector else None,
                "field_selector": k8s_search_field_selector if k8s_search_field_selector else None,
                # Add other relevant filters from your API if available, e.g., time range
            }
            pagination = {"skip": (k8s_search_page - 1) * k8s_search_limit, "limit": k8s_search_limit}

            with st.spinner("Searching K8s logs..."):
                response = client.search_k8s_logs(search_query=k8s_search_query, filter_params=filter_params, pagination=pagination)
                if response and "items" in response:
                    st.session_state.k8s_search_log_response = response
                else:
                    st.session_state.k8s_search_log_response = None
                    st.error("Search failed or no results found.")
    
    if "k8s_search_log_response" in st.session_state and st.session_state.k8s_search_log_response:
        response_data = st.session_state.k8s_search_log_response
        search_results_df = pd.DataFrame(response_data["items"])
        st.write(f"Found {response_data['total']} matching log entries. Displaying page {k8s_search_page} ({len(search_results_df)} entries)." )
        if not search_results_df.empty:
            st.dataframe(search_results_df, use_container_width=True) # Adjust columns as needed
        else:
            st.info("No matching log entries found.")
        total_k8s_search_pages = (response_data['total'] + k8s_search_limit - 1) // k8s_search_limit
        st.caption(f"Total pages: {total_k8s_search_pages if total_k8s_search_pages > 0 else 1}")

with tab_summary:
    st.header("Log Summarization (GPT)")
    st.write("Get AI-powered summaries of your logs.")
    # Placeholder for log summarization
    # st.info("Log summarization functionality will be implemented here.")

    client = st.session_state.get("log_api_client")
    if not client:
        st.warning("API client not initialized. Please configure API Key in the sidebar.")
        st.stop()

    summary_type_options = ["general", "error_focus", "performance_issues", "security_events", "key_trends"]
    analysis_type_options = ["error_patterns", "performance_bottlenecks", "security_anomalies", "usage_trends", "all_patterns"]

    summary_log_source = st.selectbox(
        "Select Log Source for Summarization/Analysis", 
        options=["Raw Text", "GCS File", "Firestore Query", "Kubernetes Pod Logs"],
        key="summary_log_source_type"
    )

    source_params = {}
    log_content_for_summary = ""

    if summary_log_source == "Raw Text":
        log_content_for_summary = st.text_area("Paste Log Content Here (max 500KB for summarization via API if dynamic fetching is not used)", height=200, key="summary_raw_text")
        source_params["log_content"] = log_content_for_summary
    elif summary_log_source == "GCS File":
        st.markdown("**GCS File Parameters**")
        gcs_sum_bucket = st.text_input("GCS Bucket Name", key="gcs_sum_bucket")
        gcs_sum_path = st.text_input("GCS File Path", key="gcs_sum_path")
        source_params = {"source_type": "gcs", "bucket_name": gcs_sum_bucket, "file_path": gcs_sum_path}
    elif summary_log_source == "Firestore Query":
        st.markdown("**Firestore Query Parameters** (Simplified - uses last query from Firestore tab or default)")
        # For simplicity, we might reuse filters from the Firestore tab if populated
        # Or provide a simplified query input here.
        # This example will require manual entry or rely on a pre-set query for the API.
        fs_sum_collection = st.text_input("Firestore Collection", value="gpt_runner_trades", key="fs_sum_coll")
        # Potentially add a few simple filter inputs here if needed for summarization context
        fs_sum_limit = st.number_input("Limit documents for summary context", value=50, key="fs_sum_limit")
        source_params = {"source_type": "firestore", "collection_name": fs_sum_collection, "limit": fs_sum_limit} 
        st.caption("Note: Complex filtering for Firestore summary source needs to be defined in the API or use a more complex UI here.")
    elif summary_log_source == "Kubernetes Pod Logs":
        st.markdown("**Kubernetes Pod Log Parameters**")
        k8s_sum_pod = st.text_input("Pod Name", key="k8s_sum_pod")
        k8s_sum_ns = st.text_input("Namespace (optional)", key="k8s_sum_ns")
        k8s_sum_container = st.text_input("Container (optional)", key="k8s_sum_container")
        k8s_sum_tail = st.number_input("Tail Lines for summary context", value=200, key="k8s_sum_tail")
        source_params = {
            "source_type": "k8s", 
            "pod_name": k8s_sum_pod, 
            "namespace": k8s_sum_ns if k8s_sum_ns else None, 
            "container_name": k8s_sum_container if k8s_sum_container else None,
            "tail_lines": k8s_sum_tail
        }

    st.markdown("---")
    # Section 1: Get Summaries
    st.subheader("Generate Log Summary")
    with st.form(key="summary_get_form"):
        summary_type = st.selectbox("Select Summary Type", options=summary_type_options, key="summary_type_select")
        custom_prompt_summary = st.text_area("Custom Instructions (optional, will be appended to default prompt)", height=100, key="summary_custom_prompt")
        submitted_get_summary = st.form_submit_button("Get Summary")

    if submitted_get_summary:
        if summary_log_source == "Raw Text" and not log_content_for_summary:
            st.warning("Please paste log content for Raw Text summarization.")
        elif summary_log_source != "Raw Text" and not all(source_params.get(k) for k in ({"GCS File": ["bucket_name", "file_path"], "Firestore Query": ["collection_name"], "Kubernetes Pod Logs": ["pod_name"]}.get(summary_log_source, []))):
             st.warning(f"Please fill all required fields for {summary_log_source} source.")
        else:
            request_payload = {
                "summary_type": summary_type,
                "custom_prompt_override": custom_prompt_summary if custom_prompt_summary else None,
            }
            if summary_log_source == "Raw Text":
                request_payload["log_content"] = log_content_for_summary
            else:
                request_payload.update(source_params)
            
            with st.spinner("Generating summary..."):
                response = client.summarize_logs(request_payload)
                if response and "summary" in response:
                    st.session_state.summary_response = response
                else:
                    st.session_state.summary_response = None
                    st.error("Failed to generate summary.")
    
    if "summary_response" in st.session_state and st.session_state.summary_response:
        st.markdown("**Generated Summary:**")
        st.markdown(st.session_state.summary_response["summary"])
        with st.expander("Summary Request Details & Stats"):
            st.json(st.session_state.summary_response)

    st.markdown("---")
    # Section 2: Analyze Log Patterns
    st.subheader("Analyze Log Patterns")
    with st.form(key="summary_analyze_form"):
        analysis_type = st.selectbox("Select Analysis Type", options=analysis_type_options, key="analysis_type_select")
        custom_prompt_analysis = st.text_area("Custom Instructions (optional)", height=100, key="analysis_custom_prompt")
        submitted_analyze_patterns = st.form_submit_button("Analyze Patterns")
    
    if submitted_analyze_patterns:
        if summary_log_source == "Raw Text" and not log_content_for_summary:
            st.warning("Please paste log content for Raw Text pattern analysis.")
        elif summary_log_source != "Raw Text" and not all(source_params.get(k) for k in ({"GCS File": ["bucket_name", "file_path"], "Firestore Query": ["collection_name"], "Kubernetes Pod Logs": ["pod_name"]}.get(summary_log_source, []))):
             st.warning(f"Please fill all required fields for {summary_log_source} source.")
        else:
            request_payload = {
                "analysis_type": analysis_type, # API expects this for pattern analysis endpoint
                "custom_prompt_override": custom_prompt_analysis if custom_prompt_analysis else None,
            }
            if summary_log_source == "Raw Text":
                request_payload["log_content"] = log_content_for_summary
            else:
                request_payload.update(source_params)
            
            with st.spinner("Analyzing log patterns..."):
                response = client.analyze_log_patterns(request_payload)
                if response and "analysis_results" in response:
                    st.session_state.analysis_response = response
                else:
                    st.session_state.analysis_response = None
                    st.error("Failed to analyze log patterns.")

    if "analysis_response" in st.session_state and st.session_state.analysis_response:
        st.markdown("**Pattern Analysis Results:**")
        st.json(st.session_state.analysis_response["analysis_results"]) # Or format nicely
        with st.expander("Analysis Request Details & Stats"):
            st.json(st.session_state.analysis_response)

with tab_search:
    st.header("Universal Log Search")
    st.write("Search across different log sources.")
    # Placeholder for universal search
    st.info("This section provides a way to search specific sources. True cross-source universal search is a future enhancement.")

    client = st.session_state.get("log_api_client")
    if not client:
        st.warning("API client not initialized. Please configure API Key in the sidebar.")
        st.stop()

    st.info("This section provides a way to search specific sources. True cross-source universal search is a future enhancement.")

    # Sub-section for GCS Search
    st.subheader("Search GCS Logs")
    with st.form(key="universal_gcs_search_logs_form"):
        uni_gcs_search_col1, uni_gcs_search_col2 = st.columns(2)
        with uni_gcs_search_col1:
            uni_gcs_search_keyword = st.text_input("Keyword to Search", key="uni_gcs_search_keyword")
            uni_gcs_search_bucket_name = st.text_input("Bucket Name (optional)", key="uni_gcs_search_bucket")
        with uni_gcs_search_col2:
            uni_gcs_search_prefix = st.text_input("File Prefix (optional)", key="uni_gcs_search_prefix")
            uni_gcs_search_file_pattern = st.text_input("File Name Pattern (regex, optional)", key="uni_gcs_search_fpattern")
        
        uni_gcs_search_page = st.number_input("Page", min_value=1, value=st.session_state.get("uni_gcs_search_page", 1), key="uni_gcs_search_page_num")
        uni_gcs_search_limit = st.selectbox("Results per page", options=[10, 25, 50, 100], index=1, key="uni_gcs_search_limit_num")
        uni_submitted_search_gcs_logs = st.form_submit_button("Search GCS Logs")

    if uni_submitted_search_gcs_logs:
        if not uni_gcs_search_keyword:
            st.warning("Please provide a keyword to search in GCS.")
        else:
            st.session_state.uni_gcs_search_page = uni_gcs_search_page
            filters = {
                "keyword": uni_gcs_search_keyword,
                "bucket_name": uni_gcs_search_bucket_name if uni_gcs_search_bucket_name else None,
                "prefix": uni_gcs_search_prefix if uni_gcs_search_prefix else None,
                "file_pattern": uni_gcs_search_file_pattern if uni_gcs_search_file_pattern else None
            }
            pagination = {"skip": (uni_gcs_search_page - 1) * uni_gcs_search_limit, "limit": uni_gcs_search_limit}
            
            with st.spinner("Searching GCS logs..."):
                response = client.search_gcs_logs(filters=filters, pagination=pagination)
                if response and "items" in response:
                    st.session_state.uni_gcs_search_response = response
                else:
                    st.session_state.uni_gcs_search_response = None
                    st.error("GCS Search failed or no results found.")

    if "uni_gcs_search_response" in st.session_state and st.session_state.uni_gcs_search_response:
        uni_gcs_response_data = st.session_state.uni_gcs_search_response
        uni_gcs_search_results_df = pd.DataFrame(uni_gcs_response_data["items"])
        st.write(f"GCS Search: Found {uni_gcs_response_data['total']} matching log entries. Displaying page {uni_gcs_search_page} ({len(uni_gcs_search_results_df)} entries)." )
        if not uni_gcs_search_results_df.empty:
            display_df_gcs = uni_gcs_search_results_df[["timestamp", "message", "raw_content", "log_file"]].copy()
            display_df_gcs["log_file"] = display_df_gcs["log_file"].apply(lambda x: x.get('path', 'N/A') if isinstance(x, dict) else 'N/A')
            st.dataframe(display_df_gcs, use_container_width=True)
        else:
            st.info("No matching log entries found in GCS for your criteria on this page.")
        uni_total_gcs_search_pages = (uni_gcs_response_data['total'] + uni_gcs_search_limit - 1) // uni_gcs_search_limit
        st.caption(f"Total GCS search pages: {uni_total_gcs_search_pages if uni_total_gcs_search_pages > 0 else 1}")

    st.markdown("---")
    # Sub-section for K8s Search
    st.subheader("Search Kubernetes Pod Logs")
    with st.form(key="universal_k8s_search_logs_form"):
        uni_k8s_search_col1, uni_k8s_search_col2 = st.columns(2)
        with uni_k8s_search_col1:
            uni_k8s_search_query = st.text_input("Search Query (keyword or regex)", key="uni_k8s_search_query")
            uni_k8s_search_namespace = st.text_input("Namespace (optional)", key="uni_k8s_search_ns")
        with uni_k8s_search_col2:
            uni_k8s_search_label_selector = st.text_input("Label Selector (optional)", key="uni_k8s_search_label")
            uni_k8s_search_field_selector = st.text_input("Field Selector (optional)", key="uni_k8s_search_field")
        
        uni_k8s_search_page = st.number_input("Page", min_value=1, value=st.session_state.get("uni_k8s_search_page", 1), key="uni_k8s_search_page_num")
        uni_k8s_search_limit = st.selectbox("Results per page", options=[10, 25, 50, 100], index=1, key="uni_k8s_search_limit_num")
        uni_submitted_search_k8s_logs = st.form_submit_button("Search K8s Logs")
    
    if uni_submitted_search_k8s_logs:
        if not uni_k8s_search_query:
            st.warning("Please provide a search query for K8s.")
        else:
            st.session_state.uni_k8s_search_page = uni_k8s_search_page
            filters = {
                "namespace": uni_k8s_search_namespace if uni_k8s_search_namespace else None,
                "label_selector": uni_k8s_search_label_selector if uni_k8s_search_label_selector else None,
                "field_selector": uni_k8s_search_field_selector if uni_k8s_search_field_selector else None,
            }
            pagination = {"skip": (uni_k8s_search_page - 1) * uni_k8s_search_limit, "limit": uni_k8s_search_limit}

            with st.spinner("Searching K8s logs..."):
                response = client.search_k8s_logs(search_query=uni_k8s_search_query, filter_params=filters, pagination=pagination)
                if response and "items" in response:
                    st.session_state.uni_k8s_search_log_response = response
                else:
                    st.session_state.uni_k8s_search_log_response = None
                    st.error("K8s Search failed or no results found.")
    
    if "uni_k8s_search_log_response" in st.session_state and st.session_state.uni_k8s_search_log_response:
        uni_k8s_response_data = st.session_state.uni_k8s_search_log_response
        uni_k8s_search_results_df = pd.DataFrame(uni_k8s_response_data["items"])
        st.write(f"K8s Search: Found {uni_k8s_response_data['total']} matching log entries. Displaying page {uni_k8s_search_page} ({len(uni_k8s_search_results_df)} entries)." )
        if not uni_k8s_search_results_df.empty:
            st.dataframe(uni_k8s_search_results_df, use_container_width=True) 
        else:
            st.info("No matching log entries found in K8s.")
        uni_total_k8s_search_pages = (uni_k8s_response_data['total'] + uni_k8s_search_limit - 1) // uni_k8s_search_limit
        st.caption(f"Total K8s search pages: {uni_total_k8s_search_pages if uni_total_k8s_search_pages > 0 else 1}")

st.sidebar.markdown("---")
st.sidebar.markdown("### About")
st.sidebar.markdown("This page provides a unified interface to monitor and analyze logs from various services integrated with the GPT Runner+ project.") 