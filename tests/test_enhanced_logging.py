"""
Test Script for Enhanced Logging System
Validates comprehensive logging with Firestore and GCS bucket integration
"""

import time
import datetime
import json
import os
from typing import Dict, Any

from runner.enhanced_logger import (
    EnhancedLogger, LogLevel, LogCategory, create_enhanced_logger
)


class EnhancedLoggingTest:
    """Test suite for enhanced logging system"""
    
    def __init__(self):
        self.test_session_id = f"test_logging_{int(time.time())}"
        self.enhanced_logger = None
        
        print("Enhanced Logging System Test Suite")
        print("=" * 50)
    
    def setup(self):
        """Setup test environment"""
        print("Setting up enhanced logging test environment...")
        
        # Create enhanced logger
        self.enhanced_logger = create_enhanced_logger(
            session_id=self.test_session_id,
            enable_gcs=True,
            enable_firestore=True
        )
        
        print(f"✅ Enhanced logger initialized with session ID: {self.test_session_id}")
    
    def test_basic_logging(self):
        """Test basic logging functionality"""
        print("\n🧪 Testing Basic Logging")
        
        # Test different log levels
        self.enhanced_logger.log_event(
            "Testing DEBUG level logging",
            LogLevel.DEBUG,
            LogCategory.SYSTEM,
            data={'test_type': 'debug_test'},
            source="test_suite"
        )
        
        self.enhanced_logger.log_event(
            "Testing INFO level logging",
            LogLevel.INFO,
            LogCategory.SYSTEM,
            data={'test_type': 'info_test'},
            source="test_suite"
        )
        
        self.enhanced_logger.log_event(
            "Testing WARNING level logging",
            LogLevel.WARNING,
            LogCategory.SYSTEM,
            data={'test_type': 'warning_test'},
            source="test_suite"
        )
        
        self.enhanced_logger.log_event(
            "Testing ERROR level logging",
            LogLevel.ERROR,
            LogCategory.ERROR,
            data={'test_type': 'error_test'},
            source="test_suite"
        )
        
        print("✅ Basic logging tests completed")
    
    def test_trade_logging(self):
        """Test trade-specific logging"""
        print("\n🧪 Testing Trade Logging")
        
        # Test successful trade execution
        trade_data = {
            'id': 'TEST_TRADE_001',
            'symbol': 'RELIANCE',
            'strategy': 'test_strategy',
            'direction': 'bullish',
            'quantity': 10,
            'entry_price': 2500.0,
            'stop_loss': 2450.0,
            'target': 2600.0,
            'bot_type': 'stock',
            'paper_trade': True,
            'confidence_level': 0.8,
            'trailing_stop_enabled': True,
            'time_based_exit_minutes': 240,
            'metadata': {
                'test_trade': True,
                'test_timestamp': datetime.datetime.now().isoformat()
            }
        }
        
        self.enhanced_logger.log_trade_execution(trade_data, success=True)
        
        # Test failed trade execution
        failed_trade_data = {
            'symbol': 'TCS',
            'strategy': 'test_strategy',
            'direction': 'bearish',
            'quantity': 5,
            'entry_price': 3500.0,
            'bot_type': 'stock',
            'paper_trade': True,
            'failure_reason': 'insufficient_margin'
        }
        
        self.enhanced_logger.log_trade_execution(failed_trade_data, success=False)
        
        print("✅ Trade logging tests completed")
    
    def test_position_logging(self):
        """Test position monitoring logging"""
        print("\n🧪 Testing Position Logging")
        
        # Test position addition
        position_data = {
            'id': 'TEST_POS_001',
            'symbol': 'INFY',
            'strategy': 'momentum',
            'bot_type': 'stock',
            'direction': 'bullish',
            'quantity': 15,
            'entry_price': 1800.0,
            'stop_loss': 1750.0,
            'target': 1900.0,
            'paper_trade': True,
            'entry_time': datetime.datetime.now().isoformat()
        }
        
        self.enhanced_logger.log_position_update(position_data, update_type="added")
        
        # Test position price update
        position_data['current_price'] = 1825.0
        position_data['unrealized_pnl'] = 375.0
        self.enhanced_logger.log_position_update(position_data, update_type="price_update")
        
        # Test position exit
        exit_data = {
            'position_id': 'TEST_POS_001',
            'symbol': 'INFY',
            'strategy': 'momentum',
            'bot_type': 'stock',
            'direction': 'bullish',
            'exit_price': 1875.0,
            'exit_quantity': 15,
            'exit_reason': 'target_hit',
            'exit_percentage': 100.0,
            'pnl': 1125.0,
            'realized_pnl': 1125.0,
            'paper_trade': True,
            'entry_price': 1800.0,
            'entry_time': datetime.datetime.now().isoformat(),
            'exit_time': datetime.datetime.now().isoformat()
        }
        
        self.enhanced_logger.log_exit_execution(exit_data, success=True)
        
        print("✅ Position logging tests completed")
    
    def test_performance_logging(self):
        """Test performance metrics logging"""
        print("\n🧪 Testing Performance Logging")
        
        # Test trading performance metrics
        trading_metrics = {
            'total_trades': 25,
            'successful_trades': 18,
            'failed_trades': 7,
            'win_rate': 72.0,
            'total_pnl': 15750.0,
            'average_pnl_per_trade': 630.0,
            'max_drawdown': -2500.0,
            'sharpe_ratio': 1.85,
            'profit_factor': 2.3,
            'largest_win': 3200.0,
            'largest_loss': -1800.0,
            'average_hold_time_minutes': 145,
            'strategies_used': ['momentum', 'vwap', 'breakout'],
            'symbols_traded': ['RELIANCE', 'TCS', 'INFY', 'HDFC', 'ICICIBANK']
        }
        
        self.enhanced_logger.log_performance_metrics(
            metrics=trading_metrics,
            metric_type="daily_trading_performance"
        )
        
        # Test system performance metrics
        system_metrics = {
            'cpu_usage_percent': 45.2,
            'memory_usage_mb': 1024,
            'disk_usage_percent': 67.8,
            'network_latency_ms': 25,
            'api_calls_per_minute': 120,
            'error_rate_percent': 0.5,
            'uptime_hours': 8.5,
            'active_positions': 3,
            'monitoring_threads': 5,
            'queue_sizes': {
                'log_queue': 12,
                'exit_queue': 0,
                'signal_queue': 3
            }
        }
        
        self.enhanced_logger.log_performance_metrics(
            metrics=system_metrics,
            metric_type="system_performance"
        )
        
        print("✅ Performance logging tests completed")
    
    def test_risk_logging(self):
        """Test risk management logging"""
        print("\n🧪 Testing Risk Logging")
        
        # Test low risk event
        low_risk_data = {
            'event': 'position_size_adjustment',
            'symbol': 'RELIANCE',
            'original_quantity': 20,
            'adjusted_quantity': 15,
            'reason': 'portfolio_risk_optimization',
            'risk_score': 0.3
        }
        
        self.enhanced_logger.log_risk_event(low_risk_data, risk_level="low")
        
        # Test medium risk event
        medium_risk_data = {
            'event': 'stop_loss_triggered',
            'symbol': 'TCS',
            'position_id': 'TEST_POS_002',
            'entry_price': 3500.0,
            'exit_price': 3450.0,
            'loss_amount': -250.0,
            'loss_percentage': -1.43,
            'reason': 'price_below_stop_loss'
        }
        
        self.enhanced_logger.log_risk_event(medium_risk_data, risk_level="medium")
        
        # Test high risk event
        high_risk_data = {
            'event': 'daily_loss_limit_approached',
            'current_daily_loss': -4500.0,
            'daily_loss_limit': -5000.0,
            'remaining_buffer': -500.0,
            'open_positions': 5,
            'total_exposure': 125000.0,
            'action_taken': 'reduce_position_sizes'
        }
        
        self.enhanced_logger.log_risk_event(high_risk_data, risk_level="high")
        
        # Test critical risk event
        critical_risk_data = {
            'event': 'emergency_exit_all_positions',
            'trigger': 'system_malfunction',
            'positions_affected': 8,
            'total_exposure': 200000.0,
            'estimated_slippage': -5000.0,
            'emergency_timestamp': datetime.datetime.now().isoformat()
        }
        
        self.enhanced_logger.log_risk_event(critical_risk_data, risk_level="critical")
        
        print("✅ Risk logging tests completed")
    
    def test_strategy_logging(self):
        """Test strategy signal logging"""
        print("\n🧪 Testing Strategy Logging")
        
        # Test momentum strategy signal
        momentum_signal = {
            'signal_type': 'bullish_momentum',
            'symbol': 'RELIANCE',
            'confidence': 0.85,
            'indicators': {
                'rsi': 65.2,
                'macd': 12.5,
                'volume_ratio': 1.8,
                'price_change_percent': 2.3
            },
            'entry_price': 2525.0,
            'stop_loss': 2475.0,
            'target': 2625.0,
            'risk_reward_ratio': 2.0,
            'timeframe': '15min'
        }
        
        self.enhanced_logger.log_strategy_signal(momentum_signal, "momentum")
        
        # Test VWAP strategy signal
        vwap_signal = {
            'signal_type': 'vwap_breakout',
            'symbol': 'TCS',
            'confidence': 0.72,
            'indicators': {
                'price_vs_vwap': 1.02,
                'volume_profile': 'above_average',
                'trend_strength': 0.78
            },
            'entry_price': 3520.0,
            'stop_loss': 3480.0,
            'target': 3600.0,
            'timeframe': '5min'
        }
        
        self.enhanced_logger.log_strategy_signal(vwap_signal, "vwap")
        
        print("✅ Strategy logging tests completed")
    
    def test_error_logging(self):
        """Test error logging"""
        print("\n🧪 Testing Error Logging")
        
        # Test various error types
        try:
            # Simulate a division by zero error
            result = 10 / 0
        except ZeroDivisionError as e:
            self.enhanced_logger.log_error(
                error=e,
                context={
                    'operation': 'test_calculation',
                    'inputs': {'numerator': 10, 'denominator': 0},
                    'expected_result': 'numeric_value'
                },
                source="test_suite"
            )
        
        try:
            # Simulate a key error
            test_dict = {'a': 1, 'b': 2}
            value = test_dict['c']
        except KeyError as e:
            self.enhanced_logger.log_error(
                error=e,
                context={
                    'operation': 'dictionary_access',
                    'available_keys': list(test_dict.keys()),
                    'requested_key': 'c'
                },
                source="test_suite"
            )
        
        try:
            # Simulate a type error
            result = "string" + 123
        except TypeError as e:
            self.enhanced_logger.log_error(
                error=e,
                context={
                    'operation': 'string_concatenation',
                    'operand_types': ['str', 'int']
                },
                source="test_suite"
            )
        
        print("✅ Error logging tests completed")
    
    def test_system_health_logging(self):
        """Test system health logging"""
        print("\n🧪 Testing System Health Logging")
        
        # Test healthy system status
        healthy_status = {
            'status': 'healthy',
            'components': {
                'database': 'connected',
                'api_server': 'running',
                'message_queue': 'active',
                'cache': 'available',
                'external_apis': 'responsive'
            },
            'performance': {
                'response_time_ms': 45,
                'throughput_rps': 150,
                'error_rate': 0.001,
                'cpu_usage': 35.2,
                'memory_usage': 68.5
            },
            'last_check': datetime.datetime.now().isoformat()
        }
        
        self.enhanced_logger.log_system_health(healthy_status)
        
        # Test degraded system status
        degraded_status = {
            'status': 'degraded',
            'components': {
                'database': 'connected',
                'api_server': 'running',
                'message_queue': 'slow',
                'cache': 'available',
                'external_apis': 'timeout_issues'
            },
            'performance': {
                'response_time_ms': 250,
                'throughput_rps': 75,
                'error_rate': 0.05,
                'cpu_usage': 85.7,
                'memory_usage': 92.1
            },
            'issues': [
                'High CPU usage detected',
                'External API timeouts increasing',
                'Message queue processing delays'
            ],
            'last_check': datetime.datetime.now().isoformat()
        }
        
        self.enhanced_logger.log_system_health(degraded_status)
        
        print("✅ System health logging tests completed")
    
    def test_batch_logging(self):
        """Test batch logging performance"""
        print("\n🧪 Testing Batch Logging Performance")
        
        start_time = time.time()
        
        # Generate a batch of log entries
        for i in range(100):
            self.enhanced_logger.log_event(
                f"Batch log entry {i+1}",
                LogLevel.INFO,
                LogCategory.SYSTEM,
                data={
                    'batch_number': i+1,
                    'timestamp': datetime.datetime.now().isoformat(),
                    'test_data': f"test_value_{i}"
                },
                source="batch_test"
            )
        
        # Force flush to measure performance
        self.enhanced_logger._flush_buffers()
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"✅ Batch logging completed: 100 entries in {duration:.2f} seconds")
        print(f"   Average: {(duration/100)*1000:.2f} ms per log entry")
    
    def test_logger_performance_metrics(self):
        """Test logger's own performance metrics"""
        print("\n🧪 Testing Logger Performance Metrics")
        
        # Get performance metrics
        metrics = self.enhanced_logger.get_performance_metrics()
        
        print("📊 Logger Performance Metrics:")
        print(f"   Logs written: {metrics['logs_written']}")
        print(f"   Firestore writes: {metrics['firestore_writes']}")
        print(f"   GCS uploads: {metrics['gcs_uploads']}")
        print(f"   Errors: {metrics['errors']}")
        print(f"   Runtime: {metrics['runtime_seconds']:.2f} seconds")
        print(f"   Logs per second: {metrics['logs_per_second']:.2f}")
        print(f"   Error rate: {metrics['error_rate']:.4f}")
        print(f"   Queue size: {metrics['queue_size']}")
        print(f"   Buffer size: {metrics['buffer_size']}")
        
        print("✅ Performance metrics test completed")
    
    def test_daily_summary(self):
        """Test daily summary creation"""
        print("\n🧪 Testing Daily Summary Creation")
        
        # Create daily summary
        summary = self.enhanced_logger.create_daily_summary()
        
        print("📋 Daily Summary Created:")
        print(f"   Date: {summary.get('date')}")
        print(f"   Session ID: {summary.get('session_id')}")
        print(f"   GCS Enabled: {summary.get('gcs_enabled')}")
        print(f"   Firestore Enabled: {summary.get('firestore_enabled')}")
        
        file_sizes = summary.get('file_sizes', {})
        print("   Log File Sizes:")
        for log_type, size in file_sizes.items():
            print(f"     {log_type}: {size} bytes")
        
        print("✅ Daily summary test completed")
    
    def cleanup(self):
        """Cleanup test environment"""
        print("\n🧹 Cleaning up test environment...")
        
        if self.enhanced_logger:
            # Create final test summary
            final_summary = self.enhanced_logger.create_daily_summary()
            
            # Log test completion
            self.enhanced_logger.log_event(
                "Enhanced logging test suite completed",
                LogLevel.INFO,
                LogCategory.SYSTEM,
                data={
                    'test_session_id': self.test_session_id,
                    'test_completion_time': datetime.datetime.now().isoformat(),
                    'final_summary': final_summary
                },
                source="test_suite"
            )
            
            # Graceful shutdown
            self.enhanced_logger.shutdown()
        
        print("✅ Cleanup complete")
    
    def run_all_tests(self):
        """Run all test cases"""
        try:
            # Setup
            self.setup()
            
            # Run test cases
            self.test_basic_logging()
            self.test_trade_logging()
            self.test_position_logging()
            self.test_performance_logging()
            self.test_risk_logging()
            self.test_strategy_logging()
            self.test_error_logging()
            self.test_system_health_logging()
            self.test_batch_logging()
            self.test_logger_performance_metrics()
            self.test_daily_summary()
            
            # Wait for background processing
            print("\n⏳ Waiting for background processing...")
            time.sleep(10)
            
            print("\n🎯 All Enhanced Logging Tests Completed Successfully!")
            print("=" * 50)
            
            # Display final metrics
            final_metrics = self.enhanced_logger.get_performance_metrics()
            print("\n📊 Final Test Session Metrics:")
            print(f"Total logs written: {final_metrics['logs_written']}")
            print(f"Firestore writes: {final_metrics['firestore_writes']}")
            print(f"GCS uploads: {final_metrics['gcs_uploads']}")
            print(f"Error count: {final_metrics['errors']}")
            print(f"Session duration: {final_metrics['runtime_seconds']:.2f} seconds")
            print(f"Average logs per second: {final_metrics['logs_per_second']:.2f}")
            
            # Check log files
            print("\n📁 Generated Log Files:")
            log_folder = f"logs/{datetime.datetime.now().strftime('%Y-%m-%d')}"
            if os.path.exists(log_folder):
                for file in os.listdir(log_folder):
                    if file.endswith('.jsonl') or file.endswith('.log'):
                        file_path = os.path.join(log_folder, file)
                        file_size = os.path.getsize(file_path)
                        print(f"  {file}: {file_size} bytes")
            
        except Exception as e:
            print(f"❌ Test suite failed with error: {e}")
            if self.enhanced_logger:
                self.enhanced_logger.log_error(
                    error=e,
                    context={'operation': 'test_suite_execution'},
                    source="test_suite"
                )
        finally:
            self.cleanup()


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
    
    test_suite = EnhancedLoggingTest()
    test_suite.run_all_tests()


if __name__ == "__main__":
    main() 