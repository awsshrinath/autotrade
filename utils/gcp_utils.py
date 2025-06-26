"""
GCP utilities for dashboard API
"""

import os
from google.cloud import firestore
from google.cloud.firestore_v1.client import Client

def get_firestore_client() -> Client:
    """
    Get a Firestore client instance.
    
    Returns:
        Client: Firestore client instance
    """
    try:
        # Get project ID from environment
        project_id = os.environ.get('GCP_PROJECT_ID', 'autotrade-453303')
        
        # Initialize Firestore client
        client = firestore.Client(project=project_id)
        
        return client
    except Exception as e:
        print(f"Warning: Could not initialize Firestore client: {e}")
        # Return a mock client for development/testing
        return None