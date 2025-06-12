"""
Paper Trading Module - Comprehensive paper trading simulation
Simulates trading with ₹1,00,000 capital distributed across stocks, options, and futures
with realistic margin calculations, SL/Target tracking, and Firestore logging
"""

import datetime
import time
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import traceback

from runner.firestore_client import FirestoreClient
from strategies.vwap_strategy import vwap_strategy, vwap_exit_strategy
from strategies.scalp_strategy import scalp_strategy
from strategies.opening_range_strategy import opening_range_strategy
from runner.config import get_config, is_paper_trade


class TradeStatus(Enum):
    OPEN = "open"
    CLOSED_TARGET = "closed_target"
    CLOSED_SL = "closed_sl"
    CLOSED_MANUAL = "closed_manual"
    CLOSED_EOD = "closed_eod"
    REJECTED_INSUFFICIENT_MARGIN = "rejected_insufficient_margin"


class SegmentType(Enum):
    STOCKS = "stocks"
    OPTIONS = "options"
    FUTURES = "futures"


@dataclass
class PaperTrade:
    """Represents a paper trade with all necessary details"""
    trade_id: str
    symbol: str
    segment: SegmentType
    strategy: str
    direction: str  # bullish/bearish
    entry_price: float
    quantity: int
    stop_loss: float
    target: float
    margin_used: float
    entry_time: datetime.datetime
    exit_price: Optional[float] = None
    exit_time: Optional[datetime.datetime] = None
    status: TradeStatus = TradeStatus.OPEN
    pnl: float = 0.0
    exit_reason: str = ""
    lot_size: int = 1  # For options and futures


@dataclass
class CapitalAllocation:
    """Tracks capital allocation across segments"""
    total_capital: float = 100000.0  # ₹1,00,000
    stocks_allocation: float = 40000.0  # 40%
    options_allocation: float = 30000.0  # 30%
    futures_allocation: float = 30000.0  # 30%
    
    # Available capital (reduces with open positions)
    stocks_available: float = 40000.0
    options_available: float = 30000.0
    futures_available: float = 30000.0
    
    # Used margins
    stocks_margin_used: float = 0.0
    options_margin_used: float = 0.0
    futures_margin_used: float = 0.0


@dataclass
class PerformanceSummary:
    """Performance summary for reporting"""
    date: str
    total_trades: int
    winning_trades: int
    losing_trades: int
    total_pnl: float
    return_percentage: float
    stocks_pnl: float
    options_pnl: float
    futures_pnl: float
    avg_win: float
    avg_loss: float
    win_rate: float


