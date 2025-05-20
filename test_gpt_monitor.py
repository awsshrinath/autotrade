from runner.gpt_self_improvement_monitor import GPTSelfImprovementMonitor
from runner.logger import Logger
from runner.firestore_client import FirestoreClient
from runner.openai_manager import OpenAIManager

# 🔧 Instantiate dependencies
logger = Logger(log_dir="logs")
firestore = FirestoreClient()
gpt = OpenAIManager()

# 🧠 Instantiate the monitor
monitor = GPTSelfImprovementMonitor(logger=logger, firestore_client=firestore, gpt_client=gpt)

# ✅ Run the analysis
monitor.analyze_errors(log_path="logs/gpt_runner.log")
