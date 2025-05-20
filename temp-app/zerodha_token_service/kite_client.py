from kiteconnect import KiteConnect
from google.cloud import secretmanager

PROJECT_ID = "autotrade-453303"

def access_secret(secret_id: str) -> str:
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{PROJECT_ID}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(name=name)
    return response.payload.data.decode("UTF-8")

def store_secret(secret_id: str, value: str):
    client = secretmanager.SecretManagerServiceClient()
    parent = f"projects/{PROJECT_ID}/secrets/{secret_id}"
    client.add_secret_version(parent=parent, payload={"data": value.encode("UTF-8")})

def get_kite_login_url():
    api_key = access_secret("ZERODHA_API_KEY")
    kite = KiteConnect(api_key=api_key)
    return kite.login_url()

def generate_access_token(request_token: str) -> str:
    api_key = access_secret("ZERODHA_API_KEY")
    api_secret = access_secret("ZERODHA_API_SECRET")
    kite = KiteConnect(api_key=api_key)
    session = kite.generate_session(request_token, api_secret=api_secret)
    return session["access_token"]
