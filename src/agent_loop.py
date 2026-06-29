# The main agent loop.
#
# Drives the agent until the LLM either produces a final answer or the
# step limit is reached.  The loop itself has no knowledge of how tools
# are implemented — it delegates entirely to the registry.

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

            response_type = response.get("type")

            if response_type == "final_answer":
                return response["content"]

            if response_type == "tool_call":
                tool_name = response["tool"]
                arguments = response.get("arguments", {})

                # Execute the tool and capture its output.
                # We call get_tool().run() directly instead of run_tool() so
                # that argument keys in `arguments` (e.g. "name") don't
                # collide with run_tool()'s own `name` parameter.
                tool = self.registry.get_tool(tool_name)
                result = tool.run(**arguments)

                # Hand the result back to the context so the LLM can see it
                # on the next turn.
                self.context.add_tool_result(tool_name, result)

            else:
                raise ValueError(f"Unknown response type: {response_type!r}")

        raise RuntimeError(
            f"AgentLoop reached max_steps ({self.max_steps}) without a final answer."
        )
