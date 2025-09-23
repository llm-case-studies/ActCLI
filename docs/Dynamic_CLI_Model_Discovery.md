# Dynamic CLI Model Discovery

This document outlines methods for dynamically discovering available models from CLI providers (Claude CLI, Codex CLI, Gemini CLI) rather than using hardcoded model lists.

## Overview

Instead of maintaining static model lists that can become outdated, CLI adapters can dynamically discover which models are actually available to the user. This approach:

- ✅ **Respects subscription levels** - Only shows models the user has access to
- ✅ **Auto-updates** - Works with new CLI versions and model releases
- ✅ **Reduces maintenance** - No need to update hardcoded model lists
- ✅ **Improves UX** - Users only see models they can actually use

## CLI Provider Capabilities

### Claude CLI ✅ Full Interactive Discovery

**Method**: Interactive `/model` slash command
**Status**: Fully supported with rich UI

```bash
# In Claude CLI interactive mode:
> /model
╭─────────────────────────────────────────────────────────────────────────────────────────────╮
│ Select Model                                                                                │
│ Switch between Claude models. Applies to this session and future Claude Code sessions.      │
│                                                                                             │
│   ❯ 1. Sonnet   Sonnet 4 for daily use ✔                                                    │
│                                                                                             │
│  Want Opus 4.1? Run /upgrade to upgrade to Max                                             │
╰─────────────────────────────────────────────────────────────────────────────────────────────╯
```

**Implementation**:
```python
async def discover_claude_models(self) -> List[ModelInfo]:
    """Use Claude CLI's /model command to discover available models"""
    proc = await asyncio.create_subprocess_exec(
        "claude",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    # Send /model command and escape to exit
    stdout, stderr = await proc.communicate(input=b"/model\n\x1b\n")
    return self._parse_claude_model_menu(stdout.decode())

def _parse_claude_model_menu(self, output: str) -> List[ModelInfo]:
    """Parse Claude's model selection UI"""
    models = []
    # Look for patterns like "1. Sonnet   Sonnet 4 for daily use ✔"
    import re
    pattern = r'(\d+)\.\s+([A-Za-z]+)\s+(.*?)(?=\n|$)'

    for match in re.finditer(pattern, output):
        number, name, description = match.groups()
        # Check if model is available (has ✔ or similar)
        available = '✔' in description or 'available' in description.lower()

        models.append(ModelInfo(
            id=name.lower(),
            display_name=name,
            description=description.strip(),
            available=available
        ))

    return models
```

### Codex CLI ✅ Full Interactive Discovery

**Method**: Interactive `/model` slash command
**Status**: Fully supported with reasoning levels

```bash
# In Codex CLI interactive mode:
> /model
▌ Select model and reasoning level
▌ Switch between OpenAI models for this and future Codex CLI session
▌
▌  1. gpt-5 minimal  — fastest responses with limited reasoning
▌  2. gpt-5 low      — balances speed with some reasoning
▌> 3. gpt-5 medium   — (current) default setting; balanced reasoning
▌  4. gpt-5 high     — maximizes reasoning depth for complex problems
```

**Implementation**:
```python
async def discover_codex_models(self) -> List[ModelInfo]:
    """Use Codex CLI's /model command to discover available models"""
    proc = await asyncio.create_subprocess_exec(
        "codex",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    # Send /model command and escape to exit
    stdout, stderr = await proc.communicate(input=b"/model\n\x1b\n")
    return self._parse_codex_model_menu(stdout.decode())

def _parse_codex_model_menu(self, output: str) -> List[ModelInfo]:
    """Parse Codex's model selection UI"""
    models = []
    # Look for patterns like "1. gpt-5 minimal  — fastest responses..."
    import re
    pattern = r'(\d+)\.\s+([\w-]+\s+[\w-]+)\s+—\s+(.*?)(?=\n|$)'

    for match in re.finditer(pattern, output):
        number, model_name, description = match.groups()
        is_current = '(current)' in description

        models.append(ModelInfo(
            id=model_name.replace(' ', '-'),  # "gpt-5 minimal" -> "gpt-5-minimal"
            display_name=model_name,
            description=description.replace('(current)', '').strip(),
            current=is_current,
            available=True
        ))

    return models
```

### Gemini CLI ❌ No Built-in Discovery

**Method**: Probe testing with known model names
**Status**: Limited - requires fallback approach

**Findings**:
- No `/model` equivalent command
- `--model` flag exists but no help/list option
- Invalid models return generic "NOT_FOUND" errors
- CLI lacks self-awareness of available models

**Implementation**:
```python
async def discover_gemini_models(self) -> List[ModelInfo]:
    """Discover Gemini models through probe testing"""
    # Known model candidates based on Google AI documentation
    candidate_models = [
        "gemini-2.5-pro",
        "gemini-1.5-flash-latest",
        "gemini-1.5-pro-latest",
        "gemini-1.0-pro",
        "default"
    ]

    available = []
    for model in candidate_models:
        try:
            is_available = await self._test_model_availability(model)
            if is_available:
                available.append(ModelInfo(
                    id=model,
                    display_name=model,
                    description=f"Gemini model: {model}",
                    available=True
                ))
        except Exception as e:
            # Model not available or other error
            continue

    return available

async def _test_model_availability(self, model: str) -> bool:
    """Test if a Gemini model is available by making a quick request"""
    try:
        proc = await asyncio.create_subprocess_exec(
            "gemini", "-p", "ping", "--model", model,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            timeout=10
        )

        stdout, stderr = await proc.communicate()

        # Check for success indicators
        return (
            proc.returncode == 0 and
            "pong" in stdout.decode().lower() and
            "error" not in stderr.decode().lower()
        )
    except (asyncio.TimeoutError, Exception):
        return False
```

