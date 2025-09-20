# Claude CLI Integration for ActCLI

## 🎯 What We Accomplished

This integration adds **subscription-based authentication** for Claude models in ActCLI, eliminating the need for API key management while providing access to the latest Claude models.

## ✨ Key Features

### 1. **Claude CLI Adapter**
- New `claude_cli` provider for ActCLI seminars
- Uses Claude CLI's subscription authentication (no API keys needed)
- Supports model selection via `--model` parameter
- Full integration with ActCLI's seminar system

### 2. **Model Listing Support**
- `actcli models list --provider claude_cli` shows available models
- Lists both aliases (`sonnet`, `opus`) and full model names
- Descriptions for each model to help users choose

### 3. **Flexible Authentication Options**
ActCLI now supports **two Claude authentication paths**:

#### Option A: Claude CLI (Subscription-based) ✨ NEW
- **Provider**: `claude_cli`
- **Auth**: Uses existing Claude subscription
- **Setup**: Install Claude CLI + browser login
- **Models**: sonnet, opus, claude-3-5-sonnet-20241022, etc.

#### Option B: Anthropic API (API Key-based)
- **Provider**: `anthropic`
- **Auth**: ANTHROPIC_API_KEY environment variable
- **Setup**: API signup + key management
- **Models**: All Anthropic API models

## 🚀 Usage Examples

### List Available Claude CLI Models
```bash
actcli models list --provider claude_cli
```

### Single Model Chat
```bash
actcli chat --multi "claude_cli:sonnet" --prompt "Explain IBNR reserves"
```

### Multi-Model Seminar (Mix Both Auth Types)
```bash
actcli chat --multi "claude_cli:sonnet,anthropic:claude-3-opus-20240229" --prompt "Compare chain ladder methods"
```

### Use Latest Models with Aliases
```bash
actcli chat --multi "claude_cli:opus" --prompt "Actuarial question"
```

## 📁 Files Modified/Added

### New Files
- `src/actcli/seminar/adapters/claude_cli.py` - Claude CLI adapter implementation
- `experiments/oauth-playground/` - Testing playground with working examples
- `CLAUDE_CLI_INTEGRATION.md` - This documentation

### Modified Files
- `src/actcli/seminar/factory.py` - Added claude_cli provider support
- `src/actcli/models/registry.py` - Added Claude CLI model listing
- `src/actcli/commands/models.py` - Integrated claude_cli in models command

## 🛠️ Technical Implementation

### Claude CLI Adapter Features
```python
class ClaudeCLIAdapter:
    - Checks Claude CLI availability at startup
    - Validates authentication before use
    - Supports model selection via --model parameter
    - Handles JSON output parsing
    - Provides detailed error messages
```

### Model Listing
- Returns known Claude models and aliases
- Caches results for performance
- Shows subscription-based cost tier
- Includes model descriptions

### Error Handling
- Clear messages when Claude CLI not installed
- Authentication validation with helpful setup instructions
- Graceful fallbacks for missing dependencies

## 🎯 Benefits for Users

### For Quick Start Users
- **Zero API key setup** - just login to Claude CLI once
- **Same billing** as Claude web interface
- **Latest models** via simple aliases
- **Familiar authentication** (same as Claude CLI)

### For Power Users
- **Mix authentication types** in same seminar
- **Model selection flexibility** (aliases or full names)
- **API and subscription** options side-by-side
- **Future-proof** - automatically gets new Claude CLI models

### For Actuarial Teams
- **Easy onboarding** - team members use existing Claude subscriptions
- **No shared API keys** to manage
- **Individual billing** through subscriptions
- **Professional models** (Sonnet, Opus) for complex actuarial work

## 🔧 Setup Instructions

### Prerequisites
1. Claude subscription (Pro/Team/Enterprise)
2. Node.js (for Claude CLI installation)

### Installation
```bash
# Install Claude CLI
npm install -g @anthropic-ai/claude-code

# Login (opens browser)
claude

# Test with ActCLI
actcli models list --provider claude_cli
actcli chat --multi "claude_cli:sonnet" --prompt "Hello from ActCLI!"
```

## 🧪 Testing Results

All tests passing:
- ✅ Claude CLI adapter initialization
- ✅ Authentication validation
- ✅ Model selection (aliases and full names)
- ✅ Multi-round seminar conversations
- ✅ Model listing via `actcli models`
- ✅ Integration with existing ActCLI features
- ✅ Error handling and user guidance

## 🚀 Future Possibilities

This pattern enables similar integrations:
- **OpenAI Codex CLI** for GPT models
- **Gemini CLI** for Google models
- **Any vendor CLI** with JSON output support

## 📋 Migration Path

Existing users: **No changes required**
- All existing `anthropic` configurations continue working
- New `claude_cli` option available alongside existing auth

New users: **Choose your path**
- Quick start → `claude_cli` (subscription)
- Full control → `anthropic` (API key)
- Both → Mix in same seminar!