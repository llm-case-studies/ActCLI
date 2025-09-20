#!/usr/bin/env python3
"""
Test the Claude CLI adapter integration
"""

import sys
import os

# Add the ActCLI source to path so we can import
sys.path.insert(0, "/home/alex/Projects/ActCLI/src")

from actcli.seminar.adapters.claude_cli import ClaudeCLIAdapter

def test_claude_cli_adapter():
    print("🧪 Testing Claude CLI Adapter")
    print("=" * 40)

    try:
        # Initialize adapter
        print("🔧 Initializing Claude CLI adapter...")
        adapter = ClaudeCLIAdapter()

        print(f"✅ Adapter created: {adapter.name}")
        print(f"📍 Model: {adapter.model_version}")
        print(f"🌐 Is local: {adapter.is_local}")

        # Test simple generation
        print("\n🤖 Testing generation...")
        prompt = "Explain actuarial reserves in one sentence."

        response = adapter.generate(prompt)
        print(f"✅ Response: {response}")

        # Test with system message
        print("\n🎭 Testing with system message...")
        response2 = adapter.generate(
            "What is chain ladder method?",
            system="You are an expert actuary. Be concise and precise."
        )
        print(f"✅ Response with system: {response2}")

        # Test round 2 context
        print("\n🔄 Testing round 2 with context...")
        response3 = adapter.generate(
            "Original question about reserves",
            round_index=2,
            context_snippets="Previous expert said: Reserves are future liabilities estimates"
        )
        print(f"✅ Round 2 response: {response3}")

        print("\n🎉 All tests passed! Claude CLI adapter working!")
        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_claude_cli_adapter()
    sys.exit(0 if success else 1)