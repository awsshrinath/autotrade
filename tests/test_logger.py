"""
Test Script for Enhanced Logging System
Validates comprehensive logging with Firestore and GCS bucket integration
"""

import unittest
from unittest.mock import MagicMock, patch
import time
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Mock external modules before imports
from tests.test_mocks import setup_all_mocks
setup_all_mocks()

from runner.enhanced_logging.core_logger import TradingLogger, LogLevel, LogCategory, LogEntry
from runner.enhanced_logging.log_types import TradeLogData

class TestTradingLogger(unittest.TestCase):

    def setUp(self):
        """Set up a mock environment for each test."""
        # Mock the logger backends
        self.firestore_patcher = patch('runner.enhanced_logging.core_logger.FirestoreLogger')
        self.gcs_patcher = patch('runner.enhanced_logging.core_logger.GCSLogger')
        self.thread_patcher = patch('threading.Thread')
        
        self.mock_firestore_logger_class = self.firestore_patcher.start()
        self.mock_gcs_logger_class = self.gcs_patcher.start()
        self.mock_thread_class = self.thread_patcher.start()
        
        self.mock_firestore_logger = self.mock_firestore_logger_class.return_value
        self.mock_gcs_logger = self.mock_gcs_logger_class.return_value
        self.mock_thread = self.mock_thread_class.return_value
        
        # Instantiate the logger with mocked dependencies
        self.logger = TradingLogger(
            session_id="test_session",
            bot_type="test_bot",
            project_id="test-project",
            enable_firestore=True,
            enable_gcs=True
        )

    def tearDown(self):
        """Clean up after each test."""
        self.firestore_patcher.stop()
        self.gcs_patcher.stop()
        self.thread_patcher.stop()

    def test_initialization(self):
        """Test if the TradingLogger initializes correctly."""
        self.assertIsNotNone(self.logger)
        self.assertEqual(self.logger.session_id, "test_session")
        self.assertTrue(self.logger.enable_firestore)
        self.assertTrue(self.logger.enable_gcs)
        # The init log should call the system event logger
        self.logger.log_system_event.assert_called_with(
            'Trading logger initialized for test_bot', 
            {'session_id': 'test_session', 'bot_type': 'test_bot', 'firestore_enabled': True, 'gcs_enabled': True}
        )

    def test_log_system_event(self):
        """Test logging of a system event."""
        with patch.object(self.logger, '_route_log') as mock_route_log:
            self.logger.log_system_event("System started", {"component": "test"})
            
            mock_route_log.assert_called_once()
            call_args = mock_route_log.call_args[0][0]
            self.assertIsInstance(call_args, LogEntry)
            self.assertEqual(call_args.message, "System started")
            self.assertEqual(call_args.level, LogLevel.INFO)
            self.assertEqual(call_args.category, LogCategory.SYSTEM)

    def test_log_trade_entry(self):
        """Test logging of a trade entry."""
        trade_data = TradeLogData(symbol="RELIANCE", quantity=10, price=2500.0, action="BUY")
        with patch.object(self.logger, '_route_log') as mock_route_log:
            self.logger.log_trade_entry(trade_data)
            mock_route_log.assert_called_once()
            entry = mock_route_log.call_args[0][0]
            self.assertEqual(entry.category, LogCategory.TRADE)
            self.assertEqual(entry.data['symbol'], "RELIANCE")

    def test_log_error(self):
        """Test logging of an error."""
        with patch.object(self.logger, '_route_log') as mock_route_log:
            try:
                1 / 0
            except Exception as e:
                self.logger.log_error(e, context={"location": "testing"})
            
            mock_route_log.assert_called_once()
            entry = mock_route_log.call_args[0][0]
            self.assertEqual(entry.level, LogLevel.ERROR)
            self.assertEqual(entry.category, LogCategory.ERROR)
            self.assertIn("division by zero", entry.data['error_message'])
            self.assertIn("traceback", entry.data)

    def test_shutdown(self):
        """Test the shutdown method."""
        with patch.object(self.logger, 'flush_all') as mock_flush:
            self.logger.shutdown()
            mock_flush.assert_called_once()


if __name__ == '__main__':
    unittest.main() 