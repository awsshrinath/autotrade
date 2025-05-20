# runner/openai_manager.py

from openai import OpenAI
from runner.secret_manager_client import access_secret
import datetime
from runner.logger import Logger

logger = Logger(datetime.date.today().isoformat())

PROJECT_ID = "autotrade-453303"  # Your GCP Project ID

class OpenAIManager:
    def __init__(self, logger):
        self.logger = logger
        self.api_key = access_secret("OPENAI_API_KEY", PROJECT_ID)

        # Initialize OpenAI client with your API key
        self.client = OpenAI(api_key=self.api_key)
        self.logger.log_event("OpenAI API client initialized successfully.")

    def get_suggestion(self, prompt_text):
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",  # You can also use "gpt-3.5-turbo" if needed
                messages=[
                    {"role": "system", "content": "You are a smart trading assistant."},
                    {"role": "user", "content": prompt_text}
                ],
                temperature=0.3,
                max_tokens=500,
            )
            suggestion = response.choices[0].message.content.strip()
            return suggestion
        except Exception as e:
            self.logger.log_event(f"OpenAI API call failed: {str(e)}")
            return None


def ask_gpt(input_data):
    """
    Ask GPT for strategy selection based on market sentiment.
    """
    try:
        prompt = f"""
You are a trading strategy selector bot.

Based on the following sentiment:
{input_data}

Respond with a strategy name (e.g., 'vwap_strategy', 'orb_strategy') and a direction (bullish, bearish, neutral)
for the bot type: {input_data.get("bot", "")}.

Reply strictly in the following JSON format:
{{
    "strategy": "<name>",
    "direction": "<bullish|bearish|neutral>"
}}
"""
        gpt = OpenAIManager(logger=logger)
        response_text = gpt.get_suggestion(prompt)

        import json
        return json.loads(response_text)
    except Exception as e:
        logger.log_event(f"[GPT ERROR] Failed to parse GPT response: {e}")
        return {
            "strategy": "vwap_strategy",
            "direction": "neutral"
        }
