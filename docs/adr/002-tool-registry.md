# ADR-002: Tool Registry

## Status

Accepted

## Context

Our Mini Claude Code agent needs to use multiple tools, such as `list_files`, and later `read_file`, `edit_file`, and `run_tests`.

A simple implementation could hardcode tool calls inside the agent loop:

```text
if tool_name == "list_files":
    call list_files
elif tool_name == "read_file":
    call read_file
```

However, this design makes the agent loop tightly coupled to every concrete tool. As the number of tools grows, the agent loop becomes harder to maintain, test, and extend.

The agent loop should focus on coordinating the reasoning cycle:

```text
Think → Act → Observe
```

It should not be responsible for knowing how every individual tool is implemented.

## Decision

We will introduce a `ToolRegistry`.

The `ToolRegistry` is responsible for:

* registering tools
* storing tool metadata
* looking up tools by name
* invoking the correct tool through a common interface

Each tool should expose at least:

* `name`
* `description`
* `run(...)`

The agent loop will interact with tools only through the registry.

Conceptually:

```text
Agent Loop → Tool Registry → Tool
```

## Consequences

### Positive

* The agent loop is decoupled from concrete tool implementations.
* New tools can be added without modifying the agent loop.
* Tool discovery becomes easier because tool metadata is stored in one place.
* The system becomes easier to test because registry behavior can be tested separately.

### Negative

* Adds one extra abstraction layer.
* For a very small project with only one tool, this may feel unnecessary.
* Tool interface design must be kept simple and consistent.

## Alternatives Considered

### Option 1: Hardcode tool calls in the agent loop

This is simple at the beginning but does not scale well. Every new tool requires modifying the agent loop.

Rejected because it violates separation of concerns and makes the agent harder to extend.

### Option 2: Use a Tool Registry

This adds a small abstraction but keeps the agent loop clean and extensible.

Accepted because Mini Claude Code is designed to grow into a multi-tool agent.

## Architecture Principle

This decision follows:

* Separation of Concerns
* Decoupling
* Open-Closed Principle

The agent loop should be responsible for coordination, while the registry should be responsible for tool management.
