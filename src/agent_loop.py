# The main agent loop.
#
# Responsibilities:
#   - Receive a user task (string)
#   - Decide which tool to call next
#   - Execute the tool
#   - Feed the result back and repeat until the task is done
#
# This is the "brain" of the agent — it will eventually call the LLM
# to decide what to do, but for now it is just a placeholder.
