import datetime
import json
import os
import time
from typing import Dict, Any, Optional, List
from dataclasses import asdict

# Import configuration
from runner.config import PAPER_TRADE, get_config

# Import new optimized logging system
try:
    from runner.enhanced_logging import TradingLogger, LogLevel, LogCategory
    from runner.enhanced_logging.log_types import TradeLogData, ErrorLogData
    NEW_LOGGING_AVAILABLE = True
except ImportError:
    NEW_LOGGING_AVAILABLE = False

# Legacy imports
from runner.risk_governor import RiskGovernor
from runner.cognitive_system import CognitiveSystem
from runner.cognitive_state_machine import CognitiveState, StateTransitionTrigger
from runner.thought_journal import DecisionType, ConfidenceLevel

# Initialize risk governor with default values
risk_guard = None  # Initialize later in TradeManager __init__


class TradeManager:
    def __init__(self, logger=None, kite=None, firestore_client=None, cognitive_system=None, 
                 max_daily_loss=5000, max_trades=10, cutoff_time="15:00"):
        self.logger = logger
        self.kite = kite
        self.firestore_client = firestore_client
        self.cognitive_system = cognitive_system
        self.open_positions = []
        
        # Get paper trading configuration
        self.paper_trade_mode = PAPER_TRADE
        
        # Initialize risk governor with proper parameters
        self.risk_guard = RiskGovernor(
            max_daily_loss=max_daily_loss,
            max_trades=max_trades,
            cutoff_time=cutoff_time
        )
        
        # Initialize new optimized logger if available
        if NEW_LOGGING_AVAILABLE:
            self.trading_logger = TradingLogger(
                session_id=f"trade_manager_{int(datetime.datetime.now().timestamp())}",
                bot_type="trade-manager"
            )
            self.use_new_logging = True
        else:
            self.use_new_logging = False
        
        if self.logger:
            self.logger.log_event(f"TradeManager initialized - Paper Trade Mode: {self.paper_trade_mode}")

    def run_strategy_once(self, strategy_name, direction, bot_type):
        """
        Run a strategy once and return the trade result.
        
        Args:
            strategy_name: Name of the strategy to run
            direction: Trading direction (bullish/bearish)
            bot_type: Type of bot (stock-trader, options-trader, etc.)
        
        Returns:
            Trade object if successful, None otherwise
        """
        try:
            # Import strategy dynamically
            if strategy_name == "orb":
                from strategies.orb_strategy import ORBStrategy
                strategy = ORBStrategy(self.kite, self.logger)
            elif strategy_name == "range_reversal":
                from strategies.range_reversal_strategy import RangeReversalStrategy
                strategy = RangeReversalStrategy(self.kite, self.logger)
            elif strategy_name == "vwap":
                from strategies.vwap_strategy import VWAPStrategy
                strategy = VWAPStrategy(self.kite, self.logger)
            else:
                error_msg = f"Unknown strategy: {strategy_name}"
                if self.logger:
                    self.logger.log_event(error_msg)
                
                # Log error with new system
                if self.use_new_logging:
                    self.trading_logger.log_error(
                        ValueError(error_msg),
                        context={'strategy_name': strategy_name, 'direction': direction, 'bot_type': bot_type},
                        source="trade_manager"
                    )
                
                return None

            # Transition to analyzing state
            if self.cognitive_system:
                self.cognitive_system.transition_state(
                    CognitiveState.ANALYZING,
                    StateTransitionTrigger.NEW_DATA_AVAILABLE,
                    f"Analyzing {strategy_name} strategy for {direction} {bot_type}"
                )

            # Generate trade signal
            trade_signal = strategy.analyze()

            # Record cognitive thought about strategy analysis
            if self.cognitive_system:
                thought_id = self.cognitive_system.record_thought(
                    decision=f"Strategy analysis completed for {strategy_name}",
                    reasoning=f"Analyzed {strategy_name} strategy for {direction} direction in {bot_type} context",
                    decision_type=DecisionType.MARKET_ANALYSIS,
                    confidence=ConfidenceLevel.MEDIUM,
                    market_context={
                        'strategy': strategy_name,
                        'direction': direction,
                        'bot_type': bot_type,
                        'signal_generated': trade_signal is not None
                    },
                    tags=['strategy_analysis', strategy_name, direction]
                )

        except Exception as e:
            error_msg = f"Error running strategy {strategy_name}: {e}"
            if self.logger:
                self.logger.log_event(error_msg)
            
            # Log error with new system
            if self.use_new_logging:
                self.trading_logger.log_error(
                    e,
                    context={'strategy_name': strategy_name, 'direction': direction, 'bot_type': bot_type},
                    source="trade_manager"
                )
            
            return None

        if not trade_signal:
            if self.logger:
                self.logger.log_event(
                    f"[INFO] No trade signal generated by {strategy_name}"
                )
            
            # Log strategy signal result with new system
            if self.use_new_logging:
                self.trading_logger.log_strategy_signal(
                    strategy=strategy_name,
                    symbol="N/A",
                    signal_data={
                        'result': 'no_signal',
                        'direction': direction,
                        'bot_type': bot_type,
                        'timestamp': datetime.datetime.now().isoformat()
                    }
                )
            
            # Record cognitive thought about no signal
            if self.cognitive_system:
                self.cognitive_system.record_thought(
                    decision="No trade signal generated",
                    reasoning=f"{strategy_name} did not produce actionable signal for {direction} {bot_type}",
                    decision_type=DecisionType.MARKET_ANALYSIS,
                    confidence=ConfidenceLevel.MEDIUM,
                    market_context={
                        'strategy': strategy_name,
                        'direction': direction,
                        'bot_type': bot_type,
                        'signal_result': 'no_signal'
                    },
                    tags=['no_signal', strategy_name]
                )
                
                # Transition back to observing
                self.cognitive_system.transition_state(
                    CognitiveState.OBSERVING,
                    StateTransitionTrigger.NEW_DATA_AVAILABLE,
                    "No signal generated, resuming observation"
                )
            
            return None

        # Execute the trade
        trade = self._execute_trade(trade_signal, bot_type, strategy_name)

        # Track the open position
        if trade:
            self.open_positions.append(trade)

        return trade

    def _execute_trade(self, trade_signal, bot_type, strategy_name=None):
        """
        Execute a trade based on the signal - routes to paper or live trading based on configuration.
        
        Args:
            trade_signal: Dictionary containing trade parameters
            bot_type: Type of bot executing the trade
            strategy_name: Name of the strategy that generated the signal
        
        Returns:
            Trade object if successful, None otherwise
        """
        try:
            # Determine trading mode
            if self.paper_trade_mode:
                return self._execute_paper_trade(trade_signal, bot_type, strategy_name)
            else:
                return self._execute_live_trade(trade_signal, bot_type, strategy_name)
                
        except Exception as e:
            error_msg = f"Error executing trade: {e}"
            if self.logger:
                self.logger.log_event(error_msg)
            
            # Log error with new system
            if self.use_new_logging:
                self.trading_logger.log_error(
                    e,
                    context={'trade_signal': trade_signal, 'bot_type': bot_type, 'strategy': strategy_name},
                    source="trade_execution"
                )
            
            return None

    def _execute_paper_trade(self, trade_signal, bot_type, strategy_name):
        """Execute a paper trade simulation"""
        try:
            # Create trade object for paper trading
            trade = {
                'id': f"paper_{int(datetime.datetime.now().timestamp())}",
                'symbol': trade_signal.get('symbol'),
                'strategy': strategy_name,
                'bot_type': bot_type,
                'direction': trade_signal.get('direction'),
                'quantity': trade_signal.get('quantity', 1),
                'entry_price': trade_signal.get('entry_price'),
                'stop_loss': trade_signal.get('stop_loss'),
                'target': trade_signal.get('target'),
                'entry_time': datetime.datetime.now().isoformat(),
                'status': 'paper_open',
                'mode': 'paper'
            }
            
            # Simulate trade execution
            if self.logger:
                self.logger.log_event(
                    f"[PAPER TRADE] Executing {trade['symbol']} - {trade['direction']} @ ₹{trade['entry_price']}"
                )
            
            # Log paper trade with enhanced logger and trigger GCS upload
            if self.use_new_logging:
                try:
                    trade_log_data = TradeLogData(
                        trade_id=trade['id'],
                        symbol=trade['symbol'],
                        strategy=strategy_name,
                        bot_type=bot_type,
                        direction=trade['direction'],
                        quantity=trade['quantity'],
                        entry_price=trade['entry_price'],
                        stop_loss=trade['stop_loss'],
                        target=trade['target'],
                        status="paper_open",
                        entry_time=datetime.datetime.now(),
                        metadata={'mode': 'paper', 'simulated': True}
                    )
                    
                    self.trading_logger.log_trade_entry(trade_log_data)
                    
                    # Force upload to GCS for paper trades
                    self.trading_logger.force_upload_to_gcs()
                    
                except Exception as e:
                    if self.logger:
                        self.logger.log_event(f"Error logging paper trade: {e}")
            
            # Record cognitive thought about paper trade
            if self.cognitive_system:
                self.cognitive_system.record_thought(
                    decision=f"Paper trade executed for {trade['symbol']}",
                    reasoning=f"Simulated {trade['direction']} trade based on {strategy_name} strategy",
                    decision_type=DecisionType.TRADE_EXECUTION,
                    confidence=ConfidenceLevel.HIGH,
                    market_context=trade,
                    trade_id=trade['id'],
                    tags=['paper_trade', 'execution', strategy_name]
                )
            
            # Log to local file for paper trades
            self._log_paper_trade_to_file(trade)
            
            return trade
            
        except Exception as e:
            if self.logger:
                self.logger.log_event(f"Error executing paper trade: {e}")
            return None

    def _execute_live_trade(self, trade_signal, bot_type, strategy_name):
        """Execute a live trade (existing implementation)"""
        # Existing live trade implementation would go here
        if self.logger:
            self.logger.log_event("Live trading not implemented in this version")
        return None

    def _log_paper_trade_to_file(self, trade):
        """Log paper trade to local file"""
        try:
            log_path = f"logs/paper_trades_{datetime.datetime.now().strftime('%Y-%m-%d')}.jsonl"
            os.makedirs("logs", exist_ok=True)
            
            with open(log_path, "a") as f:
                f.write(json.dumps(trade) + "\n")
                
        except Exception as e:
            if self.logger:
                self.logger.log_event(f"Error logging paper trade to file: {e}")

    def simulate_trade_exit(self, trade, market_data):
        """Simulate trade exit based on market data"""
        try:
            if not trade or trade.get('status') != 'paper_open':
                return
            
            current_price = market_data.get(trade['symbol'], {}).get('ltp')
            if not current_price:
                return
            
            direction = trade['direction']
            entry_price = trade['entry_price']
            stop_loss = trade['stop_loss']
            target = trade['target']
            
            # Check exit conditions
            exit_triggered = False
            exit_reason = ""
            exit_price = current_price
            
            if direction == 'bullish':
                if current_price >= target:
                    exit_triggered = True
                    exit_reason = "target_hit"
                    exit_price = target
                elif current_price <= stop_loss:
                    exit_triggered = True
                    exit_reason = "stop_loss"
                    exit_price = stop_loss
            else:  # bearish
                if current_price <= target:
                    exit_triggered = True
                    exit_reason = "target_hit"
                    exit_price = target
                elif current_price >= stop_loss:
                    exit_triggered = True
                    exit_reason = "stop_loss"
                    exit_price = stop_loss
            
            if exit_triggered:
                # Update trade with exit details
                trade['status'] = 'paper_closed'
                trade['exit_price'] = exit_price
                trade['exit_time'] = datetime.datetime.now().isoformat()
                trade['exit_reason'] = exit_reason
                
                # Calculate P&L
                if direction == 'bullish':
                    pnl = (exit_price - entry_price) * trade['quantity']
                else:
                    pnl = (entry_price - exit_price) * trade['quantity']
                
                trade['pnl'] = round(pnl, 2)
                
                # Log exit
                if self.logger:
                    self.logger.log_event(
                        f"[PAPER EXIT] {trade['symbol']} - {exit_reason} @ ₹{exit_price} | P&L: ₹{pnl:.2f}"
                    )
                
                # Log with enhanced logger and upload to GCS
                if self.use_new_logging:
                    try:
                        trade_log_data = TradeLogData(
                            trade_id=trade['id'],
                            symbol=trade['symbol'],
                            strategy=trade['strategy'],
                            bot_type=trade['bot_type'],
                            direction=trade['direction'],
                            quantity=trade['quantity'],
                            entry_price=trade['entry_price'],
                            stop_loss=trade['stop_loss'],
                            target=trade['target'],
                            exit_price=exit_price,
                            status="paper_closed",
                            pnl=pnl,
                            entry_time=datetime.datetime.fromisoformat(trade['entry_time']),
                            exit_time=datetime.datetime.now(),
                            exit_reason=exit_reason,
                            metadata={'mode': 'paper', 'simulated': True}
                        )
                        
                        self.trading_logger.log_trade_exit(trade_log_data, exit_reason)
                        
                        # Force upload to GCS for paper trade exits
                        self.trading_logger.force_upload_to_gcs()
                        
                    except Exception as e:
                        if self.logger:
                            self.logger.log_event(f"Error logging paper trade exit: {e}")
                
                # Log to file
                self._log_paper_trade_to_file(trade)
                
                return trade
                
        except Exception as e:
            if self.logger:
                self.logger.log_event(f"Error simulating trade exit: {e}")
                
        return None

    def analyze_trade_outcome(self, trade):
        """Analyze trade outcome using cognitive system"""
        if not self.cognitive_system:
            return
        
        try:
            # Determine outcome
            pnl = trade.get('pnl', 0)
            if pnl > 0:
                outcome = self.cognitive_system.decision_analysis.TradeOutcome.PROFIT
            elif pnl < 0:
                outcome = self.cognitive_system.decision_analysis.TradeOutcome.LOSS
            else:
                outcome = self.cognitive_system.decision_analysis.TradeOutcome.BREAKEVEN
            
            # Get initial confidence
            initial_confidence = trade.get('confidence_level')
            if isinstance(initial_confidence, str):
                confidence_map = {
                    'VERY_LOW': 0.1, 'LOW': 0.3, 'MEDIUM': 0.5, 
                    'HIGH': 0.7, 'VERY_HIGH': 0.9
                }
                initial_confidence = confidence_map.get(initial_confidence, 0.5)
            elif initial_confidence is None:
                initial_confidence = 0.5
            
            # Calculate time to outcome
            entry_time = trade.get('entry_time')
            exit_time = trade.get('exit_time')
            time_to_outcome = 0
            if entry_time and exit_time:
                if isinstance(entry_time, str):
                    entry_time = datetime.datetime.fromisoformat(entry_time)
                if isinstance(exit_time, str):
                    exit_time = datetime.datetime.fromisoformat(exit_time)
                time_to_outcome = (exit_time - entry_time).total_seconds() / 60  # minutes
            
            # Analyze the decision
            analysis_id = self.cognitive_system.analyze_decision(
                decision_id=trade.get('cognitive_thought_id', 'unknown'),
                decision_type='trade_entry',
                initial_confidence=initial_confidence,
                actual_outcome=outcome,
                profit_loss=trade.get('pnl', 0),
                strategy_used=trade.get('strategy', 'unknown'),
                market_context={
                    'symbol': trade.get('symbol'),
                    'entry_price': trade.get('entry_price'),
                    'exit_price': trade.get('exit_price'),
                    'direction': trade.get('direction'),
                    'bot_type': trade.get('bot_type')
                },
                time_to_outcome=time_to_outcome
            )
            
            # Log trade outcome with new system
            if self.use_new_logging:
                try:
                    trade_log_data = TradeLogData(
                        trade_id=trade.get('id', f"trade_{int(datetime.datetime.now().timestamp())}"),
                        symbol=trade.get('symbol', 'UNKNOWN'),
                        strategy=trade.get('strategy', 'unknown'),
                        bot_type=trade.get('bot_type', 'unknown'),
                        direction=trade.get('direction', 'unknown'),
                        quantity=trade.get('quantity', 0),
                        entry_price=trade.get('entry_price', 0.0),
                        stop_loss=trade.get('stop_loss'),
                        target=trade.get('target'),
                        exit_price=trade.get('exit_price'),
                        status="closed",
                        pnl=trade.get('pnl'),
                        entry_time=datetime.datetime.fromisoformat(trade.get('entry_time')) if trade.get('entry_time') else None,
                        exit_time=datetime.datetime.fromisoformat(trade.get('exit_time')) if trade.get('exit_time') else None,
                        exit_reason=trade.get('exit_reason'),
                        confidence_level=trade.get('confidence'),
                        metadata={
                            'analysis_id': analysis_id,
                            'outcome': outcome.value if hasattr(outcome, 'value') else str(outcome),
                            'time_to_outcome_minutes': time_to_outcome
                        }
                    )
                    
                    self.trading_logger.log_trade_exit(trade_log_data, trade.get('exit_reason', 'Unknown'))
                    
                except Exception as e:
                    if self.logger:
                        self.logger.log_event(f"Error logging trade outcome with new system: {e}")
            
            # Record reflection thought
            self.cognitive_system.record_thought(
                decision=f"Trade completed for {trade.get('symbol')}",
                reasoning=f"Trade outcome: {outcome.value}, PnL: {trade.get('pnl', 0)}, "
                          f"Duration: {trade.get('hold_duration', 'unknown')}",
                decision_type=DecisionType.PERFORMANCE_REVIEW,
                confidence=ConfidenceLevel.HIGH,
                market_context=trade,
                trade_id=str(trade.get('id', 'unknown')),
                tags=['trade_completion', 'performance_review', trade.get('symbol', 'unknown')]
            )
            
            # Transition to reflection state
            self.cognitive_system.transition_state(
                CognitiveState.REFLECTING,
                StateTransitionTrigger.TRADE_COMPLETED,
                f"Analyzing outcome of {trade.get('symbol')} trade"
            )
            
        except Exception as e:
            if self.logger:
                self.logger.log_event(f"Failed to analyze trade outcome: {e}")
            
            if self.use_new_logging:
                self.trading_logger.log_error(e, context={'trade': trade}, source="trade_analysis")