class PaperTrader:
    """Comprehensive paper trading simulation"""
    
    def __init__(self, logger=None, firestore_client=None):
        self.logger = logger or logging.getLogger(__name__)
        self.firestore_client = firestore_client or FirestoreClient(logger=self.logger)
        
        # Initialize capital allocation
        self.capital = CapitalAllocation()
        
        # Track active trades
        self.active_trades: List[PaperTrade] = []
        self.completed_trades: List[PaperTrade] = []
        
        # Performance tracking
        self.daily_pnl = 0.0
        self.weekly_pnl = 0.0
        self.monthly_pnl = 0.0
        
        # Margin requirements (realistic estimates)
        self.margin_requirements = {
            "NIFTY_FUTURES": 60000,  # NIFTY futures margin
            "BANKNIFTY_FUTURES": 40000,  # BANKNIFTY futures margin
            "STOCK_FUTURES": 0.15,  # 15% of notional value for stock futures
            "OPTIONS_MULTIPLIER": 1.0,  # Premium * lot_size for options
            "STOCKS_MULTIPLIER": 1.0,  # Full amount for stocks (no leverage)
        }
        
        # Lot sizes
        self.lot_sizes = {
            "NIFTY": 50,
            "BANKNIFTY": 15,
            "FINNIFTY": 40,
            "MIDCPNIFTY": 75,
            "default_stock": 1
        }
        
        self.logger.info("PaperTrader initialized with ₹1,00,000 capital allocation")

    def calculate_required_margin(self, symbol: str, segment: SegmentType, 
                                price: float, quantity: int, lot_size: int = 1) -> float:
        """Calculate required margin for a trade"""
        
        if segment == SegmentType.STOCKS:
            # For stocks, full amount required (no leverage in paper trading)
            return price * quantity
            
        elif segment == SegmentType.OPTIONS:
            # For options, premium * lot_size * quantity
            return price * lot_size * quantity
            
        elif segment == SegmentType.FUTURES:
            # For futures, use predefined margin requirements
            if "NIFTY" in symbol.upper() and "BANK" not in symbol.upper():
                return self.margin_requirements["NIFTY_FUTURES"] * quantity
            elif "BANKNIFTY" in symbol.upper():
                return self.margin_requirements["BANKNIFTY_FUTURES"] * quantity
            else:
                # Stock futures - 15% of notional value
                notional_value = price * lot_size * quantity
                return notional_value * self.margin_requirements["STOCK_FUTURES"]
        
        return 0.0

    def check_margin_availability(self, segment: SegmentType, required_margin: float) -> bool:
        """Check if sufficient margin is available for a trade"""
        
        if segment == SegmentType.STOCKS:
            return self.capital.stocks_available >= required_margin
        elif segment == SegmentType.OPTIONS:
            return self.capital.options_available >= required_margin
        elif segment == SegmentType.FUTURES:
            return self.capital.futures_available >= required_margin
            
        return False

    def get_lot_size(self, symbol: str) -> int:
        """Get lot size for a symbol"""
        symbol_upper = symbol.upper()
        
        if "NIFTY" in symbol_upper and "BANK" not in symbol_upper:
            return self.lot_sizes["NIFTY"]
        elif "BANKNIFTY" in symbol_upper:
            return self.lot_sizes["BANKNIFTY"]
        elif "FINNIFTY" in symbol_upper:
            return self.lot_sizes["FINNIFTY"]
        elif "MIDCPNIFTY" in symbol_upper:
            return self.lot_sizes["MIDCPNIFTY"]
        else:
            return self.lot_sizes["default_stock"]

    def determine_segment(self, symbol: str, strategy: str) -> SegmentType:
        """Determine the trading segment based on symbol and strategy"""
        symbol_upper = symbol.upper()
        
        # Check for futures patterns
        if any(keyword in symbol_upper for keyword in ["FUT", "FUTURES"]) or \
           (any(index in symbol_upper for index in ["NIFTY", "BANKNIFTY", "FINNIFTY"]) and "CE" not in symbol_upper and "PE" not in symbol_upper):
            return SegmentType.FUTURES
            
        # Check for options patterns
        if any(keyword in symbol_upper for keyword in ["CE", "PE", "CALL", "PUT"]):
            return SegmentType.OPTIONS
            
        # Default to stocks
        return SegmentType.STOCKS

    def execute_paper_trade(self, trade_signal: Dict[str, Any], strategy: str) -> Optional[PaperTrade]:
        """Execute a paper trade based on the signal"""
        
        try:
            symbol = trade_signal.get("symbol", "")
            entry_price = trade_signal.get("entry_price", 0.0)
            quantity = trade_signal.get("quantity", 0)
            stop_loss = trade_signal.get("stop_loss", 0.0)
            target = trade_signal.get("target", 0.0)
            direction = trade_signal.get("direction", "bullish")
            
            # Determine segment and lot size
            segment = self.determine_segment(symbol, strategy)
            lot_size = self.get_lot_size(symbol) if segment != SegmentType.STOCKS else 1
            
            # For options and futures, adjust quantity based on lot size
            if segment in [SegmentType.OPTIONS, SegmentType.FUTURES] and quantity > lot_size:
                quantity = (quantity // lot_size) * lot_size  # Round down to lot multiples
            
            # Calculate required margin
            required_margin = self.calculate_required_margin(
                symbol, segment, entry_price, quantity, lot_size
            )
            
            # Check margin availability
            if not self.check_margin_availability(segment, required_margin):
                self.logger.warning(f"Insufficient margin for {symbol}. Required: ₹{required_margin:,.2f}")
                
                # Log rejected trade to Firestore
                rejected_trade_data = {
                    "symbol": symbol,
                    "segment": segment.value,
                    "strategy": strategy,
                    "entry_price": entry_price,
                    "quantity": quantity,
                    "required_margin": required_margin,
                    "rejection_reason": "Insufficient Margin",
                    "timestamp": datetime.datetime.now().isoformat(),
                    "status": TradeStatus.REJECTED_INSUFFICIENT_MARGIN.value
                }
                
                self.firestore_client.log_trade(
                    "paper_trader", 
                    datetime.datetime.now().strftime("%Y-%m-%d"),
                    rejected_trade_data
                )
                
                return None
            
            # Create paper trade
            trade_id = f"{symbol}_{strategy}_{int(time.time())}"
            
            paper_trade = PaperTrade(
                trade_id=trade_id,
                symbol=symbol,
                segment=segment,
                strategy=strategy,
                direction=direction,
                entry_price=entry_price,
                quantity=quantity,
                stop_loss=stop_loss,
                target=target,
                margin_used=required_margin,
                entry_time=datetime.datetime.now(),
                lot_size=lot_size
            )
            
            # Update capital allocation
            self._allocate_margin(segment, required_margin)
            
            # Add to active trades
            self.active_trades.append(paper_trade)
            
            # Log trade to Firestore
            trade_data = asdict(paper_trade)
            trade_data["entry_time"] = paper_trade.entry_time.isoformat()
            trade_data["segment"] = paper_trade.segment.value
            trade_data["status"] = paper_trade.status.value
            
            self.firestore_client.log_trade(
                "paper_trader",
                datetime.datetime.now().strftime("%Y-%m-%d"),
                trade_data
            )
            
            self.logger.info(f"Paper trade executed: {symbol} {direction} @ ₹{entry_price}")
            return paper_trade
            
        except Exception as e:
            self.logger.error(f"Error executing paper trade: {e}\n{traceback.format_exc()}")
            return None

    def _allocate_margin(self, segment: SegmentType, margin_amount: float):
        """Allocate margin for a trade"""
        if segment == SegmentType.STOCKS:
            self.capital.stocks_available -= margin_amount
            self.capital.stocks_margin_used += margin_amount
        elif segment == SegmentType.OPTIONS:
            self.capital.options_available -= margin_amount
            self.capital.options_margin_used += margin_amount
        elif segment == SegmentType.FUTURES:
            self.capital.futures_available -= margin_amount
            self.capital.futures_margin_used += margin_amount

    def _release_margin(self, segment: SegmentType, margin_amount: float):
        """Release margin when a trade is closed"""
        if segment == SegmentType.STOCKS:
            self.capital.stocks_available += margin_amount
            self.capital.stocks_margin_used -= margin_amount
        elif segment == SegmentType.OPTIONS:
            self.capital.options_available += margin_amount
            self.capital.options_margin_used -= margin_amount
        elif segment == SegmentType.FUTURES:
            self.capital.futures_available += margin_amount
            self.capital.futures_margin_used -= margin_amount

    def monitor_and_exit_trades(self, current_market_data: Dict[str, float]):
        """Monitor active trades and exit based on SL/Target or market conditions"""
        
        trades_to_close = []
        
        for trade in self.active_trades:
            try:
                current_price = current_market_data.get(trade.symbol, trade.entry_price)
                should_exit, exit_reason = self._should_exit_trade(trade, current_price)
                
                if should_exit:
                    trades_to_close.append((trade, current_price, exit_reason))
                    
            except Exception as e:
                self.logger.error(f"Error monitoring trade {trade.trade_id}: {e}")
        
        # Close identified trades
        for trade, exit_price, exit_reason in trades_to_close:
            self.close_paper_trade(trade, exit_price, exit_reason)

    def _should_exit_trade(self, trade: PaperTrade, current_price: float) -> tuple[bool, str]:
        """Determine if a trade should be exited"""
        
        if trade.direction == "bullish":
            # Check target
            if current_price >= trade.target:
                return True, "Target reached"
            # Check stop loss
            if current_price <= trade.stop_loss:
                return True, "Stop loss hit"
        else:  # bearish
            # Check target
            if current_price <= trade.target:
                return True, "Target reached"
            # Check stop loss
            if current_price >= trade.stop_loss:
                return True, "Stop loss hit"
        
        # Check time-based exit (end of day)
        current_time = datetime.datetime.now().time()
        if current_time >= datetime.time(15, 20):  # 3:20 PM
            return True, "End of day square-off"
        
        return False, ""

    def close_paper_trade(self, trade: PaperTrade, exit_price: float, exit_reason: str):
        """Close a paper trade and calculate PnL"""
        
        try:
            # Calculate PnL
            if trade.direction == "bullish":
                pnl = (exit_price - trade.entry_price) * trade.quantity
            else:  # bearish
                pnl = (trade.entry_price - exit_price) * trade.quantity
            
            # Update trade details
            trade.exit_price = exit_price
            trade.exit_time = datetime.datetime.now()
            trade.pnl = pnl
            trade.exit_reason = exit_reason
            
            # Determine status based on exit reason
            if "target" in exit_reason.lower():
                trade.status = TradeStatus.CLOSED_TARGET
            elif "stop loss" in exit_reason.lower():
                trade.status = TradeStatus.CLOSED_SL
            elif "end of day" in exit_reason.lower():
                trade.status = TradeStatus.CLOSED_EOD
            else:
                trade.status = TradeStatus.CLOSED_MANUAL
            
            # Release margin
            self._release_margin(trade.segment, trade.margin_used)
            
            # Move to completed trades
            self.active_trades.remove(trade)
            self.completed_trades.append(trade)
            
            # Update PnL tracking
            self.daily_pnl += pnl
            
            # Log trade exit to Firestore
            exit_data = {
                "exit_price": exit_price,
                "exit_time": trade.exit_time.isoformat(),
                "pnl": pnl,
                "status": trade.status.value,
                "exit_reason": exit_reason
            }
            
            self.firestore_client.log_trade_exit(
                "paper_trader",
                datetime.datetime.now().strftime("%Y-%m-%d"),
                trade.symbol,
                exit_data
            )
            
            self.logger.info(f"Trade closed: {trade.symbol} - PnL: ₹{pnl:.2f} ({exit_reason})")
            
        except Exception as e:
            self.logger.error(f"Error closing trade {trade.trade_id}: {e}")

    def generate_mock_candles(self, symbol: str, current_price: float) -> List[Dict]:
        """Generate mock candle data for strategy testing"""
        import random
        
        candles = []
        price = current_price
        
        for i in range(20):
            # Simulate price movement
            change_pct = random.uniform(-0.02, 0.02)  # ±2% change
            new_price = price * (1 + change_pct)
            
            high = new_price * random.uniform(1.001, 1.01)
            low = new_price * random.uniform(0.99, 0.999)
            
            candle = {
                "high": high,
                "low": low,
                "close": new_price,
                "open": price,
                "volume": random.randint(1000, 10000)
            }
            candles.append(candle)
            price = new_price
        
        return candles

    def run_strategies_and_execute(self, market_data: Dict[str, Any]):
        """Run strategies and execute paper trades"""
        
        try:
            # Run VWAP strategy for stocks
            for symbol in ["RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK"]:
                if symbol in market_data and isinstance(market_data[symbol], dict):
                    current_price = market_data[symbol].get("ltp", 0)
                    if current_price > 0:
                        candles = self.generate_mock_candles(symbol, current_price)
                        available_capital = self.capital.stocks_available * 0.1
                        
                        signal = vwap_strategy(symbol, candles, available_capital)
                        if signal:
                            trade = self.execute_paper_trade(signal, "vwap")
                            if trade:
                                self.logger.info(f"Executed VWAP trade: {symbol}")
            
            # Run scalp strategy for options
            for index_name in ["NIFTY", "BANKNIFTY"]:
                available_capital = self.capital.options_available * 0.2
                
                signal = scalp_strategy(index_name, None, available_capital)
                if signal:
                    trade = self.execute_paper_trade(signal, "scalp")
                    if trade:
                        self.logger.info(f"Executed scalp trade: {signal['symbol']}")
            
            # Run ORB strategy for stocks/futures
            for symbol in ["NIFTY24NOVFUT", "BANKNIFTY24NOVFUT"]:
                if symbol in market_data and isinstance(market_data[symbol], dict):
                    current_price = market_data[symbol].get("ltp", 0)
                    if current_price > 0:
                        # Create mock stock data and open range for ORB
                        stock_data = {
                            "symbol": symbol,
                            "ltp": current_price
                        }
                        open_range = {
                            "high": current_price * 1.005,
                            "low": current_price * 0.995
                        }
                        available_capital = self.capital.futures_available * 0.3
                        
                        signal = opening_range_strategy(stock_data, available_capital, open_range)
                        if signal:
                            trade = self.execute_paper_trade(signal, "orb")
                            if trade:
                                self.logger.info(f"Executed ORB trade: {symbol}")
                                
        except Exception as e:
            self.logger.error(f"Error running strategies: {e}")

    def calculate_performance_summary(self, period: str = "daily") -> PerformanceSummary:
        """Calculate performance summary for reporting"""
        
        # Get trades for the specified period
        if period == "daily":
            trades = [t for t in self.completed_trades 
                     if t.exit_time and t.exit_time.date() == datetime.date.today()]
        elif period == "weekly":
            week_start = datetime.date.today() - datetime.timedelta(days=7)
            trades = [t for t in self.completed_trades 
                     if t.exit_time and t.exit_time.date() >= week_start]
        elif period == "monthly":
            month_start = datetime.date.today().replace(day=1)
            trades = [t for t in self.completed_trades 
                     if t.exit_time and t.exit_time.date() >= month_start]
        else:
            trades = self.completed_trades
        
        # Calculate metrics
        total_trades = len(trades)
        winning_trades = len([t for t in trades if t.pnl > 0])
        losing_trades = len([t for t in trades if t.pnl < 0])
        total_pnl = sum(t.pnl for t in trades)
        return_percentage = (total_pnl / self.capital.total_capital) * 100
        
        # Segment-wise PnL
        stocks_pnl = sum(t.pnl for t in trades if t.segment == SegmentType.STOCKS)
        options_pnl = sum(t.pnl for t in trades if t.segment == SegmentType.OPTIONS)
        futures_pnl = sum(t.pnl for t in trades if t.segment == SegmentType.FUTURES)
        
        # Win/Loss metrics
        winning_pnls = [t.pnl for t in trades if t.pnl > 0]
        losing_pnls = [t.pnl for t in trades if t.pnl < 0]
        
        avg_win = sum(winning_pnls) / len(winning_pnls) if winning_pnls else 0
        avg_loss = sum(losing_pnls) / len(losing_pnls) if losing_pnls else 0
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        return PerformanceSummary(
            date=datetime.date.today().isoformat(),
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            total_pnl=total_pnl,
            return_percentage=return_percentage,
            stocks_pnl=stocks_pnl,
            options_pnl=options_pnl,
            futures_pnl=futures_pnl,
            avg_win=avg_win,
            avg_loss=avg_loss,
            win_rate=win_rate
        )

    def log_performance_summary(self, period: str = "daily"):
        """Log performance summary to Firestore"""
        
        summary = self.calculate_performance_summary(period)
        
        try:
            # Log to Firestore
            collection_name = f"performance_summary_{period}"
            doc_data = asdict(summary)
            doc_data["timestamp"] = datetime.datetime.now().isoformat()
            
            self.firestore_client.db.collection(collection_name).document(summary.date).set(doc_data)
            
            self.logger.info(f"{period.title()} performance logged: Return {summary.return_percentage:.2f}%")
            
        except Exception as e:
            self.logger.error(f"Error logging {period} performance: {e}")

    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get data for dashboard integration"""
        
        return {
            "capital_allocation": asdict(self.capital),
            "active_trades": len(self.active_trades),
            "completed_trades_today": len([t for t in self.completed_trades 
                                         if t.exit_time and t.exit_time.date() == datetime.date.today()]),
            "daily_pnl": self.daily_pnl,
            "return_percentage": (self.daily_pnl / self.capital.total_capital) * 100,
            "margin_utilization": {
                "stocks": (self.capital.stocks_margin_used / self.capital.stocks_allocation) * 100,
                "options": (self.capital.options_margin_used / self.capital.options_allocation) * 100,
                "futures": (self.capital.futures_margin_used / self.capital.futures_allocation) * 100
            }
        }

    def weekly_performance_update(self):
        """Weekly performance calculation and logging"""
        self.log_performance_summary("weekly")
        
        # Reset weekly tracking if needed
        week_start = datetime.date.today() - datetime.timedelta(days=7)
        weekly_trades = [t for t in self.completed_trades 
                        if t.exit_time and t.exit_time.date() >= week_start]
        self.weekly_pnl = sum(t.pnl for t in weekly_trades)

    def monthly_performance_update(self):
        """Monthly performance calculation and logging"""
        self.log_performance_summary("monthly")
        
        # Check for dynamic capital scaling (optional feature)
        monthly_return = (self.monthly_pnl / self.capital.total_capital) * 100
        if monthly_return > 10:  # If monthly return > 10%, scale up capital
            self._scale_capital(1.1)  # 10% increase
            self.logger.info(f"Capital scaled up by 10% due to {monthly_return:.2f}% monthly return")

    def _scale_capital(self, scale_factor: float):
        """Scale capital allocation (dynamic capital scaling)"""
        self.capital.total_capital *= scale_factor
        self.capital.stocks_allocation *= scale_factor
        self.capital.options_allocation *= scale_factor
        self.capital.futures_allocation *= scale_factor
        
        # Also scale available amounts proportionally
        self.capital.stocks_available *= scale_factor
        self.capital.options_available *= scale_factor
        self.capital.futures_available *= scale_factor

    def cleanup_old_trades(self, days_to_keep: int = 30):
        """Cleanup old completed trades to manage memory"""
        cutoff_date = datetime.date.today() - datetime.timedelta(days=days_to_keep)
        
        old_trades = [t for t in self.completed_trades 
                     if t.exit_time and t.exit_time.date() < cutoff_date]
        
        for trade in old_trades:
            self.completed_trades.remove(trade)
        
        if old_trades:
            self.logger.info(f"Cleaned up {len(old_trades)} old trades")


# Paper trading toggle check
def is_paper_trading_enabled() -> bool:
    """Check if paper trading is enabled"""
    try:
        return is_paper_trade() or get_config().paper_trade
    except:
        return True  # Default to paper trading if config fails


# Factory function for easy integration
def create_paper_trader(logger=None, firestore_client=None) -> Optional[PaperTrader]:
    """Create PaperTrader instance if paper trading is enabled"""
    
    if is_paper_trading_enabled():
        return PaperTrader(logger=logger, firestore_client=firestore_client)
    
    return None


# Main execution function for testing
if __name__ == "__main__":
    # Test the paper trader
    import logging
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    trader = PaperTrader(logger=logger)
    
    # Test trade execution
    test_signal = {
        "symbol": "NIFTY24NOVFUT",
        "entry_price": 24000.0,
        "quantity": 50,
        "stop_loss": 23800.0,
        "target": 24200.0,
        "direction": "bullish"
    }
    
    trade = trader.execute_paper_trade(test_signal, "test_strategy")
    if trade:
        print(f"Test trade executed: {trade}")
        
        # Test closing the trade
        trader.close_paper_trade(trade, 24100.0, "Manual exit")
        
        # Get performance summary
        summary = trader.calculate_performance_summary()
        print(f"Performance: {summary}")
        
        # Get dashboard data
        dashboard_data = trader.get_dashboard_data()
        print(f"Dashboard data: {dashboard_data}") 