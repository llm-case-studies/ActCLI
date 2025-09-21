# OAuth Authentication Playground

Simple tests for subscription-based authentication methods. Conservative approach - verify what actually works.

## Files

- `gemini_oauth_min.py` - Google OAuth for Gemini API (minimal)
- `gemini_oauth_plus.py` - Gemini API key or OAuth (robust), friendly hints
- `claude_cli_min.py` - Claude CLI authentication test
- `codex_cli_min.py` - OpenAI CLI authentication test
- `test_auth_methods.py` - Run all tests

## Setup & Testing

### 1. Gemini Test (API key or OAuth)

Option A — API key (quickest):

```bash
pip install google-generativeai
export GOOGLE_API_KEY=...   # or set in your shell profile
python gemini_oauth_plus.py --model gemini-2.0-flash
```

Option B — OAuth (desktop flow):

```bash
pip install google-auth-oauthlib google-generativeai
# In Google Cloud Console: enable Generative Language API; create OAuth 2.0 client (Desktop) and download client_secret.json
python gemini_oauth_plus.py --oauth --model gemini-2.0-flash
```

If you hit 403/permission errors, ensure the API is enabled and consider setting `GOOGLE_CLOUD_PROJECT`.

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
