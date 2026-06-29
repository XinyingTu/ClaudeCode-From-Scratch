# Central registry that maps tool names to tool instances.
#
# Usage:
#   registry = ToolRegistry()
#   registry.register(MyTool())
#   registry.run_tool("my_tool", arg1="value")

from tools.base import BaseTool


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """Add a tool to the registry under its name."""
        self._tools[tool.name] = tool

    def get_tool(self, name: str) -> BaseTool:
        """Return the tool with the given name, or raise KeyError if not found."""
        if name not in self._tools:
            raise KeyError(f"No tool named '{name}'")
        return self._tools[name]

    def list_tools(self) -> list[str]:
        """Return a sorted list of registered tool names."""
        return sorted(self._tools.keys())

    def run_tool(self, name: str, **kwargs) -> str:
        """Look up a tool by name and run it with the given keyword arguments."""
        tool = self.get_tool(name)
        return tool.run(**kwargs)
