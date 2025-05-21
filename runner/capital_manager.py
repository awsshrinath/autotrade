from datetime import datetime

from google.cloud import firestore
from kiteconnect import KiteConnect

# Global cache for capital values
_capital_cache = {}


def get_current_capital(bot_name):
    """
    Get the current capital allocation for a specific bot.

    Args:
        bot_name (str): The name of the bot

    Returns:
        dict: A dictionary containing capital allocation information
    """
    # Check if we have a cached value
    if bot_name in _capital_cache:
        return _capital_cache[bot_name]

    # Mock capital data for testing
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

    # Get the capital data for the specified bot
    result = capital_data.get(
        bot_name,
        {"allocated": 0, "used": 0, "available": 0, "max_per_trade": 0},
    )

    # Cache the result
    _capital_cache[bot_name] = result

    return result


class CapitalManager:
    def __init__(self, kite: KiteConnect):
        self.kite = kite
        self.firestore = firestore.Client()
        self.today = datetime.now().strftime("%Y-%m-%d")

        # Fetch only once and store
        self.available_balance = self.fetch_balance()

    def fetch_balance(self) -> float:
        try:
            margin = self.kite.margins()
            cash = margin["equity"]["available"]["cash"]
            print(f"[CAPITAL] Available balance: ₹{cash}")
            # Store in Firestore
            self.firestore.collection("gpt_runner_logs").document(
                "capital_" + self.today
            ).set(
                {
                    "available_balance": cash,
                    "timestamp": datetime.now().isoformat(),
                }
            )
            return cash
        except Exception as e:
            print("[ERROR] Failed to fetch margin:", e)
            return 0.0

    def allocate(self):
        capital = self.available_balance

        if capital < 20000:
            return {
                "mode": "stock",
                "allocation": capital * 5,  # Try MIS 5X leverage
                "margin_type": "MIS",
            }
        elif capital < 50000:
            return {
                "mode": "mixed",
                "stocks": capital * 0.6,
                "options": capital * 0.4,
                "allocation": capital,
                "margin_type": "MIS",
            }
        else:
            return {
                "mode": "all",
                "futures": capital * 0.5,
                "stock_option": capital * 0.5,
                "allocation": capital,
                "margin_type": "MIS",
            }
