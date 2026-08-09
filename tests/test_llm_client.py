# Tests for AnthropicClient in src/llm_client.py
#
# No real network calls: the anthropic client's messages.create is mocked.

import sys
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from context import Context
from llm_client import AnthropicClient, DEFAULT_MODEL
from protocol import FinalAnswer


def make_client_with_mocked_api(response_text: str) -> AnthropicClient:
    """Build an AnthropicClient with its underlying SDK client mocked out."""
    client = AnthropicClient.__new__(AnthropicClient)  # skip __init__ (no API key needed)
    client.model = DEFAULT_MODEL

    text_block = MagicMock(type="text", text=response_text)
    mock_response = MagicMock(content=[text_block])

    client._client = MagicMock()
    client._client.messages.create.return_value = mock_response
    return client


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
