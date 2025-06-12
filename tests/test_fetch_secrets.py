# runner/secret_manager_client.py

import os

from google.cloud import secretmanager
from google.oauth2 import service_account


def create_secret_manager_client():
    """
    Creates a Secret Manager Client.
    If running locally, loads Service Account credentials manually.
    If running inside GCP VM, uses default credentials.
    """
    # Detect if inside GCP environment
    if os.getenv("GOOGLE_CLOUD_PROJECT"):
        # Inside GCP (VM, Cloud Run, etc.)
        client = secretmanager.SecretManagerServiceClient()
        return client
    else:
        # Local machine (Windows/Mac/Linux)
        credentials = service_account.Credentials.from_service_account_file(
            r"D:\autotrade-453303-3c843b9f1ca3.json"  # <-- Update this path if needed
        )
        client = secretmanager.SecretManagerServiceClient(credentials=credentials)
        return client


def access_secret(secret_id, project_id):
    """
    Accesses the latest version of the specified secret.
    """
    client = create_secret_manager_client()
    name = f"projects/autotrade-453303/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(name=name)
    return response.payload.data.decode("UTF-8")
