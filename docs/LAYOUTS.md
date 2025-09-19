# ActCLI Layout Options

ActCLI now supports multiple sophisticated interface layouts powered by `prompt_toolkit`.

## Available Layouts

### 1. **VSCode Style** (Default)
```bash
# Use VSCode-style interface (default)
actcli
# or explicitly
ACTCLI_LAYOUT=vscode actcli
```

**Features:**
- **Left Sidebar (25%)**: Expandable sections for models, themes, MCP servers, locations
- **ASCII Art Logo**: "ActCLI - Actuarial CLI"
- **Expandable Sections**: Click to collapse/expand ▼▶
- **Right Chat Area (75%)**: Conversation and input
- **Theme Switching**: Dark, Light, Nord themes (Ctrl+T)
- **Model Management**: See available vs active models
- **MCP Status**: Server availability and status
- **Location Management**: Read-only vs read-write paths

### 2. **Claude CLI Style**
```bash
ACTCLI_LAYOUT=claude actcli
```
Clean, minimal interface inspired by Claude CLI

### 3. **Basic Terminal**
```bash
ACTCLI_LAYOUT=basic actcli
```
Simple terminal interface (fallback)

## VSCode Layout Features

### Left Sidebar Sections

#### 🎨 ASCII Art Header
```
╔═══════════════════╗
║   ActCLI         ║
║ Actuarial CLI    ║
║                  ║
║ v0.0.1  OFFLINE  ║
╚═══════════════════╝
```

#### 🤖 Models Available
- Shows all installed models
- ● = Active in roundtable
- ○ = Available but not active

#### 🎯 Roundtable
- Current participating models
- Numbered list
- Real-time status

#### 🎨 Themes
- Dark, Light, Nord, Solarized
- ● = Current theme
- Switch with `/theme` or Ctrl+T

#### 🔌 MCP Servers
- git-mcp, docs-mcp, fs-mcp
- ● = Enabled, ○ = Disabled
- Real-time connection status

#### 📁 Locations
- 📖 Read-only paths
- 📝 Read-write paths
- Security policy display

### Keyboard Shortcuts

- **Enter**: Send message
- **F1**: Help
- **Ctrl+T**: Cycle themes
- **Ctrl+C**: Exit

### Slash Commands

- `/help` - Show help
- `/models` - Focus on models section
- `/theme` - Change theme
- `/quit` - Exit

## Technical Implementation

### Requirements
```bash
pip install '.[tui]'  # Installs prompt_toolkit
```

### Environment Variables
```bash
export ACTCLI_LAYOUT=vscode    # Default: VSCode-style
export ACTCLI_LAYOUT=claude    # Claude CLI-style
export ACTCLI_LAYOUT=basic     # Basic terminal
```

### Architecture
- `src/actcli/ui/vscode_layout.py` - VSCode-style interface
- `src/actcli/ui/claude_layout.py` - Claude CLI-style interface
- Expandable sections using `ConditionalContainer`
- Dynamic styling with theme switching
- Real-time content updates

## Customization

The VSCode layout is fully customizable:
- **Colors**: Theme-based styling
- **Sections**: Expandable/collapsible
- **Content**: Dynamic updates
- **Layout**: Configurable widths

Perfect for professional actuarial workflows with all the visual polish of modern IDEs!