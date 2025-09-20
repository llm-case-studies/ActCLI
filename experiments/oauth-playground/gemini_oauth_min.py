#!/usr/bin/env python3
"""
Minimal Google OAuth flow for Gemini API access.
Based on GPT-5 Pro research for subscription-based authentication.
"""

from google_auth_oauthlib.flow import InstalledAppFlow
import google.generativeai as genai

# Scopes for Gemini API access
SCOPES = ["https://www.googleapis.com/auth/generative-language"]

def main():
    print("🔐 Starting Google OAuth flow for Gemini...")

    # Note: This requires client_secret.json from Google Cloud Console
    # Download from: https://console.cloud.google.com/apis/credentials
    try:
        flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", scopes=SCOPES)
        creds = flow.run_local_server(port=0)
        print("✅ OAuth authentication successful!")

        # Configure Gemini with OAuth credentials
        genai.configure(credentials=creds)
        model = genai.GenerativeModel("gemini-2.0-flash-exp")

        print("🤖 Testing Gemini API...")
        resp = model.generate_content("Say hi in one sentence.")
        print(f"Gemini response: {resp.text}")

        print("🎉 Hooray!!! Gemini OAuth working!")

    except FileNotFoundError:
        print("❌ Error: client_secret.json not found")
        print("📋 To fix:")
        print("1. Go to https://console.cloud.google.com/apis/credentials")
        print("2. Create OAuth 2.0 Client ID (Desktop application)")
        print("3. Download JSON and save as 'client_secret.json' in this directory")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()