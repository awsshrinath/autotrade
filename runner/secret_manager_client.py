import os
from google.cloud import secretmanager
from google.auth import default
from google.oauth2 import service_account
from kiteconnect import KiteConnect


def create_secret_manager_client():
    """
    Creates a Secret Manager Client.
    Prioritizes Service Account credentials from GOOGLE_APPLICATION_CREDENTIALS or local key file;
    otherwise uses default credentials (GCP VM, Cloud Run, etc.).
    """
    # Try local Service Account key first
    key_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS") or "./keys/autotrade.json"
    if key_path and os.path.isfile(key_path):
        credentials = service_account.Credentials.from_service_account_file(key_path)
    else:
        # Fallback to default credentials
        credentials, _ = default()
    return secretmanager.SecretManagerServiceClient(credentials=credentials)


def access_secret(secret_id, project_id):
    """
    Accesses the latest version of the specified secret from Secret Manager.
    """
    client = create_secret_manager_client()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(name=name)
    return response.payload.data.decode("UTF-8")


def get_kite_client(project_id):
    api_key = access_secret("ZERODHA_API_KEY", project_id)
    access_token = access_secret("ZERODHA_ACCESS_TOKEN", project_id)

    kite = KiteConnect(api_key=api_key)
    kite.set_access_token(access_token)
    return kite
