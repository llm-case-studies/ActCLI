#!/usr/bin/env python3
"""
Claude subscription authentication via Claude CLI.
Uses the correct -p (print) mode with JSON output.
"""

import subprocess
import json

def main():
    print("🔐 Testing Claude CLI authentication...")

    try:
        # Test Claude CLI with -p (print) mode and JSON output
        print("🤖 Testing Claude API with subscription auth...")

        result = subprocess.run([
            "claude", "-p", "Say hi in one sentence.", "--output-format", "json"
        ], capture_output=True, text=True)

        if result.returncode == 0:
            # Parse JSON response
            try:
                data = json.loads(result.stdout.strip())
                response_text = (
                    data.get("result") or
                    data.get("text") or
                    data.get("output") or
                    data.get("content") or
                    result.stdout.strip()
                )
                print(f"✅ Claude response: {response_text}")
                print("🎉 Hooray!!! Claude CLI working with subscription auth!")
                return True
            except json.JSONDecodeError:
                print(f"✅ Claude response (raw): {result.stdout.strip()}")
                print("🎉 Hooray!!! Claude CLI working!")
                return True
        else:
            print(f"❌ Claude CLI error: {result.stderr}")
            print("📋 Tip: Make sure you're logged in to Claude CLI")
            return False

    except FileNotFoundError:
        print("❌ Claude CLI not found in PATH")
        print("📋 To fix: Install Claude CLI and login")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    main()