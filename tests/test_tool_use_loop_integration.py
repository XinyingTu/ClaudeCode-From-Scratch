# Integration test for Sprint 2's real tool-use loop.
#
# Everything is real except the network call: real AgentLoop, real
# Context, real ToolRegistry, real ListFilesTool, real
# AnthropicClient.next() translation logic. Only
# anthropic.Anthropic().messages.create is mocked, so this proves the
# whole path end to end:
#
#   Context -> AgentLoop -> AnthropicClient.next() -> "Claude" (mocked)
#     -> ToolCall -> AgentLoop -> ToolRegistry -> list_files -> Observation
#     -> Context -> AnthropicClient.next() -> "Claude" (mocked) -> FinalAnswer

import sys
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agent_loop import AgentLoop
from context import Context
from llm_client import AnthropicClient, DEFAULT_MODEL
from tools.command_tools import RunTestsTool
from tools.file_tools import ListFilesTool, ReadFileTool
from tools.registry import ToolRegistry


def make_tool_use_block(tool_name: str, tool_input: dict, call_id: str):
    # See tests/test_llm_client.py for why `name` can't be a constructor kwarg.
    block = MagicMock()
    block.type = "tool_use"
    block.name = tool_name
    block.input = tool_input
    block.id = call_id
    return block


def make_text_block(text: str):
    return MagicMock(type="text", text=text)


def test_full_loop_tool_call_then_final_answer(tmp_path):
    (tmp_path / "hello.txt").touch()

    registry = ToolRegistry()
    registry.register(ListFilesTool())

    client = AnthropicClient.__new__(AnthropicClient)  # skip __init__, no API key needed
    client.model = DEFAULT_MODEL
    client.tool_registry = registry
    client._client = MagicMock()

    tool_use_block = make_tool_use_block("list_files", {"directory": str(tmp_path)}, "toolu_01")
    first_response = MagicMock(content=[tool_use_block])
    second_response = MagicMock(content=[make_text_block("The repository contains hello.txt.")])
    client._client.messages.create.side_effect = [first_response, second_response]

    context = Context("What files are in this repository? Inspect the repository before answering.")
    loop = AgentLoop(client, registry, context)

    result = loop.run()

    assert result == "The repository contains hello.txt."
    assert client._client.messages.create.call_count == 2

    # First call: Claude sees the real tool schema and no observations yet.
    _, first_kwargs = client._client.messages.create.call_args_list[0]
    assert first_kwargs["tools"] == [{
        "name": "list_files",
        "description": ListFilesTool.description,
        "input_schema": ListFilesTool.input_schema,
    }]
    assert first_kwargs["messages"] == [
        {"role": "user", "content": "What files are in this repository? Inspect the repository before answering."},
    ]

    # Second call: Claude must see its own prior tool_use paired with the
    # tool_result — not a flattened, made-up explanatory string.
    _, second_kwargs = client._client.messages.create.call_args_list[1]
    messages = second_kwargs["messages"]
    assert messages[-2] == {
        "role": "assistant",
        "content": [{
            "type": "tool_use",
            "id": "toolu_01",
            "name": "list_files",
            "input": {"directory": str(tmp_path)},
        }],
    }
    tool_result_message = messages[-1]
    assert tool_result_message["role"] == "user"
    tool_result_block = tool_result_message["content"][0]
    assert tool_result_block["type"] == "tool_result"
    assert tool_result_block["tool_use_id"] == "toolu_01"
    assert "hello.txt" in tool_result_block["content"]


def test_full_loop_final_answer_without_any_tool_call(tmp_path):
    """Claude must be free to skip the tool entirely — this proves the loop
    doesn't force tool use; it only makes the tool available."""
    registry = ToolRegistry()
    registry.register(ListFilesTool())

    client = AnthropicClient.__new__(AnthropicClient)
    client.model = DEFAULT_MODEL
    client.tool_registry = registry
    client._client = MagicMock()
    client._client.messages.create.return_value = MagicMock(
        content=[make_text_block("I don't need to check any files to answer that.")]
    )

    context = Context("What is 2 + 2?")
    loop = AgentLoop(client, registry, context)

    result = loop.run()

    assert result == "I don't need to check any files to answer that."
    assert client._client.messages.create.call_count == 1
    assert context.observations == []


# ---------------------------------------------------------------------------
# Sprint 3: three different real tools, chosen autonomously round by round
# ---------------------------------------------------------------------------

def test_full_loop_across_three_different_tools_before_final_answer(tmp_path):
    """Claude (mocked) chooses list_files, then read_file, then run_tests,
    each in its own round, before answering. Proves: (1) AgentLoop needs no
    per-tool branching to run three different real tools, and (2) call_id
    pairing survives across every round, not just the first."""
    (tmp_path / "agent_loop.py").write_text("# real-ish source for the demo")
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_agent_loop.py").write_text("def test_it():\n    assert True\n")

    registry = ToolRegistry()
    registry.register(ListFilesTool())
    registry.register(ReadFileTool(root=str(tmp_path)))
    registry.register(RunTestsTool(root=str(tmp_path)))

    client = AnthropicClient.__new__(AnthropicClient)
    client.model = DEFAULT_MODEL
    client.tool_registry = registry
    client._client = MagicMock()

    responses = [
        MagicMock(content=[make_tool_use_block(
            "list_files", {"directory": str(tmp_path)}, "call_1")]),
        MagicMock(content=[make_tool_use_block(
            "read_file", {"path": "agent_loop.py"}, "call_2")]),
        MagicMock(content=[make_tool_use_block(
            "run_tests", {}, "call_3")]),
        MagicMock(content=[make_text_block(
            "Inspected agent_loop.py; its test suite passes.")]),
    ]
    client._client.messages.create.side_effect = responses

    context = Context("Understand how AgentLoop works and verify its tests.")
    loop = AgentLoop(client, registry, context)

    result = loop.run()

    assert result == "Inspected agent_loop.py; its test suite passes."
    assert client._client.messages.create.call_count == 4

    # Every round chose a different real tool, executed generically.
    assert [obs["tool_name"] for obs in context.observations] == [
        "list_files", "read_file", "run_tests",
    ]
    assert [obs["call_id"] for obs in context.observations] == [
        "call_1", "call_2", "call_3",
    ]
    assert "agent_loop.py" in context.observations[0]["result"]
    assert context.observations[1]["result"] == "# real-ish source for the demo"
    assert "PASSED" in context.observations[2]["result"]

    # The final request replays all three tool_use/tool_result pairs, in
    # order, each keyed to its own call_id — not flattened, not dropped.
    _, last_kwargs = client._client.messages.create.call_args_list[3]
    messages = last_kwargs["messages"]
    tool_use_ids = [
        m["content"][0]["id"] for m in messages
        if m["role"] == "assistant" and m["content"][0]["type"] == "tool_use"
    ]
    tool_result_ids = [
        m["content"][0]["tool_use_id"] for m in messages
        if m["role"] == "user" and isinstance(m["content"], list)
        and m["content"][0]["type"] == "tool_result"
    ]
    assert tool_use_ids == ["call_1", "call_2", "call_3"]
    assert tool_result_ids == ["call_1", "call_2", "call_3"]

    # Claude was offered all three tool schemas on every round, sourced
    # entirely from the registry.
    for _, kwargs in client._client.messages.create.call_args_list:
        assert [t["name"] for t in kwargs["tools"]] == [
            "list_files", "read_file", "run_tests",
        ]
