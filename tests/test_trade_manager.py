from runner.enhanced_trade_manager import create_enhanced_trade_manager, TradeRequest
from unittest.mock import Mock, patch


class MockLogger:
    def log_event(self, msg):
        print(f"[MOCK LOG] {msg}")


class MockKiteManager:
    def get_kite_client(self):
        return MockKite()


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
    kite_manager = MockKiteManager()
    firestore = MockFirestoreClient()
    trade_manager = create_enhanced_trade_manager(
        logger=MockLogger(), kite_manager=kite_manager, firestore_client=firestore
    )
    trade_manager.start_trading_session()
    
    # Mock the strategy import at the module level where it's used
    with patch('runner.enhanced_trade_manager.VWAPStrategy', MockStrategy):
        # Simulate a trade run with a known strategy
        position_id = trade_manager.run_strategy_once(
            strategy_name="vwap", direction="bullish", bot_type="stock"
        )
        
        # Verify trade was created and position tracked
        assert position_id is not None, "Position should be created"
        active_positions = trade_manager.get_active_positions()
        assert len(active_positions) == 1, "Position should be tracked"
        assert active_positions[0]['symbol'] == 'TEST'