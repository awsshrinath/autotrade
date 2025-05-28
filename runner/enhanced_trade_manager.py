"""
Enhanced Trade Manager
Comprehensive trade execution and management system with real-time position monitoring
Integrates with PositionMonitor for advanced exit strategies
"""

import asyncio
import datetime
import json
import os
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

from runner.position_monitor import PositionMonitor, ExitStrategy, ExitReason, TradeStatus
from runner.firestore_client import FirestoreClient
from runner.kiteconnect_manager import KiteConnectManager
from runner.logger import Logger
from runner.enhanced_logger import EnhancedLogger, LogLevel, LogCategory, create_enhanced_logger
from runner.capital.portfolio_manager import PortfolioManager, create_portfolio_manager
from runner.risk_governor import RiskGovernor
from runner.cognitive_system import CognitiveSystem, create_cognitive_system
from runner.thought_journal import DecisionType, ConfidenceLevel
from runner.cognitive_state_machine import CognitiveState, StateTransitionTrigger
from runner.metacognition import DecisionOutcome
from config.config_manager import get_trading_config


@dataclass
class TradeRequest:
    """Trade request data structure"""
    symbol: str
    strategy: str
    direction: str  # bullish/bearish
    quantity: int
    entry_price: float
    stop_loss: float
    target: float
    bot_type: str = "stock"
    paper_trade: bool = True
    trailing_stop_enabled: bool = False
    trailing_stop_distance: float = 0.0
    time_based_exit_minutes: int = 0
    partial_exit_levels: List[Tuple[float, float]] = None
    max_loss_pct: float = 5.0
    confidence_level: float = 0.5
    metadata: Dict[str, Any] = None


