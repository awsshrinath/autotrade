import unittest
from unittest.mock import MagicMock, patch, ANY
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Mock external modules before imports
from tests.test_mocks import setup_all_mocks
setup_all_mocks()

from runner.trade_manager import EnhancedTradeManager, TradeRequest, create_enhanced_trade_manager
from strategies.vwap_strategy import VWAPStrategy


class TestEnhancedTradeManager(unittest.TestCase):
    
    @patch('runner.trade_manager.create_trading_logger')
    @patch('runner.trade_manager.get_trading_config')
    @patch('runner.trade_manager.create_cognitive_system')
    @patch('runner.trade_manager.create_portfolio_manager')
    @patch('runner.trade_manager.PositionMonitor')
    def setUp(self, MockPositionMonitor, mock_create_portfolio_manager, 
              mock_create_cognitive_system, mock_get_trading_config, 
              mock_create_trading_logger):
        """Set up a mock environment for each test."""
        
        # Mock configuration
        self.mock_config = MagicMock()
        self.mock_config.paper_trade = True
        self.mock_config.default_capital = 100000
        self.mock_config.max_daily_loss = 5000
        mock_get_trading_config.return_value = self.mock_config

        # Mock logger
        self.mock_logger = MagicMock()
        mock_create_trading_logger.return_value = self.mock_logger
        
        # Mock dependencies
        self.mock_kite_manager = MagicMock()
        self.mock_firestore_client = MagicMock()
        self.mock_cognitive_system = mock_create_cognitive_system.return_value
        self.mock_portfolio_manager = mock_create_portfolio_manager.return_value
        
        # We need to mock the PositionMonitor instance used by TradeManager
        self.mock_position_monitor = MockPositionMonitor.return_value
        
        # Instantiate the manager
        self.trade_manager = EnhancedTradeManager(
            logger=self.mock_logger,
            kite_manager=self.mock_kite_manager,
            firestore_client=self.mock_firestore_client,
            cognitive_system=self.mock_cognitive_system,
            enable_firestore=False,
            enable_gcs=False
        )
        # The internal position monitor is created inside __init__, so we override it here for testing
        self.trade_manager.position_monitor = self.mock_position_monitor


    def test_initialization(self):
        """Test if the EnhancedTradeManager initializes correctly."""
        self.assertIsNotNone(self.trade_manager)
        self.assertIsNotNone(self.trade_manager.enhanced_logger)
        # Check that the enhanced logger was called with the expected message
        self.mock_logger.log_event.assert_called_with(
            "EnhancedTradeManager initialized with comprehensive logging",
            ANY,  # LogLevel.INFO
            ANY,  # LogCategory.SYSTEM
            data=ANY,  # data dictionary
            source='enhanced_trade_manager'
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
        # Assert that attributes that were removed are NOT present
        self.assertFalse(hasattr(trade_req, 'order_type'))
        self.assertFalse(hasattr(trade_req, 'product'))

    def test_load_strategy_placeholder(self):
        """
        Test the load_strategy method.
        Note: The current implementation is a placeholder. This test just ensures it runs without error.
        """
        try:
            self.trade_manager.load_strategy('vwap')
        except Exception as e:
            self.fail(f"load_strategy raised an exception unexpectedly: {e}")

    def test_execute_paper_trade(self):
        """Test the paper trade execution flow."""
        trade_request = TradeRequest(symbol='RELIANCE', strategy='vwap', direction='bullish', quantity=10,
                                     entry_price=2500.0, stop_loss=2490.0, target=2520.0, paper_trade=True)
        
        # Mock the return value for the risk and portfolio checks
        with patch.object(self.trade_manager, '_perform_risk_checks', return_value=True), \
             patch.object(self.trade_manager, '_perform_portfolio_checks', return_value=True), \
             patch.object(self.trade_manager, '_add_to_position_monitor', return_value='pos_123') as mock_add_to_monitor:

            position_id = self.trade_manager.execute_trade(trade_request)
            
            mock_add_to_monitor.assert_called_once_with(trade_request)
            self.assertEqual(position_id, 'pos_123')


    def test_execute_live_trade(self):
        """Test the live trade execution flow."""
        trade_request = TradeRequest(symbol='RELIANCE', strategy='vwap', direction='bullish', quantity=10,
                                     entry_price=2500.0, stop_loss=2490.0, target=2520.0, paper_trade=False)
        
        # Mock the kite client's response
        self.mock_kite_manager.place_order.return_value = "live_order_id_123"

        # Mock the risk and portfolio checks
        with patch.object(self.trade_manager, '_perform_risk_checks', return_value=True), \
             patch.object(self.trade_manager, '_perform_portfolio_checks', return_value=True), \
             patch.object(self.trade_manager, '_add_to_position_monitor', return_value='pos_456') as mock_add_to_monitor:
            
            position_id = self.trade_manager.execute_trade(trade_request)

            # Verify that a real order was placed
            self.mock_kite_manager.place_order.assert_called_once()
            
            # Verify the position was added to the monitor
            mock_add_to_monitor.assert_called_once()
            self.assertEqual(position_id, 'pos_456')


if __name__ == '__main__':
    unittest.main()