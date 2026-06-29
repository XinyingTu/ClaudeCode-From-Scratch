# Tests for list_files() in src/tools/file_tools.py

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tools.file_tools import list_files


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
