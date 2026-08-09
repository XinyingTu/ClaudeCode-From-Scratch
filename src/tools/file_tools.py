# Tools for reading and writing files.
#
# Implemented:
#   - ListFilesTool — list files in a directory
#   - ReadFileTool  — return the text contents of a file
#
# Not implemented (out of scope for this sprint): WriteFile / edit_file.

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
    input_schema = {
        "type": "object",
        "properties": {
            "directory": {
                "type": "string",
                "description": "Path of the directory to list, relative or absolute.",
            },
        },
        "required": [],
    }

    def run(self, directory: str = ".") -> str:
        files = list_files(directory)
        if not files:
            return "(no files found)"
        return "\n".join(files)


def read_file(root: str, path: str) -> str:
    """Return the text contents of `path`, resolved relative to `root`.

    Returns a human-readable error string (never raises) when the path
    escapes `root`, doesn't exist, isn't a file, or isn't text — so the
    LLM sees what went wrong and can adjust, instead of the tool call
    crashing the agent loop.
    """
    root_resolved = Path(root).resolve()
    target = (root_resolved / path).resolve()

    # Reject any path that escapes the repository root (e.g. "../../etc/passwd").
    if root_resolved != target and root_resolved not in target.parents:
        return f"Error: '{path}' is outside the repository root."
    if not target.exists():
        return f"Error: file not found: {path}"
    if not target.is_file():
        return f"Error: not a file: {path}"
    try:
        return target.read_text()
    except UnicodeDecodeError:
        return f"Error: '{path}' is not a text file."


class ReadFileTool(BaseTool):
    name = "read_file"
    description = "Read the text contents of a file inside the repository. Args: path (str, relative to the repository root)"
    input_schema = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path of the file to read, relative to the repository root.",
            },
        },
        "required": ["path"],
    }

    def __init__(self, root: str = "."):
        # `root` is fixed when the tool is constructed (by whoever wires up
        # the registry), not supplied by the LLM — this is what keeps
        # read_file scoped to the repository instead of the whole filesystem.
        self.root = root

    def run(self, path: str) -> str:
        return read_file(self.root, path)
