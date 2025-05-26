"""
Enterprise Portfolio and Capital Management System
Supports both paper trading (simulated capital) and live trading (real balance)
"""

import asyncio
import json
import os
from config.config_manager import get_trading_config
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np
from threading import Lock


@dataclass
class Position:
    symbol: str
    quantity: int
    entry_price: float
    current_price: float
    pnl: float
    risk_weight: float
    strategy: str
    entry_time: datetime
    position_type: str  # 'stock', 'option', 'future'
    is_mock: bool = False


@dataclass
class RiskMetrics:
    var_95: float  # Value at Risk
    max_drawdown: float
    sharpe_ratio: float
    win_rate: float
    avg_profit: float
    avg_loss: float
    total_trades: int
    profitable_trades: int


@dataclass
class CapitalAllocation:
    total_capital: float
    available_cash: float
    used_margin: float
    position_value: float
    day_pnl: float
    unrealized_pnl: float
    margin_utilization: float
    is_mock: bool = False


class PortfolioManager:
    """Enterprise portfolio and capital management with paper trade support"""
    
    def __init__(self, kite=None, firestore=None, logger=None, 
                 initial_capital: float = None, paper_trade: bool = None):
        
        # Use configuration file if not explicitly set
        config = get_trading_config()
        if paper_trade is None:
            paper_trade = config.paper_trade
        
        self.paper_trade = paper_trade
        self.kite = kite
        self.firestore = firestore
        self.logger = logger
        
        # Initialize capital
        if initial_capital is None:
            initial_capital = config.default_capital
        
        self.initial_capital = initial_capital
        self.positions: List[Position] = []
        self._positions_lock = Lock()
        
        # Risk management parameters from config
        self.max_daily_loss_pct = config.max_daily_loss_pct
        self.max_daily_loss = (config.max_daily_loss or 
                              (self.initial_capital * (self.max_daily_loss_pct / 100)))
        
        self.position_size_limits = {
            'stock': config.stock_position_limit,
            'option': config.option_position_limit,
            'future': config.future_position_limit
        }
        
        # Paper trading simulation
        if self.paper_trade:
            self.mock_capital = {
                'total_capital': initial_capital,
                'available_cash': initial_capital,
                'used_margin': 0.0,
                'day_pnl': 0.0,
                'positions': []
            }
            
        # Performance tracking
        self.daily_pnl = 0.0
        self.trade_history = []
        self.performance_cache = {}
        
        if self.logger:
            self.logger.log_event(
                f"PortfolioManager initialized - Paper Trade: {self.paper_trade}, "
                f"Initial Capital: ₹{initial_capital:,.2f}"
            )
    
    async def get_real_time_capital(self) -> CapitalAllocation:
        """Get real-time capital and margin information"""
        
        if self.paper_trade:
            return self._get_mock_capital()
        
        try:
            # Get real data from Kite
            margins = self.kite.margins()
            positions = self.kite.positions()
            
            # Calculate capital metrics
            available_cash = margins['equity']['available']['cash']
            used_margin = margins['equity']['utilised']['debits']
            
            # Calculate position values
            net_positions = positions.get('net', [])
            position_value = sum([
                float(pos.get('pnl', 0)) for pos in net_positions 
                if pos.get('product') in ['MIS', 'NRML']
            ])
            
            day_positions = positions.get('day', [])
            day_pnl = sum([float(pos.get('pnl', 0)) for pos in day_positions])
            
            unrealized_pnl = sum([
                float(pos.get('pnl', 0)) for pos in net_positions
                if float(pos.get('quantity', 0)) != 0
            ])
            
            # Total portfolio value
            total_capital = available_cash + position_value
            
            # Margin utilization percentage
            total_margin = available_cash + used_margin
            margin_utilization = (used_margin / total_margin * 100) if total_margin > 0 else 0
            
            allocation = CapitalAllocation(
                total_capital=total_capital,
                available_cash=available_cash,
                used_margin=used_margin,
                position_value=position_value,
                day_pnl=day_pnl,
                unrealized_pnl=unrealized_pnl,
                margin_utilization=margin_utilization,
                is_mock=False
            )
            
            if self.logger:
                self.logger.log_event(
                    f"Capital Status - Total: ₹{total_capital:,.2f}, "
                    f"Available: ₹{available_cash:,.2f}, Day PnL: ₹{day_pnl:,.2f}"
                )
            
            return allocation
            
        except Exception as e:
            if self.logger:
                self.logger.log_event(f"Error fetching real capital data: {e}")
            
            # Fallback to mock data on error
            return self._get_mock_capital()
    
    def _get_mock_capital(self) -> CapitalAllocation:
        """Get simulated capital for paper trading"""
        
        # Update mock capital based on current positions
        total_position_value = sum([pos.pnl for pos in self.positions])
        
        self.mock_capital['position_value'] = total_position_value
        self.mock_capital['total_capital'] = self.initial_capital + total_position_value
        self.mock_capital['day_pnl'] = self.daily_pnl
        
        # Calculate used margin (simplified)
        used_margin = sum([
            pos.quantity * pos.current_price * 0.2  # Assume 20% margin requirement
            for pos in self.positions if pos.quantity > 0
        ])
        
        self.mock_capital['used_margin'] = used_margin
        self.mock_capital['available_cash'] = max(0, 
            self.initial_capital - used_margin + total_position_value
        )
        
        margin_utilization = ((used_margin / self.initial_capital * 100) 
                              if self.initial_capital > 0 else 0)
        
        return CapitalAllocation(
            total_capital=self.mock_capital['total_capital'],
            available_cash=self.mock_capital['available_cash'],
            used_margin=used_margin,
            position_value=total_position_value,
            day_pnl=self.daily_pnl,
            unrealized_pnl=total_position_value,
            margin_utilization=margin_utilization,
            is_mock=True
        )
    
    def calculate_position_size(self, symbol: str, strategy: str,
                              price: float, volatility: float = 0.02,
                              confidence: float = 0.7) -> Dict:
        """Dynamic position sizing based on Kelly Criterion and risk management"""
        
        try:
            # Get available capital
            capital_data = asyncio.run(self.get_real_time_capital())
            available_capital = capital_data.available_cash
            
            # Determine asset type
            asset_type = self._get_asset_type(symbol)
            
            # Base position size limit
            max_position_value = available_capital * self.position_size_limits[asset_type]
            
            # Kelly Criterion calculation
            strategy_stats = self._get_strategy_statistics(strategy)
            win_rate = strategy_stats.get('win_rate', 0.5)
            avg_win = strategy_stats.get('avg_win', 0.02)  # 2% default
            avg_loss = strategy_stats.get('avg_loss', 0.015)  # 1.5% default
            
            if avg_loss > 0 and avg_win > 0:
                kelly_fraction = ((win_rate * avg_win - (1 - win_rate) * avg_loss) 
                             / avg_win)
                kelly_fraction = max(0, min(kelly_fraction, 0.25))  # Cap at 25%
            else:
                kelly_fraction = 0.1  # Default 10%
            
            # Volatility adjustment (reduce size for high volatility)
            vol_adjustment = max(0.3, min(1.5, 1 / (1 + volatility * 10)))
            
            # Confidence adjustment
            conf_adjustment = max(0.3, min(1.2, confidence))
            
            # Market condition adjustment
            market_adjustment = self._get_market_condition_adjustment()
            
            # Final position size calculation
            adjusted_fraction = (kelly_fraction * vol_adjustment * 
                               conf_adjustment * market_adjustment)
            position_value = min(max_position_value, 
                               available_capital * adjusted_fraction)
            
            # Calculate quantity
            if price > 0:
                quantity = int(position_value / price)
            else:
                quantity = 0
            
            # Minimum position size check
            min_trade_value = float(os.getenv("MIN_TRADE_VALUE", "1000"))
            if position_value < min_trade_value:
                quantity = 0
            
            position_info = {
                'symbol': symbol,
                'recommended_quantity': quantity,
                'position_value': quantity * price,
                'kelly_fraction': kelly_fraction,
                'vol_adjustment': vol_adjustment,
                'conf_adjustment': conf_adjustment,
                'market_adjustment': market_adjustment,
                'final_allocation_pct': ((quantity * price / available_capital * 100) 
                                        if available_capital > 0 else 0),
                'risk_amount': quantity * price * avg_loss,
                'potential_profit': quantity * price * avg_win,
                'asset_type': asset_type
            }
            
            if self.logger:
                self.logger.log_event(
                    f"Position sizing for {symbol}: Qty={quantity}, "
                    f"Value=₹{quantity * price:,.2f}, Kelly={kelly_fraction:.3f}, "
                    f"Allocation={position_info['final_allocation_pct']:.1f}%"
                )
            
            return position_info
            
        except Exception as e:
            if self.logger:
                self.logger.log_event(f"Error in position sizing for {symbol}: {e}")
            
            # Conservative fallback
            safe_quantity = (int(available_capital * 0.05 / price) 
                           if price > 0 else 0)
            return {
                'symbol': symbol,
                'recommended_quantity': safe_quantity,
                'position_value': safe_quantity * price,
                'error': str(e)
            }
    
    def risk_check_before_trade(self, trade_request: Dict) -> Tuple[bool, str]:
        """Comprehensive risk check before executing trade"""
        
        try:
            symbol = trade_request.get('symbol', '')
            quantity = trade_request.get('quantity', 0)
            price = trade_request.get('price', 0)
            
            # 1. Daily loss limit check
            capital_data = asyncio.run(self.get_real_time_capital())
            
            if capital_data.day_pnl <= -self.max_daily_loss:
                return False, (f"Daily loss limit exceeded: "
                              f"₹{capital_data.day_pnl:,.2f}")
            
            # 2. Position size check
            new_exposure = quantity * price
            max_single_position = capital_data.total_capital * 0.2  # Max 20% in single position
            
            if new_exposure > max_single_position:
                return False, (f"Position too large: ₹{new_exposure:,.2f} > "
                              f"₹{max_single_position:,.2f}")
            
            # 3. Margin utilization check
            if capital_data.margin_utilization > 80:  # Max 80% margin utilization
                return False, (f"High margin utilization: "
                              f"{capital_data.margin_utilization:.1f}%")
            
            # 4. Available cash check
            required_margin = new_exposure * 0.2  # Assume 20% margin requirement
            if required_margin > capital_data.available_cash:
                return False, (f"Insufficient cash: Required ₹{required_margin:,.2f}, "
                              f"Available ₹{capital_data.available_cash:,.2f}")
            
            # 5. Market hours check
            if not self._is_market_hours():
                return False, "Outside market hours"
            
            # 6. Volatility circuit breaker
            volatility = trade_request.get('volatility', 0)
            max_volatility = float(os.getenv("MAX_VOLATILITY_THRESHOLD", "0.05"))
            if volatility > max_volatility:
                return False, f"High volatility detected: {volatility:.1%}"
            
            # 7. Position concentration check
            current_exposure = self._get_symbol_exposure(symbol)
            total_exposure = current_exposure + new_exposure
            max_symbol_exposure = capital_data.total_capital * 0.15  # Max 15% per symbol
            
            if total_exposure > max_symbol_exposure:
                return False, f"Symbol concentration risk: {symbol}"
            
            # 8. Strategy limits check
            strategy = trade_request.get('strategy', '')
            if not self._check_strategy_limits(strategy):
                return False, f"Strategy {strategy} limits exceeded"
            
            return True, "All risk checks passed"
            
        except Exception as e:
            if self.logger:
                self.logger.log_event(f"Risk check error: {e}")
            return False, f"Risk check failed: {str(e)}"
    
    def update_position(self, symbol: str, quantity: int, price: float,
                       strategy: str, position_type: str = 'stock') -> bool:
        """Update or create position"""
        
        try:
            with self._positions_lock:
                # Find existing position
                existing_pos = None
                for i, pos in enumerate(self.positions):
                    if pos.symbol == symbol and pos.strategy == strategy:
                        existing_pos = i
                        break
                
                if existing_pos is not None:
                    # Update existing position
                    old_pos = self.positions[existing_pos]
                    new_quantity = old_pos.quantity + quantity
                    
                    if new_quantity == 0:
                        # Close position
                        self.positions.pop(existing_pos)
                    else:
                        # Update position
                        weighted_price = (((old_pos.quantity * old_pos.entry_price) + 
                                         (quantity * price)) / new_quantity)
                        
                        self.positions[existing_pos] = Position(
                            symbol=symbol,
                            quantity=new_quantity,
                            entry_price=weighted_price,
                            current_price=price,
                            pnl=(price - weighted_price) * new_quantity,
                            risk_weight=self._calculate_risk_weight(
                                symbol, new_quantity, price),
                            strategy=strategy,
                            entry_time=old_pos.entry_time,
                            position_type=position_type,
                            is_mock=self.paper_trade
                        )
                else:
                    # Create new position
                    if quantity != 0:
                        new_position = Position(
                            symbol=symbol,
                            quantity=quantity,
                            entry_price=price,
                            current_price=price,
                            pnl=0.0,
                            risk_weight=self._calculate_risk_weight(
                                symbol, quantity, price),
                            strategy=strategy,
                            entry_time=datetime.now(),
                            position_type=position_type,
                            is_mock=self.paper_trade
                        )
                        self.positions.append(new_position)
            
            # Update performance tracking
            if quantity != 0:  # Only track actual trades
                self._record_trade(symbol, quantity, price, strategy)
            
            if self.logger:
                action = "Updated" if existing_pos is not None else "Created"
                self.logger.log_event(
                    f"{action} position: {symbol} qty={quantity} @ ₹{price:.2f}"
                )
            
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.log_event(f"Error updating position {symbol}: {e}")
            return False
    
    def calculate_portfolio_metrics(self, days: int = 30) -> RiskMetrics:
        """Calculate comprehensive portfolio risk metrics"""
        
        try:
            # Get trade history
            trades = self._get_trade_history(days)
            
            if len(trades) < 5:
                return RiskMetrics(0, 0, 0, 0, 0, 0, 0, 0)
            
            # Calculate returns
            returns = [trade.get('return_pct', 0) for trade in trades if 'return_pct' in trade]
            
            if not returns:
                return RiskMetrics(0, 0, 0, 0, 0, 0, len(trades), 0)
            
            # Value at Risk (95% confidence)
            var_95 = np.percentile(returns, 5) if len(returns) >= 10 else min(returns)
            
            # Maximum Drawdown
            cumulative_returns = np.cumprod([1 + r for r in returns])
            running_max = np.maximum.accumulate(cumulative_returns)
            drawdown = (cumulative_returns - running_max) / running_max
            max_drawdown = np.min(drawdown)
            
            # Sharpe Ratio (annualized)
            mean_return = np.mean(returns)
            std_return = np.std(returns)
            sharpe_ratio = ((mean_return * 252) / (std_return * np.sqrt(252)) 
                           if std_return > 0 else 0)
            
            # Win rate and profit metrics
            profitable_trades = len([r for r in returns if r > 0])
            win_rate = profitable_trades / len(returns)
            
            positive_returns = [r for r in returns if r > 0]
            negative_returns = [r for r in returns if r < 0]
            
            avg_profit = np.mean(positive_returns) if positive_returns else 0
            avg_loss = abs(np.mean(negative_returns)) if negative_returns else 0
            
            metrics = RiskMetrics(
                var_95=var_95,
                max_drawdown=max_drawdown,
                sharpe_ratio=sharpe_ratio,
                win_rate=win_rate,
                avg_profit=avg_profit,
                avg_loss=avg_loss,
                total_trades=len(trades),
                profitable_trades=profitable_trades
            )
            
            # Cache metrics
            self.performance_cache = {
                'metrics': asdict(metrics),
                'timestamp': datetime.now().isoformat(),
                'days_analyzed': days
            }
            
            return metrics
            
        except Exception as e:
            if self.logger:
                self.logger.log_event(f"Error calculating portfolio metrics: {e}")
            return RiskMetrics(0, 0, 0, 0, 0, 0, 0, 0)
    
    def get_portfolio_summary(self) -> Dict:
        """Get comprehensive portfolio summary"""
        
        try:
            capital_data = asyncio.run(self.get_real_time_capital())
            risk_metrics = self.calculate_portfolio_metrics()
            
            # Position summary
            position_summary = {
                'total_positions': len(self.positions),
                'long_positions': len([p for p in self.positions if p.quantity > 0]),
                'short_positions': len([p for p in self.positions if p.quantity < 0]),
                'total_unrealized_pnl': sum([p.pnl for p in self.positions]),
                'positions_by_type': {}
            }
            
            # Group by position type
            for pos_type in ['stock', 'option', 'future']:
                type_positions = [p for p in self.positions if p.position_type == pos_type]
                position_summary['positions_by_type'][pos_type] = {
                    'count': len(type_positions),
                    'total_value': sum([abs(p.quantity * p.current_price) for p in type_positions]),
                    'pnl': sum([p.pnl for p in type_positions])
                }
            
            summary = {
                'timestamp': datetime.now().isoformat(),
                'paper_trade': self.paper_trade,
                'capital': asdict(capital_data),
                'positions': position_summary,
                'risk_metrics': asdict(risk_metrics),
                'daily_limits': {
                    'max_daily_loss': self.max_daily_loss,
                    'remaining_loss_capacity': (self.max_daily_loss + 
                                               capital_data.day_pnl),
                    'position_size_limits': self.position_size_limits
                },
                'system_status': {
                    'total_positions': len(self.positions),
                    'cache_size': len(self.performance_cache),
                    'last_update': datetime.now().isoformat()
                }
            }
            
            return summary
            
        except Exception as e:
            if self.logger:
                self.logger.log_event(f"Error generating portfolio summary: {e}")
            return {'error': str(e), 'timestamp': datetime.now().isoformat()}
    
    # Helper methods
    def _get_asset_type(self, symbol: str) -> str:
        """Determine asset type from symbol"""
        if 'CE' in symbol or 'PE' in symbol:
            return 'option'
        elif any(fut in symbol for fut in ['FUT', 'NIFTY', 'BANKNIFTY']):
            return 'future'
        else:
            return 'stock'
    
    def _get_strategy_statistics(self, strategy: str) -> Dict:
        """Get historical statistics for a strategy"""
        # This would typically query historical data
        # For now, using defaults based on strategy type
        strategy_defaults = {
            'vwap': {'win_rate': 0.65, 'avg_win': 0.025, 'avg_loss': 0.018},
            'scalp': {'win_rate': 0.55, 'avg_win': 0.015, 'avg_loss': 0.012},
            'momentum': {'win_rate': 0.60, 'avg_win': 0.035, 'avg_loss': 0.025},
            'orb': {'win_rate': 0.58, 'avg_win': 0.030, 'avg_loss': 0.020},
            'default': {'win_rate': 0.50, 'avg_win': 0.020, 'avg_loss': 0.015}
        }
        
        return strategy_defaults.get(strategy.lower(), strategy_defaults['default'])
    
    def _get_market_condition_adjustment(self) -> float:
        """Get market condition adjustment factor"""
        # This would typically analyze market volatility, trend, etc.
        # For now, using a simple time-based adjustment
        hour = datetime.now().hour
        
        if 9 <= hour <= 10:  # Opening hour - higher volatility
            return 0.8
        elif 15 <= hour <= 16:  # Closing hour - higher volatility
            return 0.8
        elif 11 <= hour <= 14:  # Mid-day - normal volatility
            return 1.0
        else:
            return 0.6  # Outside main trading hours
    
    def _is_market_hours(self) -> bool:
        """Check if within market hours"""
        now = datetime.now().time()
        market_open = datetime.strptime("09:15", "%H:%M").time()
        market_close = datetime.strptime("15:30", "%H:%M").time()
        
        return market_open <= now <= market_close
    
    def _get_symbol_exposure(self, symbol: str) -> float:
        """Get current exposure to a symbol"""
        total_exposure = 0
        for pos in self.positions:
            if pos.symbol == symbol:
                total_exposure += abs(pos.quantity * pos.current_price)
        return total_exposure
    
    def _check_strategy_limits(self, strategy: str) -> bool:
        """Check if strategy limits are within bounds"""
        # Count positions by strategy
        strategy_positions = [p for p in self.positions if p.strategy == strategy]
        
        # Strategy-specific limits
        strategy_limits = {
            'scalp': 5,      # Max 5 scalp positions
            'momentum': 3,   # Max 3 momentum positions
            'vwap': 4,       # Max 4 VWAP positions
            'orb': 2         # Max 2 ORB positions
        }
        
        max_positions = strategy_limits.get(strategy, 10)  # Default 10
        return len(strategy_positions) < max_positions
    
    def _calculate_risk_weight(self, symbol: str, quantity: int, price: float) -> float:
        """Calculate risk weight for position"""
        position_value = abs(quantity * price)
        capital_data = asyncio.run(self.get_real_time_capital())
        
        if capital_data.total_capital > 0:
            return position_value / capital_data.total_capital
        else:
            return 0.0
    
    def _record_trade(self, symbol: str, quantity: int, price: float, strategy: str):
        """Record trade for performance tracking"""
        trade_record = {
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'quantity': quantity,
            'price': price,
            'strategy': strategy,
            'value': quantity * price,
            'is_mock': self.paper_trade
        }
        
        self.trade_history.append(trade_record)
        
        # Keep only last 1000 trades
        if len(self.trade_history) > 1000:
            self.trade_history = self.trade_history[-1000:]
    
    def _get_trade_history(self, days: int) -> List[Dict]:
        """Get trade history for specified days"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        recent_trades = [
            trade for trade in self.trade_history
            if datetime.fromisoformat(trade['timestamp']) >= cutoff_date
        ]
        
        return recent_trades


# Factory function for backward compatibility
def create_portfolio_manager(kite=None, firestore=None, logger=None,
                           initial_capital: float = None, 
                           paper_trade: bool = None) -> PortfolioManager:
    """Create PortfolioManager instance"""
    return PortfolioManager(kite, firestore, logger, initial_capital, paper_trade)


# Backward compatibility function
def get_current_capital(bot_name: str, paper_trade: bool = None) -> Dict:
    """Get current capital allocation for a bot - backward compatible function"""
    
    if paper_trade is None:
        paper_trade = os.getenv("PAPER_TRADE", "true").lower() == "true"
    
    if paper_trade:
        # Mock capital data
        capital_data = {
            "stock-trader": {
                "allocated": 50000,
                "used": 25000,
                "available": 25000,
                "max_per_trade": 10000,
            },
            "options-trader": {
                "allocated": 100000,
                "used": 40000,
                "available": 60000,
                "max_per_trade": 20000,
            },
            "futures-trader": {
                "allocated": 200000,
                "used": 100000,
                "available": 100000,
                "max_per_trade": 50000,
            },
        }
        
        return capital_data.get(
            bot_name,
            {"allocated": 0, "used": 0, "available": 0, "max_per_trade": 0},
        )
    else:
        # For live trading, create a temporary portfolio manager to get real data
        try:
            temp_manager = PortfolioManager(paper_trade=False)
            capital_data = asyncio.run(temp_manager.get_real_time_capital())
            
            # Convert to old format for backward compatibility
            return {
                "allocated": capital_data.total_capital,
                "used": capital_data.used_margin,
                "available": capital_data.available_cash,
                "max_per_trade": capital_data.available_cash * 0.1,  # 10% max per trade
            }
        except Exception as e:
            print(f"Error getting real capital data: {e}, falling back to mock")
            return {"allocated": 0, "used": 0, "available": 0, "max_per_trade": 0}