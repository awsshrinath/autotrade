import os
import re
from datetime import datetime

import tiktoken

from gpt_runner.rag.retriever import retrieve_similar_context
from runner.firestore_client import FirestoreClient
from runner.logger import Logger
from runner.openai_manager import ask_gpt

logger = Logger(log_dir="logs")
firestore = FirestoreClient()


def extract_error_trace(log_path):
    if not os.path.exists(log_path):
        logger.log_event("[FixAgent] No log file found.")
        return None

    with open(log_path, "r") as f:
        error_lines = [line.strip() for line in f if "[ERROR]" in line]

    for line in reversed(error_lines):
        match = re.search(r"File \"(.+\.py)\", line (\d+), in (\w+)", line)
        if match:
            return {
                "file": match.group(1),
                "line": int(match.group(2)),
                "function": match.group(3),
                "error": line,
            }
    return None


def extract_function_block(filepath, function_name):
    if not os.path.exists(filepath):
        return None
    with open(filepath, "r") as f:
        lines = f.readlines()

    func_block = []
    inside = False
    indent_level = None
    for line in lines:
        if line.strip().startswith(f"def {function_name}("):
            inside = True
            indent_level = len(line) - len(line.lstrip())
        if inside:
            func_block.append(line)
            if line.strip() == "" or (
                len(line) - len(line.lstrip()) <= indent_level and
                not line.strip().startswith("def")
            ):
                break
    return "".join(func_block)


def pick_model(prompt):
    try:
        enc = tiktoken.encoding_for_model("gpt-3.5-turbo")
    except Exception:
        enc = tiktoken.get_encoding("cl100k_base")
    tokens = len(enc.encode(prompt))
    return "claude-haiku" if tokens < 1500 else "gpt-4o"


def run_code_fixer(log_path="logs/gpt_runner.log"):
    trace = extract_error_trace(log_path)
    if not trace:
        logger.log_event("[FixAgent] No valid error trace found.")
        return

    code_file_path = (
        os.path.join("Tron", trace["file"])
        if not trace["file"].startswith("/")
        else trace["file"]
    )
    code_block = extract_function_block(code_file_path, trace["function"])
    if not code_block:
        logger.log_event(
            f"[FixAgent] Could not extract function: "
            f"{trace['function']} from "
            f"{trace['file']}"
        )
        return

    similar_context = retrieve_similar_context(trace["error"])
    rag_notes = "\n".join(
        ["- " + d.get("text", "") for d, _ in similar_context]
    )

    prompt = f"""
You're an AI developer assistant. Analyze the following Python function which
caused an error:

❌ Error:
{trace['error']}

🔍 Retrieved memory of similar issues:
{rag_notes}

🧠 Function Block:
{code_block}

✅ Suggest a fix in this format:
{{
  "action": "fix_code",
  "file": "{trace['file']}",
  "function": "{trace['function']}",
  "suggested_fix": "...code snippet...",
  "reason": "explanation of the bug"
}}
"""

    model = pick_model(prompt)
    suggestion = ask_gpt(
        system_prompt="You're an AI developer.",
        user_prompt=prompt,
        model=model,
    )

    if suggestion:
        firestore.log_reflection(
            "code-fix",
            datetime.now().strftime("%Y-%m-%d"),
            {
                "trace": trace,
                "code_block": code_block,
                "model": model,
                "suggestion": suggestion,
            },
        )
        logger.log_event("[FixAgent] Suggestion logged to Firestore.")
    else:
        logger.log_event("[FixAgent] GPT returned no suggestion.")
