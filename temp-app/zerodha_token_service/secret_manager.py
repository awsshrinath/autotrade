from google.cloud import secretmanager

PROJECT_ID = "autotrade-453303"

def access_secret(secret_id):
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{PROJECT_ID}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(name=name)
    return response.payload.data.decode("UTF-8")

API_KEY = access_secret("ZERODHA_API_KEY")
API_SECRET = access_secret("ZERODHA_API_SECRET")
