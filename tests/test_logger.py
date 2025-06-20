"""
Test Script for Enhanced Logging System
Validates comprehensive logging with Firestore and GCS bucket integration
"""

import time
import datetime
import json
import os
from typing import Dict, Any
import unittest
from unittest.mock import MagicMock, patch

from runner.logger import (
    EnhancedLogger, LogLevel, LogCategory, create_enhanced_logger
)


class TestLogger(unittest.TestCase):
    def setUp(self):
        # We need to patch the actual client used by the logger's dependencies
        self.mock_firestore_client = MagicMock()
        self.patcher = patch('google.cloud.firestore.Client', return_value=self.mock_firestore_client)
        self.patcher.start()
            
        self.logger = None

    def tearDown(self):
        if self.logger:
            self.logger.shutdown()
        self.patcher.stop()

    def test_initialization(self):
        self.logger = create_enhanced_logger(session_id="test_init", enable_gcs=False, enable_firestore=False)
        self.assertIsNotNone(self.logger)
        self.assertEqual(self.logger.session_id, "test_init")
        self.assertTrue(self.logger.performance_metrics['logs_written'] > 0)

    def test_log_event_levels(self):
        self.logger = create_enhanced_logger(session_id="test_levels", enable_gcs=False, enable_firestore=False)
        
        with patch.object(self.logger, '_write_to_local_file') as mock_write:
            self.logger.log_event("Debug message", LogLevel.DEBUG, LogCategory.SYSTEM)
            mock_write.assert_called()
            self.assertEqual(mock_write.call_args[0][0].level, LogLevel.DEBUG)

            self.logger.log_event("Info message", LogLevel.INFO, LogCategory.SYSTEM)
            self.assertEqual(mock_write.call_args[0][0].level, LogLevel.INFO)

            self.logger.log_event("Warning message", LogLevel.WARNING, LogCategory.SYSTEM)
            self.assertEqual(mock_write.call_args[0][0].level, LogLevel.WARNING)

            self.logger.log_event("Error message", LogLevel.ERROR, LogCategory.SYSTEM)
            self.assertEqual(mock_write.call_args[0][0].level, LogLevel.ERROR)

            self.logger.log_event("Critical message", LogLevel.CRITICAL, LogCategory.SYSTEM)
            self.assertEqual(mock_write.call_args[0][0].level, LogLevel.CRITICAL)

    def test_log_trade_execution(self):
        self.logger = create_enhanced_logger(session_id="test_trade", enable_gcs=False, enable_firestore=False)
        trade_data = {
            "trade_id": "trade123", "symbol": "RELIANCE", "order_type": "MARKET", 
            "quantity": 10, "price": 2500.0, "direction": "buy"
        }
        
        with patch.object(self.logger, '_write_to_local_file') as mock_write:
            self.logger.log_trade_execution(trade_data, success=True)
            mock_write.assert_called()
            entry = mock_write.call_args[0][0]
            self.assertEqual(entry.category, LogCategory.TRADE)
            self.assertEqual(entry.data['trade_id'], "trade123")
            self.assertTrue(entry.data['success'])

        failed_trade_data = {
            "trade_id": "trade456", "symbol": "TCS", "order_type": "LIMIT",
            "quantity": 5, "price": 3200.0, "direction": "sell", "error": "Insufficient funds"
        }
        with patch.object(self.logger, '_write_to_local_file') as mock_write:
            self.logger.log_trade_execution(failed_trade_data, success=False)
            mock_write.assert_called()
            entry = mock_write.call_args[0][0]
            self.assertFalse(entry.data['success'])
            self.assertIn('error', entry.data)

    def test_log_position_update(self):
        self.logger = create_enhanced_logger(session_id="test_position", enable_gcs=False, enable_firestore=False)
        position_data = {
            "position_id": "pos123", "symbol": "RELIANCE", "quantity": 10,
            "pnl": 150.0, "status": "open"
        }
        with patch.object(self.logger, '_write_to_local_file') as mock_write:
            self.logger.log_position_update(position_data, update_type="added")
            mock_write.assert_called()
            entry = mock_write.call_args[0][0]
            self.assertEqual(entry.category, LogCategory.POSITION)
            self.assertEqual(entry.data['update_type'], "added")

            self.logger.log_position_update(position_data, update_type="price_update")
            entry = mock_write.call_args[0][0]
            self.assertEqual(entry.data['update_type'], "price_update")
            
    def test_log_error_method(self):
        self.logger = create_enhanced_logger(session_id="test_error_method", enable_gcs=False, enable_firestore=False)
        try:
            1 / 0
        except Exception as e:
            with patch.object(self.logger, '_write_to_local_file') as mock_write:
                self.logger.log_error(e, context={"location": "test_method"})
                mock_write.assert_called()
                entry = mock_write.call_args[0][0]
                self.assertEqual(entry.level, LogLevel.ERROR)
                self.assertEqual(entry.category, LogCategory.ERROR)
                self.assertIn("ZeroDivisionError", entry.data['error_message'])
                self.assertIn("traceback", entry.data)

    def test_shutdown(self):
        self.logger = create_enhanced_logger(session_id="test_shutdown", enable_gcs=False, enable_firestore=False)
        with patch.object(self.logger, '_flush_buffers') as mock_flush:
            self.logger.shutdown()
            mock_flush.assert_called_once()
    
    def test_daily_summary_creation(self):
        self.logger = create_enhanced_logger(session_id="test_summary", enable_gcs=False, enable_firestore=False)
        # Log some events to create a summary from
        self.logger.log_trade_execution({"pnl": 100}, success=True)
        self.logger.log_trade_execution({"pnl": -50}, success=True)
        self.logger.log_error(ValueError("Test error"))

        summary = self.logger.create_daily_summary()
        self.assertIn("Daily Trading Summary", summary)
        self.assertIn("Total Trades: 2", summary)
        self.assertIn("Total PNL: 50.00", summary)
        self.assertIn("Errors Logged: 1", summary)


def main():
    """Main test function"""
    print("🚀 Enhanced Logging System Validation")
    print("Testing comprehensive logging with Firestore and GCS integration")
    print()
    
    # Check environment
    print("🔍 Environment Check:")
    print(f"GCP_PROJECT_ID: {os.getenv('GCP_PROJECT_ID', 'Not set')}")
    print(f"ENVIRONMENT: {os.getenv('ENVIRONMENT', 'prod')}")
    print()
    
    unittest.main()


if __name__ == "__main__":
    main() 