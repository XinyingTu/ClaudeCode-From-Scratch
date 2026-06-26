# CLAUDE.md

This file documents conventions and guidance for AI assistants working in this repo.

## Project Purpose

A simplified educational coding agent inspired by Claude Code.
The goal is to learn how coding agents work — not to build production software.

## Key Files

- `src/main.py`          — entry point
- `src/agent_loop.py`    — core agent loop
- `src/llm_client.py`    — LLM API wrapper
- `src/context.py`       — context window management
- `src/session.py`       — per-run session state
- `src/prompts.py`       — system prompt and templates
- `src/tools/base.py`    — base class for all tools
- `src/tools/file_tools.py`    — file read/write tools
- `src/tools/search_tools.py`  — grep and find tools
- `src/tools/command_tools.py` — shell command tools

## Development Rules

1. **Make small incremental changes.** One module at a time. Avoid big-bang rewrites.

2. **Add tests for each new module.** No module ships without at least one test in `tests/`.

3. **Do not add real LLM API calls until the tool layer is tested.**
   Build and verify tools with plain Python first; wire up the LLM last.

4. **Explain changes before major edits.**
   Before restructuring a file or changing an interface, describe what you are about to do.

5. **Keep code beginner-readable.**
   Prefer clear variable names, short functions, and inline comments over brevity.

6. **Prefer simple Python standard library solutions first.**
   Reach for third-party packages only when the stdlib genuinely cannot do the job.

## Conventions

- Python 3.11+
- Agent outputs go in `outputs/` — never committed unless intentional
- Tests live in `tests/` and mirror the module they cover (e.g. `test_file_tools.py`)
