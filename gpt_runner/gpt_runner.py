"""
GPT Runner module for running GPT-based tasks.
This module provides functionality for analyzing trading logs, generating insights,
and suggesting code improvements using GPT models.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

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

from runner.firestore_client import FirestoreClient, fetch_recent_trades
from runner.gpt_self_improvement_monitor import run_gpt_reflection
from runner.logger import Logger
from runner.openai_manager import OpenAIManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_gpt_runner():
    """
    Run the GPT runner to process logs and generate insights.
    This is the main entry point for the GPT-based analysis pipeline.
    """
    logger = Logger(datetime.now().strftime("%Y-%m-%d"))
    logger.log_event("[GPT-RUNNER] Starting GPT Runner...")

    # Initialize clients
    firestore_client = FirestoreClient(logger)
    openai_manager = OpenAIManager(logger)

    # Get today's date and yesterday's date
    today = datetime.now().strftime("%Y-%m-%d")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    # Run analysis for each bot
    bot_names = ["stock-trader", "options-trader", "futures-trader"]

    for bot_name in bot_names:
        logger.log_event(f"[GPT-RUNNER] Analyzing {bot_name}...")

        # Fetch recent trades for the bot
        trades = fetch_recent_trades(bot_name, limit=10)

        if not trades:
            logger.log_event(f"[GPT-RUNNER] No trades found for {bot_name}")
            continue

        # Analyze trades
        analysis = analyze_trading_logs(trades, openai_manager)

        # Generate improvement suggestions
        suggestions = generate_improvement_suggestions(
            bot_name, analysis, openai_manager
        )

        # Store results in Firestore
        reflection_data = {
            "analysis": analysis,
            "suggestions": suggestions,
            "timestamp": datetime.now().isoformat(),
            "trades_analyzed": len(trades),
        }

        firestore_client.log_reflection(bot_name, today, reflection_data)
        logger.log_event(f"[GPT-RUNNER] Completed analysis for {bot_name}")

    # Run GPT self-improvement reflection
    logger.log_event("[GPT-RUNNER] Running GPT self-improvement reflection...")
    run_gpt_reflection()

    logger.log_event("[GPT-RUNNER] GPT Runner completed successfully")
    return {
        "status": "success",
        "timestamp": datetime.now().isoformat(),
        "bots_analyzed": bot_names,
    }


def analyze_trading_logs(
    logs: List[Dict[str, Any]], openai_manager: OpenAIManager
) -> Dict[str, Any]:
    """
    Analyze trading logs using GPT

    Args:
        logs: List of trade logs to analyze
        openai_manager: OpenAI manager instance

    Returns:
        Dictionary containing analysis results
    """
    if not logs:
        return {"error": "No logs provided for analysis"}

    # Format logs for GPT
    logs_text = json.dumps(logs, indent=2)

    # Create prompt for GPT
    system_prompt = """You are an expert trading system analyzer. Analyze the provided trading logs and extract insights about performance, patterns, and potential improvements. Focus on:
1. Overall performance metrics
2. Strategy effectiveness
3. Entry and exit timing
4. Risk management
5. Market conditions impact"""

    user_prompt = f"""Please analyze these trading logs and provide detailed insights:

```json
{logs_text}
```

Provide a structured analysis with the following sections:
1. Performance Summary
2. Strategy Effectiveness
3. Entry/Exit Analysis
4. Risk Management Assessment
5. Improvement Recommendations"""

    # Get analysis from GPT
    response = openai_manager.ask(system_prompt, user_prompt, model="gpt-4o")

    return {
        "raw_analysis": response,
        "timestamp": datetime.now().isoformat(),
        "trades_analyzed": len(logs),
    }


def generate_improvement_suggestions(
    bot_name: str, analysis: Dict[str, Any], openai_manager: OpenAIManager
) -> Dict[str, Any]:
    """
    Generate trading strategy improvement suggestions using GPT

    Args:
        bot_name: Name of the bot
        analysis: Analysis results from analyze_trading_logs
        openai_manager: OpenAI manager instance

    Returns:
        Dictionary containing improvement suggestions
    """
    # Get similar context from RAG
    similar_context = retrieve_similar_context(bot_name, limit=5)
    context_text = "\n\n".join([item[0].get("text", "") for item in similar_context])

    # Create prompt for GPT
    system_prompt = """You are an expert trading system developer. Based on the analysis of trading logs and historical context, suggest specific code and strategy improvements. Focus on:
1. Strategy parameter optimization
2. Entry/exit signal refinement
3. Risk management enhancements
4. Market condition adaptations
5. Specific code changes that could be implemented"""

    user_prompt = f"""Based on this analysis of {bot_name}:

```
{analysis.get('raw_analysis', 'No analysis available')}
```

And considering this historical context:

```
{context_text}
```

Provide specific, implementable improvements for the trading strategy. Include:
1. Strategy parameter adjustments
2. Signal generation improvements
3. Risk management enhancements
4. Specific code suggestions where applicable
5. Implementation priority (high/medium/low)"""

    # Get suggestions from GPT
    response = openai_manager.ask(system_prompt, user_prompt, model="gpt-4o")

    return {
        "suggestions": response,
        "timestamp": datetime.now().isoformat(),
        "bot_name": bot_name,
    }


def generate_trading_report(date_str: Optional[str] = None) -> Dict[str, Any]:
    """
    Generate a comprehensive trading report for a specific date

    Args:
        date_str: The date to generate the report for. If None, uses today's date.

    Returns:
        Dictionary containing the trading report
    """
    if date_str is None:
        date_str = datetime.now().strftime("%Y-%m-%d")

    logger = Logger(date_str)
    firestore_client = FirestoreClient(logger)

    # Fetch data for all bots
    bot_names = ["stock-trader", "options-trader", "futures-trader"]
    all_trades = {}
    all_reflections = {}

    for bot_name in bot_names:
        trades = firestore_client.fetch_trades(bot_name, date_str)
        reflection = firestore_client.fetch_reflection(bot_name, date_str)

        all_trades[bot_name] = trades
        all_reflections[bot_name] = reflection

    # Calculate performance metrics
    total_trades = sum(len(trades) for trades in all_trades.values())
    profitable_trades = sum(
        len([t for t in trades if t.get("pnl", 0) > 0])
        for trades in all_trades.values()
    )

    win_rate = profitable_trades / total_trades if total_trades > 0 else 0

    # Generate report
    report = {
        "date": date_str,
        "summary": {
            "total_trades": total_trades,
            "profitable_trades": profitable_trades,
            "win_rate": win_rate,
            "bots_active": len([bot for bot, trades in all_trades.items() if trades]),
        },
        "trades_by_bot": {bot: len(trades) for bot, trades in all_trades.items()},
        "reflections": all_reflections,
        "generated_at": datetime.now().isoformat(),
    }

    # Save report to Firestore
    try:
        firestore_client.db.collection("gpt_runner_reports").document(date_str).set(
            report
        )
        logger.log_event(f"[REPORT] Trading report generated and saved for {date_str}")
    except Exception as e:
        logger.log_event(f"[REPORT][ERROR] Failed to save report: {e}")

    return report


if __name__ == "__main__":
    run_gpt_runner()
