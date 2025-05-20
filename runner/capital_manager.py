
from kiteconnect import KiteConnect
from google.cloud import firestore
from datetime import datetime

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
            cash = margin['equity']['available']['cash']
            print(f"[CAPITAL] Available balance: ₹{cash}")
            # Store in Firestore
            self.firestore.collection("gpt_runner_logs").document("capital_" + self.today).set({
                "available_balance": cash,
                "timestamp": datetime.now().isoformat()
            })
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
                "margin_type": "MIS"
            }
        elif capital < 50000:
            return {
                "mode": "mixed",
                "stocks": capital * 0.6,
                "options": capital * 0.4,
                "allocation": capital,
                "margin_type": "MIS"
            }
        else:
            return {
                "mode": "all",
                "futures": capital * 0.5,
                "stock_option": capital * 0.5,
                "allocation": capital,
                "margin_type": "MIS"
            }
