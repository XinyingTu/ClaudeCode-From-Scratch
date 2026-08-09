# The main agent loop.
#
# Drives the agent until the LLM either produces a final answer or the
# step limit is reached.  The loop itself has no knowledge of how tools
# are implemented — it delegates entirely to the registry.
#
# The loop only understands the internal protocol defined in ADR-005
# (FinalAnswer / ToolCall). It never inspects a provider's raw response —
# that translation happens inside the LLM adapter (e.g. AnthropicClient).

from protocol import FinalAnswer, ToolCall


class AgentLoop:
    # Stop after this many steps to prevent runaway loops.
    DEFAULT_MAX_STEPS = 20

    def __init__(self, llm, tool_registry, context, max_steps: int = DEFAULT_MAX_STEPS):
        self.llm = llm
        self.registry = tool_registry
        self.context = context
        self.max_steps = max_steps

    def run(self) -> str:
        """
        Repeatedly ask the LLM what to do next until it returns a final
        answer or the step limit is hit.

        Returns the final answer string.
        Raises RuntimeError if max_steps is exhausted without a final answer.
        """
        for step in range(self.max_steps):
            response = self.llm.next(self.context)

            if isinstance(response, FinalAnswer):
                return response.content

            if isinstance(response, ToolCall):
                # Execute the tool and capture its output.
                # We call get_tool().run() directly instead of run_tool() so
                # that argument keys in `arguments` (e.g. "name") don't
                # collide with run_tool()'s own `name` parameter.
                tool = self.registry.get_tool(response.tool)
                result = tool.run(**response.arguments)

                # Hand the result back to the context so the LLM can see it
                # on the next turn.
                self.context.add_tool_result(response.tool, result)

            else:
                raise ValueError(f"Unknown response type: {type(response).__name__!r}")

        raise RuntimeError(
            f"AgentLoop reached max_steps ({self.max_steps}) without a final answer."
        )
