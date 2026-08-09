# Demo: prove the real Claude-backed LLM flows all the way through
# AgentLoop and comes back out as a printed FinalAnswer — not by calling
# AnthropicClient directly (see demo_hello_claude.py for that).
#
# Flow: Context -> AgentLoop -> AnthropicClient.next() -> Claude API
#       -> FinalAnswer -> AgentLoop -> printed result
#
# Run from the repository root:
#   ANTHROPIC_API_KEY=sk-ant-... python3 demo_agent_loop.py

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from agent_loop import AgentLoop
from context import Context
from llm_client import AnthropicClient
from tools.registry import ToolRegistry

if __name__ == "__main__":
    # An empty registry is valid: AnthropicClient always requires a
    # registry (it builds the `tools` schema from it), but a task that
    # needs no tools just gets an empty tools list.
    registry = ToolRegistry()
    context = Context("Hello! Briefly introduce yourself.")
    loop = AgentLoop(AnthropicClient(registry), registry, context)
    print(loop.run())
