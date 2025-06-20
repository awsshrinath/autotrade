import datetime

from runner.kiteconnect_manager import KiteConnectManager
from runner.logger import create_enhanced_logger

if __name__ == "__main__":
    today_date = datetime.datetime.now().strftime("%Y-%m-%d")
    logger = create_enhanced_logger(session_id=f"test_kite_{today_date}")

    kite_manager = KiteConnectManager(logger)

    print("API Key:", kite_manager.api_key)
    print("API Secret:", kite_manager.api_secret)

    kite_manager.set_access_token()
    print("Access Token:", kite_manager.access_token)

    kite_client = kite_manager.get_kite_client()
    print("KiteConnect Client Initialized:", kite_client is not None)
