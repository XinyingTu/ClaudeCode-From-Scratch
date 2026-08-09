# Thin wrapper around whichever LLM API we use.
#
# Keeps all API-specific code in one place so the rest of the agent
# does not care whether we call Claude, OpenAI, or a local model.
#
# next() is the adapter required by ADR-005: it translates Anthropic's
# raw response into the internal protocol (FinalAnswer / ToolCall) so
# AgentLoop never sees a provider-specific shape.
#
# Sprint 2 scope: next() now also builds Anthropic's real tool-use
# request (a `tools` schema list built from the injected ToolRegistry)
# and translates a `tool_use` response block into ToolCall. AgentLoop
# still only ever sees FinalAnswer / ToolCall — the tool_use/tool_result
# shapes stay inside this adapter and inside Context.build_messages().

import anthropic

from protocol import FinalAnswer, ToolCall

DEFAULT_MODEL = "claude-opus-5"


class AnthropicClient:
    """Sends messages to Claude and translates replies into our protocol.

    Credentials come from the ANTHROPIC_API_KEY environment variable —
    anthropic.Anthropic() reads it automatically. Never hardcode a key here.
    """

    def __init__(self, tool_registry, model: str = DEFAULT_MODEL):
        self._client = anthropic.Anthropic()
        self.model = model
        # Used by next() to build the `tools` schema Claude sees, and to
        # keep AnthropicClient's tool knowledge in sync with the same
        # registry AgentLoop uses to execute tools.
        self.tool_registry = tool_registry

    def send(self, message: str) -> str:
        """Send one user message and return Claude's text reply."""
        response = self._client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[{"role": "user", "content": message}],
        )
        return "".join(block.text for block in response.content if block.type == "text")

    def _tool_schemas(self) -> list[dict]:
        """Build Anthropic's tool-definition list from the registry.

        Claude decides whether to use a tool purely from this schema —
        nothing here hints at when a tool should be called.
        """
        schemas = []
        for name in self.tool_registry.list_tools():
            tool = self.tool_registry.get_tool(name)
            schemas.append({
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.input_schema,
            })
        return schemas

    def next(self, context):
        """Ask Claude what to do next, translated into the internal protocol.

        Anthropic text/end-turn responses become FinalAnswer.
        Anthropic tool_use responses become ToolCall (see ADR-005).
        """
        response = self._client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=context.build_messages(),
            tools=self._tool_schemas(),
        )

        tool_use_block = None
        for block in response.content:
            if block.type == "tool_use":
                tool_use_block = block
                break

        if tool_use_block is not None:
            return ToolCall(
                tool=tool_use_block.name,
                arguments=tool_use_block.input,
                call_id=tool_use_block.id,
            )

        text = "".join(block.text for block in response.content if block.type == "text")
        return FinalAnswer(content=text)
