# Parses and validates GPT's structured output
import json
from .allowed_actions import ALLOWED_ACTIONS

def parse_gpt_response(response: str) -> dict:
    try:
        result = json.loads(response)
        if "action" not in result or result["action"] not in ALLOWED_ACTIONS:
            raise ValueError("Invalid or missing 'action'")
        return result
    except Exception as e:
        return {"error": str(e), "raw_response": response}