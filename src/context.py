# Manages the conversation context window.
#
# Tracks the list of messages (user, assistant, tool results) that
# are passed to the LLM on each turn, and handles truncation when
# the context grows too long.
