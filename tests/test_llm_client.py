# Tests for AnthropicClient in src/llm_client.py
#
# No real network calls: the anthropic client's messages.create is mocked.

import sys
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from context import Context
from llm_client import AnthropicClient, DEFAULT_MODEL
from protocol import FinalAnswer, ToolCall
from tools.registry import ToolRegistry


def make_client_with_mocked_api(response_text: str, tool_registry=None) -> AnthropicClient:
    """Build an AnthropicClient with its underlying SDK client mocked out."""
    client = AnthropicClient.__new__(AnthropicClient)  # skip __init__ (no API key needed)
    client.model = DEFAULT_MODEL
    client.tool_registry = tool_registry if tool_registry is not None else ToolRegistry()

    text_block = MagicMock(type="text", text=response_text)
    mock_response = MagicMock(content=[text_block])

    client._client = MagicMock()
    client._client.messages.create.return_value = mock_response
    return client


def make_tool_use_block(tool_name: str, tool_input: dict, call_id: str):
    """Build a mocked Anthropic tool_use content block.

    MagicMock(name=...) is special-cased by unittest.mock (it sets the
    mock's repr, not a `.name` attribute), so `name` must be assigned
    after construction instead of passed as a kwarg.
    """
    block = MagicMock()
    block.type = "tool_use"
    block.name = tool_name
    block.input = tool_input
    block.id = call_id
    return block


def test_send_returns_text_from_response():
    client = make_client_with_mocked_api("Hello there!")
    assert client.send("Hi") == "Hello there!"


def test_send_passes_message_and_model_to_api():
    client = make_client_with_mocked_api("ok")
    client.send("What is 2+2?")

    _, kwargs = client._client.messages.create.call_args
    assert kwargs["model"] == DEFAULT_MODEL
    assert kwargs["messages"] == [{"role": "user", "content": "What is 2+2?"}]


def test_send_concatenates_multiple_text_blocks():
    client = make_client_with_mocked_api("")
    block1 = MagicMock(type="text", text="Hello, ")
    block2 = MagicMock(type="text", text="world!")
    client._client.messages.create.return_value = MagicMock(content=[block1, block2])

    assert client.send("Hi") == "Hello, world!"


# ---------------------------------------------------------------------------
# next() — the ADR-005 adapter boundary between AgentLoop and Claude
# ---------------------------------------------------------------------------

def test_next_returns_final_answer_with_claude_text():
    client = make_client_with_mocked_api("Hi, I'm Claude.")
    response = client.next(Context("Introduce yourself."))

    assert response == FinalAnswer(content="Hi, I'm Claude.")


def test_next_sends_messages_built_from_context():
    client = make_client_with_mocked_api("ok")
    context = Context("What is 2+2?")
    client.next(context)

    _, kwargs = client._client.messages.create.call_args
    assert kwargs["model"] == DEFAULT_MODEL
    assert kwargs["messages"] == context.build_messages()


def test_next_sends_tool_schema_for_registered_tools():
    """Claude must receive a real tool definition, not a hint in the prompt."""
    from tools.file_tools import ListFilesTool

    registry = ToolRegistry()
    registry.register(ListFilesTool())
    client = make_client_with_mocked_api("ok", tool_registry=registry)

    client.next(Context("anything"))

    _, kwargs = client._client.messages.create.call_args
    assert kwargs["tools"] == [{
        "name": "list_files",
        "description": ListFilesTool.description,
        "input_schema": ListFilesTool.input_schema,
    }]


def test_next_sends_empty_tools_list_when_registry_has_no_tools():
    client = make_client_with_mocked_api("ok")
    client.next(Context("anything"))

    _, kwargs = client._client.messages.create.call_args
    assert kwargs["tools"] == []


def test_next_returns_tool_call_when_claude_requests_tool_use():
    """Anthropic tool_use response -> internal ToolCall (not FinalAnswer)."""
    client = make_client_with_mocked_api("unused")
    tool_use_block = make_tool_use_block("list_files", {"directory": "."}, "toolu_01")
    client._client.messages.create.return_value = MagicMock(content=[tool_use_block])

    response = client.next(Context("What files exist?"))

    assert response == ToolCall(tool="list_files", arguments={"directory": "."}, call_id="toolu_01")


def test_next_ignores_text_blocks_alongside_a_tool_use_block():
    """When Claude both reasons in text and calls a tool, ToolCall wins."""
    client = make_client_with_mocked_api("unused")
    text_block = MagicMock(type="text", text="Let me check the repository.")
    tool_use_block = make_tool_use_block("list_files", {}, "toolu_02")
    client._client.messages.create.return_value = MagicMock(content=[text_block, tool_use_block])

    response = client.next(Context("What files exist?"))

    assert response == ToolCall(tool="list_files", arguments={}, call_id="toolu_02")
