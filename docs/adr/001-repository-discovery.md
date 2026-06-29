# ADR-001: Repository Discovery

## Status

Accepted

---

## Context

A coding agent often needs to understand an unfamiliar codebase before solving a task.

One possible approach is to load the entire repository into the LLM at once. While simple, this quickly exceeds the available context window and increases token usage as repositories grow.

The agent therefore needs a strategy for discovering only the information required to make the next decision.

---

## Decision

Repository exploration should be **incremental rather than exhaustive**.

Instead of loading every file into the LLM, the agent gathers only enough information to determine the next action. Additional files are explored only when new observations indicate they are relevant.

This allows the agent to progressively build an understanding of the repository while keeping the working context small.

---

## Trade-offs

### Pros

* Lower token usage
* Scales to large repositories
* Avoids unnecessary context
* Naturally supports iterative reasoning

### Cons

* Requires multiple LLM iterations
* Increases orchestration complexity
* May require additional tool calls

---

## Alternatives Considered

### Option 1 — Exhaustive Repository Scan

Load the entire repository before reasoning.

Rejected because it consumes excessive context, increases token usage, and does not scale to real-world repositories.

### Option 2 — Incremental Repository Discovery

Explore the repository step by step based on the current objective.

Accepted because the agent only needs enough information to make the next decision, allowing it to reason efficiently while continuously incorporating new observations.

---

## Key Principles

* Incremental Reasoning
* Context Engineering
* Cost-Aware Design
* Scalability

---

## Next Challenge

Incremental repository discovery reduces unnecessary context, but the agent still requires a mechanism for executing the actions it decides to take.