def execute_trade(trade, paper_mode=True, risk_governor=None):
    """Execute a trade with optional risk management"""
    if risk_governor and not risk_governor.can_trade():
        print(f"🚫 Trade blocked by RiskGovernor: {trade['symbol']}")
        return

    now = datetime.datetime.now().isoformat()
    trade["timestamp"] = now
    trade["mode"] = "paper" if paper_mode else "real"
    trade["status"] = "open"

    log_path = f"logs/trade_log_{trade['strategy'].lower()}.jsonl"
    os.makedirs("logs", exist_ok=True)
    with open(log_path, "a") as f:
        f.write(json.dumps(trade) + "\n")

    print(
        f"[EXECUTE-{trade['mode'].upper()}] {trade['strategy']} trade executed for {trade['symbol']}"
    )
    print(
        f"Qty: {trade['quantity']} | Entry: {trade['entry_price']} | SL: {trade['stop_loss']} | Target: {trade['target']}"
    )

    if risk_governor:
        risk_governor.update_trade(0)  # Initial placeholder for PnL


def simulate_exit(trade, candles, risk_governor=None):
    try:
        # ✅ Guard against incomplete trades
        required_keys = [
            "entry_price",
            "stop_loss",
            "target",
            "direction",
            "quantity",
            "strategy",
            "symbol",
        ]
        for key in required_keys:
            if key not in trade:
                print(
                    f"[WARN] Skipping exit simulation. Missing '{key}' in trade: {trade}"
                )
                return

        if trade["quantity"] <= 0:
            print(
                f"[WARN] Skipping exit simulation for {trade['symbol']}: quantity is 0"
            )
            return

        if not candles or not isinstance(candles, list):
            print(f"[WARN] No candles provided for simulate_exit on {trade['symbol']}")
            return

        entry = trade["entry_price"]
        sl = trade["stop_loss"]
        target = trade["target"]
        direction = trade["direction"]
        qty = trade["quantity"]
        status = "open"
        exit_price = entry
        hold_minutes = 0

        for candle in candles:
            hold_minutes += 5
            high = candle.get("high")
            low = candle.get("low")

            if high is None or low is None:
                continue

            if direction == "bullish":
                if high >= target:
                    status = "target_hit"
                    exit_price = target
                    break
                elif low <= sl:
                    status = "stop_loss_hit"
                    exit_price = sl
                    break
            else:
                if low <= target:
                    status = "target_hit"
                    exit_price = target
                    break
                elif high >= sl:
                    status = "stop_loss_hit"
                    exit_price = sl
                    break
        else:
            status = "auto_exit"
            exit_price = candles[-1].get("close", entry)

        # ✅ Update trade details safely
        trade["status"] = status
        trade["exit_price"] = exit_price
        trade["exit_time"] = candles[-1].get(
            "date", datetime.datetime.now().isoformat()
        )
        trade["hold_duration"] = f"{hold_minutes} mins"
        trade["pnl"] = round(
            (
                (exit_price - entry) * qty
                if direction == "bullish"
                else (entry - exit_price) * qty
            ),
            2,
        )

        # ✅ Log updated trade
        log_path = f"logs/trade_log_{trade['strategy'].lower()}.jsonl"
        with open(log_path, "a") as f:
            f.write(json.dumps(trade) + "\n")

        # ✅ Update RiskGovernor PnL if available
        if risk_governor:
            risk_governor.update_trade(trade["pnl"])

        print(
            f"[EXIT-{trade['mode'].upper()}] {trade['symbol']} - {status.upper()} at {exit_price} | PnL: {trade['pnl']} | Held: {trade['hold_duration']}"
        )

        # Analyze trade outcome with cognitive system if available
        # Note: This requires a TradeManager instance to be available
        # In a real implementation, this would be called from the TradeManager instance

    except Exception as e:
        print(f"[ERROR] Simulate exit failed for {trade.get('symbol', 'UNKNOWN')}: {e}")
