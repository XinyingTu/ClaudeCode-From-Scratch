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
        # Each entry is (tool_name, result_string) in execution order.
        self.observations: list[tuple[str, str]] = []

    def add_tool_result(self, tool_name: str, result: str) -> None:
        """Record one tool execution so the LLM sees it on the next turn."""
        self.observations.append((tool_name, result))

    def build_messages(self) -> list[dict]:
        """Assemble the request the LLM needs to make its next decision.

        Per ADR-005, this contains only the minimum required information:
        the original request plus any tool results observed so far.
        """
        messages = [{"role": "user", "content": self.user_request}]
        for tool_name, result in self.observations:
            messages.append({
                "role": "user",
                "content": f"[{tool_name} result]\n{result}",
            })
        return messages
