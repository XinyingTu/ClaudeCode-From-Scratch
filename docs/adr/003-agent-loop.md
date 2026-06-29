# ADR-003: Agent Loop

## Status

Accepted

---

## Context

A coding agent cannot solve most tasks with a single LLM call because the model initially has incomplete knowledge of the environment.

After each tool execution, the agent receives new observations that may change the next decision. The system therefore requires an execution loop that repeatedly coordinates reasoning and tool execution until enough information has been gathered to produce a final answer.

---

## Decision

Introduce an **Agent Loop** as the orchestration layer of the agent.

The Agent Loop is responsible for:

* building the current context
* calling the LLM
* parsing the structured response
* executing tool calls through the Tool Registry
* storing tool observations in the Context
* terminating only when the LLM explicitly returns a `final_answer`

The Agent Loop performs orchestration only. All reasoning remains the responsibility of the LLM.

To prevent unexpected infinite execution, the loop includes a configurable `max_steps` limit.

---

## Trade-offs

### Pros

* Supports iterative reasoning over newly observed information.
* Keeps orchestration independent from reasoning.
* Enables multi-step tool use without coupling the loop to specific tools.
* Simple to test because the control flow is deterministic.

### Cons

* Introduces an additional orchestration layer.
* Requires a structured communication protocol between the LLM and the Agent Loop.
* Incorrect model outputs may terminate with an error.

---

## Alternatives Considered

### Option 1 — Single LLM Call

Perform all reasoning in a single request.

Rejected because the model cannot reason over information that has not yet been observed.

### Option 2 — Iterative Agent Loop

Alternate between reasoning, acting, and observing until the task is complete.

Accepted because every observation expands the agent's understanding of the environment, enabling more informed decisions in subsequent iterations.

---

## Key Principles

* Separation of Concerns
* Explicit Protocol over Implicit Inference
* Deterministic Control Flow
* Dependency Injection
* Testability

---

## Next Challenge

An iterative Agent Loop continuously accumulates observations.

Without careful context management, the growing context will increase computational cost and eventually exceed the model's context window.

The next architectural question is how observations should be represented and managed efficiently.
