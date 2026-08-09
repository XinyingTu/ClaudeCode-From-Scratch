# Demo: prove the project can send a message to Claude and print the reply.
#
# Run from the repository root:
#   ANTHROPIC_API_KEY=sk-ant-... python3 demo_hello_claude.py

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from llm_client import AnthropicClient

if __name__ == "__main__":
    client = AnthropicClient()
    reply = client.send("Hello! Briefly introduce yourself.")
    print(reply)
