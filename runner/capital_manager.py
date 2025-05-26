"""
Enhanced Capital Manager - Replacement for the old mock-only version
Now uses the enterprise PortfolioManager with full paper trade support
"""

from runner.capital.portfolio_manager import (
    create_portfolio_manager,
    get_current_capital,
)
import os
import asyncio
from datetime import datetime


class CapitalManager:
    """Enhanced capital manager using enterprise portfolio manager"""

    def __init__(self, kite=None, firestore=None, logger=None):
        self.kite = kite
        self.firestore = firestore
        self.logger = logger

        # Determine environment
        self.paper_trade = os.getenv("PAPER_TRADE", "true").lower() == "true"
        initial_capital = float(os.getenv("DEFAULT_CAPITAL", 100000))

        # Create enterprise portfolio manager
        self.portfolio_manager = create_portfolio_manager(
            kite=kite,
            firestore=firestore,
            logger=logger,
            initial_capital=initial_capital,
            paper_trade=self.paper_trade,
        )

        if self.logger:
            self.logger.log_event(
                f"Enhanced CapitalManager initialized - Paper Trade: {self.paper_trade}, "
                f"Initial Capital: ₹{initial_capital:,.2f}"
            )

    def fetch_balance(self) -> float:
        """
        Fetch current available balance (compatible with old interface)
        """
        try:
            capital_data = asyncio.run(self.portfolio_manager.get_real_time_capital())
            available_balance = capital_data.available_cash

            if self.logger:
                self.logger.log_event(
                    f"[CAPITAL] Available balance: ₹{available_balance:,.2f}"
                )

            return available_balance

        except Exception as e:
            if self.logger:
                self.logger.log_event(f"[ERROR] Failed to fetch balance: {e}")
            return 0.0

    def allocate(self, strategy: str = None, capital_request: float = None):
        """
        Enhanced capital allocation with strategy-based logic
        """
        try:
            capital_data = asyncio.run(self.portfolio_manager.get_real_time_capital())
            total_capital = capital_data.total_capital
            available_cash = capital_data.available_cash

            # Strategy-based allocation
            if strategy and strategy.lower() in ["scalp", "options"]:
                allocation_pct = 0.05  # 5% for high-frequency strategies
            elif strategy and strategy.lower() in ["momentum", "vwap"]:
                allocation_pct = 0.1  # 10% for medium-term strategies
            elif strategy and strategy.lower() in ["swing", "orb"]:
                allocation_pct = 0.15  # 15% for longer-term strategies
            else:
                allocation_pct = 0.08  # 8% default allocation

            # Calculate allocation
            if capital_request:
                allocated_amount = min(capital_request, available_cash * allocation_pct)
            else:
                allocated_amount = available_cash * allocation_pct

            # Determine trading mode and margin type
            if total_capital < 20000:
                return {
                    "mode": "stock",
                    "allocation": allocated_amount * 5,  # 5X leverage for MIS
                    "margin_type": "MIS",
                    "available_cash": available_cash,
                    "paper_trade": self.paper_trade,
                    "strategy": strategy,
                }
            elif total_capital < 50000:
                return {
                    "mode": "mixed",
                    "stocks": allocated_amount * 0.6,
                    "options": allocated_amount * 0.4,
                    "allocation": allocated_amount,
                    "margin_type": "MIS",
                    "available_cash": available_cash,
                    "paper_trade": self.paper_trade,
                    "strategy": strategy,
                }
            else:
                return {
                    "mode": "all",
                    "futures": allocated_amount * 0.5,
                    "stock_option": allocated_amount * 0.5,
                    "allocation": allocated_amount,
                    "margin_type": "MIS",
                    "available_cash": available_cash,
                    "paper_trade": self.paper_trade,
                    "strategy": strategy,
                }

        except Exception as e:
            if self.logger:
                self.logger.log_event(f"[ERROR] Capital allocation failed: {e}")

            # Fallback allocation
            return {
                "mode": "conservative",
                "allocation": 10000,  # Conservative fallback
                "margin_type": "NRML",
                "available_cash": 10000,
                "paper_trade": True,
                "error": str(e),
            }

    def get_position_size_recommendation(
        self, symbol: str, strategy: str, price: float, volatility: float = 0.02
    ):
        """
        Get intelligent position size recommendation
        """
        try:
            position_info = self.portfolio_manager.calculate_position_size(
                symbol=symbol,
                strategy=strategy,
                price=price,
                volatility=volatility,
                confidence=0.7,
            )

            return {
                "recommended_quantity": position_info.get("recommended_quantity", 0),
                "position_value": position_info.get("position_value", 0),
                "risk_amount": position_info.get("risk_amount", 0),
                "allocation_pct": position_info.get("final_allocation_pct", 0),
                "kelly_fraction": position_info.get("kelly_fraction", 0),
                "confidence_level": 0.7,
                "paper_trade": self.paper_trade,
            }

        except Exception as e:
            if self.logger:
                self.logger.log_event(f"[ERROR] Position sizing failed: {e}")

            # Simple fallback
            safe_quantity = int(10000 / price) if price > 0 else 0
            return {
                "recommended_quantity": safe_quantity,
                "position_value": safe_quantity * price,
                "allocation_pct": 5.0,
                "error": str(e),
                "paper_trade": True,
            }

    def risk_check(self, trade_request: dict) -> tuple:
        """
        Perform comprehensive risk check
        """
        try:
            risk_passed, risk_message = self.portfolio_manager.risk_check_before_trade(
                trade_request
            )
            return risk_passed, risk_message

        except Exception as e:
            if self.logger:
                self.logger.log_event(f"[ERROR] Risk check failed: {e}")
            return False, f"Risk check error: {str(e)}"

    def update_position(
        self,
        symbol: str,
        quantity: int,
        price: float,
        strategy: str,
        position_type: str = "stock",
    ):
        """
        Update or create position in portfolio
        """
        try:
            success = self.portfolio_manager.update_position(
                symbol=symbol,
                quantity=quantity,
                price=price,
                strategy=strategy,
                position_type=position_type,
            )

            if self.logger and success:
                self.logger.log_event(
                    f"[POSITION] Updated {symbol}: {quantity} @ ₹{price:.2f}"
                )

            return success

        except Exception as e:
            if self.logger:
                self.logger.log_event(f"[ERROR] Position update failed: {e}")
            return False

    def get_portfolio_summary(self):
        """
        Get comprehensive portfolio summary
        """
        try:
            return self.portfolio_manager.get_portfolio_summary()
        except Exception as e:
            if self.logger:
                self.logger.log_event(f"[ERROR] Portfolio summary failed: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "paper_trade": self.paper_trade,
            }

    def get_risk_metrics(self, days: int = 30):
        """
        Get portfolio risk metrics
        """
        try:
            return self.portfolio_manager.calculate_portfolio_metrics(days)
        except Exception as e:
            if self.logger:
                self.logger.log_event(f"[ERROR] Risk metrics calculation failed: {e}")
            return None


# Backward compatibility functions
def get_current_capital_enhanced(bot_name: str) -> dict:
    """
    Enhanced version of get_current_capital with real portfolio management
    """
    try:
        # Use the new enterprise function
        return get_current_capital(bot_name)
    except Exception as e:
        # Fallback to basic structure
        return {
            "allocated": 0,
            "used": 0,
            "available": 0,
            "max_per_trade": 0,
            "error": str(e),
        }


# Factory function
def create_capital_manager(kite=None, firestore=None, logger=None):
    """
    Create enhanced capital manager instance
    """
    return CapitalManager(kite, firestore, logger)
