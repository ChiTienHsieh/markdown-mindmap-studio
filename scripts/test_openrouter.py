#!/usr/bin/env python3
"""
Test OpenRouter connection with Anthropic SDK and Claude Agent SDK.

Usage:
    uv run python scripts/test_openrouter.py
"""

import asyncio
import os
from pathlib import Path

# Load .env from project root
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")


def test_env_vars():
    """Verify environment variables are set correctly."""
    print("=" * 60)
    print("1. Checking environment variables...")
    print("=" * 60)

    base_url = os.environ.get("ANTHROPIC_BASE_URL", "")
    auth_token = os.environ.get("ANTHROPIC_AUTH_TOKEN", "")
    api_key = os.environ.get("ANTHROPIC_API_KEY", "NOT_SET")

    print(f"  ANTHROPIC_BASE_URL: {base_url or '(empty)'}")
    print(f"  ANTHROPIC_AUTH_TOKEN: {'sk-or-v1-...' + auth_token[-8:] if auth_token else '(empty)'}")
    print(f"  ANTHROPIC_API_KEY: {repr(api_key)}")

    if base_url != "https://openrouter.ai/api":
        print("  [WARN] ANTHROPIC_BASE_URL should be https://openrouter.ai/api")
    if not auth_token:
        print("  [ERROR] ANTHROPIC_AUTH_TOKEN is empty!")
        return False
    if api_key and api_key != "NOT_SET":
        print("  [WARN] ANTHROPIC_API_KEY should be empty string, got:", repr(api_key))

    print("  [OK] Environment variables look good!")
    return True


def test_anthropic_sdk():
    """Test Anthropic SDK with OpenRouter."""
    print("\n" + "=" * 60)
    print("2. Testing Anthropic SDK with OpenRouter...")
    print("=" * 60)

    try:
        import anthropic

        # Create client with explicit OpenRouter config
        client = anthropic.Anthropic(
            base_url=os.environ.get("ANTHROPIC_BASE_URL"),
            auth_token=os.environ.get("ANTHROPIC_AUTH_TOKEN"),
            api_key=None,
        )

        # Use the model from env, fallback to a free model
        free_model = os.environ.get("ANTHROPIC_MODEL", "openai/gpt-oss-120b:free")

        print(f"  Using free model: {free_model}")
        print("  Sending test message...")

        message = client.messages.create(
            model=free_model,
            max_tokens=100,
            messages=[
                {"role": "user", "content": "Say 'Hello from OpenRouter!' in exactly 5 words."}
            ]
        )

        # Handle both TextBlock and ThinkingBlock (reasoning models)
        response_text = ""
        for block in message.content:
            if hasattr(block, 'text'):
                response_text += block.text
            elif hasattr(block, 'thinking'):
                response_text += f"[thinking: {block.thinking[:50]}...]"

        print(f"  Response: {response_text}")
        print(f"  Model: {message.model}")
        print(f"  Usage: {message.usage.input_tokens} in / {message.usage.output_tokens} out")
        print("  [OK] Anthropic SDK works with OpenRouter!")
        return True

    except Exception as e:
        print(f"  [ERROR] {type(e).__name__}: {e}")
        return False


async def test_agent_sdk():
    """Test Claude Agent SDK with OpenRouter."""
    print("\n" + "=" * 60)
    print("3. Testing Claude Agent SDK...")
    print("=" * 60)

    try:
        from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions

        print("  Creating ClaudeSDKClient...")

        options = ClaudeAgentOptions(
            max_turns=1,
        )

        async with ClaudeSDKClient(options=options) as client:
            print("  Sending query...")
            await client.query("What is 2 + 2? Reply in one word.")

            print("  Receiving response...")
            response_text = ""
            async for message in client.receive_response():
                if hasattr(message, 'content'):
                    for block in message.content:
                        if hasattr(block, 'text'):
                            response_text += block.text

            print(f"  Response: {response_text}")

        print("  [OK] Claude Agent SDK works!")
        return True

    except ImportError as e:
        print(f"  [SKIP] claude-agent-sdk not installed: {e}")
        return None
    except Exception as e:
        print(f"  [ERROR] {type(e).__name__}: {e}")
        return False


def main():
    print("\nOpenRouter + Claude SDK Test Suite")
    print("=" * 60)

    results = {}

    # Test 1: Environment variables
    results["env"] = test_env_vars()
    if not results["env"]:
        print("\n[ABORT] Fix environment variables first!")
        return

    # Test 2: Anthropic SDK
    results["anthropic"] = test_anthropic_sdk()

    # Test 3: Agent SDK
    results["agent"] = asyncio.run(test_agent_sdk())

    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    for name, result in results.items():
        status = "[OK]" if result else "[FAIL]" if result is False else "[SKIP]"
        print(f"  {name}: {status}")


if __name__ == "__main__":
    main()
