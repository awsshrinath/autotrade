"""
Position Monitor System
Real-time position monitoring with comprehensive exit strategies
Handles stop loss, trailing stop loss, target exits, and system crash recovery
"""

import asyncio
import json
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import threading
from threading import Lock

from runner.firestore_client import FirestoreClient
from runner.kiteconnect_manager import KiteConnectManager
from runner.enhanced_logger import EnhancedLogger, LogLevel, LogCategory, create_enhanced_logger
from runner.capital.portfolio_manager import PortfolioManager
from runner.risk_governor import RiskGovernor
from config.config_manager import get_trading_config


class ExitReason(Enum):
    """Exit reasons for trades"""
    STOP_LOSS_HIT = "stop_loss_hit"
    TARGET_HIT = "target_hit"
    TRAILING_STOP_HIT = "trailing_stop_hit"
    TIME_BASED_EXIT = "time_based_exit"
    MANUAL_EXIT = "manual_exit"
    SYSTEM_CRASH_EXIT = "system_crash_exit"
    MARKET_CLOSE_EXIT = "market_close_exit"
    RISK_MANAGEMENT_EXIT = "risk_management_exit"
    BREAKEVEN_EXIT = "breakeven_exit"
    PARTIAL_EXIT = "partial_exit"


class TradeStatus(Enum):
    """Trade status enumeration"""
    OPEN = "open"
    CLOSED = "closed"
    PARTIALLY_CLOSED = "partially_closed"
    PENDING_EXIT = "pending_exit"
    ERROR = "error"


@dataclass
class ExitStrategy:
    """Exit strategy configuration"""
    stop_loss: float
    target: float
    trailing_stop_enabled: bool = False
    trailing_stop_distance: float = 0.0
    trailing_stop_trigger: float = 0.0
    time_based_exit_minutes: int = 0
    breakeven_trigger_pct: float = 0.0
    partial_exit_levels: List[Tuple[float, float]] = None  # (price_level, exit_percentage)
    max_loss_pct: float = 5.0
    max_hold_time_minutes: int = 240  # 4 hours


@dataclass
class Position:
    """Position data structure"""
    id: str
    symbol: str
    strategy: str
    bot_type: str
    direction: str  # bullish/bearish
    quantity: int
    entry_price: float
    current_price: float
    entry_time: datetime
    exit_strategy: ExitStrategy
    status: TradeStatus = TradeStatus.OPEN
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    exit_price: Optional[float] = None
    exit_time: Optional[datetime] = None
    exit_reason: Optional[ExitReason] = None
    trailing_stop_price: Optional[float] = None
    highest_price: Optional[float] = None  # For bullish positions
    lowest_price: Optional[float] = None   # For bearish positions
    partial_exits: List[Dict] = None
    last_update: datetime = None
    paper_trade: bool = True
    
    def __post_init__(self):
        if self.partial_exits is None:
            self.partial_exits = []
        if self.last_update is None:
            self.last_update = datetime.now()
        if self.highest_price is None:
            self.highest_price = self.entry_price
        if self.lowest_price is None:
            self.lowest_price = self.entry_price


