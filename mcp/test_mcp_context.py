# Sample test to check MCP context structure
from mcp.context_builder import build_mcp_context
from mcp.prompt_template import build_prompts

def test_context():
    context = build_mcp_context("options-trader")
    system, user = build_prompts(context)
    print("System Prompt:", system)
    print("User Prompt:", user[:500])  # Preview first 500 chars