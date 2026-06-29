# Tests for ToolRegistry in src/tools/registry.py

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tools.base import BaseTool
from tools.registry import ToolRegistry


# --- A minimal stub tool used across multiple tests ---

class EchoTool(BaseTool):
    name = "echo"
    description = "Returns its input as a string."

    def run(self, message: str = "") -> str:
        return message


class UpperTool(BaseTool):
    name = "upper"
    description = "Uppercases its input."

    def run(self, text: str = "") -> str:
        return text.upper()


# --- Tests ---

def test_register_tool():
    registry = ToolRegistry()
    registry.register(EchoTool())
    # After registering, the name should appear in the internal dict.
    assert "echo" in registry._tools


def test_list_tools_returns_registered_names():
    registry = ToolRegistry()
    registry.register(EchoTool())
    registry.register(UpperTool())
    assert registry.list_tools() == ["echo", "upper"]


def test_list_tools_is_sorted():
    registry = ToolRegistry()
    registry.register(UpperTool())
    registry.register(EchoTool())
    # Should always come back sorted regardless of insertion order.
    assert registry.list_tools() == ["echo", "upper"]


def test_get_tool_by_name():
    registry = ToolRegistry()
    tool = EchoTool()
    registry.register(tool)
    assert registry.get_tool("echo") is tool


def test_run_registered_tool():
    registry = ToolRegistry()
    registry.register(EchoTool())
    result = registry.run_tool("echo", message="hello")
    assert result == "hello"


def test_unknown_tool_raises_key_error():
    registry = ToolRegistry()
    with pytest.raises(KeyError):
        registry.get_tool("nonexistent")


def test_run_unknown_tool_raises_key_error():
    registry = ToolRegistry()
    with pytest.raises(KeyError):
        registry.run_tool("nonexistent")


def test_list_files_tool_registers_and_runs(tmp_path):
    # Integration check: the real ListFilesTool works through the registry.
    from tools.file_tools import ListFilesTool

    (tmp_path / "hello.txt").touch()

    registry = ToolRegistry()
    registry.register(ListFilesTool())

    assert "list_files" in registry.list_tools()
    result = registry.run_tool("list_files", directory=str(tmp_path))
    assert "hello.txt" in result
