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
from tools.file_tools import ListFilesTool
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
