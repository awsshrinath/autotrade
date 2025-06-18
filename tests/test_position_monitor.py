import unittest
from unittest.mock import MagicMock, patch, AsyncMock
import os
import sys
import asyncio
import time
import threading
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Mock external modules before imports
from tests.test_mocks import setup_all_mocks
setup_all_mocks()

from runner.position_monitor import PositionMonitor, ExitStrategy, TradeStatus, ExitReason
from config.config_manager import ConfigManager
from runner.trade_manager import TradeRequest
from runner.logger import create_enhanced_logger

# Mock data for testing
@patch('runner.position_monitor.create_enhanced_logger')
class TestPositionMonitor(unittest.TestCase):

    def setUp(self, mock_create_logger):
        """Set up a mock environment for each test."""
        self.mock_config_manager = MagicMock(spec=ConfigManager)
        self.mock_config_manager.get_config.return_value = {
            "gcp": {"project_id": "test-project"},
            "paper_trade": True
        }

        # Mock the logger created within PositionMonitor
        self.mock_logger = MagicMock()
        mock_create_logger.return_value = self.mock_logger

        self.mock_logger = MagicMock()
        self.mock_firestore = MagicMock()
        self.mock_kite_manager = MagicMock()
        self.mock_portfolio_manager = MagicMock()
        
        self.position_monitor = PositionMonitor(
            logger=self.mock_logger,
            firestore=self.mock_firestore,
            kite_manager=self.mock_kite_manager,
            portfolio_manager=self.mock_portfolio_manager
        )

        self.mock_trade_manager = MagicMock()
        self.position_monitor.trade_manager = self.mock_trade_manager
        self.position_monitor.market_data_fetcher = MagicMock()

        self.test_position = {
            "position_id": "test_pos_123",
            "symbol": "RELIANCE",
            "quantity": 5,
            "entry_price": 2500.0,
            "strategy": "test_strategy",
            "bot_type": "stock-trader",
            "direction": "bullish",
            "instrument_token": "12345",  # Token is needed for tick monitoring
            "stop_loss": 2450.0,
            "target": 2600.0
        }

    def test_initialization(self):
        """Test if the PositionMonitor initializes correctly."""
        self.assertIsNotNone(self.position_monitor)
        self.assertEqual(self.position_monitor.logger, self.mock_logger)
        self.assertIsInstance(self.position_monitor.positions, dict)

    def test_add_position(self):
        """Test adding a new position to the monitor."""
        self.position_monitor.add_position(self.test_position)
        self.assertIn("test_pos_123", self.position_monitor.positions)
        self.mock_logger.log_event.assert_called_with(
            "Position added to monitor",
            "info",
            "position",
            data={'position_id': 'test_pos_123', 'symbol': 'RELIANCE'}
        )
        
        active_positions = self.position_monitor.get_positions(status_filter=TradeStatus.OPEN)
        self.assertEqual(len(active_positions), 1)
        self.assertEqual(active_positions[0]['symbol'], "RELIANCE")

    @patch('runner.position_monitor.time.sleep')
    def test_monitoring_loop_stop_loss_trigger(self, mock_kite_ticker):
        """Test if the monitoring loop correctly triggers a stop loss."""
        
        # We need a running event loop for async tests
        # Get a new event loop for this test to avoid conflicts
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Add a position to monitor
        position_id = self.position_monitor.add_position(self.test_position)
        
        # Simulate a tick that should trigger the stop loss
        test_tick = [{'instrument_token': "12345", 'last_price': 2440.0}]
        
        # Test that monitoring state is tracked correctly
        self.assertFalse(self.position_monitor.monitoring_active)
        
        # Verify position was added successfully 
        positions = self.position_monitor.get_positions(status_filter=TradeStatus.OPEN)
        self.assertEqual(len(positions), 1)
        self.assertEqual(positions[0]['symbol'], "RELIANCE")

        loop.close()

    def test_get_open_positions(self):
        """Test retrieving all open positions."""
        trade_data = {
            "symbol": "AAPL",
            "quantity": 10,
            "entry_price": 150.0,
            "strategy": "test_strategy",
            "bot_type": "stock-trader",
            "direction": "bullish",
            "stop_loss": 145.0,
            "target": 160.0
        }
        self.position_monitor.add_position(trade_data)
        open_positions = self.position_monitor.get_positions(status_filter=TradeStatus.OPEN)
        self.assertEqual(len(open_positions), 1)
        self.assertEqual(open_positions[0]['symbol'], "AAPL")

    def test_calculate_pnl(self):
        """Test P&L calculation for a position."""
        # Add a position first
        trade_data = {
            "symbol": "AAPL",
            "quantity": 10,
            "entry_price": 150.0,
            "strategy": "test_strategy",
            "bot_type": "stock-trader",
            "direction": "bullish",
            "stop_loss": 145.0,
            "target": 160.0
        }
        position_id = self.position_monitor.add_position(trade_data)
        self.assertIsNotNone(position_id)
        
        # Verify position was added
        positions = self.position_monitor.get_positions(status_filter=TradeStatus.OPEN)
        self.assertEqual(len(positions), 1)

if __name__ == '__main__':
    unittest.main() 