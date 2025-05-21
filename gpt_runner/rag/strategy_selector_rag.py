from gpt_runner.openai_manager import ask_gpt
from gpt_runner.rag.retriever import retrieve_similar_context


def strategy_with_memory(today_market_summary):
    similar_cases = retrieve_similar_context(today_market_summary)
    context = "\n".join(
        f"{i + 1}. {d['date']} - {d['summary']}"
        for i, (d, _) in enumerate(similar_cases)
    )

    prompt = f"""Today's Market Snapshot:
{today_market_summary}

Similar Past Cases:
{context}

Based on these, what is the most suitable strategy for today's market?
"""
    return ask_gpt(prompt)
