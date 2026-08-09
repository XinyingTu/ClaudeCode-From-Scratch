# ADR-001: Repository Discovery

## Status

Accepted

## Context

A coding agent often needs to understand an unfamiliar codebase before solving a task.

One possible approach is to load the entire repository into the LLM at once. While simple, this quickly exceeds the available context window and increases token usage as repositories grow.

The agent therefore needs a strategy for discovering only the information required to make the next decision.

## Decision

Repository exploration should be incremental instead of exhaustive.

## Reason

The agent should gather only enough information to make the next decision, rather than loading the entire repository into the LLM.

## Trade-offs

### Pros

- Lower token usage
- Scales to large repositories
- Avoids unnecessary context
- Naturally supports iterative reasoning

### Cons

- Requires multiple LLM iterations
- Increases orchestration complexity
- May require additional tool calls

## Alternatives Considered

### Option 1: Exhaustive Repository Scan

Rejected because it increases token usage and does not scale.

### Option 2: Incremental Repository Discovery

Accepted because the agent only needs enough context to make the next decision.

## Future Considerations

## First Principles

**Minimize Information** (incremental discovery, context engineering, YAGNI, cost-aware design)

Acquire, process, and retain only the minimum sufficient information required for the next decision. Loading a full repository violates this principle; incremental discovery satisfies it.

## Next Challenge

Incremental repository discovery requires the agent to perform actions such as listing and reading files. The next challenge is supporting multiple tools without coupling the Agent Loop to every concrete tool.

If repository summarization or caching is introduced in the future, this decision may be revisited.
