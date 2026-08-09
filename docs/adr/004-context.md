# ADR-004: Context

## Status

Accepted

## Context

The Agent Loop (ADR-003) repeatedly asks the LLM what to do next and executes tool calls in response. Each tool execution produces an observation that the LLM needs to see on its *next* call — otherwise the loop cannot make progress, since the LLM would keep re-deciding from the same starting information.

This means the working state of one task — the original request plus every tool result observed so far — has to live somewhere. If the Agent Loop stored and shaped that state itself, it would be doing two jobs at once: coordinating the reasoning cycle (its actual responsibility per ADR-003), and knowing how to turn accumulated history into an LLM-consumable request.

The Agent Loop needs a place to record observations and a way to turn that history into the next request, without itself knowing the message-storage details.

## Decision

Introduce a **Context** object that owns the working state of a single task.

One user request is treated as one task, and one task owns exactly one `Context` (see README, Agent Execution Loop). `Context` holds:

- `user_request` — the original request text, set once at construction.
- `observations` — an ordered list of tool execution records, appended to over the course of the loop.

`Context` exposes two operations:

- `add_tool_result(tool_name, result, call_id=None, arguments=None)` — records one tool execution. `call_id`/`arguments` are optional: they are only present when the response came from a provider adapter that supplied a real tool-call id (e.g. `AnthropicClient`); callers that don't need provider-native pairing (such as tests) can omit them.
- `build_messages()` — assembles `user_request` plus every recorded observation into the message list handed to the LLM on the next round.

`build_messages()` chooses between two representations per observation:

- No `call_id`: a flattened `{"role": "user", "content": "[tool_name result]\n..."}` message.
- `call_id` present: a paired `assistant` message replaying the `tool_use` block (name, id, input) followed by a `user` message carrying the matching `tool_result` block — so the LLM sees its own prior tool call alongside the real result, matching how a real tool-use protocol expects history to be replayed.

The Agent Loop only calls `context.add_tool_result(...)`, forwarding whatever `call_id`/`arguments` the `ToolCall` it received already carried (per ADR-005). It never constructs a message shape itself — that decision belongs entirely to `Context`.

## Trade-offs

### Pros

- Single owner of "how does this task's history become the next LLM request" — the Agent Loop stays orchestration-only.
- The Agent Loop and its tests don't need to know Anthropic's `tool_use`/`tool_result` shapes.
- The optional `call_id` lets the same `Context` class serve both plain observations (used by existing tests and non-provider callers) and paired provider replay, without two separate classes.

### Cons

- `build_messages()` now contains provider-shaped dictionaries (`tool_use`, `tool_result`, `tool_use_id`) — a provider-specific detail living inside a class that is otherwise meant to be provider-neutral. This is flagged, not hidden — see ADR-005's Next Challenge.
- No compaction or truncation strategy exists yet. `observations` grows without bound for the life of a task; long-running tasks will eventually need this addressed (tracked in the README roadmap, Phase 3).

## Alternatives Considered

### Option 1 — Agent Loop holds the message list directly

The Agent Loop appends to its own list of provider-shaped messages as it executes tools.

**Rejected**

Mixes orchestration with state representation, and forces the Agent Loop to know provider-specific message shapes — the exact coupling ADR-003 assigns elsewhere.

### Option 2 — Context as an opaque message accumulator

Callers append pre-built message dicts directly to `Context`; `Context` just stores and returns them in order.

**Rejected**

Pushes the shape decision out to every caller instead of centralizing it in one place, defeating the point of having a dedicated component.

### Option 3 — Context owns typed observations and translates them internally

Callers record structured facts (`tool_name`, `result`, `call_id`, `arguments`); `Context` alone decides how those facts become messages.

**Accepted**

Keeps the translation logic in exactly one place, and lets that logic evolve (e.g. adding the paired `tool_use`/`tool_result` form in Sprint 2) without changing any caller.

## First Principles

**Single Responsibility**

`Context` owns working state and its translation into LLM input. The Agent Loop owns orchestration. `AnthropicClient` owns provider translation of responses. None of these responsibilities overlap.

**Hide Change**

Whether an observation renders as a flattened string or a paired `tool_use`/`tool_result` block is decided entirely inside `build_messages()`. Callers of `add_tool_result()` and the Agent Loop are unaffected either way.

**Minimize Information**

`build_messages()` assembles only the original request plus the tool results observed so far — nothing else is retained or sent.

## Next Challenge

`Context.build_messages()` currently emits Anthropic's own block vocabulary directly rather than a fully neutral internal shape translated by a separate adapter — acceptable for a single-provider project, but worth revisiting if a second provider is ever added (see ADR-005's Next Challenge, which this ADR feeds into).

Separately, `observations` has no compaction or truncation strategy. As task length grows, this Context will need a policy for what to keep, summarize, or drop.
