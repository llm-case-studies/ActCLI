# OAuth Authentication Playground

Simple tests for subscription-based authentication methods. Conservative approach - verify what actually works.

## Files

- `gemini_oauth_min.py` - Google OAuth for Gemini API
- `claude_cli_min.py` - Claude CLI authentication test
- `codex_cli_min.py` - OpenAI CLI authentication test
- `test_auth_methods.py` - Run all tests

## Setup & Testing

### 1. Gemini OAuth Test

**Prerequisites:**
- Google account with Gemini access
- Google Cloud project with Generative AI API enabled

**Setup:**
1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Create OAuth 2.0 Client ID (Desktop application)
3. Download JSON and save as `client_secret.json` in this directory
4. Install dependencies: `pip install google-auth-oauthlib google-generativeai`

**Test:**
```bash
python gemini_oauth_min.py
```

### 2. Claude CLI Test

**Setup:**
1. Install Claude CLI: `npm install -g @anthropic-ai/claude-cli`
2. Login: `claude auth login`

**Test:**
```bash
python claude_cli_min.py
```

### 3. OpenAI CLI Test

**Setup:**
1. Install OpenAI CLI: `pip install openai-cli`
2. Login: `openai auth login`

**Test:**
```bash
python codex_cli_min.py
```

### 4. Run All Tests

```bash
python test_auth_methods.py
```

## Expected Results

Each test should either:
- Print "🎉 Hooray!!! [Method] working!" if successful
- Show specific error messages if setup needed

Goal: Get at least one method working to prove the subscription-based approach.