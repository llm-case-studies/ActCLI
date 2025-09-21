#!/usr/bin/env python3
"""
Robust Gemini auth playground: supports API key and OAuth (desktop).

Usage:
  - API key path:
      export GOOGLE_API_KEY=...  # Makersuite or Google AI Studio key
      python gemini_oauth_plus.py --model gemini-1.5-flash

  - OAuth path (regular Google account):
      python gemini_oauth_plus.py --oauth --model gemini-1.5-flash

Notes:
  - For some Workspace setups you may need GOOGLE_CLOUD_PROJECT (and optionally location).
  - If browser auth opens but fails at redirect, ensure localhost callback is reachable.
"""

from __future__ import annotations

import argparse
import os
import sys

try:
    from google_auth_oauthlib.flow import InstalledAppFlow
    import google.generativeai as genai
except Exception as e:  # pragma: no cover
    print("❌ Missing deps. Install: pip install google-auth-oauthlib google-generativeai")
    raise


SCOPES = ["https://www.googleapis.com/auth/generative-language"]


def configure_gemini_with_api_key() -> None:
    key = os.getenv("GOOGLE_API_KEY")
    if not key:
        print("❌ GOOGLE_API_KEY not set. Export it or use --oauth.")
        sys.exit(2)
    genai.configure(api_key=key)


def configure_gemini_with_oauth() -> None:
    client_config = {
        "installed": {
            "client_id": "293899367432-j6f7s0sp34av5h522q53l4b7m5u27hrc.apps.googleusercontent.com",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        }
    }
    flow = InstalledAppFlow.from_client_config(client_config, scopes=SCOPES)
    creds = flow.run_console()
    genai.configure(credentials=creds)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="gemini-1.5-flash", help="Model ID e.g. gemini-1.5-flash or gemini-1.5-pro")
    ap.add_argument("--prompt", default="Say hi in one sentence.")
    ap.add_argument("--oauth", action="store_true", help="Use OAuth (no client_secret.json needed)")
    args = ap.parse_args()

    print("🔐 Gemini auth playground (API key or OAuth)")
    print(f"Model: {args.model}")

    try:
        if args.oauth:
            configure_gemini_with_oauth()
            print("✅ OAuth configured")
        else:
            configure_gemini_with_api_key()
            print("✅ API key configured")

        model = genai.GenerativeModel(args.model)
        print("🤖 Generating…")
        resp = model.generate_content(args.prompt)
        text = getattr(resp, "text", None) or getattr(resp, "candidates", None) or str(resp)
        print("\n=== Gemini Response ===\n")
        print(text if isinstance(text, str) else resp)
        print("\n🎉 Success")
    except Exception as e:
        print(f"❌ Error: {e}")
        if "permission" in str(e).lower() or "403" in str(e):
            print("Hint: Ensure Generative Language API is enabled for your project/account.")
            if not os.getenv("GOOGLE_CLOUD_PROJECT"):
                print("Hint: Some setups require GOOGLE_CLOUD_PROJECT to be set.")
        sys.exit(1)


if __name__ == "__main__":
    main()