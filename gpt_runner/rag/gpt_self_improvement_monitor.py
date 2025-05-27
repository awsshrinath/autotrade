from datetime import datetime

from gpt_runner.rag.rag_worker import embed_logs_for_today
from gpt_runner.rag.retriever import retrieve_similar_context
from runner.firestore_client import FirestoreClient
from runner.logger import Logger
from runner.openai_manager import OpenAIManager


class GPTSelfImprovementMonitor:
    """Monitor for GPT self-improvement and analysis"""
    
    def __init__(self, logger, firestore_client, gpt_client):
        self.logger = logger
        self.firestore_client = firestore_client
        self.gpt_client = gpt_client
    
    def analyze_errors(self, log_path, bot_name):
        """Analyze errors from log file and provide improvement suggestions"""
        try:
            self.logger.log_event(f"[GPT] Analyzing errors for bot: {bot_name}")
            
            # Read log file and analyze errors
            with open(log_path, 'r') as f:
                log_content = f.read()
            
            # Use GPT to analyze the logs
            prompt = f"""Analyze the following log content for errors and issues:
            
{log_content}

Provide specific suggestions for improvement and error prevention."""
            
            suggestion = self.gpt_client.get_suggestion(prompt)
            self.logger.log_event(f"[GPT] Error analysis: {suggestion}")
            
            # Store analysis to Firestore
            self.firestore_client.log_reflection(
                bot_name, 
                datetime.now().strftime("%Y-%m-%d"), 
                suggestion
            )
            
        except Exception as e:
            self.logger.log_event(f"[GPT][ERROR] Error analysis failed: {e}")


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
