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

6. **(Sprint 2)** `AnthropicClient.next()` now produces both response
   types. It sends a real `tools` schema (built from the injected
   `ToolRegistry`, via each tool's `name` / `description` / `input_schema`)
   so Claude — not our code — decides whether to answer directly or call
   `list_files`. A `tool_use` content block in the response is translated
   into `ToolCall(tool, arguments, call_id)`; otherwise the text blocks
   become `FinalAnswer`, as before. `AgentLoop` is unchanged by this: it
   still only branches on `isinstance(response, FinalAnswer | ToolCall)`.

7. **(Sprint 2)** `Context.build_messages()` now represents a tool
   observation two ways, chosen by whether `call_id` is set:
   - No `call_id` (e.g. tests that call `add_tool_result(name, result)`
     directly): the original flattened `"[tool result]\n..."` string.
   - `call_id` present (set by `AnthropicClient` from Claude's `tool_use`
     block id, and threaded through by `AgentLoop`): an `assistant`
     message replaying the exact `tool_use` block Claude sent, followed
     by a `user` message with the matching `tool_result` block. This lets
     Claude see its own prior tool call paired with the real result on
     the next turn, instead of a made-up explanatory string.

   `AgentLoop` never constructs either shape itself — it only forwards
   `call_id`/`arguments` from the `ToolCall` it already has.

---

## Next Challenge (revised after Sprint 2)

The `ToolCall` ⇄ `FinalAnswer` round trip, including real tool execution
and paired tool-use/tool-result replay, now works end-to-end for a single
tool (`list_files`). This surfaced one tension worth tracking rather than
solving now:

`Context.build_messages()` directly emits Anthropic's own block vocabulary
(`"type": "tool_use"`, `"tool_use_id"`, etc.) rather than a fully
neutral internal shape translated by a separate adapter. This matches
the "Reality Check" above — we deliberately kept the adapter thin and did
not introduce a second translation layer for a single-provider project.
If a second provider is ever added, `Context` would need either parallel
build-methods per provider or a real internal event representation with
per-provider adapters translating on the way out. Until multi-provider
support is an actual requirement, this is intentional debt, not a bug.

The next challenge, when it comes, is adding a second real tool
(`read_file`) and seeing whether one `call_id`-keyed observation shape
still holds, or whether provider-specific request assembly needs to move
out of `Context` entirely.

## Implementation Status (Sprint 3)

A second and third real tool (`read_file`, `run_tests`) were added purely
by registering two new `BaseTool` subclasses in `ToolRegistry`. The
question posed above — whether the one `call_id`-keyed observation shape
still holds — is answered: it does. No change was required to
`protocol.py`, `agent_loop.py`, `context.py`, or `AnthropicClient.next()`.
`AnthropicClient._tool_schemas()` already built its `tools` list from
`tool_registry.list_tools()`, so a third registered tool is simply a third
schema entry with no code change. `AgentLoop.run()` already dispatched by
`registry.get_tool(response.tool).run(**response.arguments)`, so a third
tool name is just another registry lookup. This confirms ADR-002's and
ADR-003's predictions rather than revising them — see
`tests/test_tool_use_loop_integration.py::test_full_loop_across_three_different_tools_before_final_answer`
for the full three-tool, multi-round proof.

One latent tension surfaced by having three tools instead of one:
`AnthropicClient.next()` only reads the *first* `tool_use` block out of a
response (`break` on the first match). Anthropic's API allows a single
turn to request several tool calls at once, and with only one tool
available that case was moot — Claude had nothing else to batch. With
three tools it becomes a real possibility (e.g. reading two files in one
turn), and today any block after the first would be silently dropped
rather than executed or reported. This is not fixed here — the mission
scope for this sprint is read-only, single-call-per-round tool use — but
it is now a concrete, observable gap rather than a hypothetical one, and
should be the next thing addressed if/when multi-tool-call turns are
seen in practice.

Separately, `ReadFileTool` and `RunTestsTool` each re-implement their own
"stay inside `root`" path-containment check (see `src/tools/file_tools.py`
and `src/tools/command_tools.py`). This duplication was left as-is rather
than extracted into a shared helper on `BaseTool`, since two call sites
don't yet justify a new abstraction — but a third repo-scoped tool should
prompt revisiting this.
