# Base class that every tool must inherit from.
#
# Defines the common interface:
#   - name:          str  — identifier the LLM uses to call the tool
#   - description:   str  — shown to the LLM so it knows what the tool does
#   - input_schema:  dict — JSON Schema for the tool's arguments, sent to
#                           providers that need one (e.g. Anthropic tool use)
#   - run(**kwargs)       — executes the tool and returns a result string

from abc import ABC, abstractmethod


class BaseTool(ABC):
    # Subclasses define these as class-level attributes.
    name: str
    description: str
    # Tools with no arguments can leave this as-is.
    input_schema: dict = {"type": "object", "properties": {}}

    @abstractmethod
    def run(self, **kwargs) -> str:
        """Execute the tool and return a plain-text result."""
        ...