class EnhancedTradeManager:
    """Enhanced trade management system with comprehensive position monitoring"""
    
    def __init__(self, logger: Logger = None, kite_manager: KiteConnectManager = None, 
                 firestore_client: FirestoreClient = None, cognitive_system: CognitiveSystem = None):
        self.logger = logger
        self.kite_manager = kite_manager
        self.firestore_client = firestore_client
        
        # Initialize enhanced logger
        self.enhanced_logger = create_enhanced_logger(
            session_id=f"trade_manager_{int(time.time())}",
            enable_gcs=True,
            enable_firestore=True
        )
        
        # Configuration
        self.config = get_trading_config()
        
        # Initialize cognitive system
        self.cognitive_system = cognitive_system
        if self.cognitive_system is None:
            try:
                self.cognitive_system = create_cognitive_system(logger=self.logger)
                if self.logger:
                    self.logger.log_event("Cognitive system initialized for EnhancedTradeManager")
            except Exception as e:
                if self.logger:
                    self.logger.log_event(f"Failed to initialize cognitive system: {e}")
                self.cognitive_system = None
        
        # Initialize portfolio manager
        try:
            self.portfolio_manager = create_portfolio_manager(
                paper_trade=self.config.paper_trade,
                initial_capital=self.config.default_capital
            )
        except Exception as e:
            if self.logger:
                self.logger.log_event(f"Failed to initialize portfolio manager: {e}")
            self.portfolio_manager = None
        
        # Initialize risk governor
        self.risk_governor = RiskGovernor(
            max_daily_loss=self.config.max_daily_loss,
            max_trades=10,  # Configurable
            cutoff_time="15:20"
        )
        
        # Initialize position monitor
        self.position_monitor = PositionMonitor(
            logger=self.logger,
            firestore=self.firestore_client,
            kite_manager=self.kite_manager,
            portfolio_manager=self.portfolio_manager
        )
        
        # Strategy mapping
        self.strategy_map = {}
        
        # Trade execution stats
        self.execution_stats = {
            'total_trades': 0,
            'successful_trades': 0,
            'failed_trades': 0,
            'paper_trades': 0,
            'real_trades': 0,
            'total_pnl': 0.0
        }
        
        if self.logger:
            self.logger.log_event("EnhancedTradeManager initialized")
        
        # Enhanced logging for initialization
        self.enhanced_logger.log_event(
            "EnhancedTradeManager initialized with comprehensive logging",
            LogLevel.INFO,
            LogCategory.SYSTEM,
            data={
                'config': {
                    'paper_trade': self.config.paper_trade if self.config else True,
                    'max_daily_loss': self.config.max_daily_loss if self.config else 0,
                    'default_capital': self.config.default_capital if self.config else 0
                },
                'components': {
                    'cognitive_system': self.cognitive_system is not None,
                    'portfolio_manager': self.portfolio_manager is not None,
                    'kite_manager': self.kite_manager is not None,
                    'firestore_client': self.firestore_client is not None
                },
                'execution_stats': self.execution_stats
            },
            source="enhanced_trade_manager"
        )
    
    def start_trading_session(self):
        """Start the trading session with position monitoring"""
        try:
            # Start position monitoring
            self.position_monitor.start_monitoring()
            
            # Load any existing positions from recovery
            self.position_monitor.load_positions_from_recovery()
            
            if self.logger:
                self.logger.log_event("Trading session started with position monitoring")
                
        except Exception as e:
            if self.logger:
                self.logger.log_event(f"Error starting trading session: {e}")
    
    def stop_trading_session(self):
        """Stop the trading session and save state"""
        try:
            # Stop position monitoring
            self.position_monitor.stop_monitoring()
            
            # Emergency exit all positions if needed
            open_positions = self.position_monitor.get_positions(TradeStatus.OPEN)
            if open_positions:
                self.position_monitor.emergency_exit_all("Trading session ended")
            
            if self.logger:
                self.logger.log_event("Trading session stopped")
                
        except Exception as e:
            if self.logger:
                self.logger.log_event(f"Error stopping trading session: {e}")
    
    def execute_trade(self, trade_request: TradeRequest) -> Optional[str]:
        """
        Execute a trade with comprehensive risk management and monitoring
        
        Args:
            trade_request: TradeRequest object with trade details
            
        Returns:
            Position ID if successful, None if failed
        """
        try:
            # Enhanced logging for trade request
            self.enhanced_logger.log_event(
                f"Trade execution requested: {trade_request.symbol}",
                LogLevel.INFO,
                LogCategory.TRADE,
                data={
                    'symbol': trade_request.symbol,
                    'strategy': trade_request.strategy,
                    'direction': trade_request.direction,
                    'quantity': trade_request.quantity,
                    'entry_price': trade_request.entry_price,
                    'stop_loss': trade_request.stop_loss,
                    'target': trade_request.target,
                    'paper_trade': trade_request.paper_trade,
                    'confidence_level': trade_request.confidence_level,
                    'trailing_stop_enabled': trade_request.trailing_stop_enabled,
                    'time_based_exit_minutes': trade_request.time_based_exit_minutes
                },
                symbol=trade_request.symbol,
                strategy=trade_request.strategy,
                bot_type=trade_request.bot_type,
                source="enhanced_trade_manager"
            )
            
            # Record cognitive thought about trade decision
            if self.cognitive_system:
                thought_id = self.cognitive_system.record_thought(
                    decision=f"Executing trade for {trade_request.symbol}",
                    reasoning=f"Strategy: {trade_request.strategy}, Direction: {trade_request.direction}, "
                              f"Entry: ₹{trade_request.entry_price:.2f}, SL: ₹{trade_request.stop_loss:.2f}, "
                              f"Target: ₹{trade_request.target:.2f}",
                    decision_type=DecisionType.TRADE_ENTRY,
                    confidence=self._map_confidence_to_level(trade_request.confidence_level),
                    market_context={
                        'symbol': trade_request.symbol,
                        'entry_price': trade_request.entry_price,
                        'direction': trade_request.direction,
                        'strategy': trade_request.strategy,
                        'bot_type': trade_request.bot_type
                    },
                    strategy_id=trade_request.strategy,
                    tags=['trade_execution', trade_request.bot_type, trade_request.strategy]
                )
                
                # Transition to analyzing state
                self.cognitive_system.transition_state(
                    CognitiveState.ANALYZING,
                    StateTransitionTrigger.SIGNAL_DETECTED,
                    f"Analyzing trade execution for {trade_request.symbol}"
                )
            
            # 1. Risk checks
            if not self._perform_risk_checks(trade_request):
                return None
            
            # 2. Portfolio checks
            if not self._perform_portfolio_checks(trade_request):
                return None
            
            # 3. Execute the trade
            if trade_request.paper_trade:
                success = self._execute_paper_trade(trade_request)
            else:
                success = self._execute_real_trade(trade_request)
            
            if not success:
                self.execution_stats['failed_trades'] += 1
                
                # Enhanced logging for failed trade
                self.enhanced_logger.log_trade_execution(
                    trade_data={
                        'symbol': trade_request.symbol,
                        'strategy': trade_request.strategy,
                        'direction': trade_request.direction,
                        'quantity': trade_request.quantity,
                        'entry_price': trade_request.entry_price,
                        'bot_type': trade_request.bot_type,
                        'paper_trade': trade_request.paper_trade,
                        'failure_reason': 'execution_failed'
                    },
                    success=False
                )
                
                return None
            
            # 4. Add to position monitor
            position_id = self._add_to_position_monitor(trade_request)
            
            if position_id:
                # Update statistics
                self.execution_stats['total_trades'] += 1
                self.execution_stats['successful_trades'] += 1
                if trade_request.paper_trade:
                    self.execution_stats['paper_trades'] += 1
                else:
                    self.execution_stats['real_trades'] += 1
                
                # Update risk governor
                self.risk_governor.update_trade(0)  # Initial P&L is 0
                
                # Enhanced logging for successful trade
                self.enhanced_logger.log_trade_execution(
                    trade_data={
                        'id': position_id,
                        'symbol': trade_request.symbol,
                        'strategy': trade_request.strategy,
                        'direction': trade_request.direction,
                        'quantity': trade_request.quantity,
                        'entry_price': trade_request.entry_price,
                        'stop_loss': trade_request.stop_loss,
                        'target': trade_request.target,
                        'bot_type': trade_request.bot_type,
                        'paper_trade': trade_request.paper_trade,
                        'confidence_level': trade_request.confidence_level,
                        'trailing_stop_enabled': trade_request.trailing_stop_enabled,
                        'time_based_exit_minutes': trade_request.time_based_exit_minutes,
                        'metadata': trade_request.metadata or {}
                    },
                    success=True
                )
                
                # Store trade details in cognitive memory
                if self.cognitive_system:
                    trade_memory = f"Executed {trade_request.direction} trade for {trade_request.symbol} at ₹{trade_request.entry_price:.2f}"
                    self.cognitive_system.store_memory(
                        content=trade_memory,
                        importance=self.cognitive_system.memory.ImportanceLevel.HIGH,
                        tags=['trade_execution', trade_request.symbol, trade_request.bot_type],
                        metadata={
                            'position_id': position_id,
                            'entry_price': trade_request.entry_price,
                            'strategy': trade_request.strategy,
                            'timestamp': datetime.datetime.now().isoformat()
                        }
                    )
                
                if self.logger:
                    self.logger.log_event(
                        f"Trade executed successfully: {trade_request.symbol} "
                        f"({trade_request.direction}) Qty: {trade_request.quantity} "
                        f"Entry: ₹{trade_request.entry_price:.2f} "
                        f"Position ID: {position_id}"
                    )
                
                return position_id
            
        except Exception as e:
            self.enhanced_logger.log_error(
                error=e,
                context={
                    'trade_request': {
                        'symbol': trade_request.symbol,
                        'strategy': trade_request.strategy,
                        'direction': trade_request.direction,
                        'quantity': trade_request.quantity,
                        'entry_price': trade_request.entry_price
                    },
                    'operation': 'execute_trade'
                },
                source="enhanced_trade_manager"
            )
            
            if self.logger:
                self.logger.log_event(f"Error executing trade for {trade_request.symbol}: {e}")
            self.execution_stats['failed_trades'] += 1
            return None
    
    def _perform_risk_checks(self, trade_request: TradeRequest) -> bool:
        """Perform comprehensive risk checks"""
        try:
            # 1. Risk Governor check
            if not self.risk_governor.can_trade():
                self.enhanced_logger.log_risk_event(
                    risk_data={
                        'event': 'trade_blocked_by_risk_governor',
                        'symbol': trade_request.symbol,
                        'strategy': trade_request.strategy,
                        'reason': 'risk_governor_limits_exceeded',
                        'current_loss': self.risk_governor.total_loss,
                        'max_daily_loss': self.risk_governor.max_daily_loss,
                        'trade_count': self.risk_governor.trade_count,
                        'max_trades': self.risk_governor.max_trades
                    },
                    risk_level="high"
                )
                
                if self.logger:
                    self.logger.log_event(f"Trade blocked by RiskGovernor: {trade_request.symbol}")
                
                # Record cognitive thought about blocked trade
                if self.cognitive_system:
                    self.cognitive_system.record_thought(
                        decision="Trade blocked by risk management",
                        reasoning="RiskGovernor prevented trade execution due to risk limits",
                        decision_type=DecisionType.RISK_ASSESSMENT,
                        confidence=ConfidenceLevel.VERY_HIGH,
                        market_context={'blocked_symbol': trade_request.symbol},
                        tags=['risk_management', 'trade_blocked']
                    )
                
                return False
            
            # 2. Portfolio Manager risk check
            if self.portfolio_manager:
                trade_data = {
                    'symbol': trade_request.symbol,
                    'quantity': trade_request.quantity,
                    'price': trade_request.entry_price
                }
                
                can_trade, reason = self.portfolio_manager.risk_check_before_trade(trade_data)
                if not can_trade:
                    self.enhanced_logger.log_risk_event(
                        risk_data={
                            'event': 'trade_blocked_by_portfolio_manager',
                            'symbol': trade_request.symbol,
                            'reason': reason,
                            'trade_value': trade_request.quantity * trade_request.entry_price
                        },
                        risk_level="medium"
                    )
                    
                    if self.logger:
                        self.logger.log_event(f"Trade blocked by PortfolioManager: {reason}")
                    return False
            
            # 3. Position size validation
            position_value = trade_request.quantity * trade_request.entry_price
            if position_value < 1000:  # Minimum trade value
                self.enhanced_logger.log_risk_event(
                    risk_data={
                        'event': 'trade_blocked_minimum_value',
                        'symbol': trade_request.symbol,
                        'position_value': position_value,
                        'minimum_required': 1000
                    },
                    risk_level="low"
                )
                
                if self.logger:
                    self.logger.log_event(f"Trade value too small: ₹{position_value:.2f}")
                return False
            
            # 4. Stop loss validation
            if trade_request.direction == 'bullish':
                if trade_request.stop_loss >= trade_request.entry_price:
                    self.enhanced_logger.log_risk_event(
                        risk_data={
                            'event': 'invalid_stop_loss_bullish',
                            'symbol': trade_request.symbol,
                            'entry_price': trade_request.entry_price,
                            'stop_loss': trade_request.stop_loss
                        },
                        risk_level="medium"
                    )
                    
                    if self.logger:
                        self.logger.log_event("Invalid stop loss for bullish trade")
                    return False
            else:
                if trade_request.stop_loss <= trade_request.entry_price:
                    self.enhanced_logger.log_risk_event(
                        risk_data={
                            'event': 'invalid_stop_loss_bearish',
                            'symbol': trade_request.symbol,
                            'entry_price': trade_request.entry_price,
                            'stop_loss': trade_request.stop_loss
                        },
                        risk_level="medium"
                    )
                    
                    if self.logger:
                        self.logger.log_event("Invalid stop loss for bearish trade")
                    return False
            
            return True
            
        except Exception as e:
            self.enhanced_logger.log_error(
                error=e,
                context={
                    'operation': 'risk_checks',
                    'symbol': trade_request.symbol
                },
                source="enhanced_trade_manager"
            )
            
            if self.logger:
                self.logger.log_event(f"Error in risk checks: {e}")
            return False
    
    def _perform_portfolio_checks(self, trade_request: TradeRequest) -> bool:
        """Perform portfolio-level checks"""
        try:
            if not self.portfolio_manager:
                return True
            
            # Get position sizing recommendation
            position_info = asyncio.run(
                self.portfolio_manager.calculate_position_size(
                    symbol=trade_request.symbol,
                    price=trade_request.entry_price,
                    strategy=trade_request.strategy,
                    confidence=trade_request.confidence_level
                )
            )
            
            # Check if recommended quantity is reasonable
            recommended_qty = position_info.get('recommended_quantity', 0)
            if recommended_qty == 0:
                if self.logger:
                    self.logger.log_event(f"Portfolio manager recommends 0 quantity for {trade_request.symbol}")
                return False
            
            # Adjust quantity if needed (optional)
            if trade_request.quantity > recommended_qty * 1.5:  # Allow 50% deviation
                if self.logger:
                    self.logger.log_event(
                        f"Adjusting quantity from {trade_request.quantity} to {recommended_qty} "
                        f"based on portfolio manager recommendation"
                    )
                trade_request.quantity = recommended_qty
            
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.log_event(f"Error in portfolio checks: {e}")
            return True  # Don't block trade on portfolio check errors
    
    def _execute_paper_trade(self, trade_request: TradeRequest) -> bool:
        """Execute paper trade"""
        try:
            if self.logger:
                self.logger.log_event(
                    f"[PAPER-TRADE] Executing {trade_request.symbol} "
                    f"({trade_request.direction}) Qty: {trade_request.quantity} "
                    f"Entry: ₹{trade_request.entry_price:.2f}"
                )
            
            # For paper trading, we just log the trade
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.log_event(f"Paper trade execution failed: {e}")
            return False
    
    def _execute_real_trade(self, trade_request: TradeRequest) -> bool:
        """Execute real trade"""
        try:
            if not self.kite_manager or not self.kite_manager.get_kite_client():
                if self.logger:
                    self.logger.log_event("Kite client not available for real trade")
                return False
            
            kite = self.kite_manager.get_kite_client()
            
            # Determine transaction type
            transaction_type = "BUY" if trade_request.direction == 'bullish' else "SELL"
            
            # Place market order
            order_params = {
                'tradingsymbol': trade_request.symbol,
                'exchange': 'NSE',
                'transaction_type': transaction_type,
                'quantity': trade_request.quantity,
                'order_type': 'MARKET',
                'product': 'MIS',  # Intraday
                'validity': 'DAY'
            }
            
            order_id = kite.place_order(**order_params)
            
            if self.logger:
                self.logger.log_event(
                    f"[REAL-TRADE] Order placed for {trade_request.symbol} "
                    f"Order ID: {order_id} | Qty: {trade_request.quantity}"
                )
            
            # Store order ID in metadata
            if trade_request.metadata is None:
                trade_request.metadata = {}
            trade_request.metadata['order_id'] = order_id
            
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.log_event(f"Real trade execution failed: {e}")
            return False
    
    def _add_to_position_monitor(self, trade_request: TradeRequest) -> Optional[str]:
        """Add trade to position monitor"""
        try:
            # Create trade data for position monitor
            trade_data = {
                'symbol': trade_request.symbol,
                'strategy': trade_request.strategy,
                'bot_type': trade_request.bot_type,
                'direction': trade_request.direction,
                'quantity': trade_request.quantity,
                'entry_price': trade_request.entry_price,
                'stop_loss': trade_request.stop_loss,
                'target': trade_request.target,
                'paper_trade': trade_request.paper_trade,
                'timestamp': datetime.datetime.now().isoformat(),
                'trailing_stop_enabled': trade_request.trailing_stop_enabled,
                'trailing_stop_distance': trade_request.trailing_stop_distance,
                'time_based_exit_minutes': trade_request.time_based_exit_minutes,
                'partial_exit_levels': trade_request.partial_exit_levels or [],
                'max_loss_pct': trade_request.max_loss_pct,
                'confidence_level': trade_request.confidence_level,
                'metadata': trade_request.metadata or {}
            }
            
            # Add to position monitor
            position_id = self.position_monitor.add_position(trade_data)
            
            return position_id
            
        except Exception as e:
            if self.logger:
                self.logger.log_event(f"Error adding to position monitor: {e}")
            return None
    
    def manual_exit_position(self, position_id: str, exit_percentage: float = 100.0) -> bool:
        """Manually exit a position"""
        return self.position_monitor.manual_exit_position(position_id, exit_percentage)
    
    def move_position_to_breakeven(self, position_id: str) -> bool:
        """Move position stop loss to breakeven"""
        return self.position_monitor.move_to_breakeven(position_id)
    
    def enable_trailing_stop(self, position_id: str, distance: float, trigger_price: float = None) -> bool:
        """Enable trailing stop for a position"""
        return self.position_monitor.enable_trailing_stop(position_id, distance, trigger_price)
    
    def get_active_positions(self) -> List[Dict[str, Any]]:
        """Get all active positions"""
        return self.position_monitor.get_positions(TradeStatus.OPEN)
    
    def get_closed_positions(self) -> List[Dict[str, Any]]:
        """Get all closed positions"""
        return self.position_monitor.get_positions(TradeStatus.CLOSED)
    
    def get_position_details(self, position_id: str) -> Optional[Dict[str, Any]]:
        """Get details of a specific position"""
        return self.position_monitor.get_position(position_id)
    
    def emergency_exit_all_positions(self, reason: str = "Emergency exit"):
        """Emergency exit all open positions"""
        self.position_monitor.emergency_exit_all(reason)
    
    def get_trading_stats(self) -> Dict[str, Any]:
        """Get comprehensive trading statistics"""
        monitor_stats = self.position_monitor.get_monitoring_stats()
        
        stats = {
            'execution_stats': self.execution_stats,
            'monitoring_stats': monitor_stats,
            'risk_governor_stats': {
                'can_trade': self.risk_governor.can_trade(),
                'total_loss': self.risk_governor.total_loss,
                'trade_count': self.risk_governor.trade_count,
                'max_daily_loss': self.risk_governor.max_daily_loss,
                'max_trades': self.risk_governor.max_trades
            },
            'portfolio_stats': self._get_portfolio_stats(),
            'last_update': datetime.datetime.now().isoformat()
        }
        
        # Enhanced logging for trading statistics
        self.enhanced_logger.log_performance_metrics(
            metrics=stats,
            metric_type="comprehensive_trading_stats"
        )
        
        return stats
    
    def _get_portfolio_stats(self) -> Dict[str, Any]:
        """Get portfolio statistics"""
        try:
            if self.portfolio_manager:
                capital_data = asyncio.run(self.portfolio_manager.get_real_time_capital())
                return {
                    'total_capital': capital_data.total_capital,
                    'available_cash': capital_data.available_cash,
                    'used_margin': capital_data.used_margin,
                    'day_pnl': capital_data.day_pnl,
                    'margin_utilization': capital_data.margin_utilization,
                    'is_mock': capital_data.is_mock
                }
            else:
                return {'error': 'Portfolio manager not available'}
        except Exception as e:
            return {'error': str(e)}
    
    def _map_confidence_to_level(self, confidence: float) -> ConfidenceLevel:
        """Map confidence score to ConfidenceLevel enum"""
        if confidence >= 0.8:
            return ConfidenceLevel.VERY_HIGH
        elif confidence >= 0.65:
            return ConfidenceLevel.HIGH
        elif confidence >= 0.4:
            return ConfidenceLevel.MEDIUM
        elif confidence >= 0.2:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.VERY_LOW
    
    def analyze_trade_outcome(self, position_id: str):
        """Analyze trade outcome using cognitive system"""
        if not self.cognitive_system:
            return
        
        try:
            position_data = self.get_position_details(position_id)
            if not position_data or position_data['status'] != 'closed':
                return
            
            # Determine outcome
            realized_pnl = position_data.get('realized_pnl', 0)
            exit_reason = position_data.get('exit_reason')
            
            if exit_reason == 'target_hit':
                outcome = DecisionOutcome.SUCCESS
            elif exit_reason == 'stop_loss_hit':
                outcome = DecisionOutcome.FAILURE
            elif realized_pnl > 0:
                outcome = DecisionOutcome.PARTIAL_SUCCESS
            else:
                outcome = DecisionOutcome.FAILURE
            
            # Calculate time to outcome
            entry_time = datetime.datetime.fromisoformat(position_data['entry_time'])
            exit_time = datetime.datetime.fromisoformat(position_data['exit_time'])
            time_to_outcome = (exit_time - entry_time).total_seconds() / 60  # minutes
            
            # Analyze the decision
            self.cognitive_system.analyze_decision(
                decision_id=position_id,
                decision_type='trade_entry',
                initial_confidence=position_data.get('confidence_level', 0.5),
                actual_outcome=outcome,
                profit_loss=realized_pnl,
                strategy_used=position_data.get('strategy', 'unknown'),
                market_context=position_data,
                time_to_outcome=time_to_outcome
            )
            
            # Record reflection thought
            self.cognitive_system.record_thought(
                decision=f"Trade completed for {position_data.get('symbol')}",
                reasoning=f"Trade outcome: {outcome.value}, P&L: ₹{realized_pnl:.2f}, "
                          f"Duration: {time_to_outcome:.0f} minutes, Reason: {exit_reason}",
                decision_type=DecisionType.PERFORMANCE_REVIEW,
                confidence=ConfidenceLevel.HIGH,
                market_context=position_data,
                trade_id=position_id,
                tags=['trade_completion', 'performance_review', position_data.get('symbol', 'unknown')]
            )
            
        except Exception as e:
            if self.logger:
                self.logger.log_event(f"Failed to analyze trade outcome for {position_id}: {e}")
    
    def run_strategy_once(self, strategy_name: str, direction: str, bot_type: str) -> Optional[str]:
        """
        Run a strategy once and execute a trade if a signal is generated
        
        Args:
            strategy_name: Name of the strategy to run
            direction: Direction preference (bullish/bearish)
            bot_type: Type of bot (stock/options/futures)
            
        Returns:
            Position ID if trade executed, None otherwise
        """
        try:
            # Record cognitive thought about strategy selection
            if self.cognitive_system:
                self.cognitive_system.record_thought(
                    decision=f"Running {strategy_name} strategy for {bot_type}",
                    reasoning=f"Selected {strategy_name} strategy with {direction} direction for {bot_type} bot",
                    decision_type=DecisionType.STRATEGY_SELECTION,
                    confidence=ConfidenceLevel.MEDIUM,
                    market_context={
                        'strategy': strategy_name,
                        'direction': direction,
                        'bot_type': bot_type
                    },
                    tags=['strategy_execution', strategy_name, bot_type]
                )
            
            if strategy_name not in self.strategy_map:
                if self.logger:
                    self.logger.log_event(f"Strategy {strategy_name} not found in strategy map")
                return None
            
            # Get the strategy function
            strategy_func = self.strategy_map[strategy_name]
            
            # Run the strategy to get a trade signal
            trade_signal = strategy_func(symbol=bot_type, direction=direction)
            
            if not trade_signal:
                if self.logger:
                    self.logger.log_event(f"No trade signal generated by {strategy_name}")
                return None
            
            # Convert trade signal to TradeRequest
            trade_request = TradeRequest(
                symbol=trade_signal.get('symbol', 'UNKNOWN'),
                strategy=strategy_name,
                direction=trade_signal.get('direction', direction),
                quantity=trade_signal.get('quantity', 1),
                entry_price=trade_signal.get('entry_price', 0),
                stop_loss=trade_signal.get('stop_loss', 0),
                target=trade_signal.get('target', 0),
                bot_type=bot_type,
                paper_trade=self.config.paper_trade,
                confidence_level=trade_signal.get('confidence', 0.5),
                trailing_stop_enabled=trade_signal.get('trailing_stop_enabled', False),
                trailing_stop_distance=trade_signal.get('trailing_stop_distance', 0),
                time_based_exit_minutes=trade_signal.get('time_based_exit_minutes', 0),
                partial_exit_levels=trade_signal.get('partial_exit_levels', []),
                max_loss_pct=trade_signal.get('max_loss_pct', 5.0)
            )
            
            # Execute the trade
            position_id = self.execute_trade(trade_request)
            
            return position_id
            
        except Exception as e:
            if self.logger:
                self.logger.log_event(f"Error running strategy {strategy_name}: {e}")
            return None
    
    def load_strategy(self, strategy_name: str):
        """Load a strategy into the strategy map"""
        # This would be implemented to load actual strategy functions
        # For now, it's a placeholder
        if self.logger:
            self.logger.log_event(f"Strategy {strategy_name} loaded")
    
    def start_trading(self, strategy_name: str, market_data_fetcher):
        """Start trading with a specific strategy"""
        try:
            # Start the trading session
            self.start_trading_session()
            
            # Load the strategy
            self.load_strategy(strategy_name)
            
            if self.logger:
                self.logger.log_event(f"Started trading with strategy: {strategy_name}")
                
        except Exception as e:
            if self.logger:
                self.logger.log_event(f"Error starting trading: {e}")


# Factory function for creating enhanced trade manager
def create_enhanced_trade_manager(logger: Logger = None, kite_manager: KiteConnectManager = None,
                                 firestore_client: FirestoreClient = None) -> EnhancedTradeManager:
    """Create an enhanced trade manager instance"""
    return EnhancedTradeManager(
        logger=logger,
        kite_manager=kite_manager,
        firestore_client=firestore_client
    ) 