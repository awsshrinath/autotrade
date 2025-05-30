import os
from datetime import datetime

import tiktoken

# Try to import RAG functionality, fallback if not available
try:
    from gpt_runner.rag.retriever import retrieve_similar_context
    RAG_AVAILABLE = True
except ImportError as e:
    print(f"Warning: RAG modules not available: {e}")
    RAG_AVAILABLE = False
    
    def retrieve_similar_context(*args, **kwargs):
        """Fallback function when RAG is not available"""
        print("Warning: RAG not available - using empty context")
        return []

from mcp.context_builder import build_mcp_context
from mcp.prompt_template import build_prompts
from mcp.response_parser import parse_gpt_response
from runner.firestore_client import FirestoreClient
from runner.openai_manager import OpenAIManager


class GPTSelfImprovementMonitor:
    def __init__(
        self,
        logger,
        firestore_client: FirestoreClient,
        gpt_client: OpenAIManager,
    ):
        self.logger = logger
        self.firestore_client = firestore_client
        self.gpt = gpt_client

    def analyze_errors(self, log_path="logs/gpt_runner.log", bot_names=None):
        if not os.path.exists(log_path):
            self.logger.log_event(f"[GPT SelfFix] Log file not found: {log_path}")
            return

        if bot_names is None:
            bot_names = ["stock-trader", "options-trader", "futures-trader"]

        with open(log_path, "r") as f:
            error_lines = [line for line in f if "[ERROR]" in line]

        if not error_lines:
            self.logger.log_event("[GPT SelfFix] No errors found in logs.")
            return

        today_error_summary = "\n".join(error_lines[-10:])
        similar_failures = retrieve_similar_context(today_error_summary)
        rag_context = ["- " + d.get("text", "") for d, _ in similar_failures]

        for bot_name in bot_names:
            context = build_mcp_context(bot_name=bot_name)
            context["retrieved_knowledge"] = rag_context

            system_prompt, user_prompt = build_prompts(context)
            model = self.pick_model_based_on_tokens(user_prompt)
            response = self.gpt.ask(system_prompt, user_prompt, model=model)

            parsed = parse_gpt_response(response)

            self.firestore_client.log_reflection(
                bot_name,
                datetime.now().strftime("%Y-%m-%d"),
                {
                    "type": "mcp_fix",
                    "model": model,
                    "errors": error_lines[:5],
                    "context": context,
                    "suggestion": parsed,
                },
            )

            self.logger.log_event(
                f"[GPT SelfFix] Logged MCP suggestion for {bot_name}."
            )

    def pick_model_based_on_tokens(self, prompt: str):
        try:
            enc = tiktoken.encoding_for_model("gpt-3.5-turbo")
        except:
            enc = tiktoken.get_encoding("cl100k_base")

        token_count = len(enc.encode(prompt))
        if token_count > 1500:
            return "gpt-4o"
        return "gpt-3.5-turbo"


def run_gpt_reflection(bot_name=None):
    """
    Run the GPT self-improvement reflection process for a specific bot.

    Args:
        bot_name (str): The name of the bot to run reflection for. If None, runs for all bots.
    """
    from runner.firestore_client import FirestoreClient
    from runner.logger import Logger
    from runner.openai_manager import OpenAIManager

    logger = Logger(today_date=datetime.now().strftime("%Y-%m-%d"))
    firestore = FirestoreClient(logger=logger)
    gpt = OpenAIManager(logger=logger)

    monitor = GPTSelfImprovementMonitor(
        logger=logger, firestore_client=firestore, gpt_client=gpt
    )

    if bot_name:
        monitor.analyze_errors(bot_names=[bot_name])
    else:
        monitor.analyze_errors()

    logger.log_event(
        f"[GPT Reflection] Completed reflection for {bot_name or 'all bots'}"
    )
