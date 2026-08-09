# ADR-005: Internal Communication Protocol

## Status

Accepted

---

## Context

The Agent Loop and the LLM are independent systems.

The Loop is responsible for orchestration.

The LLM is responsible for reasoning.

Neither side can directly invoke the other's functions or access its internal state.

Therefore, they require a shared communication contract.

The Agent Loop must know how to construct requests.

The LLM must know how to communicate its decisions in a structured form.

This decision builds on ADR-004 (Context), where the Loop assembles the working state into an LLM request. The next challenge is defining how both sides communicate throughout the execution loop.

---

## Decision

The Agent Loop communicates with the LLM through an internal communication protocol.

The protocol is bidirectional.

### Request

The Agent Loop sends a structured request assembled from the current Context.

The request contains only the minimum information required for the LLM to make the next decision.

`build_messages()` is responsible for assembling this request.

### Response

The LLM returns one structured response.

Version 1 supports two response types:

- `ToolCall`
- `FinalAnswer`

The Agent Loop depends only on this internal protocol.

Provider-specific communication protocols are translated into the internal protocol through a thin adapter.

---

## Trade-offs

### Pros

- Defines a clear communication contract between the Agent Loop and the LLM.
- Both requests and responses have explicit structures.
- The orchestration layer remains independent of provider-specific APIs.
- Provider-specific changes are isolated at the system boundary.
- The protocol can evolve without changing the Agent Loop.

### Cons

- Introduces a small translation layer.
- Requires maintaining an internal protocol.

---

## Alternatives Considered

### Option 1 — Natural Language Communication

The LLM returns free-form text (for example, "Please read README.md"), and the Agent Loop interprets the intent.

**Rejected**

Natural language is ambiguous and forces the Agent Loop to perform reasoning instead of orchestration.

---

### Option 2 — Depend Directly on Provider Protocols

The Agent Loop directly depends on a provider's communication protocol (for example, Anthropic Tool Use).

**Rejected**

This tightly couples the orchestration layer to a specific provider.

Changes to external protocols would propagate into the Agent Loop.

---

### Option 3 — Internal Protocol with Thin Adapters

The Agent Loop communicates through a provider-independent internal protocol.

Provider-specific protocols are translated through thin adapters.

**Accepted**

The orchestration layer depends only on stable internal abstractions while provider-specific details remain isolated.

---

## First Principles

### Hide Change

Provider-specific protocol changes are isolated inside adapters instead of propagating into the Agent Loop.

### Depend on Stable Abstractions

The Agent Loop depends on an internal protocol rather than provider-specific communication protocols.

### Single Responsibility

The Agent Loop coordinates execution.

Adapters translate between external and internal protocols.

### Minimize Information

Requests contain only the minimum sufficient information required for the LLM to make the next decision.

---

## Reality Check

Claude Code currently targets only the Claude API.

Therefore, it directly relies on Anthropic's Tool Use protocol rather than introducing an additional provider-independent protocol.

This is a product decision rather than an architectural principle.

If Claude Code were to support multiple model providers in the future, the same architectural reasoning would naturally lead to isolating provider-specific protocols behind a stable internal abstraction.

Our Mini Claude Code derives the architecture from first principles and therefore defines a small internal protocol while keeping the implementation minimal through a thin adapter.

---

## Implementation Status

ADR-005 is now implemented in code (Sprint 1.5).

1. `src/protocol.py` defines the internal typed protocol described above:
   `FinalAnswer` and `ToolCall`, as plain frozen dataclasses.

2. `AgentLoop` no longer inspects provider-style raw dict responses
   (e.g. `response.get("type")`, `response["content"]`). It depends only
   on the internal protocol, branching on `isinstance(response, FinalAnswer)`
   / `isinstance(response, ToolCall)`.

3. `FakeLLM` and the AgentLoop test suite were migrated to construct and
   return `FinalAnswer` / `ToolCall` instances instead of dicts, preserving
   all previously verified behavior.

4. `AnthropicClient` currently acts as the provider boundary described in
   Option 3 / "Hide Change" above: it receives Anthropic SDK responses and
   translates them into the internal protocol through its `next(context)`
   method, so the translation adapter lives entirely at the edge.

5. The real-Claude `FinalAnswer` path now runs end-to-end:

   ```
   Context
     → AgentLoop
       → AnthropicClient.next()
         → Anthropic SDK
           → Claude API
         → translated back into FinalAnswer
       → AgentLoop returns FinalAnswer.content
   ```

6. `ToolCall` is part of the internal protocol and is consumed by
   `AgentLoop`, but `AnthropicClient.next()` cannot yet produce one —
   real Anthropic tool-use translation is intentionally deferred to a
   later sprint. `AnthropicClient` is therefore a partial adapter today:
   correct for the shape it implements, incomplete for the protocol it
   depends on.

7. `Context.build_messages()` is sufficient for the current text-only,
   no-tool-calls request shape. It has not yet been exercised against
   real tool results, so it does not yet address how tool results should
   be represented in Anthropic's native message format (e.g. `tool_result`
   content blocks) versus the flattened string it produces today.

---

## Next Challenge

The FinalAnswer path is implemented end-to-end. The next challenge is
extending `AnthropicClient` to translate Claude's real tool-use responses
into `ToolCall`, and extending `Context.build_messages()` to represent
tool results in the provider's native format on the request side — without
leaking either shape into `AgentLoop`.
