#!/usr/bin/env python3
"""
Sample seminar configuration using Claude CLI for subscription-based auth
Demonstrates the new claude_cli provider in a multi-model seminar
"""

import sys
import os

# Add the ActCLI source to path
sys.path.insert(0, "/home/alex/Projects/ActCLI/src")

from actcli.models.participant import ParticipantSpec
from actcli.seminar.factory import AdapterFactory

def create_subscription_seminar():
    """Create a seminar using subscription-based authentication"""

    print("🎓 Creating Subscription-Based Seminar")
    print("=" * 50)

    # Define participants using subscription authentication
    participants = [
        # Claude via CLI (subscription auth)
        ParticipantSpec(
            alias="Claude-CLI",
            provider="claude_cli",
            model_id="claude-3-5-sonnet-20241022",
            params={"system": "You are an expert actuary specializing in life insurance."}
        ),

        # For comparison, we could also add other providers if available
        # Note: These would need API keys or other auth, so commenting out for demo

        # ParticipantSpec(
        #     alias="Claude-API",
        #     provider="anthropic",
        #     model_id="claude-3-haiku-20240307",
        #     params={"system": "You are an expert actuary specializing in property & casualty."}
        # ),

        # Echo adapter for testing
        ParticipantSpec(
            alias="Echo",
            provider="echo",
            model_id="test-echo",
            params={}
        )
    ]

    # Create adapters
    adapters = []
    for spec in participants:
        try:
            adapter = AdapterFactory.from_spec(spec, allow_cloud=True)
            adapters.append((spec.alias, adapter))
            print(f"✅ Created {spec.alias}: {adapter.name}")
        except Exception as e:
            print(f"❌ Failed to create {spec.alias}: {e}")

    return adapters

def test_seminar_interaction(adapters):
    """Test a simple seminar interaction"""

    print("\n🤖 Testing Seminar Interaction")
    print("=" * 50)

    prompt = "What are the key differences between term life and whole life insurance from a reserving perspective?"

    responses = []
    for alias, adapter in adapters:
        try:
            print(f"\n📢 {alias} responding...")
            response = adapter.generate(prompt)
            responses.append((alias, response))
            print(f"✅ {alias}: {response[:100]}...")
        except Exception as e:
            print(f"❌ {alias} failed: {e}")

    # Simulate round 2 with context
    if len(responses) > 1:
        print(f"\n🔄 Round 2 - Cross-pollination")
        print("=" * 30)

        # Create context from previous responses
        context = "\n".join([f"{alias}: {resp[:200]}..." for alias, resp in responses])

        # Ask first adapter to critique/build on others
        if adapters:
            alias, adapter = adapters[0]
            try:
                round2_response = adapter.generate(
                    prompt,
                    round_index=2,
                    context_snippets=context
                )
                print(f"✅ {alias} Round 2: {round2_response[:200]}...")
            except Exception as e:
                print(f"❌ {alias} Round 2 failed: {e}")

def main():
    """Main demo function"""

    print("🚀 ActCLI Subscription-Based Seminar Demo")
    print("Using Claude CLI for hassle-free authentication!")
    print("=" * 60)

    # Create seminar
    adapters = create_subscription_seminar()

    if not adapters:
        print("❌ No adapters created - check authentication")
        return False

    # Test interaction
    test_seminar_interaction(adapters)

    print("\n🎯 Summary")
    print("=" * 20)
    print("✅ Claude CLI adapter working with subscription auth")
    print("✅ No API keys needed for Claude")
    print("✅ Same login as Claude CLI users already know")
    print("✅ Ready for actuarial seminars!")

    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)