# Internal communication protocol between AgentLoop and the LLM (ADR-005).
#
# The Agent Loop depends only on these two response types — never on a
# provider's raw response shape. Provider adapters (e.g. AnthropicClient)
# translate their own responses into these before handing them to the loop.

from dataclasses import dataclass, field


@dataclass(frozen=True)
class FinalAnswer:
    """The LLM is done reasoning; content is the answer to show the user."""
    content: str


@dataclass(frozen=True)
class ToolCall:
    """The LLM wants one tool executed before it continues.

    call_id is an opaque correlation id supplied by the provider adapter
    (e.g. Anthropic's tool_use block id). AgentLoop passes it straight
    through to Context so the result can be paired back to this exact
    call. It defaults to None for callers that don't need pairing
    (tests, simple providers).
    """
    tool: str
    arguments: dict = field(default_factory=dict)
    call_id: str | None = None
