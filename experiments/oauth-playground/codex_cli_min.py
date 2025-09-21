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
        # Check if Codex CLI is installed
        result = subprocess.run(["codex", "--version"], capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ Codex CLI not installed")
            print("📋 To fix:")
            print("1. Install Codex CLI: npm install -g @openai/codex")
            print("2. Login: codex (and sign in with ChatGPT)")
            return

        print(f"✅ Codex CLI version: {result.stdout.strip()}")

        # Test with a simple exec command (like the GPT-5 Pro discussion suggested)
        print("🤖 Testing Codex CLI...")
        exec_result = subprocess.run([
            "codex", "exec", "Say hi in one sentence."
        ], capture_output=True, text=True, timeout=30)

        if exec_result.returncode == 0:
            print(f"✅ Codex response: {exec_result.stdout.strip()}")
            print("🎉 Hooray!!! Codex CLI working!")
        else:
            print(f"❌ Codex CLI error: {exec_result.stderr}")
            print("📋 Note: You might need to authenticate with 'codex' and sign in with ChatGPT")

    except FileNotFoundError:
        print("❌ Codex CLI not found in PATH")
        print("📋 To fix:")
        print("1. Install Codex CLI: npm install -g @openai/codex")
        print("2. Login: codex (and sign in with ChatGPT)")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()