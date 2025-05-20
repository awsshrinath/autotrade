# runner/gpt_self_improvement_monitor.py

from datetime import datetime
from runner.firestore_client import FirestoreClient

class GPTSelfImprovementMonitor:
    def __init__(self, logger, firestore_client: FirestoreClient, gpt_client):
        self.logger = logger
        self.firestore_client = firestore_client
        self.gpt = gpt_client

    def analyze(self, bot_name="stock-trader"):
        date_str = datetime.now().strftime("%Y-%m-%d")
        trades = self.firestore_client.fetch_trades(bot_name, date_str)

        if not trades:
            self.logger.log_event(f"[GPT Reflection] No trades found for {bot_name} on {date_str}")
            return

        summary_prompt = self._build_prompt(trades)
        reflection = self.gpt.ask(summary_prompt)

        if reflection:
            self.firestore_client.log_reflection(bot_name, date_str, reflection)
            self.logger.log_event("[GPT Reflection] Reflection complete and stored.")
        else:
            self.logger.log_event("[GPT Reflection] No reflection generated.")

    def _build_prompt(self, trades):
        summary_lines = []
        for trade in trades:
            line = f"{trade['timestamp']}: {trade['symbol']} | Entry: {trade['entry_price']} | Exit: {trade.get('exit_price', 'NA')} | Status: {trade['status']}"
            summary_lines.append(line)

        summary = "\n".join(summary_lines)
        return (
            "Analyze the following trades for performance and suggest improvements:\n\n"
            f"{summary}\n\n"
            "Provide insights like entry timing, stop loss accuracy, and missed targets."
        )
