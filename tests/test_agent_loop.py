# Tests for src/agent_loop.py
#
# Focus on the loop's control flow:
#   - Does it call the right tool given a mocked LLM response?
#   - Does it stop when the task is marked done?
#   - Does it handle tool errors gracefully?
