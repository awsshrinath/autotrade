from runner.trade_manager import TradeManager
from unittest.mock import Mock, patch


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


class MockStrategy:
    def __init__(self, kite, logger):
        self.kite = kite
        self.logger = logger
    
    def analyze(self):
        # Return a proper trade signal that the trade manager expects
        return {
            "symbol": "TEST",
            "entry_price": 100,
            "stop_loss": 95,
            "target": 110,
            "quantity": 50,
            "direction": "bullish",
            "id": "test_trade_123",
            "confidence": 0.8
        }


def test_run_strategy_once():
    kite = MockKite()
    firestore = MockFirestoreClient()
    trade_manager = TradeManager(
        logger=MockLogger(), kite=kite, firestore_client=firestore
    )
    
    # Mock the strategy import at the module level where it's used
    with patch('runner.trade_manager.VWAPStrategy', MockStrategy):
        # Simulate a trade run with a known strategy
        trade = trade_manager.run_strategy_once(
            strategy_name="vwap", direction="bullish", bot_type="stock"
        )
        
        # Verify trade was created and position tracked
        assert trade is not None, "Trade should be created"
        assert len(trade_manager.open_positions) == 1, "Position should be tracked"
        assert trade_manager.open_positions[0]['symbol'] == 'TEST'