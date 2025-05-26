from datetime import datetime

from gpt_runner.rag.embedder import embed_logs_for_today
from gpt_runner.rag.retriever import retrieve_similar_context
from mcp.context_builder import build_mcp_context
from mcp.prompt_template import build_prompts
from mcp.response_parser import parse_gpt_response
from runner.firestore_client import FirestoreClient
from runner.logger import Logger
from runner.openai_manager import OpenAIManager, ask_gpt

context = build_mcp_context(bot_name="options-trader")
system, user = build_prompts(context)
gpt_response = ask_gpt(system, user)
parsed = parse_gpt_response(gpt_response)
print("Parsed GPT Action:", parsed)


def run_reflection(bot_name):
    logger = Logger(datetime.now().strftime("%Y-%m-%d"))
    logger.log_event(f"[GPT] Starting self-reflection for bot: {bot_name}")

    try:
        embed_logs_for_today(bot_name, logger)

        context = retrieve_similar_context(
            bot_name, query="analyze today's performance"
        )
        prompt = f"""You are an AI trading analyst. Based on this context:
{context}


        Reflect on the bot's performance today. Identify 1 mistake and suggest an improvement.
        """.strip()

        gpt = OpenAIManager(logger)
        suggestion = gpt.get_suggestion(prompt)

        logger.log_event(f"[GPT] Reflection: {suggestion}")

        # Store to Firestore for memory
        client = FirestoreClient(logger)
        client.log_reflection(bot_name, datetime.now().strftime("%Y-%m-%d"), suggestion)

    except Exception as e:
        logger.log_event(f"[GPT][ERROR] Self-reflection failed: {e}")
