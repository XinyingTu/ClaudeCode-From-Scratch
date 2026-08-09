# Demo: prove Claude can autonomously choose between three real, read-only
# tools — list_files, read_file, run_tests — picking its own order, not a
# hardcoded sequence.
#
# Flow (NOT fixed by this script — Claude decides at each step):
#   Context -> AgentLoop -> AnthropicClient.next() -> Claude API
#     -> Claude decides: ToolCall(list_files | read_file | run_tests) or FinalAnswer
#     -> (if ToolCall) AgentLoop -> ToolRegistry -> real tool -> Observation
#        -> Context -> Claude reasons again
#   -> FinalAnswer -> AgentLoop returns
#
# The printed "Tool calls observed" section shows exactly which tools ran
# and in what order, so autonomous multi-tool behavior is visible rather
# than assumed.
#
# Run from the repository root:
#   ANTHROPIC_API_KEY=sk-ant-... python3 demo_multi_tool_agent.py

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from agent_loop import AgentLoop
from context import Context
from llm_client import AnthropicClient
from tools.command_tools import RunTestsTool
from tools.file_tools import ListFilesTool, ReadFileTool
from tools.registry import ToolRegistry

REPO_ROOT = str(Path(__file__).parent)

if __name__ == "__main__":
    registry = ToolRegistry()
    registry.register(ListFilesTool())
    # read_file/run_tests are scoped to this repository at construction
    # time — Claude only ever supplies a path/target relative to it.
    registry.register(ReadFileTool(root=REPO_ROOT))
    registry.register(RunTestsTool(root=REPO_ROOT))

    context = Context(
        "Inspect this repository, explain how AgentLoop works, and verify "
        "the relevant tests. Use the tools available to you as needed."
    )
    loop = AgentLoop(AnthropicClient(registry), registry, context)
    answer = loop.run()

    print("=== Tool calls observed (in order) ===")
    if context.observations:
        for i, obs in enumerate(context.observations, start=1):
            print(f"{i}. tool={obs['tool_name']!r} call_id={obs['call_id']!r} arguments={obs['arguments']}")
            preview = obs["result"][:300]
            print(f"   result preview: {preview!r}")
    else:
        print("(none — Claude answered without calling any tool)")

    print("\n=== Final Answer ===")
    print(answer)
