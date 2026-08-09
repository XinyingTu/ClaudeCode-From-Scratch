# Tests for list_files() and read_file() in src/tools/file_tools.py

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tools.file_tools import read_file, list_files


def make_files(tmp_path: Path, relative_paths: list[str]) -> None:
    """Helper: create empty files inside tmp_path."""
    for rel in relative_paths:
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.touch()


def test_returns_files_in_flat_directory(tmp_path):
    make_files(tmp_path, ["a.txt", "b.py"])
    assert list_files(str(tmp_path)) == ["a.txt", "b.py"]


def test_recurses_into_subdirectories(tmp_path):
    make_files(tmp_path, ["top.txt", "sub/nested.txt"])
    assert list_files(str(tmp_path)) == ["sub/nested.txt", "top.txt"]


def test_ignores_hidden_files(tmp_path):
    make_files(tmp_path, ["visible.txt", ".hidden"])
    assert list_files(str(tmp_path)) == ["visible.txt"]


def test_ignores_hidden_directories(tmp_path):
    make_files(tmp_path, ["visible.txt", ".git/config", ".git/HEAD"])
    assert list_files(str(tmp_path)) == ["visible.txt"]


def test_returns_sorted_results(tmp_path):
    make_files(tmp_path, ["z.txt", "a.txt", "m.txt"])
    assert list_files(str(tmp_path)) == ["a.txt", "m.txt", "z.txt"]


def test_empty_directory_returns_empty_list(tmp_path):
    assert list_files(str(tmp_path)) == []


def test_paths_are_relative_not_absolute(tmp_path):
    make_files(tmp_path, ["sub/file.txt"])
    results = list_files(str(tmp_path))
    assert all(not Path(p).is_absolute() for p in results)


# ---------------------------------------------------------------------------
# read_file()
# ---------------------------------------------------------------------------

def test_read_file_returns_contents(tmp_path):
    (tmp_path / "hello.txt").write_text("hello world\n")
    assert read_file(str(tmp_path), "hello.txt") == "hello world\n"


def test_read_file_supports_nested_paths(tmp_path):
    nested = tmp_path / "sub" / "nested.txt"
    nested.parent.mkdir(parents=True)
    nested.write_text("nested content")
    assert read_file(str(tmp_path), "sub/nested.txt") == "nested content"


def test_read_file_missing_path_returns_error_string(tmp_path):
    result = read_file(str(tmp_path), "does_not_exist.txt")
    assert "not found" in result.lower()


def test_read_file_rejects_path_outside_root(tmp_path):
    outside = tmp_path.parent / "outside_secret.txt"
    outside.write_text("should not be readable")
    try:
        result = read_file(str(tmp_path), "../outside_secret.txt")
        assert "outside the repository root" in result
    finally:
        outside.unlink()


def test_read_file_rejects_directory_path(tmp_path):
    (tmp_path / "subdir").mkdir()
    result = read_file(str(tmp_path), "subdir")
    assert "not a file" in result.lower()


def test_read_file_does_not_raise_on_bad_input(tmp_path):
    # None of these should raise — the tool must hand the LLM a plain
    # error string it can react to, not an exception that crashes the loop.
    read_file(str(tmp_path), "missing.txt")
    read_file(str(tmp_path), "../../etc/passwd")
