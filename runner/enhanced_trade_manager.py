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
import traceback
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
                self.cognitive_system.record_thought(
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
                self.cognitive_system.transition_state(
                    CognitiveState.ANALYZING,
                    StateTransitionTrigger.SIGNAL_DETECTED,
                    f"Analyzing trade execution for {trade_request.symbol}"
                )
            
            if not self._perform_risk_checks(trade_request):
                return None
            
            if not self._perform_portfolio_checks(trade_request):
                return None
            
            if trade_request.paper_trade:
                success = self._execute_paper_trade(trade_request)
            else:
                success = self._execute_real_trade(trade_request)
            
            if not success:
                self.execution_stats['failed_trades'] += 1
                return None
            
            position_id = self._add_to_position_monitor(trade_request)
            
            if position_id:
                self.execution_stats['total_trades'] += 1
                self.execution_stats['successful_trades'] += 1
                if trade_request.paper_trade:
                    self.execution_stats['paper_trades'] += 1
                else:
                    self.execution_stats['real_trades'] += 1
                return position_id
            
            return None
            
        except Exception as e:
            self.enhanced_logger.log_error(
                f"Critical error in trade execution for {trade_request.symbol}",
                error=str(e),
                source="enhanced_trade_manager"
            )
            if self.logger:
                self.logger.log_event(f"Critical trade execution error: {e}")
            return None

    def _execute_paper_trade(self, trade_request: TradeRequest) -> bool:
        """Simulate a paper trade"""
        try:
            self.enhanced_logger.log_event(
                "Paper trade executed successfully",
                LogLevel.INFO,
                LogCategory.TRADE,
                data={
                    'symbol': trade_request.symbol,
                    'strategy': trade_request.strategy,
                    'quantity': trade_request.quantity,
                    'entry_price': trade_request.entry_price,
                    'mode': 'paper'
                },
                symbol=trade_request.symbol,
                strategy=trade_request.strategy,
                bot_type=trade_request.bot_type
            )
            return True
        except Exception as e:
            if self.logger:
                self.logger.log_event(f"Error in paper trade simulation for {trade_request.symbol}: {e}")
            return False

    def _execute_real_trade(self, trade_request: TradeRequest) -> bool:
        """Execute a real trade using KiteConnect"""
        try:
            if not self.kite_manager or not self.kite_manager.get_kite_client():
                raise ConnectionError("KiteConnect client not initialized.")
            
            kite = self.kite_manager.get_kite_client()
            
            order_params = {
                "tradingsymbol": trade_request.symbol,
                "exchange": "NFO" if trade_request.bot_type == "options" else "NSE",
                "transaction_type": "BUY" if trade_request.direction == "bullish" else "SELL",
                "quantity": trade_request.quantity,
                "product": "MIS",
                "order_type": "LIMIT",
                "price": trade_request.entry_price,
                "validity": "DAY"
            }
            
            order_id = kite.place_order(**order_params)
            
            if self.logger:
                self.logger.log_event(f"Real trade executed for {trade_request.symbol}, Order ID: {order_id}")
            
            self.enhanced_logger.log_event(
                "Real trade executed successfully",
                LogLevel.INFO,
                LogCategory.TRADE,
                data={'order_id': order_id, **order_params, 'mode': 'live'},
                symbol=trade_request.symbol,
                strategy=trade_request.strategy
            )
            return True
        
        except Exception as e:
            if self.logger:
                self.logger.log_event(f"Real trade execution failed for {trade_request.symbol}: {e}")
            
            self.enhanced_logger.log_error(
                "Real trade execution failed",
                error=str(e),
                data={'symbol': trade_request.symbol, 'strategy': trade_request.strategy}
            )
            return False

    def _add_to_position_monitor(self, trade_request: TradeRequest) -> Optional[str]:
        """Add executed trade to position monitor"""
        try:
            exit_strategy = ExitStrategy(
                stop_loss_price=trade_request.stop_loss,
                target_price=trade_request.target,
                trailing_stop_enabled=trade_request.trailing_stop_enabled,
                trailing_stop_distance=trade_request.trailing_stop_distance,
                time_based_exit_minutes=trade_request.time_based_exit_minutes,
                partial_exit_levels=trade_request.partial_exit_levels
            )
            
            position_id = self.position_monitor.add_position(
                symbol=trade_request.symbol,
                quantity=trade_request.quantity,
                entry_price=trade_request.entry_price,
                direction=trade_request.direction,
                exit_strategy=exit_strategy,
                strategy_name=trade_request.strategy,
                bot_type=trade_request.bot_type
            )
            
            return position_id
        
        except Exception as e:
            if self.logger:
                self.logger.log_event(f"Failed to add position to monitor: {e}")
            return None
    
    def manual_exit_position(self, position_id: str, exit_percentage: float = 100.0) -> bool:
        """Manually exit a position"""
        return self.position_monitor.exit_position(position_id, ExitReason.MANUAL, exit_percentage)

    def move_position_to_breakeven(self, position_id: str) -> bool:
        """Move SL to breakeven"""
        return self.position_monitor.move_to_breakeven(position_id)

    def enable_trailing_stop(self, position_id: str, distance: float, trigger_price: float = None) -> bool:
        """Enable or update trailing stop"""
        return self.position_monitor.enable_trailing_stop(position_id, distance, trigger_price)

    def get_active_positions(self) -> List[Dict[str, Any]]:
        """Get all active positions"""
        return self.position_monitor.get_positions(status=TradeStatus.OPEN)
    
    def get_closed_positions(self) -> List[Dict[str, Any]]:
        """Get all closed positions"""
        return self.position_monitor.get_positions(status=TradeStatus.CLOSED)

    def get_position_details(self, position_id: str) -> Optional[Dict[str, Any]]:
        """Get details for a specific position"""
        return self.position_monitor.get_position(position_id)

    def emergency_exit_all_positions(self, reason: str = "Emergency exit"):
        """Emergency exit all positions"""
        self.position_monitor.emergency_exit_all(reason)

    def get_trading_stats(self) -> Dict[str, Any]:
        """Get trading statistics"""
        portfolio_stats = self._get_portfolio_stats()
        
        return {
            **self.execution_stats,
            'open_positions': len(self.get_active_positions()),
            'closed_positions': len(self.get_closed_positions()),
            'realized_pnl': portfolio_stats.get('realized_pnl', 0),
            'unrealized_pnl': portfolio_stats.get('unrealized_pnl', 0),
            'total_pnl_pct': portfolio_stats.get('total_pnl_pct', 0),
            'portfolio_value': portfolio_stats.get('portfolio_value', 0)
        }

    def _get_portfolio_stats(self) -> Dict[str, Any]:
        """Get portfolio statistics"""
        if self.portfolio_manager:
            return self.portfolio_manager.get_portfolio_summary()
        return {}

    def _map_confidence_to_level(self, confidence: float) -> ConfidenceLevel:
        """Map a float confidence score to a ConfidenceLevel enum"""
        if confidence >= 0.8:
            return ConfidenceLevel.HIGH
        elif confidence >= 0.5:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW

    def analyze_trade_outcome(self, position_id: str):
        """Analyze the outcome of a trade using the cognitive system"""
        if not self.cognitive_system:
            return
        
        position = self.get_position_details(position_id)
        if not position or position.get('status') != TradeStatus.CLOSED:
            return
            
        outcome = DecisionOutcome.PROFITABLE if position.get('pnl', 0) > 0 else DecisionOutcome.LOSS_MAKING
        
        self.cognitive_system.metacognition.reflect_on_decision(
            decision_id=position.get('thought_id'),
            outcome=outcome,
            feedback=f"Trade closed with P&L: {position.get('pnl')}"
        )

    def run_strategy_once(self, strategy_name: str, direction: str, bot_type: str) -> Optional[str]:
        """
        Run a single trading strategy cycle.
        This is a placeholder for a more complex signal-driven system.
        """
        # In a real system, you'd get these values from a strategy module
        trade_params = {
            "symbol": "BANKNIFTY24JUL49000CE",
            "quantity": 15,
            "entry_price": 250.0,
            "stop_loss": 230.0,
            "target": 280.0
        }
        
        trade_request = TradeRequest(
            symbol=trade_params["symbol"],
            strategy=strategy_name,
            direction=direction,
            quantity=trade_params["quantity"],
            entry_price=trade_params["entry_price"],
            stop_loss=trade_params["stop_loss"],
            target=trade_params["target"],
            bot_type=bot_type,
            paper_trade=self.config.paper_trade
        )
        
        return self.execute_trade(trade_request)

    def load_strategy(self, strategy_name: str):
        """Dynamically load a strategy module"""
        pass  # Placeholder

    def start_trading(self, strategy_name: str, market_data_fetcher):
        """Main trading loop for a given strategy"""
        pass # Placeholder

def create_enhanced_trade_manager(logger: Logger = None, kite_manager: KiteConnectManager = None,
                                 firestore_client: FirestoreClient = None, cognitive_system: CognitiveSystem = None) -> EnhancedTradeManager:
    """Factory function for EnhancedTradeManager"""
    return EnhancedTradeManager(
        logger=logger, 
        kite_manager=kite_manager, 
        firestore_client=firestore_client,
        cognitive_system=cognitive_system
    ) 