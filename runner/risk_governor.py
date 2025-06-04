import logging
from datetime import datetime, time, date
from typing import Dict, List, Optional, Union
import json
import os


class RiskGovernor:
    """
    Comprehensive risk management system to prevent unsafe trading behavior
    """
    
    def __init__(self, max_daily_loss: float = 5000, max_trades: int = 10, 
                 cutoff_time: str = "15:00", max_position_value: float = 50000,
                 max_capital_risk_pct: float = 2.0, logger=None):
        # FIXED: Add comprehensive validation
        if max_daily_loss <= 0:
            raise ValueError("max_daily_loss must be positive")
        if max_trades <= 0:
            raise ValueError("max_trades must be positive")
        if max_position_value <= 0:
            raise ValueError("max_position_value must be positive")
        if not (0 < max_capital_risk_pct <= 100):
            raise ValueError("max_capital_risk_pct must be between 0 and 100")
        
        self.max_daily_loss = abs(max_daily_loss)  # Ensure positive
        self.max_trades = max_trades
        self.cutoff_time = cutoff_time
        self.max_position_value = max_position_value
        self.max_capital_risk_pct = max_capital_risk_pct
        
        # FIXED: Enhanced tracking
        self.total_loss = 0.0
        self.trade_count = 0
        self.position_count = 0
        self.total_position_value = 0.0
        self.realized_pnl = 0.0
        self.unrealized_pnl = 0.0
        self.max_drawdown = 0.0
        self.peak_value = 0.0
        
        # FIXED: Trade history and risk tracking
        self.trade_history: List[Dict] = []
        self.position_history: List[Dict] = []
        self.risk_violations: List[Dict] = []
        self.emergency_stop_triggered = False
        self.stop_reasons: List[str] = []
        
        # FIXED: Time-based controls
        self.last_trade_time = None
        self.min_trade_interval = 30  # seconds between trades
        self.trading_session_start = None
        self.trading_session_end = None
        
        # FIXED: Dynamic risk adjustments
        self.consecutive_losses = 0
        self.win_rate = 0.0
        self.avg_loss_per_trade = 0.0
        self.risk_adjustment_factor = 1.0
        
        # FIXED: Advanced position tracking
        self.open_positions: Dict[str, Dict] = {}
        self.symbol_exposure: Dict[str, float] = {}
        self.strategy_exposure: Dict[str, float] = {}
        
        self.logger = logger
        
        # FIXED: Load state from file if exists
        self._load_state()
        
        if self.logger:
            self.logger.log_event(f"✅ RiskGovernor initialized - Max Daily Loss: ₹{self.max_daily_loss}, Max Trades: {self.max_trades}")

    def _log(self, message: str, level: str = "info"):
        """Safe logging with fallback"""
        if self.logger:
            if hasattr(self.logger, 'log_event'):
                self.logger.log_event(message)
            else:
                print(f"[RISK] {message}")
        else:
            print(f"[RISK] {message}")

    def _validate_trade_timing(self) -> tuple[bool, str]:
        """Validate if trading is allowed based on time constraints"""
        try:
            now = datetime.now()
            current_time_str = now.strftime("%H:%M")
            
            # FIXED: Check market hours (Indian market: 9:15 AM to 3:30 PM)
            market_start = time(9, 15)
            market_end = time(15, 30)
            current_time = now.time()
            
            if not (market_start <= current_time <= market_end):
                return False, f"Outside market hours ({current_time_str})"
            
            # FIXED: Check cutoff time
            try:
                cutoff_hour, cutoff_minute = map(int, self.cutoff_time.split(":"))
                cutoff_time = time(cutoff_hour, cutoff_minute)
                
                if current_time >= cutoff_time:
                    return False, f"Time cutoff reached ({current_time_str} ≥ {self.cutoff_time})"
            except (ValueError, AttributeError):
                self._log(f"Invalid cutoff time format: {self.cutoff_time}")
            
            # FIXED: Check minimum interval between trades
            if self.last_trade_time:
                time_since_last = (now - self.last_trade_time).total_seconds()
                if time_since_last < self.min_trade_interval:
                    return False, f"Too soon since last trade ({time_since_last:.0f}s < {self.min_trade_interval}s)"
            
            # FIXED: Check weekend trading
            if now.weekday() >= 5:  # Saturday = 5, Sunday = 6
                return False, f"Weekend trading not allowed ({now.strftime('%A')})"
            
            return True, "Time validation passed"
            
        except Exception as e:
            self._log(f"Error in time validation: {e}")
            return False, f"Time validation error: {e}"

    def _validate_position_limits(self, trade_value: float, symbol: str = None, 
                                strategy: str = None) -> tuple[bool, str]:
        """Validate position limits and exposure"""
        try:
            # FIXED: Check individual position size
            if trade_value > self.max_position_value:
                return False, f"Position value ₹{trade_value:.2f} exceeds limit ₹{self.max_position_value}"
            
            # FIXED: Check total position value
            new_total_value = self.total_position_value + trade_value
            max_total_position = self.max_position_value * 5  # Allow up to 5x single position limit
            
            if new_total_value > max_total_position:
                return False, f"Total position value would exceed limit (₹{new_total_value:.2f} > ₹{max_total_position})"
            
            # FIXED: Check symbol concentration
            if symbol:
                current_symbol_exposure = self.symbol_exposure.get(symbol, 0)
                max_symbol_exposure = self.max_position_value * 2  # Max 2x position per symbol
                
                if current_symbol_exposure + trade_value > max_symbol_exposure:
                    return False, f"Symbol {symbol} exposure would exceed limit"
            
            # FIXED: Check strategy concentration
            if strategy:
                current_strategy_exposure = self.strategy_exposure.get(strategy, 0)
                max_strategy_exposure = self.max_position_value * 3  # Max 3x position per strategy
                
                if current_strategy_exposure + trade_value > max_strategy_exposure:
                    return False, f"Strategy {strategy} exposure would exceed limit"
            
            return True, "Position limits validation passed"
            
        except Exception as e:
            self._log(f"Error in position validation: {e}")
            return False, f"Position validation error: {e}"

    def _validate_risk_limits(self) -> tuple[bool, str]:
        """Validate risk-based limits"""
        try:
            # FIXED: Check daily loss limit
            if self.total_loss <= -self.max_daily_loss:
                return False, f"Max daily loss reached (₹{self.total_loss:.2f} ≤ -₹{self.max_daily_loss})"
            
            # FIXED: Check trade count
            if self.trade_count >= self.max_trades:
                return False, f"Max trades reached ({self.trade_count} ≥ {self.max_trades})"
            
            # FIXED: Check consecutive losses
            max_consecutive_losses = 5
            if self.consecutive_losses >= max_consecutive_losses:
                return False, f"Too many consecutive losses ({self.consecutive_losses} ≥ {max_consecutive_losses})"
            
            # FIXED: Check win rate threshold
            min_win_rate = 0.2  # 20% minimum win rate after 10 trades
            if self.trade_count >= 10 and self.win_rate < min_win_rate:
                return False, f"Win rate too low ({self.win_rate:.1%} < {min_win_rate:.1%})"
            
            # FIXED: Check drawdown
            max_allowed_drawdown = self.max_daily_loss * 0.8  # 80% of daily loss limit
            if self.max_drawdown <= -max_allowed_drawdown:
                return False, f"Max drawdown exceeded (₹{self.max_drawdown:.2f} ≤ -₹{max_allowed_drawdown})"
            
            return True, "Risk limits validation passed"
            
        except Exception as e:
            self._log(f"Error in risk validation: {e}")
            return False, f"Risk validation error: {e}"

    def can_trade(self, trade_value: float = 0, symbol: str = None, 
                  strategy: str = None) -> bool:
        """
        Comprehensive trading permission check
        
        Args:
            trade_value: Value of the proposed trade
            symbol: Trading symbol (for concentration limits)
            strategy: Strategy name (for strategy limits)
            
        Returns:
            True if trading is allowed, False otherwise
        """
        try:
            # FIXED: Check emergency stop
            if self.emergency_stop_triggered:
                self._log("❌ Emergency stop is active - no trading allowed")
                return False
            
            # FIXED: Time validation
            time_ok, time_msg = self._validate_trade_timing()
            if not time_ok:
                self._log(f"⏰ {time_msg}")
                return False
            
            # FIXED: Risk limits validation
            risk_ok, risk_msg = self._validate_risk_limits()
            if not risk_ok:
                self._log(f"💰 {risk_msg}")
                self._record_violation("risk_limit", risk_msg)
                return False
            
            # FIXED: Position limits validation (if trade value provided)
            if trade_value > 0:
                position_ok, position_msg = self._validate_position_limits(trade_value, symbol, strategy)
                if not position_ok:
                    self._log(f"📊 {position_msg}")
                    self._record_violation("position_limit", position_msg)
                    return False
            
            return True
            
        except Exception as e:
            self._log(f"❌ Error in can_trade check: {e}")
            return False

    def update_trade(self, pnl: float, trade_value: float = 0, symbol: str = None, 
                    strategy: str = None, trade_id: str = None):
        """
        Update trade statistics with comprehensive tracking
        
        Args:
            pnl: Profit/Loss of the trade
            trade_value: Value of the trade
            symbol: Trading symbol
            strategy: Strategy used
            trade_id: Unique trade identifier
        """
        try:
            # FIXED: Validate inputs
            if not isinstance(pnl, (int, float)):
                raise ValueError("PnL must be a number")
            
            # FIXED: Update core statistics
            self.total_loss += pnl
            self.realized_pnl += pnl
            self.trade_count += 1
            self.last_trade_time = datetime.now()
            
            # FIXED: Update position tracking
            if trade_value > 0:
                self.total_position_value = max(0, self.total_position_value - trade_value)  # Close position
                
                # Update symbol exposure
                if symbol:
                    self.symbol_exposure[symbol] = max(0, self.symbol_exposure.get(symbol, 0) - trade_value)
                
                # Update strategy exposure
                if strategy:
                    self.strategy_exposure[strategy] = max(0, self.strategy_exposure.get(strategy, 0) - trade_value)
            
            # FIXED: Track consecutive losses
            if pnl < 0:
                self.consecutive_losses += 1
            else:
                self.consecutive_losses = 0
            
            # FIXED: Update win rate
            winning_trades = sum(1 for trade in self.trade_history if trade.get('pnl', 0) > 0)
            if self.trade_count > 0:
                self.win_rate = winning_trades / self.trade_count
            
            # FIXED: Update drawdown tracking
            self.peak_value = max(self.peak_value, self.total_loss)
            current_drawdown = self.total_loss - self.peak_value
            self.max_drawdown = min(self.max_drawdown, current_drawdown)
            
            # FIXED: Record trade in history
            trade_record = {
                'trade_id': trade_id or f"trade_{self.trade_count}",
                'timestamp': datetime.now().isoformat(),
                'pnl': pnl,
                'trade_value': trade_value,
                'symbol': symbol,
                'strategy': strategy,
                'total_pnl': self.total_loss,
                'trade_number': self.trade_count,
                'consecutive_losses': self.consecutive_losses
            }
            self.trade_history.append(trade_record)
            
            # FIXED: Log trade update
            status = "🟢 PROFIT" if pnl > 0 else "🔴 LOSS"
            self._log(f"{status} Trade {self.trade_count}: ₹{pnl:.2f} | Total: ₹{self.total_loss:.2f} | Drawdown: ₹{self.max_drawdown:.2f}")
            
            # FIXED: Check for emergency conditions
            self._check_emergency_conditions()
            
            # FIXED: Save state
            self._save_state()
            
        except Exception as e:
            self._log(f"❌ Error updating trade: {e}")

    def add_position(self, symbol: str, strategy: str, position_value: float, trade_id: str = None):
        """Add a new position to tracking"""
        try:
            if position_value <= 0:
                raise ValueError("Position value must be positive")
            
            # FIXED: Update position tracking
            self.position_count += 1
            self.total_position_value += position_value
            
            # FIXED: Update exposures
            self.symbol_exposure[symbol] = self.symbol_exposure.get(symbol, 0) + position_value
            self.strategy_exposure[strategy] = self.strategy_exposure.get(strategy, 0) + position_value
            
            # FIXED: Record position
            position_id = trade_id or f"pos_{self.position_count}"
            self.open_positions[position_id] = {
                'symbol': symbol,
                'strategy': strategy,
                'value': position_value,
                'timestamp': datetime.now().isoformat()
            }
            
            self._log(f"📈 Position added: {symbol} (₹{position_value:.2f}) | Total: ₹{self.total_position_value:.2f}")
            
        except Exception as e:
            self._log(f"❌ Error adding position: {e}")

    def remove_position(self, trade_id: str):
        """Remove a position from tracking"""
        try:
            if trade_id in self.open_positions:
                position = self.open_positions.pop(trade_id)
                self.total_position_value = max(0, self.total_position_value - position['value'])
                
                # Update exposures
                symbol = position['symbol']
                strategy = position['strategy']
                value = position['value']
                
                self.symbol_exposure[symbol] = max(0, self.symbol_exposure.get(symbol, 0) - value)
                self.strategy_exposure[strategy] = max(0, self.strategy_exposure.get(strategy, 0) - value)
                
                self._log(f"📉 Position removed: {symbol} (₹{value:.2f}) | Total: ₹{self.total_position_value:.2f}")
            
        except Exception as e:
            self._log(f"❌ Error removing position: {e}")

    def _check_emergency_conditions(self):
        """Check for emergency stop conditions"""
        try:
            # FIXED: Rapid loss condition
            if self.total_loss <= -self.max_daily_loss * 0.9:  # 90% of daily limit
                self._trigger_emergency_stop("Approaching daily loss limit")
            
            # FIXED: Too many consecutive losses
            if self.consecutive_losses >= 7:
                self._trigger_emergency_stop("Too many consecutive losses")
            
            # FIXED: Severe drawdown
            if self.max_drawdown <= -self.max_daily_loss * 0.8:
                self._trigger_emergency_stop("Severe drawdown detected")
            
            # FIXED: Win rate collapse
            if self.trade_count >= 15 and self.win_rate < 0.15:  # 15% win rate
                self._trigger_emergency_stop("Win rate collapse")
                
        except Exception as e:
            self._log(f"❌ Error checking emergency conditions: {e}")

    def _trigger_emergency_stop(self, reason: str):
        """Trigger emergency stop with detailed logging"""
        if not self.emergency_stop_triggered:
            self.emergency_stop_triggered = True
            self.stop_reasons.append(f"{datetime.now().isoformat()}: {reason}")
            
            self._log(f"🚨 EMERGENCY STOP TRIGGERED: {reason}")
            self._log(f"🚨 Current stats - Trades: {self.trade_count}, P&L: ₹{self.total_loss:.2f}, Drawdown: ₹{self.max_drawdown:.2f}")
            
            self._record_violation("emergency_stop", reason)
            self._save_state()

    def _record_violation(self, violation_type: str, description: str):
        """Record risk violations for analysis"""
        violation = {
            'type': violation_type,
            'description': description,
            'timestamp': datetime.now().isoformat(),
            'total_pnl': self.total_loss,
            'trade_count': self.trade_count
        }
        self.risk_violations.append(violation)

    def reset_day(self):
        """Reset daily statistics with comprehensive cleanup"""
        try:
            self._log("🔄 Resetting daily risk statistics...")
            
            # FIXED: Save current day data before reset
            self._save_daily_summary()
            
            # Reset core statistics
            self.total_loss = 0.0
            self.trade_count = 0
            self.position_count = 0
            self.total_position_value = 0.0
            self.realized_pnl = 0.0
            self.unrealized_pnl = 0.0
            self.max_drawdown = 0.0
            self.peak_value = 0.0
            
            # Reset tracking
            self.consecutive_losses = 0
            self.win_rate = 0.0
            self.emergency_stop_triggered = False
            self.last_trade_time = None
            
            # Clear collections but keep for analysis
            self.trade_history.clear()
            self.position_history.clear()
            self.risk_violations.clear()
            self.stop_reasons.clear()
            self.open_positions.clear()
            self.symbol_exposure.clear()
            self.strategy_exposure.clear()
            
            self._log("✅ Daily reset completed")
            
        except Exception as e:
            self._log(f"❌ Error resetting day: {e}")

    def get_risk_summary(self) -> Dict:
        """Get comprehensive risk summary"""
        try:
            return {
                'timestamp': datetime.now().isoformat(),
                'total_pnl': self.total_loss,
                'trade_count': self.trade_count,
                'position_count': self.position_count,
                'total_position_value': self.total_position_value,
                'max_drawdown': self.max_drawdown,
                'consecutive_losses': self.consecutive_losses,
                'win_rate': self.win_rate,
                'emergency_stop_active': self.emergency_stop_triggered,
                'violations_count': len(self.risk_violations),
                'symbol_exposures': dict(self.symbol_exposure),
                'strategy_exposures': dict(self.strategy_exposure),
                'limits': {
                    'max_daily_loss': self.max_daily_loss,
                    'max_trades': self.max_trades,
                    'max_position_value': self.max_position_value,
                    'cutoff_time': self.cutoff_time
                },
                'can_trade_now': self.can_trade()
            }
        except Exception as e:
            self._log(f"❌ Error generating risk summary: {e}")
            return {'error': str(e)}

    def _save_state(self):
        """Save risk governor state to file"""
        try:
            state_file = f"logs/risk_state_{date.today().strftime('%Y-%m-%d')}.json"
            os.makedirs("logs", exist_ok=True)
            
            state = {
                'total_loss': self.total_loss,
                'trade_count': self.trade_count,
                'position_count': self.position_count,
                'total_position_value': self.total_position_value,
                'max_drawdown': self.max_drawdown,
                'consecutive_losses': self.consecutive_losses,
                'emergency_stop_triggered': self.emergency_stop_triggered,
                'trade_history': self.trade_history[-100:],  # Keep last 100 trades
                'risk_violations': self.risk_violations,
                'symbol_exposure': dict(self.symbol_exposure),
                'strategy_exposure': dict(self.strategy_exposure),
                'last_save': datetime.now().isoformat()
            }
            
            with open(state_file, 'w') as f:
                json.dump(state, f, indent=2)
                
        except Exception as e:
            self._log(f"❌ Error saving risk state: {e}")

    def _load_state(self):
        """Load risk governor state from file"""
        try:
            state_file = f"logs/risk_state_{date.today().strftime('%Y-%m-%d')}.json"
            
            if os.path.exists(state_file):
                with open(state_file, 'r') as f:
                    state = json.load(f)
                
                # Restore state
                self.total_loss = state.get('total_loss', 0.0)
                self.trade_count = state.get('trade_count', 0)
                self.position_count = state.get('position_count', 0)
                self.total_position_value = state.get('total_position_value', 0.0)
                self.max_drawdown = state.get('max_drawdown', 0.0)
                self.consecutive_losses = state.get('consecutive_losses', 0)
                self.emergency_stop_triggered = state.get('emergency_stop_triggered', False)
                self.trade_history = state.get('trade_history', [])
                self.risk_violations = state.get('risk_violations', [])
                self.symbol_exposure = state.get('symbol_exposure', {})
                self.strategy_exposure = state.get('strategy_exposure', {})
                
                self._log("✅ Risk governor state loaded from file")
                
        except Exception as e:
            self._log(f"⚠️ Could not load risk state: {e}")

    def _save_daily_summary(self):
        """Save daily summary for analysis"""
        try:
            summary_file = f"logs/daily_risk_summary_{date.today().strftime('%Y-%m-%d')}.json"
            os.makedirs("logs", exist_ok=True)
            
            summary = self.get_risk_summary()
            summary['final_summary'] = True
            
            with open(summary_file, 'w') as f:
                json.dump(summary, f, indent=2)
                
        except Exception as e:
            self._log(f"❌ Error saving daily summary: {e}")

    def clear_emergency_stop(self, reason: str = "Manual override"):
        """Clear emergency stop with logging"""
        if self.emergency_stop_triggered:
            self.emergency_stop_triggered = False
            self.stop_reasons.append(f"{datetime.now().isoformat()}: Cleared - {reason}")
            self._log(f"🔓 Emergency stop cleared: {reason}")
            self._save_state()

    def get_position_limits_remaining(self) -> Dict:
        """Get remaining position limits"""
        return {
            'max_position_value': self.max_position_value,
            'current_total_value': self.total_position_value,
            'remaining_capacity': max(0, (self.max_position_value * 5) - self.total_position_value),
            'position_count': self.position_count,
            'symbol_count': len(self.symbol_exposure),
            'strategy_count': len(self.strategy_exposure)
        }
