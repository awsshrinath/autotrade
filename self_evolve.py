from runner.logger import Logger
import datetime
import os
import sys

# Add project root to path to fix import issues
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from gpt_runner.gpt_runner import run_gpt_runner

def self_evolve():
    today_date = datetime.datetime.now().strftime("%Y-%m-%d")
    logger = Logger(today_date)
    logger.log_event("Starting self-evolution pipeline...")

    # 1. Run GPT analysis and get improvement suggestions
    gpt_results = run_gpt_runner()
    logger.log_event(f"GPT analysis results: {gpt_results}")

    # 2. Apply code/strategy patch (to staging branch or temp file)
    # 3. Backtest the new code/strategy
    # 4. Deploy if better, else revert

    logger.log_event("Self-evolution pipeline complete.")

if __name__ == "__main__":
    self_evolve() 