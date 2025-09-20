#!/usr/bin/env python3
"""
Simple test harness for basic authentication methods.
Conservative approach - just test what we can actually verify.
"""

import subprocess
import sys
from pathlib import Path

def test_gemini_oauth():
    """Test Gemini OAuth flow"""
    print("\n🔍 Testing Gemini OAuth...")

    if not Path("client_secret.json").exists():
        print("❌ client_secret.json not found")
        print("📋 Need to download from Google Cloud Console")
        return False

    try:
        result = subprocess.run([sys.executable, "gemini_oauth_min.py"],
                              capture_output=True, text=True, timeout=60)

        if "Hooray!!!" in result.stdout:
            print("✅ Gemini OAuth: WORKING")
            return True
        else:
            print(f"❌ Gemini OAuth output: {result.stdout}")
            if result.stderr:
                print(f"❌ Errors: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("⏰ Gemini OAuth: TIMEOUT (probably waiting for browser)")
        return False
    except Exception as e:
        print(f"❌ Gemini OAuth error: {e}")
        return False

def test_claude_cli():
    """Test Claude CLI authentication"""
    print("\n🔍 Testing Claude CLI...")

    try:
        result = subprocess.run([sys.executable, "claude_cli_min.py"],
                              capture_output=True, text=True, timeout=30)

        if "Hooray!!!" in result.stdout:
            print("✅ Claude CLI: WORKING")
            return True
        else:
            print(f"❌ Claude CLI output: {result.stdout}")
            if result.stderr:
                print(f"❌ Errors: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Claude CLI error: {e}")
        return False

def test_openai_cli():
    """Test OpenAI CLI authentication"""
    print("\n🔍 Testing OpenAI CLI...")

    try:
        result = subprocess.run([sys.executable, "codex_cli_min.py"],
                              capture_output=True, text=True, timeout=30)

        if "Hooray!!!" in result.stdout:
            print("✅ OpenAI CLI: WORKING")
            return True
        else:
            print(f"❌ OpenAI CLI output: {result.stdout}")
            if result.stderr:
                print(f"❌ Errors: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ OpenAI CLI error: {e}")
        return False

def main():
    print("🧪 Basic Authentication Methods Test")
    print("=" * 40)

    results = {}
    results["gemini_oauth"] = test_gemini_oauth()
    results["claude_cli"] = test_claude_cli()
    results["openai_cli"] = test_openai_cli()

    # Simple summary
    print("\n📊 RESULTS")
    print("=" * 40)

    working_count = sum(results.values())

    for method, status in results.items():
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {method}")

    print(f"\n🎯 {working_count}/3 methods working")

if __name__ == "__main__":
    main()