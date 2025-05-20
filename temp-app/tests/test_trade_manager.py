
import pytest
from unittest.mock import MagicMock
from runner.trade_manager import TradeManager
from google.cloud import firestore

class MockLogger:
    def log_event(self, msg):
        print(f"[MOCK LOG] {msg}")

class MockKite:
    def place_order(self, *args, **kwargs):
        print("[MOCK KITE] Order placed")
        return 12345

class MockFirestoreClient:
    def log_trade(self, trade_data):
        print(f"[MOCK FIRESTORE] Trade Logged: {trade_data}")

def mock_strategy_function(symbol, direction):
    # Mocked strategy function that always returns a trade signal
    return {
        "symbol": symbol,
        "entry_price": 100,
        "stop_loss": 95,
        "target": 110,
        "quantity": 50,
        "direction": direction
    }

def test_run_strategy_once():
    kite = MockKite()
    firestore = MockFirestoreClient()
    trade_manager = TradeManager(logger=MockLogger(), kite=kite, firestore_client=firestore)
    # Attach mock strategy
    trade_manager.strategy_map = {
        "mock_strategy": mock_strategy_function
    }

    # Simulate a trade run
    trade_manager.run_strategy_once(strategy_name="mock_strategy", direction="bullish", bot_type="stock")

    # Verify open positions tracked
    assert len(trade_manager.open_positions) == 1
