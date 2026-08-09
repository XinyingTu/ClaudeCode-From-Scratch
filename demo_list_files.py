# Demo: prove Claude can decide, on its own, to call the real list_files
# tool before answering — not because we hardcoded "if user asks about
# the repo, call list_files", but because Claude chose to use the tool
# schema it was given.
#
# Flow: Context -> AgentLoop -> AnthropicClient.next() -> Claude API
#   -> Claude decides: ToolCall("list_files") or FinalAnswer
#   -> (if ToolCall) AgentLoop -> ToolRegistry -> real list_files()
#      -> Observation stored in Context -> Claude reasons again
#   -> FinalAnswer -> AgentLoop returns
#
# The printed "Tool calls observed" section makes it visible whether a
# real tool call happened, so this isn't just Claude answering from
# prior knowledge.
#
# Run from the repository root:
#   ANTHROPIC_API_KEY=sk-ant-... python3 demo_list_files.py

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from agent_loop import AgentLoop
from context import Context
from llm_client import AnthropicClient
from tools.file_tools import ListFilesTool
from tools.registry import ToolRegistry

if __name__ == "__main__":
    registry = ToolRegistry()
    registry.register(ListFilesTool())

    context = Context(
        "What files are in this repository? Inspect the repository before answering."
    )
    loop = AgentLoop(AnthropicClient(registry), registry, context)
    answer = loop.run()

    print("=== Tool calls observed ===")
    if context.observations:
        for obs in context.observations:
            print(f"- tool={obs['tool_name']!r} call_id={obs['call_id']!r} arguments={obs['arguments']}")
            preview = obs["result"][:300]
            print(f"  result preview: {preview!r}")
    else:
        print("(none — Claude answered without calling any tool)")

    print("\n=== Final Answer ===")
    print(answer)
