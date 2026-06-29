# Tools for reading and writing files.
#
# Planned tools:
#   - ReadFile(path)           — return the contents of a file
#   - WriteFile(path, content) — write or overwrite a file
#   - ListDirectory(path)      — list files in a directory

from pathlib import Path

from tools.base import BaseTool


def list_files(directory: str) -> list[str]:
    """Return a sorted list of relative file paths inside `directory`, recursively.

    Hidden files and directories (names starting with '.') are skipped.
    Paths are relative to `directory`.
    """
    root = Path(directory)
    results = []
    for path in root.rglob("*"):
        # Skip anything whose name starts with '.' at any level.
        if any(part.startswith(".") for part in path.parts[len(root.parts):]):
            continue
        if path.is_file():
            results.append(str(path.relative_to(root)))
    return sorted(results)


class ListFilesTool(BaseTool):
    name = "list_files"
    description = "List all non-hidden files inside a directory, recursively. Args: directory (str)"

    def run(self, directory: str = ".") -> str:
        files = list_files(directory)
        if not files:
            return "(no files found)"
        return "\n".join(files)
