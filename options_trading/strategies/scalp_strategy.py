from strategies.base_strategy import BaseStrategy
from runner.utils.option_utils import get_next_expiry_and_atm_option
from runner.config import SCALP_CONFIG

class ScalpStrategy(BaseStrategy):
    def __init__(self, kite, logger):
        self.kite = kite
        self.logger = logger

    def analyze(self):
        try:
            self.logger.log_event("[SCALP] Scanning for ATM options using config-based filters...")

            expiry, ce_symbol, pe_symbol, ce_price, pe_price = get_next_expiry_and_atm_option(self.kite)

            min_price = SCALP_CONFIG.get("min_price", 100)
            max_price = SCALP_CONFIG.get("max_price", 120)
            sl_buffer = SCALP_CONFIG.get("sl_buffer", 30)
            target_buffer = SCALP_CONFIG.get("target_buffer", 60)
            qty = SCALP_CONFIG.get("quantity", 75)

            if min_price <= ce_price <= max_price:
                trade = {
                    "symbol": ce_symbol,
                    "entry_price": ce_price,
                    "stop_loss": ce_price - sl_buffer,
                    "target": ce_price + target_buffer,
                    "quantity": qty,
                    "direction": "bullish",
                    "strategy": "scalp"
                }
                self.logger.log_event(f"[SCALP] Bullish signal: {trade}")
                return trade

            if min_price <= pe_price <= max_price:
                trade = {
                    "symbol": pe_symbol,
                    "entry_price": pe_price,
                    "stop_loss": pe_price - sl_buffer,
                    "target": pe_price + target_buffer,
                    "quantity": qty,
                    "direction": "bearish",
                    "strategy": "scalp"
                }
                self.logger.log_event(f"[SCALP] Bearish signal: {trade}")
                return trade

            self.logger.log_event("[SCALP] No valid option found in configured range.")
            return None

        except Exception as e:
            self.logger.log_event(f"[SCALP][ERROR] {e}")
            return None

    def should_exit(self, trade, current_price):
        try:
            if current_price <= trade["stop_loss"]:
                return "sl_hit"
            elif current_price >= trade["target"]:
                return "target_hit"
            return None
        except Exception as e:
            self.logger.log_event(f"[SCALP][ERROR] Exit logic failed: {e}")
            return None
