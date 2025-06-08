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
                self.logger.log_event(f"[Firestore Error] log_trade failed: {e}")

    def fetch_trades(self, bot_name, date_str=None, date=None):
        # Handle backward compatibility for 'date' parameter
        if date_str is None and date is not None:
            date_str = date
        elif date_str is None:
            raise ValueError("Either date_str or date parameter must be provided")
            
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
                self.logger.log_event(f"[Firestore Error] fetch_trades failed: {e}")
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

            print(f"[FIRESTORE] ⚠️ No open trade found for {symbol} to update exit.")
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
                self.logger.log_event(f"Reflection logged for {bot_name} on {date_str}")
        except Exception as e:
            if self.logger:
                self.logger.log_event(f"[Firestore Error] log_reflection failed: {e}")

    def store_daily_plan(self, plan):
        try:
            date_str = plan.get("date", datetime.datetime.now().strftime("%Y-%m-%d"))
            doc_ref = self.db.collection("gpt_runner_daily_plan").document(date_str)
            doc_ref.set(plan)
            if self.logger:
                self.logger.log_event(
                    f"[Firestore] Stored daily strategy plan for {date_str}"
                )
        except Exception as e:
            if self.logger:
                self.logger.log_event(f"[Firestore Error] store_daily_plan failed: {e}")

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

            doc_ref = self.db.collection("gpt_runner_daily_plan").document(date_str)
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
                self.logger.log_event(f"[Firestore Error] fetch_daily_plan failed: {e}")
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
                self.logger.log_event(f"[Firestore Error] fetch_reflection failed: {e}")
            return ""

    # --- COGNITIVE SYSTEM LOGGING ---

    def log_cognitive_thought(self, thought_data):
        """Log a cognitive thought entry"""
        try:
            doc_ref = self.db.collection("thought_journal").document()
            doc_ref.set(thought_data)
            if self.logger:
                self.logger.log_event(f"Cognitive thought logged: {thought_data.get('decision', 'Unknown')}")
        except Exception as e:
            if self.logger:
                self.logger.log_event(f"[Firestore Error] log_cognitive_thought failed: {e}")

    def log_memory_item(self, collection_name, memory_data):
        """Log a memory item to specified cognitive collection"""
        try:
            doc_ref = self.db.collection(collection_name).document()
            doc_ref.set(memory_data)
            if self.logger:
                self.logger.log_event(f"Memory item logged to {collection_name}")
        except Exception as e:
            if self.logger:
                self.logger.log_event(f"[Firestore Error] log_memory_item failed: {e}")

    def log_state_transition(self, transition_data):
        """Log a cognitive state transition"""
        try:
            doc_ref = self.db.collection("state_transitions").document()
            doc_ref.set(transition_data)
            if self.logger:
                self.logger.log_event(f"State transition logged: {transition_data.get('from_state')} -> {transition_data.get('to_state')}")
        except Exception as e:
            if self.logger:
                self.logger.log_event(f"[Firestore Error] log_state_transition failed: {e}")

    def log_decision_analysis(self, analysis_data):
        """Log a decision analysis result"""
        try:
            doc_ref = self.db.collection("decision_analysis").document()
            doc_ref.set(analysis_data)
            if self.logger:
                self.logger.log_event(f"Decision analysis logged: {analysis_data.get('decision_id', 'Unknown')}")
        except Exception as e:
            if self.logger:
                self.logger.log_event(f"[Firestore Error] log_decision_analysis failed: {e}")

    def log_bias_detection(self, bias_data):
        """Log a detected cognitive bias"""
        try:
            doc_ref = self.db.collection("bias_tracking").document()
            doc_ref.set(bias_data)
            if self.logger:
                self.logger.log_event(f"Bias detection logged: {bias_data.get('bias_type', 'Unknown')}")
        except Exception as e:
            if self.logger:
                self.logger.log_event(f"[Firestore Error] log_bias_detection failed: {e}")

    def log_learning_metric(self, learning_data):
        """Log a learning progress metric"""
        try:
            doc_ref = self.db.collection("learning_metrics").document()
            doc_ref.set(learning_data)
            if self.logger:
                self.logger.log_event(f"Learning metric logged: {learning_data.get('learning_type', 'Unknown')}")
        except Exception as e:
            if self.logger:
                self.logger.log_event(f"[Firestore Error] log_learning_metric failed: {e}")

    def log_performance_attribution(self, attribution_data):
        """Log a performance attribution analysis"""
        try:
            doc_ref = self.db.collection("performance_attribution").document()
            doc_ref.set(attribution_data)
            if self.logger:
                self.logger.log_event(f"Performance attribution logged")
        except Exception as e:
            if self.logger:
                self.logger.log_event(f"[Firestore Error] log_performance_attribution failed: {e}")

    def log_system_error(self, collection_name, error_type, error_message, error_details):
        """Log system errors to Firestore for monitoring and debugging"""
        try:
            error_data = {
                "error_type": error_type,
                "error_message": error_message,
                "error_details": error_details,
                "timestamp": datetime.datetime.now().isoformat(),
                "source": "system_error_handler"
            }
            doc_ref = self.db.collection(collection_name).document()
            doc_ref.set(error_data)
            if self.logger:
                self.logger.log_event(f"System error logged to {collection_name}: {error_type}")
        except Exception as e:
            if self.logger:
                self.logger.log_event(f"[Firestore Error] log_system_error failed: {e}")
            # Fallback: print to console if Firestore logging fails
            print(f"Failed to log system error to Firestore: {e}")

    def get_cognitive_summary(self, days_back=7):
        """Get a summary of cognitive system activity"""
        try:
            cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days_back)
            
            # Count recent thoughts
            thoughts_query = (
                self.db.collection("thought_journal")
                .where("timestamp", ">=", cutoff_date)
            )
            thoughts_count = len(list(thoughts_query.stream()))
            
            # Count recent state transitions
            transitions_query = (
                self.db.collection("state_transitions")
                .where("timestamp", ">=", cutoff_date)
            )
            transitions_count = len(list(transitions_query.stream()))
            
            # Count detected biases
            biases_query = (
                self.db.collection("bias_tracking")
                .where("timestamp", ">=", cutoff_date)
            )
            biases_count = len(list(biases_query.stream()))
            
            summary = {
                "period_days": days_back,
                "thoughts_recorded": thoughts_count,
                "state_transitions": transitions_count,
                "biases_detected": biases_count,
                "timestamp": datetime.datetime.now().isoformat()
            }
            
            if self.logger:
                self.logger.log_event(f"Cognitive summary generated: {summary}")
            
            return summary
            
        except Exception as e:
            if self.logger:
                self.logger.log_event(f"[Firestore Error] get_cognitive_summary failed: {e}")
            return {}

    def cleanup_old_cognitive_data(self, days_to_keep=30):
        """Clean up old cognitive data to manage storage costs"""
        try:
            cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days_to_keep)
            
            # Collections to clean up (excluding long_term_memory and episodic_memory)
            collections_to_clean = [
                "working_memory",
                "short_term_memory", 
                "thought_journal",
                "state_transitions"
            ]
            
            total_deleted = 0
            
            for collection_name in collections_to_clean:
                # Get old documents
                old_docs_query = (
                    self.db.collection(collection_name)
                    .where("timestamp", "<", cutoff_date)
                    .limit(100)  # Process in batches
                )
                
                old_docs = list(old_docs_query.stream())
                
                # Delete old documents
                for doc in old_docs:
                    doc.reference.delete()
                    total_deleted += 1
            
            if self.logger:
                self.logger.log_event(f"Cleaned up {total_deleted} old cognitive records older than {days_to_keep} days")
            
            return total_deleted
            
        except Exception as e:
            if self.logger:
                self.logger.log_event(f"[Firestore Error] cleanup_old_cognitive_data failed: {e}")
            return 0


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
        yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime(
            "%Y-%m-%d"
        )

        # Try to get today's trades first
        collection_ref = (
            client.collection("gpt_runner_trades").document(bot_name).collection(today)
        )
        docs = (
            collection_ref.order_by("entry_time", direction=firestore.Query.DESCENDING)
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
