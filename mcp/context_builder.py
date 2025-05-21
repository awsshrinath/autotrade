# Builds the structured context for GPT using MCP format
from runner.firestore_client import fetch_recent_trades
from runner.market_monitor import get_latest_market_context
from runner.capital_manager import get_current_capital


def build_mcp_context(bot_name: str) -> dict:
    trades = fetch_recent_trades(bot_name=bot_name, limit=5)
    market = get_latest_market_context()
    capital = get_current_capital(bot_name)

    context = {
        "bot": bot_name,
        "capital": capital,
        "market": market,
        "trades": trades,
        "retrieved_knowledge": [],  # to be filled by RAG if needed
        "actions_allowed": [
            "suggest_strategy",
            "fix_code",
            "update_sl",
            "log_reflection",
        ],
    }
    return context
