import os
import random

# Skip locust import if OpenAI API key is not set to avoid collection errors
try:
    # Set a dummy OpenAI API key if not present to prevent import errors
    if not os.getenv('OPENAI_API_KEY'):
        os.environ['OPENAI_API_KEY'] = 'dummy-key-for-testing'
    from locust import HttpUser, task, between
except ImportError:
    # Create dummy classes if locust is not available
    class HttpUser:
        pass
    def task(weight=1):
        def decorator(func):
            return func
        # Handle both @task and @task(weight) syntax
        if callable(weight):
            return weight
        return decorator
    def between(min_wait, max_wait):
        return lambda: min_wait

class TradingSystemUser(HttpUser):
    wait_time = between(1, 5)  # Wait 1-5 seconds between tasks

    def on_start(self):
        """On start, log in a user"""
        # In a real system, you'd perform a login here
        # For now, we'll just print a message
        print("Starting new user...")

    @task
    def get_market_regime(self):
        """Simulate fetching the market regime"""
        instrument_id = 256265  # NIFTY 50
        self.client.get(f"/market/regime/{instrument_id}")

    @task(3) # This task will be picked 3x more often
    def get_latest_candle(self):
        """Simulate fetching the latest candle data"""
        instrument_token = random.choice([256265, 260105, 11924738]) # NIFTY, BANKNIFTY, NIFTY IT
        self.client.get(f"/market/latest_candle/{instrument_token}")

    @task
    def get_correlation_matrix(self):
        """Simulate fetching the correlation matrix"""
        self.client.get("/market/correlation")

if __name__ == "__main__":
    # This allows running the script directly for local testing
    # but it's typically run via the `locust` command
    print("This script should be run with the 'locust' command.")
    print("Example: locust -f tests/test_load.py --host=http://localhost:8000") 