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
    """The LLM wants one tool executed before it continues."""
    tool: str
    arguments: dict = field(default_factory=dict)
