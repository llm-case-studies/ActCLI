#!/usr/bin/env python3
"""
Minimal Google OAuth flow for Gemini API access.
"""

import sys
try:
    from importlib.metadata import version, PackageNotFoundError
    try:
        lib_version = version('google-auth-oauthlib')
        print(f"✅ google-auth-oauthlib version: {lib_version}")
    except PackageNotFoundError:
        print("❌ google-auth-oauthlib is not installed.")
        sys.exit(1)

    from google_auth_oauthlib.flow import InstalledAppFlow
    import google.generativeai as genai

except ImportError as e:
    print(f"❌ Import error: {e}")
    print("📋 Please make sure you have run 'pip install google-auth-oauthlib google-generativeai'")
    sys.exit(1)


# Scopes for Gemini API access
SCOPES = ["https://www.googleapis.com/auth/generative-language"]

def main():
    print("\n🔐 Starting Google OAuth flow for Gemini...")

    try:
        print("🔧 Creating InstalledAppFlow from client_secret.json...")
        flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", scopes=SCOPES)
        print("✅ InstalledAppFlow created successfully.")

        print("🌐 Starting local server for authentication...")
        creds = flow.run_local_server(port=0)
        print("✅ OAuth authentication successful!")

        print("🔧 Configuring Gemini with OAuth credentials...")
        genai.configure(credentials=creds)
        model = genai.GenerativeModel("gemini-1.5-flash")
        print("✅ Gemini configured successfully.")

        print("🤖 Testing Gemini API...")
        resp = model.generate_content("Say hi in one sentence.")
        print(f"Gemini response: {resp.text}")

        print("\n🎉 Hooray!!! Gemini OAuth working!")

    except FileNotFoundError:
        print("\n❌ Error: client_secret.json not found")
        print("📋 To fix:")
        print("1. Go to https://console.cloud.google.com/apis/credentials")
        print("2. Create OAuth 2.0 Client ID (Desktop application)")
        print("3. Download JSON and save as 'client_secret.json' in this directory")
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")

if __name__ == "__main__":
    main()
