# A tool for running this project's test suite — not a general shell tool.
#
# run_tests always executes a fixed command (`pytest <target>`) against a
# path constrained to live inside the repository's tests/ directory. The
# LLM can only choose which tests to run, never what command runs.

import subprocess
import sys
from pathlib import Path

from tools.base import BaseTool


def run_tests(root: str, target: str = "tests") -> str:
    """Run pytest over `target` (a path inside `root`'s tests/ directory).

    Returns a human-readable pass/fail summary plus captured stdout/stderr —
    never raises for a failing test run. `target` is rejected if it resolves
    outside tests/, so this cannot be used to execute arbitrary paths.
    """
    root_resolved = Path(root).resolve()
    tests_dir = (root_resolved / "tests").resolve()
    requested = (root_resolved / target).resolve()

    if requested != tests_dir and tests_dir not in requested.parents:
        return f"Error: '{target}' is outside the tests/ directory."
    if not requested.exists():
        return f"Error: test path not found: {target}"

    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", str(requested), "-v"],
            cwd=root_resolved,
            capture_output=True,
            text=True,
            timeout=120,
        )
    except subprocess.TimeoutExpired:
        return "Error: test run timed out after 120 seconds."

    status = "PASSED" if result.returncode == 0 else "FAILED"
    return f"{status} (exit code {result.returncode})\n{result.stdout}{result.stderr}"


class RunTestsTool(BaseTool):
    name = "run_tests"
    description = (
        "Run this project's pytest test suite, or a subset of it, and report "
        "pass/fail plus test output. Args: target (str, optional, a path under "
        "tests/, defaults to the whole tests/ directory)"
    )
    input_schema = {
        "type": "object",
        "properties": {
            "target": {
                "type": "string",
                "description": "Path under tests/ to run, e.g. 'tests/test_agent_loop.py'. Defaults to the whole tests/ directory.",
            },
        },
        "required": [],
    }

    def __init__(self, root: str = "."):
        # `root` is fixed at construction time, same rationale as
        # ReadFileTool.root: the repository boundary is not something the
        # LLM gets to choose via arguments.
        self.root = root

    def run(self, target: str = "tests") -> str:
        return run_tests(self.root, target)
