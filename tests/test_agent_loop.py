# Tests for AgentLoop in src/agent_loop.py
#
# We use three fakes to avoid real LLM calls:
#   FakeLLM     — returns a pre-scripted sequence of responses
#   FakeContext — records everything passed to add_tool_result
#   inline tool stubs built with BaseTool

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agent_loop import AgentLoop
from context import Context
from protocol import FinalAnswer, ToolCall
from tools.base import BaseTool
from tools.file_tools import ListFilesTool
from tools.registry import ToolRegistry


# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------

class FakeLLM:
    """Returns responses from a fixed list, one per call to next()."""

    def __init__(self, responses: list):
        self._responses = list(responses)
        self._index = 0

    def next(self, context):
        if self._index >= len(self._responses):
            raise RuntimeError("FakeLLM ran out of scripted responses")
        response = self._responses[self._index]
        self._index += 1
        return response


class FakeContext:
    """Minimal context stub; records tool results for inspection."""

    def __init__(self):
        self.tool_results: list[tuple[str, str]] = []

    def add_tool_result(self, tool_name: str, result: str, call_id=None, arguments=None) -> None:
        # call_id/arguments mirror the real Context.add_tool_result signature
        # (see context.py); this fake only needs the (tool_name, result) pair.
        self.tool_results.append((tool_name, result))


# A simple tool that returns a fixed string.
class GreetTool(BaseTool):
    name = "greet"
    description = "Says hello."

    def run(self, name: str = "world") -> str:
        return f"Hello, {name}!"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_registry(*tools) -> ToolRegistry:
    registry = ToolRegistry()
    for tool in tools:
        registry.register(tool)
    return registry


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_final_answer_returned_immediately():
    """A single FinalAnswer response ends the loop right away."""
    llm = FakeLLM([
        FinalAnswer(content="Done!"),
    ])
    loop = AgentLoop(llm, make_registry(), FakeContext())
    assert loop.run() == "Done!"


def test_tool_call_then_final_answer():
    """One tool call followed by a final answer completes successfully."""
    llm = FakeLLM([
        ToolCall(tool="greet", arguments={"name": "Alice"}),
        FinalAnswer(content="Said hello."),
    ])
    ctx = FakeContext()
    loop = AgentLoop(llm, make_registry(GreetTool()), ctx)
    result = loop.run()

    assert result == "Said hello."
    # The tool result should have been stored in context.
    assert ctx.tool_results == [("greet", "Hello, Alice!")]


def test_multiple_tool_calls_before_final_answer():
    """The loop handles several consecutive tool calls correctly."""
    llm = FakeLLM([
        ToolCall(tool="greet", arguments={"name": "Bob"}),
        ToolCall(tool="greet", arguments={"name": "Carol"}),
        FinalAnswer(content="All done."),
    ])
    ctx = FakeContext()
    loop = AgentLoop(llm, make_registry(GreetTool()), ctx)
    assert loop.run() == "All done."
    assert len(ctx.tool_results) == 2


def test_tool_result_stored_in_context():
    """The exact tool output is what gets stored in context."""
    llm = FakeLLM([
        ToolCall(tool="greet", arguments={"name": "Dev"}),
        FinalAnswer(content="ok"),
    ])
    ctx = FakeContext()
    loop = AgentLoop(llm, make_registry(GreetTool()), ctx)
    loop.run()
    assert ctx.tool_results[0] == ("greet", "Hello, Dev!")


def test_max_steps_raises_runtime_error():
    """If the LLM never returns a FinalAnswer, RuntimeError is raised."""
    # Always return a tool call — the loop will never finish on its own.
    responses = [
        ToolCall(tool="greet", arguments={})
    ] * 50  # more than max_steps
    llm = FakeLLM(responses)
    loop = AgentLoop(llm, make_registry(GreetTool()), FakeContext(), max_steps=3)
    with pytest.raises(RuntimeError, match="max_steps"):
        loop.run()


def test_unknown_tool_raises_key_error():
    """Calling a tool that isn't registered propagates KeyError."""
    llm = FakeLLM([
        ToolCall(tool="no_such_tool", arguments={}),
    ])
    loop = AgentLoop(llm, make_registry(), FakeContext())
    with pytest.raises(KeyError):
        loop.run()


def test_unknown_response_type_raises_value_error():
    """A response that isn't FinalAnswer or ToolCall raises ValueError."""
    llm = FakeLLM([
        "something_weird",
    ])
    loop = AgentLoop(llm, make_registry(), FakeContext())
    with pytest.raises(ValueError, match="Unknown response type"):
        loop.run()


def test_tool_registry_injected_not_created_internally():
    """AgentLoop must accept the registry from outside, not create one."""
    registry = make_registry(GreetTool())
    llm = FakeLLM([FinalAnswer(content="hi")])
    loop = AgentLoop(llm, registry, FakeContext())
    # The registry passed in must be the exact same object.
    assert loop.registry is registry


def test_tool_arguments_default_to_empty_dict():
    """A ToolCall with no explicit arguments should not crash."""
    llm = FakeLLM([
        ToolCall(tool="greet"),  # arguments defaults to {}
        FinalAnswer(content="ok"),
    ])
    loop = AgentLoop(llm, make_registry(GreetTool()), FakeContext())
    # GreetTool.run() defaults name to "world", so this should work fine.
    assert loop.run() == "ok"


# ---------------------------------------------------------------------------
# Sprint 2: real list_files ToolCall (with call_id) through a real Context
# ---------------------------------------------------------------------------

def test_list_files_tool_call_becomes_observation_with_call_id(tmp_path):
    """A ToolCall carrying a call_id must execute through the real Registry
    and be stored in the real Context as a pairable Observation."""
    (tmp_path / "hello.txt").touch()

    llm = FakeLLM([
        ToolCall(
            tool="list_files",
            arguments={"directory": str(tmp_path)},
            call_id="toolu_repo_01",
        ),
        FinalAnswer(content="This repository contains hello.txt."),
    ])
    context = Context("What files are in this repository?")
    loop = AgentLoop(llm, make_registry(ListFilesTool()), context)

    result = loop.run()

    assert result == "This repository contains hello.txt."

    # The tool actually ran (real ListFilesTool, real filesystem lookup).
    assert len(context.observations) == 1
    observation = context.observations[0]
    assert observation["tool_name"] == "list_files"
    assert observation["call_id"] == "toolu_repo_01"
    assert "hello.txt" in observation["result"]

    # And the next request would show Claude its own tool call paired
    # with the result, not a flattened string.
    messages = context.build_messages()
    assert messages[1]["role"] == "assistant"
    assert messages[1]["content"][0]["type"] == "tool_use"
    assert messages[1]["content"][0]["id"] == "toolu_repo_01"
    assert messages[2]["content"][0]["type"] == "tool_result"
    assert messages[2]["content"][0]["tool_use_id"] == "toolu_repo_01"
