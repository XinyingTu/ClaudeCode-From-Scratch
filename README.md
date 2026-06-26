# mini-claude-code

A simplified educational coding agent inspired by Claude Code.

Built as a learning project to understand how AI coding agents work from the inside:
how they manage context, call tools, and iterate toward a solution.

## Goals

- Readable over clever — every module should be understandable by a beginner
- Build bottom-up: tools first, agent loop second, LLM integration last
- Each new module ships with tests before moving on

## Project Structure

```
src/
  main.py            Entry point — parses args, starts a session
  agent_loop.py      The core loop: pick a tool, run it, repeat
  llm_client.py      Thin wrapper around the LLM API
  context.py         Manages the conversation context window
  session.py         Holds state for a single agent run
  prompts.py         System prompt and prompt templates

  tools/
    __init__.py      Tool registry
    base.py          Base class all tools inherit from
    file_tools.py    Read, write, and list files
    search_tools.py  Grep and find-files
    command_tools.py Run shell commands safely

tests/
  test_file_tools.py
  test_agent_loop.py

examples/
  sample_project/    A small dummy codebase for the agent to work on

outputs/             Agent-generated files (not committed by default)
```

## Development Order

1. Implement and test `tools/base.py`
2. Implement and test `tools/file_tools.py`
3. Implement and test `tools/search_tools.py`
4. Implement and test `tools/command_tools.py`
5. Implement `context.py` and `session.py`
6. Implement `agent_loop.py` with a mock LLM
7. Wire up `llm_client.py` with a real API

## Getting Started

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt   # (coming soon)
python src/main.py
```
