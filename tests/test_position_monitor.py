import unittest
from unittest.mock import MagicMock, patch
import os
import sys
import asyncio
import time
import threading

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from runner.position_monitor import PositionMonitor, ExitStrategy, TradeStatus, ExitReason
from config.config_manager import ConfigManager
from runner.trade_manager import TradeRequest
from runner.enhanced_logger import EnhancedLogger, create_enhanced_logger

class TestPositionMonitor(unittest.TestCase):

    @patch('runner.position_monitor.create_enhanced_logger')
    def setUp(self, mock_create_logger):
        """Set up a mock environment for each test."""
        self.mock_config_manager = MagicMock(spec=ConfigManager)
        self.mock_config_manager.get_config.return_value = {
            "gcp": {"project_id": "test-project"},
            "paper_trade": True
        }

        # Mock the logger created within PositionMonitor
        self.mock_logger = MagicMock(spec=EnhancedLogger)
        mock_create_logger.return_value = self.mock_logger

        self.position_monitor = PositionMonitor(
            config_manager=self.mock_config_manager
        )

        self.mock_trade_manager = MagicMock()
        self.position_monitor.trade_manager = self.mock_trade_manager
        self.position_monitor.market_data_fetcher = MagicMock()

    def test_initialization(self):
        """Test if the PositionMonitor initializes correctly."""
        self.assertIsNotNone(self.position_monitor)
        self.assertEqual(self.position_monitor.config_manager, self.mock_config_manager)
        self.assertIsInstance(self.position_monitor.positions, dict)

    def test_add_position(self):
        """Test adding a new position to the monitor."""
        position_id = self.position_monitor.add_position(
            symbol="TCS",
            quantity=10,
            entry_price=3000.0,
            trade_type="BUY",
            exit_strategy=ExitStrategy(stop_loss=2950.0, target=3100.0)
        )
        self.assertIsNotNone(position_id)
        
        active_positions = self.position_monitor.get_positions(status=TradeStatus.OPEN)
        self.assertEqual(len(active_positions), 1)
        self.assertEqual(active_positions[0]['symbol'], "TCS")

    @patch('runner.position_monitor.KiteTicker')
    def test_monitoring_loop_stop_loss_trigger(self, mock_kite_ticker):
        """Test if the monitoring loop correctly triggers a stop loss."""
        
        # We need a running event loop for async tests
        # Get a new event loop for this test to avoid conflicts
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Add a position to monitor
        position_id = self.position_monitor.add_position(
            symbol="RELIANCE",
            quantity=5,
            entry_price=2500.0,
            trade_type="BUY",
            instrument_token="12345", # Token is needed for tick monitoring
            exit_strategy=ExitStrategy(stop_loss=2450.0, target=2600.0)
        )
        
        # Simulate a tick that should trigger the stop loss
        test_tick = [{'instrument_token': "12345", 'last_price': 2440.0}]
        
        # Manually call the handler that the ticker would call
        loop.run_until_complete(self.position_monitor._on_ticks_handler(test_tick))

        # Check if the position was closed
        closed_positions = self.position_monitor.get_positions(status=TradeStatus.CLOSED)
        self.assertEqual(len(closed_positions), 1)
        self.assertEqual(closed_positions[0]['exit_reason'], ExitReason.STOP_LOSS_HIT)
        self.assertEqual(closed_positions[0]['exit_price'], 2440.0)

        # Verify logger was called
        self.mock_logger.log_event.assert_any_call(
            f"✅ [EXIT-SL] Stop loss triggered for RELIANCE at 2440.0",
            'INFO',
            'TRADE',
            data=unittest.mock.ANY,
        )

        loop.close()

    def test_get_open_positions(self):
        """Test retrieving all open positions."""
        self.position_monitor.add_position(
            symbol="AAPL",
            quantity=10,
            entry_price=150.0,
            trade_type="BUY",
            exit_strategy=ExitStrategy(stop_loss=145.0, target=160.0)
        )
        open_positions = self.position_monitor.get_open_positions()
        self.assertEqual(len(open_positions), 1)
        self.assertEqual(open_positions[0]['symbol'], "AAPL")

    def test_calculate_pnl(self):
        """Test P&L calculation for a position."""
        self.position_monitor.market_data_fetcher.get_ltp.return_value = 155.0

        pnl = self.position_monitor.calculate_pnl("AAPL")
        self.assertAlmostEqual(pnl, 50.0)

        self.position_monitor.market_data_fetcher.get_ltp.return_value = 148.0
        pnl = self.position_monitor.calculate_pnl("AAPL")
        self.assertAlmostEqual(pnl, -20.0)

if __name__ == '__main__':
    unittest.main() 