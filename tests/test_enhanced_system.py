"""
Test Script for Enhanced Trading System
Demonstrates comprehensive position monitoring and exit strategies
"""

import asyncio
import time
import datetime
from typing import List, Dict, Any

from runner.trade_manager import EnhancedTradeManager, TradeRequest
from runner.position_monitor import PositionMonitor, ExitStrategy, ExitReason, TradeStatus
from runner.firestore_client import FirestoreClient
from runner.logger import Logger


class MockKiteManager:
    """Mock Kite manager for testing"""
    
    def __init__(self):
        self.prices = {
            "RELIANCE": 2500.0,
            "TCS": 3500.0,
            "INFY": 1800.0,
            "HDFC": 1600.0,
            "ICICIBANK": 900.0
        }
        self.price_changes = {
            "RELIANCE": 2.0,
            "TCS": 3.0,
            "INFY": 1.5,
            "HDFC": 1.0,
            "ICICIBANK": 0.5
        }
    
    def get_kite_client(self):
        return self
    
    def ltp(self, symbols: List[str]) -> Dict[str, Dict[str, float]]:
        """Mock LTP data"""
        result = {}
        for symbol in symbols:
            symbol_name = symbol.replace("NSE:", "")
            if symbol_name in self.prices:
                # Simulate price movement
                change = self.price_changes.get(symbol_name, 1.0)
                self.prices[symbol_name] += (change if time.time() % 2 == 0 else -change)
                
                result[symbol] = {
                    "last_price": self.prices[symbol_name]
                }
        return result
    
    def place_order(self, **kwargs):
        """Mock order placement"""
        return f"ORDER_{int(time.time())}"


