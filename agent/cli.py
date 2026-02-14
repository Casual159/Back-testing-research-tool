#!/usr/bin/env python3
"""
CLI for testing the backtesting agent.

Usage:
    python -m agent.cli "What strategies are available?"
    python -m agent.cli --interactive
"""

import argparse
import asyncio
import sys
from uuid import UUID

from .core import create_agent


async def chat_once(message: str, conversation_id: str | None = None):
    """Send a single message and print response."""
    agent = create_agent()

    conv_id = UUID(conversation_id) if conversation_id else None
    response = await agent.chat(message, conv_id)

    print(f"\n{'='*60}")
    print(f"Phase: {response.phase.value}")
    print(f"Conversation: {response.conversation_id}")
    print(f"Tokens: {response.tokens_used} | Cost: ${response.cost_usd:.4f}")
    print(f"{'='*60}\n")

    print(response.message)

    if response.tool_calls:
        print(f"\n{'─'*60}")
        print(f"Tool calls: {len(response.tool_calls)}")
        for tc in response.tool_calls:
            print(f"  • {tc.tool_name}({tc.arguments})")

    if response.awaiting_confirmation:
        print(f"\n⏳ Awaiting confirmation: {response.confirmation_prompt}")

    return response.conversation_id


async def interactive_mode():
    """Run interactive chat session."""
    agent = create_agent()
    conversation_id = None

    print("Backtesting Research Agent")
    print("Type 'quit' or 'exit' to end the session")
    print("Type 'new' to start a new conversation")
    print("=" * 60)

    while True:
        try:
            user_input = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue

        if user_input.lower() in ("quit", "exit"):
            print("Goodbye!")
            break

        if user_input.lower() == "new":
            conversation_id = None
            print("Started new conversation.")
            continue

        response = await agent.chat(user_input, conversation_id)
        conversation_id = response.conversation_id

        print(
            f"\n[{response.phase.value}] (tokens: {response.tokens_used}, ${response.cost_usd:.4f})"
        )
        print("─" * 60)
        print(response.message)

        if response.tool_calls:
            print(f"\n📦 Tools used: {', '.join(tc.tool_name for tc in response.tool_calls)}")


def main():
    parser = argparse.ArgumentParser(description="Backtesting Research Agent CLI")
    parser.add_argument("message", nargs="?", help="Message to send")
    parser.add_argument("-i", "--interactive", action="store_true", help="Interactive mode")
    parser.add_argument("-c", "--conversation", help="Continue conversation by ID")

    args = parser.parse_args()

    if args.interactive:
        asyncio.run(interactive_mode())
    elif args.message:
        asyncio.run(chat_once(args.message, args.conversation))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
