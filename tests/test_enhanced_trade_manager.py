import unittest
from unittest.mock import MagicMock, patch
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Mock external modules before imports
from tests.test_mocks import setup_all_mocks
setup_all_mocks()

from runner.enhanced_trade_manager import EnhancedTradeManager, TradeRequest
from config.config_manager import ConfigManager

class TestEnhancedTradeManager(unittest.TestCase):

    def setUp(self):
        """Set up the test environment before each test."""
        # Create a proper config mock with all required attributes
        self.mock_config = MagicMock()
        self.mock_config.paper_trade = True
        self.mock_config.default_capital = 100000
        self.mock_config.max_daily_loss = 5000
        self.mock_config.features = {"enhanced_trade_execution": True}
        self.mock_config.gcp = {"project_id": "test-project"}

        # Mock the enhanced logger creation
        mock_logger = MagicMock()
        mock_logger.log_event = MagicMock()
        mock_logger.log_trade = MagicMock()
        
        with patch('runner.enhanced_trade_manager.get_trading_config', return_value=self.mock_config):
            with patch('runner.enhanced_trade_manager.create_portfolio_manager', return_value=MagicMock()):
                with patch('runner.enhanced_trade_manager.CognitiveSystem', return_value=MagicMock()):
                    with patch('runner.enhanced_trade_manager.create_trading_logger', return_value=mock_logger):
                        self.trade_manager = EnhancedTradeManager(
                            enable_firestore=False,
                            enable_gcs=False
                        )

        self.mock_kite_client = MagicMock()
        self.trade_manager.kite_client = self.mock_kite_client
        # We also need to mock the logger inside, as it's created internally
        self.trade_manager.enhanced_logger = MagicMock()
        self.mock_logger = self.trade_manager.enhanced_logger

    def test_initialization(self):
        """Test if the EnhancedTradeManager initializes correctly."""
        self.assertIsNotNone(self.trade_manager)
        self.assertIsNotNone(self.trade_manager.enhanced_logger)

    def test_create_trade_request(self):
        """Test the creation of a TradeRequest object."""
        trade_req = TradeRequest(
            symbol="RELIANCE",
            strategy="vwap",
            direction="bullish",
            quantity=10,
            entry_price=2500.0,
            stop_loss=2450.0,
            target=2600.0,
            bot_type="stock",
            paper_trade=True
        )
        self.assertEqual(trade_req.symbol, "RELIANCE")
        self.assertEqual(trade_req.quantity, 10)
        self.assertTrue(trade_req.paper_trade)
        self.assertEqual(trade_req.order_type, "LIMIT")
        self.assertEqual(trade_req.product, "MIS")

    @patch('runner.enhanced_trade_manager.PositionMonitor')
    @patch('runner.enhanced_trade_manager.uuid.uuid4')
    def test_execute_paper_trade_flow(self, mock_uuid, mock_position_monitor):
        """Test the basic paper trade execution flow."""
        mock_uuid.return_value.hex = "test_trade_id"
        self.trade_manager.is_paper_trade = True
        # We need to mock the internal PositionMonitor instance as well
        self.trade_manager.position_monitor = mock_position_monitor

        trade_request = TradeRequest(
            symbol="RELIANCE",
            strategy="orb",
            direction="bullish",
            quantity=5,
            entry_price=1500.0,
            stop_loss=1480.0,
            target=1550.0,
            paper_trade=True,
            metadata={"source": "test"}
        )

        # Mock the _add_to_position_monitor to return a position ID
        self.trade_manager._add_to_position_monitor = MagicMock(return_value="pos_12345")

        position_id = self.trade_manager.execute_trade(trade_request)

        # Verify that the trade was added to the monitor
        self.trade_manager._add_to_position_monitor.assert_called_once_with(trade_request)
        
        # Verify a position ID was returned
        self.assertEqual(position_id, "pos_12345")

        # Verify logging
        self.trade_manager.enhanced_logger.log_event.assert_any_call(
            f"Trade execution requested: {trade_request.symbol}",
            'INFO',
            'TRADE',
            data=unittest.mock.ANY,
            source="enhanced_trade_manager"
        )

        self.mock_kite_client.place_order.assert_not_called()
        self.mock_logger.log_trade_entry.assert_called_once()
        call_args = self.mock_logger.log_trade_entry.call_args[0][0]
        self.assertEqual(call_args.symbol, "RELIANCE")
        self.assertEqual(call_args.status, "COMPLETED")


if __name__ == '__main__':
    unittest.main() 