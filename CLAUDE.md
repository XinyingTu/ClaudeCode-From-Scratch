# CLAUDE.md

This file documents conventions and context for AI assistants working in this repo.

## Project Purpose

Learning project: build a minimal coding agent inspired by Claude Code.

## Key Files

- `src/main.py` — entry point
- `src/agent.py` — agent loop
- `src/tools.py` — tool definitions
- `src/prompts.py` — prompt templates

## Conventions

- Python 3.11+
- No implementation should be added to a file without a corresponding test in `tests/`
- Agent outputs go in `outputs/`, never committed unless intentional