class PositionMonitor:
    """Real-time position monitoring and exit management system"""
    
    def __init__(self, logger: EnhancedLogger = None, firestore: FirestoreClient = None, 
                 kite_manager: KiteConnectManager = None, portfolio_manager: PortfolioManager = None):
        self.logger = logger
        self.firestore = firestore
        self.kite_manager = kite_manager
        self.portfolio_manager = portfolio_manager
        
        # Initialize enhanced logger
        self.enhanced_logger = create_enhanced_logger(
            session_id=f"position_monitor_{int(time.time())}",
            enable_gcs=True,
            enable_firestore=True
        )
        
        # Configuration
        self.config = get_trading_config()
        
        # Position tracking
        self.positions: Dict[str, Position] = {}
        self.positions_lock = Lock()
        
        # Monitoring control
        self.monitoring_active = False
        self.monitor_thread = None
        self.update_interval = 5  # seconds
        
        # Exit execution
        self.exit_queue = asyncio.Queue()
        self.exit_executor_active = False
        
        # Recovery system
        self.crash_recovery_file = "data/position_recovery.json"
        self.ensure_recovery_directory()
        
        # Performance tracking
        self.exit_stats = {
            'total_exits': 0,
            'stop_loss_exits': 0,
            'target_exits': 0,
            'trailing_stop_exits': 0,
            'manual_exits': 0,
            'system_exits': 0
        }
        
        if self.logger:
            self.logger.log_event("PositionMonitor initialized")
        
        self.enhanced_logger.log_event(
            "PositionMonitor initialized with enhanced logging",
            LogLevel.INFO,
            LogCategory.SYSTEM,
            data={
                'update_interval': self.update_interval,
                'recovery_file': self.crash_recovery_file,
                'config': {
                    'paper_trade': self.config.paper_trade if self.config else True
                }
            },
            source="position_monitor"
        )
    
    def ensure_recovery_directory(self):
        """Ensure recovery directory exists"""
        os.makedirs(os.path.dirname(self.crash_recovery_file), exist_ok=True)
    
    def add_position(self, trade_data: Dict[str, Any]) -> str:
        """
        Add a new position to monitor
        
        Args:
            trade_data: Trade data dictionary
            
        Returns:
            Position ID
        """
        try:
            # Create exit strategy from trade data
            exit_strategy = ExitStrategy(
                stop_loss=trade_data.get('stop_loss', 0),
                target=trade_data.get('target', 0),
                trailing_stop_enabled=trade_data.get('trailing_stop_enabled', False),
                trailing_stop_distance=trade_data.get('trailing_stop_distance', 0),
                trailing_stop_trigger=trade_data.get('trailing_stop_trigger', 0),
                time_based_exit_minutes=trade_data.get('time_based_exit_minutes', 0),
                breakeven_trigger_pct=trade_data.get('breakeven_trigger_pct', 0),
                partial_exit_levels=trade_data.get('partial_exit_levels', []),
                max_loss_pct=trade_data.get('max_loss_pct', 5.0),
                max_hold_time_minutes=trade_data.get('max_hold_time_minutes', 240)
            )
            
            # Create position
            position_id = f"{trade_data['symbol']}_{trade_data['strategy']}_{int(time.time())}"
            position = Position(
                id=position_id,
                symbol=trade_data['symbol'],
                strategy=trade_data['strategy'],
                bot_type=trade_data.get('bot_type', 'stock'),
                direction=trade_data['direction'],
                quantity=trade_data['quantity'],
                entry_price=trade_data['entry_price'],
                current_price=trade_data['entry_price'],
                entry_time=datetime.fromisoformat(trade_data.get('timestamp', datetime.now().isoformat())),
                exit_strategy=exit_strategy,
                paper_trade=trade_data.get('paper_trade', True)
            )
            
            with self.positions_lock:
                self.positions[position_id] = position
            
            # Save to recovery file
            self.save_positions_for_recovery()
            
            # Log to Firestore
            if self.firestore:
                self.firestore.log_trade(
                    bot_name=trade_data.get('bot_type', 'stock-trader'),
                    date_str=datetime.now().strftime("%Y-%m-%d"),
                    trade_data={
                        **trade_data,
                        'id': position_id,
                        'status': 'open',
                        'monitor_added': datetime.now().isoformat()
                    }
                )
            
            # Enhanced logging
            self.enhanced_logger.log_position_update(
                position_data={
                    'id': position_id,
                    'symbol': position.symbol,
                    'strategy': position.strategy,
                    'bot_type': position.bot_type,
                    'direction': position.direction,
                    'quantity': position.quantity,
                    'entry_price': position.entry_price,
                    'stop_loss': position.exit_strategy.stop_loss,
                    'target': position.exit_strategy.target,
                    'trailing_stop_enabled': position.exit_strategy.trailing_stop_enabled,
                    'paper_trade': position.paper_trade,
                    'entry_time': position.entry_time.isoformat()
                },
                update_type="added"
            )
            
            if self.logger:
                self.logger.log_event(
                    f"Position added to monitor: {position.symbol} "
                    f"({position.direction}) Qty: {position.quantity} "
                    f"Entry: ₹{position.entry_price:.2f} "
                    f"SL: ₹{position.exit_strategy.stop_loss:.2f} "
                    f"Target: ₹{position.exit_strategy.target:.2f}"
                )
            
            return position_id
            
        except Exception as e:
            self.enhanced_logger.log_error(
                error=e,
                context={
                    'trade_data': trade_data,
                    'operation': 'add_position'
                },
                source="position_monitor"
            )
            
            if self.logger:
                self.logger.log_event(f"Error adding position to monitor: {e}")
            return None
    
    def start_monitoring(self):
        """Start the position monitoring system"""
        if self.monitoring_active:
            if self.logger:
                self.logger.log_event("Position monitoring already active")
            return
        
        self.monitoring_active = True
        
        # Start monitoring thread
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
        
        # Start exit executor
        asyncio.create_task(self._exit_executor())
        
        # Load positions from recovery file
        self.load_positions_from_recovery()
        
        if self.logger:
            self.logger.log_event("Position monitoring started")
    
    def stop_monitoring(self):
        """Stop the position monitoring system"""
        self.monitoring_active = False
        self.exit_executor_active = False
        
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=10)
        
        # Save final state
        self.save_positions_for_recovery()
        
        if self.logger:
            self.logger.log_event("Position monitoring stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                self._update_all_positions()
                self._check_exit_conditions()
                time.sleep(self.update_interval)
            except Exception as e:
                if self.logger:
                    self.logger.log_event(f"Error in monitoring loop: {e}")
                time.sleep(self.update_interval)
    
    def _update_all_positions(self):
        """Update current prices for all positions"""
        if not self.positions:
            return
        
        try:
            # Get all symbols
            symbols = []
            with self.positions_lock:
                for position in self.positions.values():
                    if position.status == TradeStatus.OPEN:
                        symbols.append(f"NSE:{position.symbol}")
            
            if not symbols:
                return
            
            # Fetch current prices
            if self.kite_manager and self.kite_manager.get_kite_client():
                kite = self.kite_manager.get_kite_client()
                ltp_data = kite.ltp(symbols)
                
                # Update positions
                with self.positions_lock:
                    for position in self.positions.values():
                        if position.status == TradeStatus.OPEN:
                            symbol_key = f"NSE:{position.symbol}"
                            if symbol_key in ltp_data:
                                new_price = ltp_data[symbol_key]['last_price']
                                self._update_position_price(position, new_price)
            
        except Exception as e:
            if self.logger:
                self.logger.log_event(f"Error updating position prices: {e}")
    
    def _update_position_price(self, position: Position, new_price: float):
        """Update position with new price and calculate metrics"""
        position.current_price = new_price
        position.last_update = datetime.now()
        
        # Update highest/lowest prices for trailing stops
        if position.direction == 'bullish':
            if new_price > position.highest_price:
                position.highest_price = new_price
                # Update trailing stop if enabled
                if position.exit_strategy.trailing_stop_enabled:
                    self._update_trailing_stop(position)
        else:  # bearish
            if new_price < position.lowest_price:
                position.lowest_price = new_price
                # Update trailing stop if enabled
                if position.exit_strategy.trailing_stop_enabled:
                    self._update_trailing_stop(position)
        
        # Calculate unrealized P&L
        if position.direction == 'bullish':
            position.unrealized_pnl = (new_price - position.entry_price) * position.quantity
        else:
            position.unrealized_pnl = (position.entry_price - new_price) * position.quantity
    
    def _update_trailing_stop(self, position: Position):
        """Update trailing stop loss price"""
        if not position.exit_strategy.trailing_stop_enabled:
            return
        
        distance = position.exit_strategy.trailing_stop_distance
        
        if position.direction == 'bullish':
            # For bullish positions, trail below the highest price
            new_trailing_stop = position.highest_price - distance
            if position.trailing_stop_price is None or new_trailing_stop > position.trailing_stop_price:
                position.trailing_stop_price = new_trailing_stop
        else:
            # For bearish positions, trail above the lowest price
            new_trailing_stop = position.lowest_price + distance
            if position.trailing_stop_price is None or new_trailing_stop < position.trailing_stop_price:
                position.trailing_stop_price = new_trailing_stop
    
    def _check_exit_conditions(self):
        """Check exit conditions for all positions"""
        with self.positions_lock:
            for position in list(self.positions.values()):
                if position.status == TradeStatus.OPEN:
                    exit_signal = self._evaluate_exit_conditions(position)
                    if exit_signal:
                        asyncio.create_task(self._queue_exit(position, exit_signal))
    
    def _evaluate_exit_conditions(self, position: Position) -> Optional[Tuple[ExitReason, float, float]]:
        """
        Evaluate exit conditions for a position
        
        Returns:
            Tuple of (exit_reason, exit_price, exit_percentage) or None
        """
        current_price = position.current_price
        
        # 1. Stop Loss Check
        if position.direction == 'bullish':
            if current_price <= position.exit_strategy.stop_loss:
                return (ExitReason.STOP_LOSS_HIT, position.exit_strategy.stop_loss, 100.0)
        else:
            if current_price >= position.exit_strategy.stop_loss:
                return (ExitReason.STOP_LOSS_HIT, position.exit_strategy.stop_loss, 100.0)
        
        # 2. Target Check
        if position.direction == 'bullish':
            if current_price >= position.exit_strategy.target:
                return (ExitReason.TARGET_HIT, position.exit_strategy.target, 100.0)
        else:
            if current_price <= position.exit_strategy.target:
                return (ExitReason.TARGET_HIT, position.exit_strategy.target, 100.0)
        
        # 3. Trailing Stop Check
        if position.trailing_stop_price is not None:
            if position.direction == 'bullish':
                if current_price <= position.trailing_stop_price:
                    return (ExitReason.TRAILING_STOP_HIT, position.trailing_stop_price, 100.0)
            else:
                if current_price >= position.trailing_stop_price:
                    return (ExitReason.TRAILING_STOP_HIT, position.trailing_stop_price, 100.0)
        
        # 4. Time-based Exit
        if position.exit_strategy.time_based_exit_minutes > 0:
            time_held = (datetime.now() - position.entry_time).total_seconds() / 60
            if time_held >= position.exit_strategy.time_based_exit_minutes:
                return (ExitReason.TIME_BASED_EXIT, current_price, 100.0)
        
        # 5. Max Hold Time
        time_held = (datetime.now() - position.entry_time).total_seconds() / 60
        if time_held >= position.exit_strategy.max_hold_time_minutes:
            return (ExitReason.TIME_BASED_EXIT, current_price, 100.0)
        
        # 6. Max Loss Check
        loss_pct = abs(position.unrealized_pnl) / (position.entry_price * position.quantity) * 100
        if position.unrealized_pnl < 0 and loss_pct >= position.exit_strategy.max_loss_pct:
            return (ExitReason.RISK_MANAGEMENT_EXIT, current_price, 100.0)
        
        # 7. Partial Exit Levels
        for price_level, exit_pct in position.exit_strategy.partial_exit_levels or []:
            if position.direction == 'bullish' and current_price >= price_level:
                return (ExitReason.PARTIAL_EXIT, price_level, exit_pct)
            elif position.direction == 'bearish' and current_price <= price_level:
                return (ExitReason.PARTIAL_EXIT, price_level, exit_pct)
        
        # 8. Market Close Check (3:20 PM)
        current_time = datetime.now().time()
        market_close_time = datetime.strptime("15:20", "%H:%M").time()
        if current_time >= market_close_time:
            return (ExitReason.MARKET_CLOSE_EXIT, current_price, 100.0)
        
        return None
    
    async def _queue_exit(self, position: Position, exit_signal: Tuple[ExitReason, float, float]):
        """Queue position for exit"""
        await self.exit_queue.put((position, exit_signal))
    
    async def _exit_executor(self):
        """Execute exits from the queue"""
        self.exit_executor_active = True
        
        while self.exit_executor_active:
            try:
                # Wait for exit signal
                position, exit_signal = await asyncio.wait_for(
                    self.exit_queue.get(), timeout=1.0
                )
                
                # Execute the exit
                await self._execute_exit(position, exit_signal)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                if self.logger:
                    self.logger.log_event(f"Error in exit executor: {e}")
    
    async def _execute_exit(self, position: Position, exit_signal: Tuple[ExitReason, float, float]):
        """Execute position exit"""
        exit_reason, exit_price, exit_percentage = exit_signal
        
        try:
            # Calculate exit quantity
            exit_quantity = int(position.quantity * (exit_percentage / 100))
            if exit_quantity <= 0:
                return
            
            # Execute the trade
            if position.paper_trade:
                success = await self._execute_paper_exit(position, exit_price, exit_quantity, exit_reason)
            else:
                success = await self._execute_real_exit(position, exit_price, exit_quantity, exit_reason)
            
            if success:
                # Update position
                self._update_position_after_exit(position, exit_price, exit_quantity, exit_reason, exit_percentage)
                
                # Update statistics
                self.exit_stats['total_exits'] += 1
                if exit_reason == ExitReason.STOP_LOSS_HIT:
                    self.exit_stats['stop_loss_exits'] += 1
                elif exit_reason == ExitReason.TARGET_HIT:
                    self.exit_stats['target_exits'] += 1
                elif exit_reason == ExitReason.TRAILING_STOP_HIT:
                    self.exit_stats['trailing_stop_exits'] += 1
                
                if self.logger:
                    self.logger.log_event(
                        f"Position exit executed: {position.symbol} "
                        f"Reason: {exit_reason.value} "
                        f"Price: ₹{exit_price:.2f} "
                        f"Qty: {exit_quantity} "
                        f"P&L: ₹{position.realized_pnl:.2f}"
                    )
            
        except Exception as e:
            if self.logger:
                self.logger.log_event(f"Error executing exit for {position.symbol}: {e}")
    
    async def _execute_paper_exit(self, position: Position, exit_price: float, 
                                 exit_quantity: int, exit_reason: ExitReason) -> bool:
        """Execute paper trade exit"""
        try:
            # For paper trading, we just simulate the exit
            if self.logger:
                self.logger.log_event(
                    f"[PAPER-EXIT] {position.symbol} - {exit_reason.value} "
                    f"at ₹{exit_price:.2f} | Qty: {exit_quantity}"
                )
            return True
        except Exception as e:
            if self.logger:
                self.logger.log_event(f"Paper exit failed for {position.symbol}: {e}")
            return False
    
    async def _execute_real_exit(self, position: Position, exit_price: float, 
                                exit_quantity: int, exit_reason: ExitReason) -> bool:
        """Execute real trade exit"""
        try:
            if not self.kite_manager or not self.kite_manager.get_kite_client():
                if self.logger:
                    self.logger.log_event("Kite client not available for real exit")
                return False
            
            kite = self.kite_manager.get_kite_client()
            
            # Determine order type and transaction type
            transaction_type = "SELL" if position.direction == 'bullish' else "BUY"
            
            # Place market order for immediate exit
            order_params = {
                'tradingsymbol': position.symbol,
                'exchange': 'NSE',
                'transaction_type': transaction_type,
                'quantity': exit_quantity,
                'order_type': 'MARKET',
                'product': 'MIS',  # Intraday
                'validity': 'DAY'
            }
            
            order_id = kite.place_order(**order_params)
            
            if self.logger:
                self.logger.log_event(
                    f"[REAL-EXIT] Order placed for {position.symbol} "
                    f"Order ID: {order_id} | Qty: {exit_quantity}"
                )
            
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.log_event(f"Real exit failed for {position.symbol}: {e}")
            return False
    
    def _update_position_after_exit(self, position: Position, exit_price: float, 
                                   exit_quantity: int, exit_reason: ExitReason, exit_percentage: float):
        """Update position after exit execution"""
        # Calculate realized P&L for this exit
        if position.direction == 'bullish':
            exit_pnl = (exit_price - position.entry_price) * exit_quantity
        else:
            exit_pnl = (position.entry_price - exit_price) * exit_quantity
        
        position.realized_pnl += exit_pnl
        
        # Record partial exit
        exit_record = {
            'timestamp': datetime.now().isoformat(),
            'exit_price': exit_price,
            'exit_quantity': exit_quantity,
            'exit_reason': exit_reason.value,
            'exit_percentage': exit_percentage,
            'pnl': exit_pnl
        }
        position.partial_exits.append(exit_record)
        
        # Update position quantity
        position.quantity -= exit_quantity
        
        # Update position status
        if position.quantity <= 0:
            position.status = TradeStatus.CLOSED
            position.exit_price = exit_price
            position.exit_time = datetime.now()
            position.exit_reason = exit_reason
        else:
            position.status = TradeStatus.PARTIALLY_CLOSED
        
        # Enhanced logging for exit
        self.enhanced_logger.log_exit_execution(
            exit_data={
                'position_id': position.id,
                'symbol': position.symbol,
                'strategy': position.strategy,
                'bot_type': position.bot_type,
                'direction': position.direction,
                'exit_price': exit_price,
                'exit_quantity': exit_quantity,
                'exit_reason': exit_reason.value,
                'exit_percentage': exit_percentage,
                'pnl': exit_pnl,
                'realized_pnl': position.realized_pnl,
                'remaining_quantity': position.quantity,
                'status': position.status.value,
                'paper_trade': position.paper_trade,
                'entry_price': position.entry_price,
                'entry_time': position.entry_time.isoformat(),
                'exit_time': datetime.now().isoformat(),
                'partial_exits': position.partial_exits
            },
            success=True
        )
        
        # Log to Firestore
        if self.firestore:
            trade_data = {
                'id': position.id,
                'symbol': position.symbol,
                'strategy': position.strategy,
                'bot_type': position.bot_type,
                'direction': position.direction,
                'entry_price': position.entry_price,
                'exit_price': exit_price,
                'quantity': exit_quantity,
                'entry_time': position.entry_time.isoformat(),
                'exit_time': datetime.now().isoformat(),
                'exit_reason': exit_reason.value,
                'pnl': exit_pnl,
                'status': 'closed' if position.quantity <= 0 else 'partially_closed',
                'paper_trade': position.paper_trade,
                'partial_exits': position.partial_exits,
                'realized_pnl': position.realized_pnl
            }
            
            self.firestore.log_trade(
                bot_name=position.bot_type + '-trader',
                date_str=datetime.now().strftime("%Y-%m-%d"),
                trade_data=trade_data
            )
        
        # Save to recovery file
        self.save_positions_for_recovery()
    
    def manual_exit_position(self, position_id: str, exit_percentage: float = 100.0) -> bool:
        """Manually exit a position"""
        try:
            with self.positions_lock:
                if position_id not in self.positions:
                    return False
                
                position = self.positions[position_id]
                if position.status != TradeStatus.OPEN:
                    return False
                
                # Queue for manual exit
                exit_signal = (ExitReason.MANUAL_EXIT, position.current_price, exit_percentage)
                asyncio.create_task(self._queue_exit(position, exit_signal))
                
                return True
                
        except Exception as e:
            if self.logger:
                self.logger.log_event(f"Error in manual exit: {e}")
            return False
    
    def move_to_breakeven(self, position_id: str) -> bool:
        """Move position stop loss to breakeven"""
        try:
            with self.positions_lock:
                if position_id not in self.positions:
                    return False
                
                position = self.positions[position_id]
                if position.status != TradeStatus.OPEN:
                    return False
                
                # Update stop loss to entry price
                position.exit_strategy.stop_loss = position.entry_price
                
                if self.logger:
                    self.logger.log_event(
                        f"Moved {position.symbol} stop loss to breakeven: ₹{position.entry_price:.2f}"
                    )
                
                return True
                
        except Exception as e:
            if self.logger:
                self.logger.log_event(f"Error moving to breakeven: {e}")
            return False
    
    def enable_trailing_stop(self, position_id: str, distance: float, trigger_price: float = None) -> bool:
        """Enable trailing stop for a position"""
        try:
            with self.positions_lock:
                if position_id not in self.positions:
                    return False
                
                position = self.positions[position_id]
                if position.status != TradeStatus.OPEN:
                    return False
                
                # Enable trailing stop
                position.exit_strategy.trailing_stop_enabled = True
                position.exit_strategy.trailing_stop_distance = distance
                
                if trigger_price:
                    position.exit_strategy.trailing_stop_trigger = trigger_price
                
                # Initialize trailing stop price
                self._update_trailing_stop(position)
                
                if self.logger:
                    self.logger.log_event(
                        f"Enabled trailing stop for {position.symbol}: "
                        f"Distance: ₹{distance:.2f}"
                    )
                
                return True
                
        except Exception as e:
            if self.logger:
                self.logger.log_event(f"Error enabling trailing stop: {e}")
            return False
    
    def get_positions(self, status_filter: TradeStatus = None) -> List[Dict[str, Any]]:
        """Get all positions with optional status filter"""
        with self.positions_lock:
            positions = []
            for position in self.positions.values():
                if status_filter is None or position.status == status_filter:
                    positions.append(asdict(position))
            return positions
    
    def get_position(self, position_id: str) -> Optional[Dict[str, Any]]:
        """Get specific position by ID"""
        with self.positions_lock:
            if position_id in self.positions:
                return asdict(self.positions[position_id])
            return None
    
    def save_positions_for_recovery(self):
        """Save positions to recovery file for crash recovery"""
        try:
            with self.positions_lock:
                recovery_data = {
                    'timestamp': datetime.now().isoformat(),
                    'positions': [asdict(pos) for pos in self.positions.values()],
                    'exit_stats': self.exit_stats
                }
                
                with open(self.crash_recovery_file, 'w') as f:
                    json.dump(recovery_data, f, indent=2, default=str)
                    
        except Exception as e:
            if self.logger:
                self.logger.log_event(f"Error saving recovery data: {e}")
    
    def load_positions_from_recovery(self):
        """Load positions from recovery file after system restart"""
        try:
            if not os.path.exists(self.crash_recovery_file):
                return
            
            with open(self.crash_recovery_file, 'r') as f:
                recovery_data = json.load(f)
            
            # Load positions
            for pos_data in recovery_data.get('positions', []):
                # Convert back to Position object
                exit_strategy = ExitStrategy(**pos_data['exit_strategy'])
                
                position = Position(
                    id=pos_data['id'],
                    symbol=pos_data['symbol'],
                    strategy=pos_data['strategy'],
                    bot_type=pos_data['bot_type'],
                    direction=pos_data['direction'],
                    quantity=pos_data['quantity'],
                    entry_price=pos_data['entry_price'],
                    current_price=pos_data['current_price'],
                    entry_time=datetime.fromisoformat(pos_data['entry_time']),
                    exit_strategy=exit_strategy,
                    status=TradeStatus(pos_data['status']),
                    unrealized_pnl=pos_data['unrealized_pnl'],
                    realized_pnl=pos_data['realized_pnl'],
                    paper_trade=pos_data['paper_trade']
                )
                
                # Only load open positions
                if position.status == TradeStatus.OPEN:
                    with self.positions_lock:
                        self.positions[position.id] = position
            
            # Load stats
            self.exit_stats.update(recovery_data.get('exit_stats', {}))
            
            if self.logger:
                self.logger.log_event(
                    f"Recovered {len(self.positions)} positions from crash recovery file"
                )
                
        except Exception as e:
            if self.logger:
                self.logger.log_event(f"Error loading recovery data: {e}")
    
    def emergency_exit_all(self, reason: str = "Emergency exit"):
        """Emergency exit all open positions"""
        try:
            with self.positions_lock:
                open_positions = [
                    pos for pos in self.positions.values() 
                    if pos.status == TradeStatus.OPEN
                ]
            
            # Enhanced logging for emergency exit
            self.enhanced_logger.log_risk_event(
                risk_data={
                    'event': 'emergency_exit_all',
                    'reason': reason,
                    'open_positions_count': len(open_positions),
                    'positions': [
                        {
                            'id': pos.id,
                            'symbol': pos.symbol,
                            'quantity': pos.quantity,
                            'unrealized_pnl': pos.unrealized_pnl
                        } for pos in open_positions
                    ]
                },
                risk_level="critical"
            )
            
            for position in open_positions:
                exit_signal = (ExitReason.SYSTEM_CRASH_EXIT, position.current_price, 100.0)
                asyncio.create_task(self._queue_exit(position, exit_signal))
            
            if self.logger:
                self.logger.log_event(
                    f"Emergency exit initiated for {len(open_positions)} positions. Reason: {reason}"
                )
                
        except Exception as e:
            self.enhanced_logger.log_error(
                error=e,
                context={
                    'operation': 'emergency_exit_all',
                    'reason': reason
                },
                source="position_monitor"
            )
            
            if self.logger:
                self.logger.log_event(f"Error in emergency exit: {e}")
    
    def get_monitoring_stats(self) -> Dict[str, Any]:
        """Get monitoring statistics"""
        with self.positions_lock:
            open_positions = len([p for p in self.positions.values() if p.status == TradeStatus.OPEN])
            closed_positions = len([p for p in self.positions.values() if p.status == TradeStatus.CLOSED])
            
            total_unrealized_pnl = sum(
                p.unrealized_pnl for p in self.positions.values() 
                if p.status == TradeStatus.OPEN
            )
            
            total_realized_pnl = sum(
                p.realized_pnl for p in self.positions.values()
            )
        
        stats = {
            'monitoring_active': self.monitoring_active,
            'total_positions': len(self.positions),
            'open_positions': open_positions,
            'closed_positions': closed_positions,
            'total_unrealized_pnl': total_unrealized_pnl,
            'total_realized_pnl': total_realized_pnl,
            'exit_stats': self.exit_stats,
            'last_update': datetime.now().isoformat()
        }
        
        # Log performance metrics
        self.enhanced_logger.log_performance_metrics(
            metrics=stats,
            metric_type="position_monitoring"
        )
        
        return stats 