# Tests for the internal communication protocol in src/protocol.py (ADR-005)

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from protocol import FinalAnswer, ToolCall


def test_final_answer_holds_content():
    assert FinalAnswer(content="Done!").content == "Done!"


def test_tool_call_holds_tool_and_arguments():
    call = ToolCall(tool="greet", arguments={"name": "Alice"})
    assert call.tool == "greet"
    assert call.arguments == {"name": "Alice"}


def test_tool_call_arguments_default_to_empty_dict():
    assert ToolCall(tool="greet").arguments == {}


def test_tool_call_instances_have_independent_default_arguments():
    """The default {} must not be a single shared mutable object."""
    first = ToolCall(tool="greet")
    second = ToolCall(tool="greet")
    first.arguments["name"] = "Alice"
    assert second.arguments == {}
