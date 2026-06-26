# Thin wrapper around whichever LLM API we use.
#
# Keeps all API-specific code in one place so the rest of the agent
# does not care whether we call Claude, OpenAI, or a local model.
#
# NOTE: Do not add real API calls here until the tool layer is tested.
