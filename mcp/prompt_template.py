# Formats the MCP context into GPT-ready prompt
import json


def build_prompts(context: dict) -> tuple:
    system_prompt = (
        "You are an AI agent managing an automated trading bot. "
        "Only respond using allowed actions. Analyze the context and suggest improvements or decisions."
    )
    user_prompt = (
        f"Context:\n{json.dumps(context, indent=2)}\n\nWhat is your recommendation?"
    )
    return system_prompt, user_prompt
