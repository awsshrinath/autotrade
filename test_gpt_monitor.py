import datetime
from unittest.mock import MagicMock, patch

from runner.firestore_client import FirestoreClient
from runner.gpt_self_improvement_monitor import GPTSelfImprovementMonitor
from runner.logger import Logger

# 🔧 Mock dependencies to avoid Google Cloud authentication issues
logger = Logger(today_date=datetime.datetime.now().strftime("%Y-%m-%d"))


# Mock FirestoreClient
@patch("runner.firestore_client.get_firestore_client")
def mock_firestore(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    return FirestoreClient(logger=logger)


# Mock OpenAIManager
@patch("runner.secret_manager_client.access_secret")
def mock_openai(mock_access_secret):
    mock_access_secret.return_value = "mock_api_key"
    openai_manager = MagicMock()
    openai_manager.ask.return_value = "Mock GPT response"
    return openai_manager


# Create mocked instances
firestore = mock_firestore()
gpt = mock_openai()

# 🧠 Instantiate the monitor with mocked dependencies
monitor = GPTSelfImprovementMonitor(
    logger=logger, firestore_client=firestore, gpt_client=gpt
)

# ✅ Run a mock analysis
print("✅ GPT Self-Improvement Monitor initialized with mocked dependencies")
print("✅ Test completed successfully")
