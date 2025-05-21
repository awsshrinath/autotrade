import hashlib

from google.api_core.exceptions import NotFound
from google.cloud import secretmanager
from kiteconnect import KiteConnect

PROJECT_ID = "autotrade-453303"
# Secret IDs - using descriptive names instead of hardcoded password strings
ACCESS_TOKEN_SECRET_ID = "ZERODHA_ACCESS_TOKEN"  # nosec
API_KEY_SECRET_ID = "ZERODHA_API_KEY"  # nosec
API_SECRET_SECRET_ID = "ZERODHA_API_SECRET"  # nosec


def access_secret(secret_id: str) -> str:
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{PROJECT_ID}/secrets/{secret_id}/versions/latest"
    try:
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8").strip()
    except NotFound:
        raise Exception(
            f"❌ Secret '{secret_id}' not found in Secret Manager."
        )


def update_access_token(token_value: str):
    client = secretmanager.SecretManagerServiceClient()
    parent = f"projects/{PROJECT_ID}/secrets/{ACCESS_TOKEN_SECRET_ID}"
    client.add_secret_version(
        request={
            "parent": parent,
            "payload": {"data": token_value.encode("UTF-8")},
        }
    )
    print("✅ Access token updated in Secret Manager.")


def calculate_checksum(api_key, request_token, api_secret):
    combined = api_key + request_token + api_secret
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()


def main():
    print("🔐 Fetching API key and secret from Secret Manager...")
    api_key = access_secret(API_KEY_SECRET_ID)
    api_secret = access_secret(API_SECRET_SECRET_ID)

    kite = KiteConnect(api_key=api_key)

    print("\n👉 Open this URL in your browser and log in:")
    print(kite.login_url())

    request_token = input(
        "\n🔁 Paste the request_token from the redirected URL here:\n> "
    ).strip()

    print("\n🔎 Debug Info:")
    print(f"🔑 API Key        : {api_key}")
    print(f"🔒 API Secret     : {api_secret}")
    print(f"🔁 Request Token  : {request_token}")
    print(
        f"✅ Checksum       : {calculate_checksum(api_key, request_token, api_secret)}"
    )

    try:
        print("\n⏳ Exchanging request token for access token...")
        data = kite.generate_session(
            request_token=request_token, api_secret=api_secret
        )
        access_token = data["access_token"]
        print(f"✅ Got access token: {access_token[:6]}...")

        update_access_token(access_token)

    except Exception as e:
        print("\n❌ Failed to generate session.")
        print(f"❗ Error: {e}")
        print("💡 Make sure the request_token is valid and not reused.")
        print("💡 Check if API key and secret are correct in Secret Manager.")
        return


if __name__ == "__main__":
    main()
