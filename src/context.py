# Manages the conversation context window.
#
# Tracks the list of messages (user, assistant, tool results) that
# are passed to the LLM on each turn, and handles truncation when
# the context grows too long.


class Context:
    """Holds the working state of a single agent task.

    The AgentLoop reads and writes this object on every iteration.
    The LLM receives it via llm.next(context) so it can build a request.
    """

    def __init__(self, user_request: str):
        self.user_request = user_request
        # Each entry is a dict: tool_name, result, call_id, arguments.
        # call_id is None unless the provider adapter supplied one (see
        # ToolCall.call_id in protocol.py).
        self.observations: list[dict] = []

    def add_tool_result(
        self,
        tool_name: str,
        result: str,
        call_id: str | None = None,
        arguments: dict | None = None,
    ) -> None:
        """Record one tool execution so the LLM sees it on the next turn.

        call_id/arguments are optional so callers that don't need
        provider-native pairing (e.g. existing tests) can keep calling
        this with just (tool_name, result).
        """
        self.observations.append({
            "tool_name": tool_name,
            "result": result,
            "call_id": call_id,
            "arguments": arguments or {},
        })

    def build_messages(self) -> list[dict]:
        """Assemble the request the LLM needs to make its next decision.

        Per ADR-005, this contains only the minimum required information:
        the original request plus any tool results observed so far.

        When an observation carries a call_id (set by a provider adapter
        that speaks a real tool-use protocol, e.g. Anthropic), it is
        replayed as a paired tool_use/tool_result message so the model
        sees its own prior tool request alongside the result. Without a
        call_id, it falls back to the plain flattened text form.
        """
        messages = [{"role": "user", "content": self.user_request}]
        for obs in self.observations:
            if obs["call_id"] is None:
                messages.append({
                    "role": "user",
                    "content": f"[{obs['tool_name']} result]\n{obs['result']}",
                })
                continue

            messages.append({
                "role": "assistant",
                "content": [{
                    "type": "tool_use",
                    "id": obs["call_id"],
                    "name": obs["tool_name"],
                    "input": obs["arguments"],
                }],
            })
            messages.append({
                "role": "user",
                "content": [{
                    "type": "tool_result",
                    "tool_use_id": obs["call_id"],
                    "content": obs["result"],
                }],
            })
        return messages
