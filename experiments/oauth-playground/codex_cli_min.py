#!/usr/bin/env python3
"""
OpenAI subscription authentication via OpenAI CLI.
Based on GPT-5 Pro research for subscription-based authentication.
"""

import subprocess
import sys
import json

def main():
    print("🔐 Testing OpenAI CLI authentication...")

    try:
        # Check if OpenAI CLI is installed
        result = subprocess.run(["openai", "--version"], capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ OpenAI CLI not installed")
            print("📋 To fix:")
            print("1. Install OpenAI CLI: pip install openai-cli")
            print("2. Login: openai auth login")
            return

        print(f"✅ OpenAI CLI version: {result.stdout.strip()}")

        # Test authentication by listing models (requires auth)
        models_result = subprocess.run(
            ["openai", "api", "models.list", "--limit", "1"],
            capture_output=True, text=True
        )

        if models_result.returncode != 0:
            print("❌ Not authenticated with OpenAI")
            print("📋 To fix: Run 'openai auth login'")
            print(f"Error: {models_result.stderr}")
            return

        print("✅ OpenAI authentication verified!")

        # Test a simple completion
        print("🤖 Testing OpenAI API...")
        completion_result = subprocess.run([
            "openai", "api", "completions.create",
            "-m", "gpt-3.5-turbo-instruct",
            "-p", "Say hi in one sentence.",
            "--max-tokens", "50"
        ], capture_output=True, text=True)

        if completion_result.returncode == 0:
            try:
                response = json.loads(completion_result.stdout)
                text = response.get("choices", [{}])[0].get("text", "").strip()
                print(f"OpenAI response: {text}")
                print("🎉 Hooray!!! OpenAI CLI working!")
            except json.JSONDecodeError:
                print(f"✅ OpenAI API responded: {completion_result.stdout}")
                print("🎉 Hooray!!! OpenAI CLI working!")
        else:
            print(f"❌ OpenAI API error: {completion_result.stderr}")

    except FileNotFoundError:
        print("❌ OpenAI CLI not found in PATH")
        print("📋 To fix:")
        print("1. Install OpenAI CLI: pip install openai-cli")
        print("2. Login: openai auth login")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()