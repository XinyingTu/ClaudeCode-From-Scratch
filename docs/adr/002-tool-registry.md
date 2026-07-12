# ADR-002: Tool Registry

## Status

Accepted

## Context

A coding agent will gradually support multiple tools such as `list_files`, `read_file`, `edit_file`, and `run_tests`.

A straightforward implementation is to hardcode tool dispatch inside the agent loop:

```text
if tool_name == "list_files":
    list_files(...)
elif tool_name == "read_file":
    read_file(...)
```

Although simple initially, this approach tightly couples the agent loop to every concrete tool. As the number of tools grows, the orchestration logic becomes harder to maintain, test, and extend.

The responsibility of the agent loop is to coordinate the reasoning cycle — think, act, observe — not to manage how every tool is implemented.

## Decision

Introduce a **Tool Registry** as an independent architectural component.

The Tool Registry is responsible for:

- registering tool instances
- storing tool metadata
- looking up tools by name
- invoking the selected tool

Each tool exposes a common interface: `name`, `description`, and `run(...)`.

Each tool is represented as an object rather than a standalone function, allowing it to encapsulate both behavior and runtime state.

The agent loop communicates only with the Tool Registry. The `ToolRegistry` is created outside the `AgentLoop` and injected into it, keeping orchestration independent from dependency creation.

## Trade-offs

### Pros

- Decouples the agent loop from concrete tool implementations
- New tools can be added without modifying orchestration logic
- Tool metadata is centralized for easier discovery
- Tool objects encapsulate both behavior and state
- Dependency Injection improves testability and flexibility

### Cons

- Introduces one additional abstraction layer
- Slightly increases complexity for very small projects
- Requires all tools to implement a consistent interface

## Alternatives Considered

### Option 1 — Hardcoded Tool Dispatch

Simple but tightly couples the agent loop with every tool. Rejected because it does not scale.

### Option 2 — Tool Registry

Separates orchestration from tool management through a common interface. Accepted because the project is intended to evolve into a multi-tool coding agent.

## First Principles

**Hide Change** (encapsulation, information hiding, Open-Closed Principle)

The Tool Registry isolates concrete tool implementations behind a common interface. New tools can be added without modifying the Agent Loop.

**Single Responsibility** (Separation of Concerns, SRP)

The Agent Loop is responsible for orchestration only. Tool management is delegated to the Tool Registry.

**Depend on Stable Abstractions** (Dependency Injection, decoupling)

The Agent Loop depends on the Tool Registry interface, not on any concrete tool. The registry is injected at construction time.

## Next Challenge

The Tool Registry separates tool management from orchestration, but the system still needs a mechanism for repeatedly reasoning, acting, and observing until a task is complete.
