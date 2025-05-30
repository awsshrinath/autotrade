import datetime
import json
import os
import time
from typing import Dict, Any, Optional, List
from dataclasses import asdict

# Import new optimized logging system
try:
    from runner.enhanced_logging import TradingLogger, LogLevel, LogCategory
    from runner.enhanced_logging.log_types import TradeLogData, ErrorLogData
    NEW_LOGGING_AVAILABLE = True
except ImportError:
    NEW_LOGGING_AVAILABLE = False

# Legacy imports
from runner.risk_governor import RiskGovernor
from runner.cognitive.cognitive_system import CognitiveSystem, DecisionType, ConfidenceLevel, CognitiveState, StateTransitionTrigger

# Initialize risk governor
risk_guard = RiskGovernor()


class TradeManager:
    def __init__(self, logger=None, kite=None, firestore_client=None, cognitive_system=None):
        self.logger = logger
        self.kite = kite
        self.firestore_client = firestore_client
        self.cognitive_system = cognitive_system
        self.open_positions = []
        
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
            self.logger.log_event("TradeManager initialized")

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
        Execute a trade based on the signal.
        
        Args:
            trade_signal: Dictionary containing trade parameters
            bot_type: Type of bot executing the trade
            strategy_name: Name of the strategy that generated the signal
        
        Returns:
            Trade object if successful, None otherwise
        """
        try:
            # Record cognitive thought about trade decision
            thought_id = None
            confidence_level = None
            if self.cognitive_system:
                confidence_level = ConfidenceLevel.HIGH if trade_signal.get('confidence', 0.5) > 0.7 else ConfidenceLevel.MEDIUM
                thought_id = self.cognitive_system.record_thought(
                    decision=f"Executing trade for {trade_signal.get('symbol')}",
                    reasoning=f"Strategy {strategy_name} generated signal with confidence {trade_signal.get('confidence', 'unknown')}",
                    decision_type=DecisionType.TRADE_EXECUTION,
                    confidence=confidence_level,
                    market_context=trade_signal,
                    trade_id=str(trade_signal.get('id', 'unknown')),
                    tags=['trade_execution', strategy_name or 'unknown', trade_signal.get('symbol', 'unknown')]
                )

        except Exception as e:
            if self.logger:
                self.logger.log_event(f"Error in cognitive processing: {e}")
            
            if self.use_new_logging:
                self.trading_logger.log_error(e, context={'trade_signal': trade_signal}, source="cognitive_system")

        # Check risk management
        if not risk_guard.can_trade():
            if self.logger:
                self.logger.log_event(
                    f"🚫 Trade blocked by RiskGovernor: {trade_signal['symbol']}"
                )
            
            # Log risk block with new system
            if self.use_new_logging:
                error_data = ErrorLogData(
                    error_id=f"risk_block_{int(datetime.datetime.now().timestamp())}",
                    error_type="RiskManagementBlock",
                    error_message=f"Trade blocked by RiskGovernor for {trade_signal.get('symbol')}",
                    context={'trade_signal': trade_signal, 'risk_reason': 'risk_governor_block'}
                )
                self.trading_logger.firestore_logger.log_alert(error_data, severity="medium")
            
            # Record cognitive thought about blocked trade
            if self.cognitive_system:
                self.cognitive_system.record_thought(
                    decision="Trade blocked by risk management",
                    reasoning="RiskGovernor prevented trade execution due to risk limits",
                    decision_type=DecisionType.RISK_ASSESSMENT,
                    confidence=ConfidenceLevel.VERY_HIGH,
                    market_context={
                        'blocked_symbol': trade_signal.get('symbol'),
                        'reason': 'risk_governor_block'
                    },
                    tags=['risk_management', 'trade_blocked']
                )
            
            return None

        # Transition to executing state
        if self.cognitive_system:
            self.cognitive_system.transition_state(
                CognitiveState.EXECUTING,
                StateTransitionTrigger.SIGNAL_DETECTED,
                f"Executing trade for {trade_signal.get('symbol')}"
            )

        # Create the trade object
        trade = {
            **trade_signal,
            "timestamp": datetime.datetime.now().isoformat(),
            "mode": "paper",  # Default to paper trading
            "status": "open",
            "bot_type": bot_type,
            "cognitive_thought_id": thought_id if self.cognitive_system else None,
            "confidence_level": confidence_level.value if self.cognitive_system else None
        }

        # Log the trade with new system
        if self.use_new_logging:
            try:
                trade_log_data = TradeLogData(
                    trade_id=trade.get('id', f"trade_{int(datetime.datetime.now().timestamp())}"),
                    symbol=trade.get('symbol', 'UNKNOWN'),
                    strategy=strategy_name or trade.get('strategy', 'unknown'),
                    bot_type=bot_type,
                    direction=trade.get('direction', 'unknown'),
                    quantity=trade.get('quantity', 0),
                    entry_price=trade.get('entry_price', 0.0),
                    stop_loss=trade.get('stop_loss'),
                    target=trade.get('target'),
                    status="open",
                    entry_time=datetime.datetime.now(),
                    confidence_level=trade.get('confidence'),
                    metadata={
                        'mode': trade.get('mode'),
                        'cognitive_thought_id': thought_id,
                        'timestamp': trade.get('timestamp')
                    }
                )
                
                self.trading_logger.log_trade_entry(trade_log_data, urgent=True)
                
            except Exception as e:
                if self.logger:
                    self.logger.log_event(f"Error logging trade with new system: {e}")

        # Log to Firestore (legacy)
        if self.firestore_client:
            try:
                date_str = datetime.datetime.now().strftime("%Y-%m-%d")
                self.firestore_client.log_trade(bot_type, date_str, trade)
            except Exception as e:
                if self.logger:
                    self.logger.log_event(f"Failed to log trade to Firestore: {e}")

        if self.logger:
            self.logger.log_event(
                f"[EXECUTE-{trade['mode'].upper()}] {trade.get('strategy', 'UNKNOWN')} trade executed for {trade['symbol']}"
            )
            self.logger.log_event(
                f"Qty: {trade['quantity']} | Entry: {trade['entry_price']} | SL: {trade['stop_loss']} | Target: {trade['target']}"
            )

        # Update the risk governor
        risk_guard.update_trade(0)  # Initial placeholder for PnL

        # Store trade details in cognitive memory
        if self.cognitive_system:
            trade_memory = f"Executed {trade.get('direction')} trade for {trade['symbol']} at {trade['entry_price']}"
            self.cognitive_system.store_memory(
                content=trade_memory,
                importance=self.cognitive_system.memory.ImportanceLevel.HIGH,
                tags=['trade_execution', trade['symbol'], bot_type],
                metadata={
                    'trade_id': trade.get('id'),
                    'entry_price': trade['entry_price'],
                    'strategy': strategy_name,
                    'timestamp': trade['timestamp']
                }
            )

        return trade

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


def execute_trade(trade, paper_mode=True):
    if not risk_guard.can_trade():
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

    risk_guard.update_trade(0)  # Initial placeholder for PnL


def simulate_exit(trade, candles):
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

        # ✅ Update RiskGovernor PnL
        risk_guard.update_trade(trade["pnl"])

        print(
            f"[EXIT-{trade['mode'].upper()}] {trade['symbol']} - {status.upper()} at {exit_price} | PnL: {trade['pnl']} | Held: {trade['hold_duration']}"
        )

        # Analyze trade outcome with cognitive system if available
        # Note: This requires a TradeManager instance to be available
        # In a real implementation, this would be called from the TradeManager instance

    except Exception as e:
        print(f"[ERROR] Simulate exit failed for {trade.get('symbol', 'UNKNOWN')}: {e}")
