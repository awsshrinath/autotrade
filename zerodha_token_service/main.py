from flask import Flask, request, jsonify
from kite_client import get_kite_login_url, generate_access_token, store_secret
import os

app = Flask(__name__)

@app.route("/login_url", methods=["GET"])
def login_url():
    url = get_kite_login_url()
    return jsonify({"login_url": url})

@app.route("/upload_token", methods=["POST"])
def upload_token():
    req_data = request.get_json()
    request_token = req_data.get("request_token")

    if not request_token:
        return jsonify({"error": "Missing request_token"}), 400

    access_token = generate_access_token(request_token)
    store_secret("ZERODHA_ACCESS_TOKEN", access_token)

    return jsonify({"message": "Access token stored successfully", "token": access_token})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)