# ActCLI UI Improvements

## Overview

ActCLI's interface has been enhanced to provide a Claude CLI-inspired experience with better visual hierarchy, persistent status information, and improved command completion.

## Key Improvements

### 1. Enhanced Layout System (`src/actcli/ui/layout.py`)

**Features:**
- **Persistent Status Header**: Always shows current mode, models, and audit status
- **Clean Input Area**: Proper spacing and visual separation like Claude CLI
- **Professional Response Grid**: Better organization of multi-model responses
- **Conversation Separators**: Clear visual breaks between interactions

**Usage:**
```python
from actcli.ui.layout import print_persistent_header, print_input_prompt_area

# Show persistent status
print_persistent_header(mode="OFFLINE", models=["llama3", "claude"], audit=True)

# Create clean input area
print_input_prompt_area()
```

### 2. Enhanced TUI with Better Completions (`src/actcli/repl_tui.py`)

**Improvements:**
- **Smart Command Completion**: Descriptions shown alongside commands
- **Claude CLI-inspired Styling**: Professional color scheme and layout
- **Enhanced Key Bindings**: Tab completion, multi-line support
- **Status-aware Toolbar**: Dynamic status information in bottom bar

**Features:**
- Tab completion with descriptions
- Multi-column completion display
- Shift+Enter for multi-line input
- Mouse support for modern terminals

### 3. Better Multi-Model Response Display

**Before:** Mixed colored rectangles that were confusing
**After:** Clean, professional grid layout with:
- Clear model identification
- Response time information
- Proper text wrapping and truncation
- Visual hierarchy that's easy to scan

## Usage Examples

### Standard REPL (Enhanced)
```bash
actcli chat --repl
```
- Shows persistent header with status
- Clean input area with proper spacing
- Enhanced command suggestions

### TUI Mode (Claude CLI-style)
```bash
actcli chat --repl --tui
# or
export ACTCLI_USE_TUI=1
actcli chat --repl
```
- Full prompt_toolkit interface
- Tab completion with descriptions
- Status-aware bottom toolbar

### Legacy Mode (if needed)
```bash
actcli chat --repl --no-tui
```

## Visual Hierarchy

### Header Section
```
┌─ ActCLI • chat(seminar) • MODE: OFFLINE • participants: llama3, claude • audit: ON ─┐
│                                                                                      │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

### Input Section
```
─────────────────────────────────────────────────────────────────────────────────────────

Type your prompt or /help for commands

actcli> _
```

### Response Section
```
┌─ Model Responses ──────────────────────────────────────────────────────────────────────┐
│ Model        Response                                                          Time    │
│ llama3       Considering reserving strategies, I'd recommend...                850ms   │
│ claude       Here are three approaches to consider...                          420ms   │
│ gpt          Based on actuarial best practices...                              650ms   │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

## Configuration

### Environment Variables
- `ACTCLI_USE_TUI=1`: Enable TUI mode by default
- `ACTCLI_MODE=hybrid`: Set hybrid mode for cloud+local models

### Project Config (`actcli.toml`)
```toml
[defaults]
mode = "offline"
banner = true
models = "llama3,claude,gpt"
```

## Troubleshooting

### TUI Not Working
```bash
pip install '.[tui]'  # Install prompt_toolkit
```

### Layout Issues
- Make sure terminal supports ANSI colors
- Check terminal width (minimum 80 characters recommended)
- Use `--no-color` flag if colors cause issues

## Future Enhancements

1. **Live Status Updates**: Real-time model status in header
2. **Expandable Responses**: Click/key to expand truncated responses
3. **Command History**: Better history search and management
4. **Syntax Highlighting**: For prompts and responses
5. **Split Pane View**: Side-by-side model comparison

## Technical Details

### Dependencies
- `rich`: Enhanced terminal output and styling
- `prompt_toolkit`: Advanced TUI capabilities (optional)
- `readchar`: Key input handling for selection UI

### Architecture
- **Separation of Concerns**: Layout logic separate from business logic
- **Backwards Compatible**: Old interface still available
- **Progressive Enhancement**: Features gracefully degrade if dependencies missing