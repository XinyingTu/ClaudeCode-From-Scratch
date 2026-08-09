# Tests for Context.build_messages() in src/context.py (ADR-005)

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from context import Context


def test_build_messages_with_no_observations():
    context = Context("Hello!")
    assert context.build_messages() == [
        {"role": "user", "content": "Hello!"},
    ]


def test_build_messages_includes_tool_results_in_order():
    context = Context("Read the file.")
    context.add_tool_result("read_file", "line one")
    context.add_tool_result("read_file", "line two")

    assert context.build_messages() == [
        {"role": "user", "content": "Read the file."},
        {"role": "user", "content": "[read_file result]\nline one"},
        {"role": "user", "content": "[read_file result]\nline two"},
    ]
