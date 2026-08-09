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


# ---------------------------------------------------------------------------
# Sprint 2: structured tool_use/tool_result pairing (only when call_id is set)
# ---------------------------------------------------------------------------

def test_build_messages_pairs_tool_use_and_tool_result_when_call_id_present():
    context = Context("What files are in this repository?")
    context.add_tool_result(
        "list_files",
        "a.txt\nb.txt",
        call_id="toolu_01",
        arguments={"directory": "."},
    )

    assert context.build_messages() == [
        {"role": "user", "content": "What files are in this repository?"},
        {
            "role": "assistant",
            "content": [{
                "type": "tool_use",
                "id": "toolu_01",
                "name": "list_files",
                "input": {"directory": "."},
            }],
        },
        {
            "role": "user",
            "content": [{
                "type": "tool_result",
                "tool_use_id": "toolu_01",
                "content": "a.txt\nb.txt",
            }],
        },
    ]


def test_build_messages_mixes_paired_and_unpaired_observations():
    """A call_id-less observation still falls back to the flattened form,
    even alongside a paired one — the two shapes can coexist."""
    context = Context("Investigate.")
    context.add_tool_result("legacy_tool", "legacy result")
    context.add_tool_result("list_files", "a.txt", call_id="toolu_99", arguments={})

    messages = context.build_messages()
    assert messages[1] == {"role": "user", "content": "[legacy_tool result]\nlegacy result"}
    assert messages[2]["role"] == "assistant"
    assert messages[3]["content"][0]["tool_use_id"] == "toolu_99"
