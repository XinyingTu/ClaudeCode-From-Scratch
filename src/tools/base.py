# Base class (or dataclass) that every tool must inherit from.
#
# Defines the common interface:
#   - name:        str  — identifier the LLM uses to call the tool
#   - description: str  — shown to the LLM so it knows what the tool does
#   - run(**kwargs)     — executes the tool and returns a result string