## Unified CLI Adapter Interface

```python
from dataclasses import dataclass
from typing import List, Optional
import asyncio

@dataclass
class ModelInfo:
    id: str                    # Model identifier for --model flag
    display_name: str         # Human-readable name
    description: str          # Model description/capabilities
    available: bool = True    # Whether user has access
    current: bool = False     # Currently selected model
    reasoning_level: Optional[str] = None  # For Codex models

class CLIModelDiscovery:
    """Base class for CLI model discovery"""

    def __init__(self, cli_binary: str, cli_type: str):
        self.cli_binary = cli_binary
        self.cli_type = cli_type

    async def discover_models(self) -> List[ModelInfo]:
        """Discover available models for this CLI"""
        if self.cli_type == "claude":
            return await self._discover_via_interactive("/model")
        elif self.cli_type == "codex":
            return await self._discover_via_interactive("/model")
        elif self.cli_type == "gemini":
            return await self._discover_via_probing()
        else:
            raise ValueError(f"Unsupported CLI type: {self.cli_type}")

    async def _discover_via_interactive(self, command: str) -> List[ModelInfo]:
        """Use interactive command to discover models"""
        proc = await asyncio.create_subprocess_exec(
            self.cli_binary,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        # Send command and escape to exit
        input_data = f"{command}\n\x1b\n".encode()
        stdout, stderr = await proc.communicate(input=input_data)

        return self._parse_model_output(stdout.decode())

    async def _discover_via_probing(self) -> List[ModelInfo]:
        """Discover models by testing known candidates"""
        # Implementation depends on CLI type
        pass

    def _parse_model_output(self, output: str) -> List[ModelInfo]:
        """Parse CLI output to extract model information"""
        # Implementation depends on CLI type and output format
        pass
```

## Integration with ActCLI

### Adapter Factory Updates

```python
class AdapterFactory:
    async def create_adapter(self, provider: str) -> BaseAdapter:
        adapter = super().create_adapter(provider)

        # Add dynamic model discovery
        if hasattr(adapter, 'discover_models'):
            try:
                models = await adapter.discover_models()
                adapter.set_available_models(models)
            except Exception as e:
                # Fall back to static model list
                logger.warning(f"Model discovery failed for {provider}: {e}")

        return adapter
```

### CLI Commands Integration

```python
# actcli models list --provider claude_cli --refresh
async def list_cli_models(provider: str, refresh: bool = False):
    """List models available through CLI provider"""
    adapter = factory.create_adapter(provider)

    if refresh or not adapter.has_cached_models():
        models = await adapter.discover_models()
        adapter.cache_models(models)
    else:
        models = adapter.get_cached_models()

    for model in models:
        status = "✓" if model.available else "✗"
        current = " (current)" if model.current else ""
        print(f"{status} {model.display_name}{current}")
        print(f"    {model.description}")
```

### Caching Strategy

```python
class ModelCache:
    def __init__(self, ttl_seconds: int = 3600):  # 1 hour cache
        self._cache = {}
        self._ttl = ttl_seconds

    async def get_models(self, provider: str, force_refresh: bool = False) -> List[ModelInfo]:
        cache_key = provider

        if force_refresh or self._is_expired(cache_key):
            discovery = CLIModelDiscovery.for_provider(provider)
            models = await discovery.discover_models()
            self._cache[cache_key] = {
                'models': models,
                'timestamp': time.time()
            }

        return self._cache[cache_key]['models']

    def _is_expired(self, key: str) -> bool:
        if key not in self._cache:
            return True
        return time.time() - self._cache[key]['timestamp'] > self._ttl
```

## Error Handling

```python
class ModelDiscoveryError(Exception):
    """Raised when model discovery fails"""
    pass

async def safe_discover_models(cli_type: str) -> List[ModelInfo]:
    """Discover models with fallback to static list"""
    try:
        discovery = CLIModelDiscovery(cli_type)
        return await discovery.discover_models()
    except Exception as e:
        logger.warning(f"Dynamic discovery failed for {cli_type}: {e}")
        return get_static_model_list(cli_type)
```

## Usage Examples

```python
# Discover all available models
claude_models = await discover_claude_models()
codex_models = await discover_codex_models()
gemini_models = await discover_gemini_models()

# Use in ActCLI chat
actcli chat --multi "sonnet,gpt-5-high,gemini-2.5-pro" --rounds 2

# List available models
actcli models list --provider claude_cli
actcli models list --provider codex_cli
actcli models list --provider gemini_cli --refresh
```

## Benefits

1. **User Experience**: Only show models users can actually access
2. **Maintenance**: No need to update hardcoded model lists
3. **Accuracy**: Always reflects current subscription/plan status
4. **Adaptability**: Works with new CLI versions and model releases
5. **Error Reduction**: Eliminates "model not found" errors from outdated lists

## Implementation Priority

1. **Phase 1**: Implement Claude CLI discovery (highest value, most reliable)
2. **Phase 2**: Implement Codex CLI discovery (good reliability)
3. **Phase 3**: Implement Gemini CLI probing (fallback approach)
4. **Phase 4**: Add caching and error handling
5. **Phase 5**: Integrate with ActCLI commands and UI