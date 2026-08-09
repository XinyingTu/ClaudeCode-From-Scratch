# Thin wrapper around whichever LLM API we use.
#
# Keeps all API-specific code in one place so the rest of the agent
# does not care whether we call Claude, OpenAI, or a local model.
#
# next() is the adapter required by ADR-005: it translates Anthropic's
# raw response into the internal protocol (FinalAnswer / ToolCall) so
# AgentLoop never sees a provider-specific shape.
#
# Sprint 1.5 scope: only the FinalAnswer path is translated. Claude's
# real tool-use protocol is not wired up yet — that is a later step.

import anthropic

from protocol import FinalAnswer

DEFAULT_MODEL = "claude-opus-5"


class AnthropicClient:
    """Sends a single message to Claude and returns the reply text.

    Credentials come from the ANTHROPIC_API_KEY environment variable —
    anthropic.Anthropic() reads it automatically. Never hardcode a key here.
    """

    def __init__(self, model: str = DEFAULT_MODEL):
        self._client = anthropic.Anthropic()
        self.model = model

    def send(self, message: str) -> str:
        """Send one user message and return Claude's text reply."""
        response = self._client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[{"role": "user", "content": message}],
        )
        return "".join(block.text for block in response.content if block.type == "text")

    def next(self, context) -> FinalAnswer:
        """Ask Claude what to do next, translated into the internal protocol.

        This sprint only implements the FinalAnswer path (see ADR-005) —
        Claude's reply text becomes the final answer directly.
        """
        response = self._client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=context.build_messages(),
        )
        text = "".join(block.text for block in response.content if block.type == "text")
        return FinalAnswer(content=text)
