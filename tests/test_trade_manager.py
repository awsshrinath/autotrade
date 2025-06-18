from runner.trade_manager import EnhancedTradeManager, TradeRequest
import unittest
from unittest.mock import MagicMock, patch
from runner.strategies.vwap_strategy import VWAPStrategy


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
    trade_manager = EnhancedTradeManager(
        logger=MockLogger(),
        kite_manager=kite_manager,
        firestore_client=firestore,
        enable_firestore=False, # Disable for testing
        enable_gcs=False # Disable for testing
    )
    trade_manager.start_trading_session()
    
    # Mock the strategy import at the module level where it's used
    with patch('runner.trade_manager.VWAPStrategy', MockStrategy):
        # Simulate a trade run with a known strategy
        position_id = trade_manager.run_strategy_once(
            strategy_name="vwap", direction="bullish", bot_type="stock"
        )
        
        # Verify trade was created and position tracked
        assert position_id is not None, "Position should be created"
        active_positions = trade_manager.get_active_positions()
        assert len(active_positions) == 1, "Position should be tracked"
        assert active_positions[0]['symbol'] == 'TEST'


class TestEnhancedTradeManager(unittest.TestCase):
    def setUp(self):
        self.mock_logger = MagicMock()
        with patch('runner.trade_manager.create_trading_logger', return_value=self.mock_logger):
            self.trade_manager = EnhancedTradeManager(logger=self.mock_logger)

    def test_singleton_instance(self):
        with patch('runner.trade_manager.create_trading_logger', return_value=self.mock_logger):
            instance1 = EnhancedTradeManager(logger=self.mock_logger)
            instance2 = EnhancedTradeManager(logger=self.mock_logger)
            self.assertIs(instance1, instance2)

    def test_load_strategy(self):
        self.trade_manager.load_strategy('vwap', VWAPStrategy)
        self.assertIn('vwap', self.trade_manager.strategy_map)
        self.assertEqual(self.trade_manager.strategy_map['vwap'], VWAPStrategy)

    @patch('runner.trade_manager.VWAPStrategy', MagicMock())
    def test_start_trading(self):
        self.trade_manager.load_strategy('vwap', VWAPStrategy)
        with self.assertRaises(ValueError):
            self.trade_manager.start_trading('invalid_strategy', MagicMock())

    def test_execute_trade_paper(self):
        trade_request = TradeRequest(symbol='RELIANCE', strategy='vwap', direction='bullish', quantity=10,
                                     entry_price=2500.0, stop_loss=2490.0, target=2520.0, paper_trade=True)

        with patch('runner.trade_manager.PositionMonitor.add_position') as mock_add_position:
            self.trade_manager.execute_trade(trade_request)
            mock_add_position.assert_called_once()

    def test_execute_trade_live(self):
        trade_request = TradeRequest(symbol='RELIANCE', strategy='vwap', direction='bullish', quantity=10,
                                     entry_price=2500.0, stop_loss=2490.0, target=2520.0, paper_trade=False)

        with patch('runner.trade_manager.KiteConnectManager') as mock_kite_manager:
            mock_kite_manager.place_order.return_value = '12345'
            self.trade_manager.kite_manager = mock_kite_manager
            with patch('runner.trade_manager.PositionMonitor.add_position') as mock_add_position:
                self.trade_manager.execute_trade(trade_request)
                mock_add_position.assert_called_once()
                self.assertIn('12345', self.trade_manager.live_orders)


if __name__ == '__main__':
    unittest.main()