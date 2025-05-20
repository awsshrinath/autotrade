from gpt_runner.rag.retriever import retrieve_similar_context
from gpt_runner.openai_manager import ask_gpt
from gpt_runner.firestore_client import fetch_today_trade_summary

def run_self_improvement():
    today_summary = fetch_today_trade_summary()
    similar_failures = retrieve_similar_context(today_summary)
    examples = "\n".join(f"{i+1}. {d['date']} - {d['summary']}" for i, (d, _) in enumerate(similar_failures))

    prompt = f"""Today's Trades Summary:
{today_summary}

Past Similar Failures:
{examples}

What improvements should be applied to avoid these issues in future trades?
"""
    return ask_gpt(prompt)