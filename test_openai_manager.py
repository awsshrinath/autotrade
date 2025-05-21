# test_openai_manager.py

import datetime

from runner.logger import Logger
from runner.openai_manager import OpenAIManager

if __name__ == "__main__":
    today_date = datetime.datetime.now().strftime("%Y-%m-%d")
    logger = Logger(today_date)

    openai_manager = OpenAIManager(logger)

    prompt = "Give me a motivational quote to start my trading day."

    suggestion = openai_manager.get_suggestion(prompt)

    if suggestion:
        print("✅ GPT Suggestion Received:")
        print(suggestion)
    else:
        print("❌ Failed to fetch suggestion from OpenAI.")