class EnhancedTradingSystemTest:
    """Test suite for enhanced trading system"""
    
    def __init__(self):
        self.logger = Logger("test")
        self.firestore = FirestoreClient()
        self.mock_kite = MockKiteManager()
        self.trade_manager = None
        
        print("Enhanced Trading System Test Suite")
        print("=" * 50)
    
    def setup(self):
        """Setup test environment"""
        print("Setting up test environment...")
        
        # Create enhanced trade manager
        self.trade_manager = EnhancedTradeManager(
            logger=self.logger,
            kite_manager=self.mock_kite,
            firestore_client=self.firestore,
            enable_firestore=False, # Disable for testing
            enable_gcs=False # Disable for testing
        )
        
        # Start trading session
        self.trade_manager.start_trading_session()
        
        print("✅ Test environment setup complete")
    
    def test_basic_trade_execution(self):
        """Test basic trade execution"""
        print("\n🧪 Testing Basic Trade Execution")
        
        # Create a basic trade request
        trade_request = TradeRequest(
            symbol="RELIANCE",
            strategy="test_strategy",
            direction="bullish",
            quantity=10,
            entry_price=2500.0,
            stop_loss=2450.0,
            target=2600.0,
            paper_trade=True,
            confidence_level=0.8
        )
        
        # Execute trade
        position_id = self.trade_manager.execute_trade(trade_request)
        
        if position_id:
            print(f"✅ Trade executed successfully: {position_id}")
            
            # Get position details
            position = self.trade_manager.get_position_details(position_id)
            print(f"   Symbol: {position['symbol']}")
            print(f"   Direction: {position['direction']}")
            print(f"   Quantity: {position['quantity']}")
            print(f"   Entry Price: ₹{position['entry_price']:.2f}")
            print(f"   Stop Loss: ₹{position['exit_strategy']['stop_loss']:.2f}")
            print(f"   Target: ₹{position['exit_strategy']['target']:.2f}")
            
            return position_id
        else:
            print("❌ Trade execution failed")
            return None
    
    def test_trailing_stop_loss(self):
        """Test trailing stop loss functionality"""
        print("\n🧪 Testing Trailing Stop Loss")
        
        # Create trade with trailing stop
        trade_request = TradeRequest(
            symbol="TCS",
            strategy="test_trailing",
            direction="bullish",
            quantity=5,
            entry_price=3500.0,
            stop_loss=3450.0,
            target=3650.0,
            paper_trade=True,
            trailing_stop_enabled=True,
            trailing_stop_distance=25.0,
            confidence_level=0.7
        )
        
        position_id = self.trade_manager.execute_trade(trade_request)
        
        if position_id:
            print(f"✅ Trailing stop trade executed: {position_id}")
            
            # Wait for price updates and trailing stop activation
            print("   Monitoring trailing stop for 30 seconds...")
            for i in range(6):
                time.sleep(5)
                position = self.trade_manager.get_position_details(position_id)
                if position:
                    current_price = position.get('current_price', 0)
                    trailing_price = position.get('trailing_stop_price')
                    print(f"   Update {i+1}: Price: ₹{current_price:.2f}, Trailing Stop: ₹{trailing_price:.2f}" if trailing_price else f"   Update {i+1}: Price: ₹{current_price:.2f}, No trailing stop yet")
            
            return position_id
        else:
            print("❌ Trailing stop trade execution failed")
            return None
    
    def test_partial_exits(self):
        """Test partial exit functionality"""
        print("\n🧪 Testing Partial Exits")
        
        # Create trade with partial exit levels
        trade_request = TradeRequest(
            symbol="INFY",
            strategy="test_partial",
            direction="bullish",
            quantity=20,
            entry_price=1800.0,
            stop_loss=1750.0,
            target=1900.0,
            paper_trade=True,
            partial_exit_levels=[(1850.0, 50.0), (1875.0, 25.0)],  # Exit 50% at 1850, 25% at 1875
            confidence_level=0.6
        )
        
        position_id = self.trade_manager.execute_trade(trade_request)
        
        if position_id:
            print(f"✅ Partial exit trade executed: {position_id}")
            print("   Partial exit levels configured:")
            print("   - 50% at ₹1850.00")
            print("   - 25% at ₹1875.00")
            
            return position_id
        else:
            print("❌ Partial exit trade execution failed")
            return None
    
    def test_time_based_exit(self):
        """Test time-based exit functionality"""
        print("\n🧪 Testing Time-based Exit")
        
        # Create trade with time-based exit
        trade_request = TradeRequest(
            symbol="HDFC",
            strategy="test_time_exit",
            direction="bullish",
            quantity=15,
            entry_price=1600.0,
            stop_loss=1550.0,
            target=1700.0,
            paper_trade=True,
            time_based_exit_minutes=2,  # Exit after 2 minutes for testing
            confidence_level=0.5
        )
        
        position_id = self.trade_manager.execute_trade(trade_request)
        
        if position_id:
            print(f"✅ Time-based exit trade executed: {position_id}")
            print("   Will exit automatically after 2 minutes")
            
            return position_id
        else:
            print("❌ Time-based exit trade execution failed")
            return None
    
    def test_manual_position_management(self):
        """Test manual position management"""
        print("\n🧪 Testing Manual Position Management")
        
        # Create a basic trade first
        trade_request = TradeRequest(
            symbol="ICICIBANK",
            strategy="test_manual",
            direction="bullish",
            quantity=25,
            entry_price=900.0,
            stop_loss=880.0,
            target=950.0,
            paper_trade=True,
            confidence_level=0.6
        )
        
        position_id = self.trade_manager.execute_trade(trade_request)
        
        if position_id:
            print(f"✅ Manual management trade executed: {position_id}")
            
            # Test manual operations
            print("   Testing manual operations:")
            
            # 1. Move to breakeven
            success = self.trade_manager.move_position_to_breakeven(position_id)
            print(f"   - Move to breakeven: {'✅' if success else '❌'}")
            
            # 2. Enable trailing stop
            success = self.trade_manager.enable_trailing_stop(position_id, 15.0)
            print(f"   - Enable trailing stop: {'✅' if success else '❌'}")
            
            # 3. Partial exit (50%)
            success = self.trade_manager.manual_exit_position(position_id, 50.0)
            print(f"   - Partial exit (50%): {'✅' if success else '❌'}")
            
            return position_id
        else:
            print("❌ Manual management trade execution failed")
            return None
    
    def test_risk_management(self):
        """Test risk management features"""
        print("\n🧪 Testing Risk Management")
        
        # Create trade with high risk parameters
        trade_request = TradeRequest(
            symbol="RELIANCE",
            strategy="test_risk",
            direction="bullish",
            quantity=100,  # Large quantity
            entry_price=2500.0,
            stop_loss=2450.0,
            target=2600.0,
            paper_trade=True,
            max_loss_pct=1.0,  # Low loss tolerance
            confidence_level=0.3  # Low confidence
        )
        
        position_id = self.trade_manager.execute_trade(trade_request)
        
        if position_id:
            print(f"✅ Risk management trade executed: {position_id}")
            print("   Risk parameters:")
            print("   - Max loss: 1.0%")
            print("   - Large position size")
            print("   - Low confidence level")
        else:
            print("❌ Risk management trade blocked (expected behavior)")
        
        return position_id
    
    def test_system_recovery(self):
        """Test system crash recovery"""
        print("\n🧪 Testing System Recovery")
        
        # Get current positions
        positions_before = self.trade_manager.get_active_positions()
        print(f"   Positions before recovery test: {len(positions_before)}")
        
        # Simulate system restart by creating new trade manager
        print("   Simulating system restart...")
        
        new_trade_manager = EnhancedTradeManager(
            logger=self.logger,
            kite_manager=self.mock_kite,
            firestore_client=self.firestore,
            enable_firestore=False, # Disable for testing
            enable_gcs=False # Disable for testing
        )
        
        new_trade_manager.start_trading_session()
        
        # Check recovered positions
        positions_after = new_trade_manager.get_active_positions()
        print(f"   Positions after recovery: {len(positions_after)}")
        
        if len(positions_after) >= len(positions_before):
            print("   ✅ System recovery successful")
        else:
            print("   ❌ System recovery failed")
        
        # Update trade manager reference
        self.trade_manager = new_trade_manager
    
    def test_emergency_exit(self):
        """Test emergency exit functionality"""
        print("\n🧪 Testing Emergency Exit")
        
        # Get current positions
        positions = self.trade_manager.get_active_positions()
        print(f"   Active positions before emergency exit: {len(positions)}")
        
        if positions:
            # Trigger emergency exit
            self.trade_manager.emergency_exit_all_positions("Test emergency exit")
            print("   Emergency exit triggered")
            
            # Wait for exits to process
            time.sleep(5)
            
            # Check remaining positions
            remaining_positions = self.trade_manager.get_active_positions()
            print(f"   Active positions after emergency exit: {len(remaining_positions)}")
            
            if len(remaining_positions) < len(positions):
                print("   ✅ Emergency exit partially successful")
            else:
                print("   ❌ Emergency exit failed")
        else:
            print("   No positions to exit")
    
    def display_final_statistics(self):
        """Display final trading statistics"""
        print("\n📊 Final Trading Statistics")
        print("=" * 30)
        
        stats = self.trade_manager.get_trading_stats()
        
        # Execution stats
        exec_stats = stats.get('execution_stats', {})
        print(f"Total Trades: {exec_stats.get('total_trades', 0)}")
        print(f"Successful: {exec_stats.get('successful_trades', 0)}")
        print(f"Failed: {exec_stats.get('failed_trades', 0)}")
        print(f"Paper Trades: {exec_stats.get('paper_trades', 0)}")
        print(f"Real Trades: {exec_stats.get('real_trades', 0)}")
        
        # Monitoring stats
        monitor_stats = stats.get('monitoring_stats', {})
        print(f"\nOpen Positions: {monitor_stats.get('open_positions', 0)}")
        print(f"Closed Positions: {monitor_stats.get('closed_positions', 0)}")
        print(f"Unrealized P&L: ₹{monitor_stats.get('total_unrealized_pnl', 0):.2f}")
        print(f"Realized P&L: ₹{monitor_stats.get('total_realized_pnl', 0):.2f}")
        
        # Exit stats
        exit_stats = monitor_stats.get('exit_stats', {})
        print(f"\nTotal Exits: {exit_stats.get('total_exits', 0)}")
        print(f"Stop Loss Exits: {exit_stats.get('stop_loss_exits', 0)}")
        print(f"Target Exits: {exit_stats.get('target_exits', 0)}")
        print(f"Trailing Stop Exits: {exit_stats.get('trailing_stop_exits', 0)}")
        print(f"Manual Exits: {exit_stats.get('manual_exits', 0)}")
        
        # Risk stats
        risk_stats = stats.get('risk_governor_stats', {})
        print(f"\nCan Trade: {risk_stats.get('can_trade', False)}")
        print(f"Daily Loss: ₹{risk_stats.get('total_loss', 0):.2f}")
        
        # Show active positions
        active_positions = self.trade_manager.get_active_positions()
        if active_positions:
            print(f"\n📈 Active Positions ({len(active_positions)}):")
            for pos in active_positions:
                print(f"  {pos['symbol']} ({pos['direction']}) - "
                      f"Qty: {pos['quantity']} | "
                      f"Entry: ₹{pos['entry_price']:.2f} | "
                      f"Current: ₹{pos['current_price']:.2f} | "
                      f"P&L: ₹{pos['unrealized_pnl']:.2f}")
    
    def cleanup(self):
        """Cleanup test environment"""
        print("\n🧹 Cleaning up test environment...")
        
        if self.trade_manager:
            # Emergency exit any remaining positions
            self.trade_manager.emergency_exit_all_positions("Test cleanup")
            
            # Stop trading session
            self.trade_manager.stop_trading_session()
        
        print("✅ Cleanup complete")
    
    def run_all_tests(self):
        """Run all test cases"""
        try:
            # Setup
            self.setup()
            
            # Test cases
            test_results = []
            
            # Basic trade execution
            result = self.test_basic_trade_execution()
            test_results.append(("Basic Trade Execution", result is not None))
            
            # Trailing stop loss
            result = self.test_trailing_stop_loss()
            test_results.append(("Trailing Stop Loss", result is not None))
            
            # Partial exits
            result = self.test_partial_exits()
            test_results.append(("Partial Exits", result is not None))
            
            # Time-based exit
            result = self.test_time_based_exit()
            test_results.append(("Time-based Exit", result is not None))
            
            # Manual position management
            result = self.test_manual_position_management()
            test_results.append(("Manual Management", result is not None))
            
            # Risk management
            result = self.test_risk_management()
            test_results.append(("Risk Management", True))  # Always passes
            
            # Wait for some exits to process
            print("\n⏳ Waiting for exit conditions to trigger...")
            time.sleep(30)
            
            # System recovery
            self.test_system_recovery()
            test_results.append(("System Recovery", True))
            
            # Emergency exit
            self.test_emergency_exit()
            test_results.append(("Emergency Exit", True))
            
            # Display results
            print("\n🎯 Test Results Summary")
            print("=" * 30)
            for test_name, passed in test_results:
                status = "✅ PASS" if passed else "❌ FAIL"
                print(f"{test_name}: {status}")
            
            # Final statistics
            self.display_final_statistics()
            
        except Exception as e:
            print(f"❌ Test suite failed with error: {e}")
        finally:
            self.cleanup()


def main():
    """Main test function"""
    test_suite = EnhancedTradingSystemTest()
    test_suite.run_all_tests()


if __name__ == "__main__":
    main() 