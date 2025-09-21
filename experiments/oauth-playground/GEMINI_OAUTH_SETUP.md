# Gemini OAuth Setup - Why No Browser Popup?

## 🔍 **Why the browser didn't open:**

The OAuth flow **requires** a real `client_secret.json` file from Google Cloud Console. Without it, the script exits with:
```
❌ client_secret.json not found. See GCP Console → Credentials → OAuth client (Desktop app).
```

## 📋 **To get browser popup working, you need:**

### Step 1: Google Cloud Setup
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create or select a project
3. Enable **"Generative Language API"**
4. Go to **APIs & Services > Credentials**
5. Click **"Create Credentials" > "OAuth client ID"**
6. Choose **"Desktop application"**
7. Download the JSON file as `client_secret.json`

### Step 2: Place File
```bash
# Put the downloaded file here:
cp ~/Downloads/client_secret_*.json experiments/oauth-playground/client_secret.json
```

### Step 3: Test OAuth Flow
```bash
python experiments/oauth-playground/gemini_oauth_plus.py --oauth --model gemini-2.0-flash
```

**Then you would see:**
1. ✅ OAuth configured
2. 🌐 **Browser opens automatically**
3. Google login page appears
4. You login with your Google account
5. Google asks permission for "Generative Language API"
6. You approve
7. Browser redirects to localhost (script captures the token)
8. 🤖 Gemini generates response

## 🎯 **What the client_secret.json contains:**

```json
{
  "installed": {
    "client_id": "your-client-id.apps.googleusercontent.com",
    "project_id": "your-project-id",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_secret": "your-client-secret",
    "redirect_uris": ["http://localhost", "urn:ietf:wg:oauth:2.0:oob"]
  }
}
```

## 🔄 **OAuth Flow (when it works):**

1. **Script starts** OAuth flow with `InstalledAppFlow.from_client_secrets_file()`
2. **Browser opens** to `https://accounts.google.com/o/oauth2/auth?...`
3. **User logs in** with Google account
4. **Google shows permissions** for Generative Language API
5. **User approves** access
6. **Browser redirects** to `http://localhost:PORT/callback?code=...`
7. **Script captures** the authorization code
8. **Script exchanges** code for access token
9. **Script configures** Gemini with credentials
10. **✅ Ready to use** Gemini API with user's account

## 🚫 **Why it's not "zero-friction" like Claude/Codex CLI:**

- **Claude CLI**: `npm install -g @anthropic-ai/claude-code` → `claude` → login → done
- **Codex CLI**: `npm install -g @openai/codex` → `codex` → login → done
- **Gemini OAuth**: Create GCP project → Enable API → Create OAuth → Download JSON → Place file → Run script → Browser login

The Gemini approach requires **5 manual setup steps** vs **3 for CLI tools**.

## 💡 **Alternative: API Key (Simpler)**

For testing, API key is much simpler:
```bash
# Get key from https://makersuite.google.com/app/apikey
export GOOGLE_API_KEY="your-api-key"
python experiments/oauth-playground/gemini_oauth_plus.py --model gemini-2.0-flash
```

This would work immediately without OAuth setup complexity.