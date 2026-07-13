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

This decision builds on ADR-004 (Context), where the Loop assembles the current working state into an LLM request. The next challenge is defining how both sides communicate throughout the execution loop.

---

## Decision

The agent defines an internal communication protocol between the Agent Loop and the LLM.

The protocol is **bidirectional**.

### Request

The Agent Loop sends a structured request assembled from the current Context.

The request contains the minimum information required for the LLM to make the next decision.

`build_messages()` is responsible for constructing this request.

### Response

The LLM returns one structured response.

Version 1 supports two response types:

- `ToolCall`
- `FinalAnswer`

The Agent Loop depends only on this internal protocol.

Provider-specific protocols (such as Anthropic Tool Use) are translated into the internal protocol through a thin adapter layer.

---

## Trade-offs

### Pros

- Defines a clear communication contract between the Agent Loop and the LLM.
- Both requests and responses have explicit structures.
- The Agent Loop is independent of provider-specific APIs.
- Provider-specific changes are isolated inside adapters.
- The protocol can evolve without changing the orchestration logic.

### Cons

- Introduces a small translation layer.
- Requires maintaining an internal protocol definition.

---

## Alternatives Considered

### Option 1 — Natural Language Communication

The LLM returns free-form text (for example, "Please read README.md"), and the Agent Loop interprets the intent.

**Rejected**

Natural language is ambiguous and forces the Agent Loop to perform reasoning instead of orchestration.

---

### Option 2 — Depend Directly on Provider Protocols

The Agent Loop directly processes provider-specific protocols (such as Anthropic Tool Use).

**Rejected**

This tightly couples the orchestration layer to a specific model provider.

Supporting another provider would require changing the Agent Loop.

---

### Option 3 — Internal Protocol with Thin Adapters

Define a provider-independent internal protocol.

Translate provider-specific protocols through thin adapters.

**Accepted**

The orchestration layer depends only on stable internal abstractions while provider-specific details remain isolated.

---

## First Principles

- **Hide Change**  
  Provider-specific protocol changes are isolated inside adapters.

- **Depend on Stable Abstractions**  
  The Agent Loop depends on an internal protocol instead of provider-specific APIs.

- **Single Responsibility**  
  The Agent Loop orchestrates execution. Adapters translate external protocols.

- **Minimize Information**  
  Requests contain only the minimum information required for the LLM to make the next decision.

---

## Reality Check

Claude Code follows the same architectural idea.

Instead of defining its own provider protocol, it relies on Anthropic's Tool Use protocol to communicate with the Claude API.

Our Mini Claude Code adopts the same architectural principle but defines a small internal protocol for educational purposes. A thin adapter translates between Anthropic's protocol and our internal protocol.

---

## Next Challenge

The protocol defines how the Agent Loop and the LLM communicate.

The next challenge is implementing the protocol objects and integrating them into the execution loop while keeping the orchestration layer independent of provider-specific APIs.
