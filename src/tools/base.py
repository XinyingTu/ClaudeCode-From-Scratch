# Base class that every tool must inherit from.
#
# Defines the common interface:
#   - name:        str  — identifier the LLM uses to call the tool
#   - description: str  — shown to the LLM so it knows what the tool does
#   - run(**kwargs)     — executes the tool and returns a result string

from abc import ABC, abstractmethod


class BaseTool(ABC):
    # Subclasses define these as class-level attributes.
    name: str
    description: str

    @abstractmethod
    def run(self, **kwargs) -> str:
        """Execute the tool and return a plain-text result."""
        ...
