# Tests for run_tests() and RunTestsTool in src/tools/command_tools.py

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tools.command_tools import run_tests, RunTestsTool


def make_test_repo(tmp_path: Path, test_file_name: str, test_file_body: str) -> None:
    """Helper: create a minimal repo with one tests/<name>.py file."""
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / test_file_name).write_text(test_file_body)


def test_run_tests_reports_pass_when_all_tests_pass(tmp_path):
    make_test_repo(tmp_path, "test_ok.py", "def test_ok():\n    assert 1 + 1 == 2\n")

    result = run_tests(str(tmp_path))

    assert result.startswith("PASSED")
    assert "1 passed" in result


def test_run_tests_reports_fail_when_a_test_fails(tmp_path):
    make_test_repo(tmp_path, "test_bad.py", "def test_bad():\n    assert 1 + 1 == 3\n")

    result = run_tests(str(tmp_path))

    assert result.startswith("FAILED")
    assert "1 failed" in result


def test_run_tests_can_target_a_single_file(tmp_path):
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_a.py").write_text("def test_a():\n    assert True\n")
    (tests_dir / "test_b.py").write_text("def test_b():\n    assert False\n")

    result = run_tests(str(tmp_path), target="tests/test_a.py")

    assert result.startswith("PASSED")
    assert "1 passed" in result


def test_run_tests_rejects_target_outside_tests_dir(tmp_path):
    make_test_repo(tmp_path, "test_ok.py", "def test_ok():\n    assert True\n")
    (tmp_path / "secret.py").write_text("SECRET = 1\n")

    result = run_tests(str(tmp_path), target="../secret.py")

    assert "outside the tests/ directory" in result


def test_run_tests_missing_target_returns_error(tmp_path):
    make_test_repo(tmp_path, "test_ok.py", "def test_ok():\n    assert True\n")

    result = run_tests(str(tmp_path), target="tests/does_not_exist.py")

    assert "not found" in result.lower()


def test_run_tests_tool_schema_and_run(tmp_path):
    make_test_repo(tmp_path, "test_ok.py", "def test_ok():\n    assert True\n")

    tool = RunTestsTool(root=str(tmp_path))

    assert tool.name == "run_tests"
    assert "target" in tool.input_schema["properties"]
    assert tool.input_schema["required"] == []

    result = tool.run()
    assert result.startswith("PASSED")
