"""
Enhanced Main Trading System
Uses EnhancedTradeManager with comprehensive position monitoring and exit strategies
"""

import datetime
import time
import signal
import sys
import os
from typing import Optional

from runner.enhanced_trade_manager import EnhancedTradeManager, TradeRequest, create_enhanced_trade_manager
from runner.firestore_client import FirestoreClient
from runner.kiteconnect_manager import KiteConnectManager
from runner.logger import Logger
from runner.enhanced_logger import EnhancedLogger, LogLevel, LogCategory, create_enhanced_logger
from runner.market_data_fetcher import MarketDataFetcher
from runner.gpt_self_improvement_monitor import GPTSelfImprovementMonitor
from runner.openai_manager import OpenAIManager
from config.config_manager import get_trading_config


class EnhancedTradingSystem:
    """Enhanced trading system with comprehensive position management"""
    
    def __init__(self):
        self.config = get_trading_config()
        self.logger = None
        self.enhanced_logger = None
        self.trade_manager = None
        self.firestore_client = None
        self.kite_manager = None
        self.market_data_fetcher = None
        self.monitor = None
        self.running = False
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def initialize(self):
        """Initialize all system components"""
        try:
            # Initialize enhanced logger first
            today_date = datetime.datetime.now().strftime("%Y-%m-%d")
            session_id = f"enhanced_trading_system_{int(time.time())}"
            
            self.enhanced_logger = create_enhanced_logger(
                session_id=session_id,
                enable_gcs=True,
                enable_firestore=True
            )
            
            # Initialize legacy logger for backward compatibility
            self.logger = Logger(today_date)
            
            self.enhanced_logger.log_event(
                "Enhanced Trading System initialization started",
                LogLevel.INFO,
                LogCategory.SYSTEM,
                data={
                    'session_id': session_id,
                    'date': today_date,
                    'config': {
                        'paper_trade': self.config.paper_trade if self.config else True,
                        'max_daily_loss': self.config.max_daily_loss if self.config else 0,
                        'default_capital': self.config.default_capital if self.config else 0
                    }
                },
                source="main_system"
            )
            
            self.logger.log_event("Enhanced Trading System starting...")
            
            # Initialize Firestore
            self.firestore_client = FirestoreClient()
            self.enhanced_logger.log_event(
                "Firestore client initialized",
                LogLevel.INFO,
                LogCategory.SYSTEM,
                source="main_system"
            )
            self.logger.log_event("Firestore client initialized")
            
            # Initialize Kite Connect
            self.kite_manager = KiteConnectManager(self.logger)
            if not self.config.paper_trade:
                if not self.kite_manager.initialize():
                    self.enhanced_logger.log_event(
                        "Failed to initialize Kite Connect - switching to paper trade mode",
                        LogLevel.WARNING,
                        LogCategory.SYSTEM,
                        data={
                            'original_mode': 'live_trading',
                            'fallback_mode': 'paper_trading',
                            'reason': 'kite_initialization_failed'
                        },
                        source="main_system"
                    )
                    self.logger.log_event("Failed to initialize Kite Connect - switching to paper trade mode")
                    self.config.paper_trade = True
                else:
                    self.enhanced_logger.log_event(
                        "Kite Connect initialized successfully for live trading",
                        LogLevel.INFO,
                        LogCategory.SYSTEM,
                        data={'trading_mode': 'live'},
                        source="main_system"
                    )
                    self.logger.log_event("Kite Connect initialized successfully")
            else:
                self.enhanced_logger.log_event(
                    "Running in paper trade mode",
                    LogLevel.INFO,
                    LogCategory.SYSTEM,
                    data={'trading_mode': 'paper'},
                    source="main_system"
                )
                self.logger.log_event("Running in paper trade mode")
            
            # Initialize market data fetcher
            self.market_data_fetcher = MarketDataFetcher(
                kite_manager=self.kite_manager,
                logger=self.logger
            )
            
            # Initialize enhanced trade manager
            self.trade_manager = create_enhanced_trade_manager(
                logger=self.logger,
                kite_manager=self.kite_manager,
                firestore_client=self.firestore_client
            )
            
            # Initialize monitoring system
            openai_manager = OpenAIManager()
            self.monitor = GPTSelfImprovementMonitor(
                self.logger, 
                self.firestore_client, 
                openai_manager
            )
            
            self.enhanced_logger.log_event(
                "All system components initialized successfully",
                LogLevel.INFO,
                LogCategory.SYSTEM,
                data={
                    'components': {
                        'firestore_client': True,
                        'kite_manager': self.kite_manager is not None,
                        'market_data_fetcher': True,
                        'trade_manager': True,
                        'monitor': True
                    },
                    'trading_mode': 'paper' if self.config.paper_trade else 'live'
                },
                source="main_system"
            )
            
            self.logger.log_event("All system components initialized successfully")
            return True
            
        except Exception as e:
            if self.enhanced_logger:
                self.enhanced_logger.log_error(
                    error=e,
                    context={'operation': 'system_initialization'},
                    source="main_system"
                )
            
            if self.logger:
                self.logger.log_event(f"Failed to initialize system: {e}")
            else:
                print(f"Failed to initialize system: {e}")
            return False
    
    def wait_for_market_open(self):
        """Wait for market to open"""
        now = datetime.datetime.now()
        market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
        
        if now < market_open:
            wait_seconds = (market_open - now).total_seconds()
            self.logger.log_event(f"Waiting for market open at 9:15 AM... ({wait_seconds:.0f} seconds)")
            time.sleep(wait_seconds)
        
        self.logger.log_event("Market is now open - starting trading session")
    
    def start_trading_session(self):
        """Start the main trading session"""
        try:
            self.running = True
            
            # Start the trading session
            self.trade_manager.start_trading_session()
            
            # Load existing positions from recovery
            positions = self.trade_manager.get_active_positions()
            if positions:
                self.enhanced_logger.log_event(
                    f"Recovered {len(positions)} active positions from previous session",
                    LogLevel.INFO,
                    LogCategory.RECOVERY,
                    data={
                        'recovered_positions_count': len(positions),
                        'positions': [
                            {
                                'id': pos['id'],
                                'symbol': pos['symbol'],
                                'direction': pos['direction'],
                                'quantity': pos['quantity'],
                                'entry_price': pos['entry_price'],
                                'unrealized_pnl': pos['unrealized_pnl']
                            } for pos in positions
                        ]
                    },
                    source="main_system"
                )
                
                self.logger.log_event(f"Recovered {len(positions)} active positions from previous session")
                for pos in positions:
                    self.logger.log_event(
                        f"Active position: {pos['symbol']} ({pos['direction']}) "
                        f"Qty: {pos['quantity']} Entry: ₹{pos['entry_price']:.2f} "
                        f"Current P&L: ₹{pos['unrealized_pnl']:.2f}"
                    )
            
            self.enhanced_logger.log_event(
                "Trading session started successfully",
                LogLevel.INFO,
                LogCategory.SYSTEM,
                data={
                    'session_start_time': datetime.datetime.now().isoformat(),
                    'recovered_positions': len(positions) if positions else 0
                },
                source="main_system"
            )
            
            self.logger.log_event("Trading session started successfully")
            
        except Exception as e:
            self.enhanced_logger.log_error(
                error=e,
                context={'operation': 'start_trading_session'},
                source="main_system"
            )
            
            self.logger.log_event(f"Error starting trading session: {e}")
            self.running = False
    
    def run_trading_loop(self, strategy_name: str = "vwap"):
        """Main trading loop"""
        try:
            loop_count = 0
            last_stats_time = datetime.datetime.now()
            
            while self.running:
                loop_count += 1
                loop_start = datetime.datetime.now()
                
                try:
                    # Check if market is still open
                    if not self._is_market_open():
                        self.logger.log_event("Market closed - stopping trading loop")
                        break
                    
                    # Run strategy for different bot types
                    bot_types = ["stock", "options", "futures"]
                    directions = ["bullish", "bearish"]
                    
                    for bot_type in bot_types:
                        for direction in directions:
                            if not self.running:
                                break
                            
                            try:
                                # Run strategy once
                                position_id = self.trade_manager.run_strategy_once(
                                    strategy_name=strategy_name,
                                    direction=direction,
                                    bot_type=bot_type
                                )
                                
                                if position_id:
                                    self.logger.log_event(
                                        f"New position created: {position_id} "
                                        f"({bot_type} - {direction})"
                                    )
                                
                            except Exception as e:
                                self.logger.log_event(
                                    f"Error running {strategy_name} for {bot_type}-{direction}: {e}"
                                )
                    
                    # Print stats every 10 minutes
                    if (datetime.datetime.now() - last_stats_time).total_seconds() > 600:
                        self._print_trading_stats()
                        last_stats_time = datetime.datetime.now()
                    
                    # Sleep between loops
                    time.sleep(30)  # 30 seconds between strategy runs
                    
                except Exception as e:
                    self.logger.log_event(f"Error in trading loop iteration {loop_count}: {e}")
                    time.sleep(60)  # Wait longer on errors
            
            self.logger.log_event(f"Trading loop completed after {loop_count} iterations")
            
        except Exception as e:
            self.logger.log_event(f"Fatal error in trading loop: {e}")
        finally:
            self._cleanup()
    
    def _is_market_open(self) -> bool:
        """Check if market is currently open"""
        now = datetime.datetime.now()
        current_time = now.time()
        
        # Market hours: 9:15 AM to 3:30 PM
        market_open = datetime.time(9, 15)
        market_close = datetime.time(15, 30)
        
        # Check if it's a weekday
        if now.weekday() >= 5:  # Saturday = 5, Sunday = 6
            return False
        
        return market_open <= current_time <= market_close
    
    def _print_trading_stats(self):
        """Print current trading statistics"""
        try:
            stats = self.trade_manager.get_trading_stats()
            
            # Enhanced logging for statistics
            self.enhanced_logger.log_performance_metrics(
                metrics=stats,
                metric_type="periodic_trading_stats"
            )
            
            self.logger.log_event("=== TRADING STATISTICS ===")
            
            # Execution stats
            exec_stats = stats.get('execution_stats', {})
            self.logger.log_event(
                f"Trades: {exec_stats.get('total_trades', 0)} total, "
                f"{exec_stats.get('successful_trades', 0)} successful, "
                f"{exec_stats.get('failed_trades', 0)} failed"
            )
            self.logger.log_event(
                f"Paper: {exec_stats.get('paper_trades', 0)}, "
                f"Real: {exec_stats.get('real_trades', 0)}"
            )
            
            # Monitoring stats
            monitor_stats = stats.get('monitoring_stats', {})
            self.logger.log_event(
                f"Positions: {monitor_stats.get('open_positions', 0)} open, "
                f"{monitor_stats.get('closed_positions', 0)} closed"
            )
            self.logger.log_event(
                f"P&L: Unrealized ₹{monitor_stats.get('total_unrealized_pnl', 0):.2f}, "
                f"Realized ₹{monitor_stats.get('total_realized_pnl', 0):.2f}"
            )
            
            # Exit stats
            exit_stats = monitor_stats.get('exit_stats', {})
            self.logger.log_event(
                f"Exits: {exit_stats.get('total_exits', 0)} total, "
                f"SL: {exit_stats.get('stop_loss_exits', 0)}, "
                f"Target: {exit_stats.get('target_exits', 0)}, "
                f"Trailing: {exit_stats.get('trailing_stop_exits', 0)}"
            )
            
            # Risk stats
            risk_stats = stats.get('risk_governor_stats', {})
            self.logger.log_event(
                f"Risk: Can trade: {risk_stats.get('can_trade', False)}, "
                f"Daily loss: ₹{risk_stats.get('total_loss', 0):.2f}"
            )
            
            self.logger.log_event("========================")
            
        except Exception as e:
            self.enhanced_logger.log_error(
                error=e,
                context={'operation': 'print_trading_stats'},
                source="main_system"
            )
            
            self.logger.log_event(f"Error printing stats: {e}")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.log_event(f"Received signal {signum} - initiating graceful shutdown")
        self.running = False
    
    def _cleanup(self):
        """Cleanup and shutdown"""
        try:
            self.enhanced_logger.log_event(
                "System cleanup initiated",
                LogLevel.INFO,
                LogCategory.SYSTEM,
                source="main_system"
            )
            
            self.logger.log_event("Starting system cleanup...")
            
            if self.trade_manager:
                # Emergency exit all positions if needed
                open_positions = self.trade_manager.get_active_positions()
                if open_positions:
                    self.enhanced_logger.log_risk_event(
                        risk_data={
                            'event': 'system_shutdown_emergency_exit',
                            'open_positions_count': len(open_positions),
                            'reason': 'system_shutdown',
                            'positions': [
                                {
                                    'id': pos['id'],
                                    'symbol': pos['symbol'],
                                    'quantity': pos['quantity'],
                                    'unrealized_pnl': pos['unrealized_pnl']
                                } for pos in open_positions
                            ]
                        },
                        risk_level="high"
                    )
                    
                    self.logger.log_event(f"Emergency exiting {len(open_positions)} open positions")
                    self.trade_manager.emergency_exit_all_positions("System shutdown")
                    
                    # Wait a bit for exits to process
                    time.sleep(10)
                
                # Stop trading session
                self.trade_manager.stop_trading_session()
            
            # Final stats
            self._print_trading_stats()
            
            # Run analysis
            if self.monitor:
                try:
                    self.monitor.analyze(bot_name="enhanced-trading-system")
                except Exception as e:
                    self.enhanced_logger.log_error(
                        error=e,
                        context={'operation': 'final_analysis'},
                        source="main_system"
                    )
                    self.logger.log_event(f"Error in final analysis: {e}")
            
            # Shutdown enhanced logger
            if self.enhanced_logger:
                self.enhanced_logger.log_event(
                    "System cleanup completed successfully",
                    LogLevel.INFO,
                    LogCategory.SYSTEM,
                    data={
                        'cleanup_timestamp': datetime.datetime.now().isoformat(),
                        'session_duration': 'calculated_in_logger'
                    },
                    source="main_system"
                )
                
                # Create and upload final summary
                summary = self.enhanced_logger.create_daily_summary()
                
                # Graceful shutdown of enhanced logger
                self.enhanced_logger.shutdown()
            
            self.logger.log_event("System cleanup completed")
            
        except Exception as e:
            if self.enhanced_logger:
                self.enhanced_logger.log_error(
                    error=e,
                    context={'operation': 'system_cleanup'},
                    source="main_system"
                )
            
            if self.logger:
                self.logger.log_event(f"Error during cleanup: {e}")
            else:
                print(f"Error during cleanup: {e}")
    
    def run_manual_commands(self):
        """Interactive mode for manual commands"""
        print("\n=== Enhanced Trading System - Manual Mode ===")
        print("Available commands:")
        print("  positions - Show active positions")
        print("  stats - Show trading statistics")
        print("  exit <position_id> [percentage] - Exit position")
        print("  breakeven <position_id> - Move to breakeven")
        print("  trailing <position_id> <distance> - Enable trailing stop")
        print("  emergency - Emergency exit all positions")
        print("  quit - Exit manual mode")
        print()
        
        while True:
            try:
                command = input("Enter command: ").strip().lower()
                
                if command == "quit":
                    break
                elif command == "positions":
                    self._show_positions()
                elif command == "stats":
                    self._print_trading_stats()
                elif command.startswith("exit "):
                    self._handle_exit_command(command)
                elif command.startswith("breakeven "):
                    self._handle_breakeven_command(command)
                elif command.startswith("trailing "):
                    self._handle_trailing_command(command)
                elif command == "emergency":
                    self._handle_emergency_exit()
                else:
                    print("Unknown command. Type 'quit' to exit.")
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")
    
    def _show_positions(self):
        """Show active positions"""
        positions = self.trade_manager.get_active_positions()
        
        if not positions:
            print("No active positions")
            return
        
        print(f"\n=== Active Positions ({len(positions)}) ===")
        for pos in positions:
            print(f"ID: {pos['id']}")
            print(f"  Symbol: {pos['symbol']} ({pos['direction']})")
            print(f"  Qty: {pos['quantity']} | Entry: ₹{pos['entry_price']:.2f}")
            print(f"  Current: ₹{pos['current_price']:.2f} | P&L: ₹{pos['unrealized_pnl']:.2f}")
            print(f"  SL: ₹{pos['exit_strategy']['stop_loss']:.2f} | Target: ₹{pos['exit_strategy']['target']:.2f}")
            print(f"  Strategy: {pos['strategy']} | Duration: {pos.get('duration', 'Unknown')}")
            print()
    
    def _handle_exit_command(self, command):
        """Handle exit command"""
        parts = command.split()
        if len(parts) < 2:
            print("Usage: exit <position_id> [percentage]")
            return
        
        position_id = parts[1]
        percentage = float(parts[2]) if len(parts) > 2 else 100.0
        
        success = self.trade_manager.manual_exit_position(position_id, percentage)
        if success:
            print(f"Exit order placed for {percentage}% of position {position_id}")
        else:
            print(f"Failed to exit position {position_id}")
    
    def _handle_breakeven_command(self, command):
        """Handle breakeven command"""
        parts = command.split()
        if len(parts) < 2:
            print("Usage: breakeven <position_id>")
            return
        
        position_id = parts[1]
        success = self.trade_manager.move_position_to_breakeven(position_id)
        if success:
            print(f"Moved position {position_id} to breakeven")
        else:
            print(f"Failed to move position {position_id} to breakeven")
    
    def _handle_trailing_command(self, command):
        """Handle trailing stop command"""
        parts = command.split()
        if len(parts) < 3:
            print("Usage: trailing <position_id> <distance>")
            return
        
        position_id = parts[1]
        distance = float(parts[2])
        
        success = self.trade_manager.enable_trailing_stop(position_id, distance)
        if success:
            print(f"Enabled trailing stop for position {position_id} with distance ₹{distance:.2f}")
        else:
            print(f"Failed to enable trailing stop for position {position_id}")
    
    def _handle_emergency_exit(self):
        """Handle emergency exit"""
        confirm = input("Are you sure you want to emergency exit ALL positions? (yes/no): ")
        if confirm.lower() == "yes":
            self.trade_manager.emergency_exit_all_positions("Manual emergency exit")
            print("Emergency exit initiated for all positions")
        else:
            print("Emergency exit cancelled")


def main():
    """Main function"""
    print("Enhanced TRON Trading System")
    print("=" * 50)
    
    # Create trading system
    trading_system = EnhancedTradingSystem()
    
    # Initialize system
    if not trading_system.initialize():
        print("Failed to initialize trading system")
        return 1
    
    # Check command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "manual":
            # Manual mode
            trading_system.start_trading_session()
            trading_system.run_manual_commands()
            trading_system._cleanup()
            return 0
        elif sys.argv[1] == "stats":
            # Just show stats
            trading_system.start_trading_session()
            trading_system._print_trading_stats()
            trading_system._cleanup()
            return 0
    
    try:
        # Wait for market open
        trading_system.wait_for_market_open()
        
        # Start trading session
        trading_system.start_trading_session()
        
        # Get strategy from config or use default
        strategy_name = trading_system.config.default_strategy or "vwap"
        
        # Run main trading loop
        trading_system.run_trading_loop(strategy_name)
        
    except KeyboardInterrupt:
        trading_system.logger.log_event("Received keyboard interrupt")
    except Exception as e:
        trading_system.logger.log_event(f"Unexpected error: {e}")
        return 1
    finally:
        trading_system._cleanup()
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 