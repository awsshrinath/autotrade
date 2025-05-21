# runner/firestore_client.py

import datetime

from google.cloud import firestore

_firestore_client = None


def get_firestore_client():
    global _firestore_client
    if _firestore_client is None:
        _firestore_client = firestore.Client()
    return _firestore_client


class FirestoreClient:
    def __init__(self, logger=None):
        self.db = get_firestore_client()
        self.logger = logger

    # --- TRADE LOGGING ---

    def log_trade(self, bot_name, date_str, trade_data):
        try:
            doc_ref = (
                self.db.collection("gpt_runner_trades")
                .document(bot_name)
                .collection(date_str)
                .document()
            )
            doc_ref.set(trade_data)
            if self.logger:
                self.logger.log_event(
                    f"Trade logged for {bot_name} on {date_str}: {trade_data}"
                )
        except Exception as e:
            if self.logger:
                self.logger.log_event(
                    f"[Firestore Error] log_trade failed: {e}"
                )

    def fetch_trades(self, bot_name, date_str):
        try:
            collection_ref = (
                self.db.collection("gpt_runner_trades")
                .document(bot_name)
                .collection(date_str)
            )
            docs = collection_ref.stream()
            return [doc.to_dict() for doc in docs]
        except Exception as e:
            if self.logger:
                self.logger.log_event(
                    f"[Firestore Error] fetch_trades failed: {e}"
                )
            return []

    # --- TRADE EXIT LOGGING ---

    def log_trade_exit(self, bot_name, date_str, symbol, exit_data):
        try:
            collection = (
                self.db.collection("gpt_runner_trades")
                .document(bot_name)
                .collection(date_str)
            )
            # Find matching trade by symbol and status "open"
            docs = (
                collection.where("symbol", "==", symbol)
                .where("status", "==", "open")
                .stream()
            )

            for doc in docs:
                doc.reference.update(
                    {
                        "exit_price": exit_data.get("exit_price"),
                        "exit_time": exit_data.get("exit_time"),
                        "status": exit_data.get("status"),
                    }
                )
                print(f"[FIRESTORE] ✅ Exit updated for {symbol}")
                return

            print(
                f"[FIRESTORE] ⚠️ No open trade found for {symbol} to update exit."
            )
        except Exception as e:
            print(f"[FIRESTORE] ❌ Failed to update exit for {symbol}: {e}")

    # --- GPT SELF-REFLECTION LOGGING ---

    def log_reflection(self, bot_name, date_str, reflection_text):
        try:
            doc_ref = (
                self.db.collection("gpt_runner_reflections")
                .document(bot_name)
                .collection("days")
                .document(date_str)
            )
            doc_ref.set({"reflection": reflection_text})
            if self.logger:
                self.logger.log_event(
                    f"Reflection logged for {bot_name} on {date_str}"
                )
        except Exception as e:
            if self.logger:
                self.logger.log_event(
                    f"[Firestore Error] log_reflection failed: {e}"
                )

    def store_daily_plan(self, plan):
        try:
            date_str = plan.get(
                "date", datetime.datetime.now().strftime("%Y-%m-%d")
            )
            doc_ref = self.db.collection("gpt_runner_daily_plan").document(
                date_str
            )
            doc_ref.set(plan)
            if self.logger:
                self.logger.log_event(
                    f"[Firestore] Stored daily strategy plan for {date_str}"
                )
        except Exception as e:
            if self.logger:
                self.logger.log_event(
                    f"[Firestore Error] store_daily_plan failed: {e}"
                )

    def fetch_daily_plan(self, date_str=None):
        """
        Fetch the daily trading plan from Firestore

        Args:
            date_str (str): The date to fetch the plan for. If None, uses today's date.

        Returns:
            dict: The daily plan or an empty dict if not found
        """
        try:
            if date_str is None:
                date_str = datetime.datetime.now().strftime("%Y-%m-%d")

            doc_ref = self.db.collection("gpt_runner_daily_plan").document(
                date_str
            )
            doc = doc_ref.get()

            if doc.exists:
                plan = doc.to_dict()
                if self.logger:
                    self.logger.log_event(
                        f"[Firestore] Fetched daily plan for {date_str}"
                    )
                return plan
            else:
                if self.logger:
                    self.logger.log_event(
                        f"[Firestore] No daily plan found for {date_str}"
                    )
                return {}

        except Exception as e:
            if self.logger:
                self.logger.log_event(
                    f"[Firestore Error] fetch_daily_plan failed: {e}"
                )
            return {}

    def fetch_reflection(self, bot_name, date_str):
        try:
            doc_ref = (
                self.db.collection("gpt_runner_reflections")
                .document(bot_name)
                .collection("days")
                .document(date_str)
            )
            doc = doc_ref.get()
            return doc.to_dict().get("reflection", "") if doc.exists else ""
        except Exception as e:
            if self.logger:
                self.logger.log_event(
                    f"[Firestore Error] fetch_reflection failed: {e}"
                )
            return ""


def fetch_recent_trades(bot_name, limit=5):
    """
    Fetches the most recent trades for a specific bot.

    Args:
        bot_name (str): The name of the bot
        limit (int): Maximum number of trades to return

    Returns:
        list: List of recent trades
    """
    try:
        client = get_firestore_client()
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        yesterday = (
            datetime.datetime.now() - datetime.timedelta(days=1)
        ).strftime("%Y-%m-%d")

        # Try to get today's trades first
        collection_ref = (
            client.collection("gpt_runner_trades")
            .document(bot_name)
            .collection(today)
        )
        docs = (
            collection_ref.order_by(
                "entry_time", direction=firestore.Query.DESCENDING
            )
            .limit(limit)
            .stream()
        )
        trades = [doc.to_dict() for doc in docs]

        # If we don't have enough trades from today, get some from yesterday
        if len(trades) < limit:
            remaining = limit - len(trades)
            collection_ref = (
                client.collection("gpt_runner_trades")
                .document(bot_name)
                .collection(yesterday)
            )
            docs = (
                collection_ref.order_by(
                    "entry_time", direction=firestore.Query.DESCENDING
                )
                .limit(remaining)
                .stream()
            )
            trades.extend([doc.to_dict() for doc in docs])

        return trades
    except Exception as e:
        print(f"[Firestore Error] fetch_recent_trades failed: {e}")
        return []
