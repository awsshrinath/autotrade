import unittest
from unittest.mock import MagicMock, patch
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from runner.enhanced_trade_manager import EnhancedTradeManager, TradeRequest

class TestEnhancedTradeManager(unittest.TestCase):

    def setUp(self):
        """Set up a mock environment for each test."""
        # Mock the dependencies of EnhancedTradeManager
        self.mock_logger = MagicMock()
        self.mock_kite_manager = MagicMock()
        self.mock_firestore_client = MagicMock()
        self.mock_cognitive_system = MagicMock()

        self.trade_manager = EnhancedTradeManager(
            logger=self.mock_logger,
            kite_manager=self.mock_kite_manager,
            firestore_client=self.mock_firestore_client,
            cognitive_system=self.mock_cognitive_system
        )

    def test_initialization(self):
        """Test if the EnhancedTradeManager initializes correctly."""
        self.assertIsNotNone(self.trade_manager)
        self.assertEqual(self.trade_manager.logger, self.mock_logger)
        self.trade_manager.enhanced_logger.log_event.assert_called_with(
            "EnhancedTradeManager initialized with comprehensive logging",
            'INFO', # Assuming LogLevel.INFO is 'INFO'
            'SYSTEM', # Assuming LogCategory.SYSTEM is 'SYSTEM'
            data=unittest.mock.ANY,
            source="enhanced_trade_manager"
        )

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

    @patch('runner.enhanced_trade_manager.PositionMonitor')
    def test_execute_paper_trade_flow(self, mock_position_monitor):
        """Test the basic paper trade execution flow."""
        # We need to mock the internal PositionMonitor instance as well
        self.trade_manager.position_monitor = mock_position_monitor

        trade_request = TradeRequest(
            symbol="INFY",
            strategy="orb",
            direction="bullish",
            quantity=5,
            entry_price=1500.0,
            stop_loss=1480.0,
            target=1550.0,
            paper_trade=True
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


if __name__ == '__main__':
    unittest.main() 