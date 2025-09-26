from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .adapters.base import ModelAdapter
from .adapters.ollama import OllamaAdapter
from .adapters.openai import OpenAIAdapter
from .adapters.anthropic import AnthropicAdapter
from .adapters.codex_cli import CodexCLIAdapter
from .adapters.gemini_cli import GeminiCLIAdapter
from .adapters.claude_cli import ClaudeCLIAdapter
from .adapters.gemini import GeminiAdapter
from .adapters.echo import EchoAdapter
from ..models.participant import ParticipantSpec


@dataclass
class BoundParams:
    seed: Optional[int] = None
    system: Optional[str] = None
    timeout_s: Optional[int] = None
    temperature: Optional[float] = None  # reserved; some adapters may not support
    reasoning: Optional[str] = None  # minimal|low|medium|high (provider-specific)


class BoundAdapter:
    """Wrap a ModelAdapter and bind default params (seed/system/timeout).

    Bound values override values passed at generate()-time when not None.
    """

    def __init__(
        self,
        base: ModelAdapter,
        *,
        alias: Optional[str] = None,
        params: Optional[BoundParams] = None,
    ) -> None:
        self._base = base
        self._bound = params or BoundParams()
        # Surface required attributes
        self.name = alias or getattr(base, "name", "unknown")
        self.is_local = getattr(base, "is_local", False)
        self.model_version = getattr(base, "model_version", "")

    def generate(
        self,
        prompt: str,
        *,
        system: str = "",
        seed: Optional[int] = None,
        temperature: Optional[float] = None,
        timeout_s: int = 30,
        round_index: int = 1,
        context_snippets: Optional[str] = None,
    ) -> str:
        sys_val = self._bound.system if self._bound.system is not None else system
        seed_val = self._bound.seed if self._bound.seed is not None else seed
        temp_val = (
            self._bound.temperature
            if self._bound.temperature is not None
            else temperature
        )
        # Scheduler enforces outer timeout; we still pass the bound value for adapter internals
        tmo = self._bound.timeout_s if self._bound.timeout_s is not None else timeout_s
        # Attempt full signature including optional parameters some adapters may not support
        try:
            return self._base.generate(
                prompt,
                system=sys_val or "",
                seed=seed_val,
                temperature=temp_val,
                timeout_s=int(tmo),
                round_index=round_index,
                context_snippets=context_snippets,
                reasoning=self._bound.reasoning,  # type: ignore[arg-type]
            )
        except TypeError:
            # Fallback without reasoning
            try:
                return self._base.generate(
                    prompt,
                    system=sys_val or "",
                    seed=seed_val,
                    temperature=temp_val,
                    timeout_s=int(tmo),
                    round_index=round_index,
                    context_snippets=context_snippets,
                )
            except TypeError:
                # Fallback without temperature (legacy adapters)
                return self._base.generate(
                    prompt,
                    system=sys_val or "",
                    seed=seed_val,
                    timeout_s=int(tmo),
                    round_index=round_index,
                    context_snippets=context_snippets,
                )


class AdapterFactory:
    @staticmethod
    def from_spec(spec: ParticipantSpec, *, allow_cloud: bool) -> ModelAdapter:
        provider = spec.provider.lower()
        alias = spec.alias
        params = BoundParams(
            seed=int(spec.params.get("seed"))
            if isinstance(spec.params.get("seed"), int)
            else None,
            system=str(spec.params.get("system"))
            if spec.params.get("system") is not None
            else None,
            timeout_s=int(spec.params.get("timeout_s"))
            if isinstance(spec.params.get("timeout_s"), int)
            else None,
            temperature=float(spec.params.get("temperature"))
            if isinstance(spec.params.get("temperature"), float)
            else None,
            reasoning=str(spec.params.get("reasoning")).lower()
            if isinstance(spec.params.get("reasoning"), str)
            else None,
        )
        base: ModelAdapter
        try:
            if provider == "ollama":
                base = OllamaAdapter(model=spec.model_id or "", host=spec.host)
            elif provider == "openai":
                if not allow_cloud:
                    return BoundAdapter(
                        EchoAdapter(name=f"{alias or spec.model_id}(cloud-blocked)"),
                        alias=alias or "openai",
                        params=params,
                    )
                base = OpenAIAdapter(model=spec.model_id or "gpt-4o-mini")
            elif provider == "anthropic":
                if not allow_cloud:
                    return BoundAdapter(
                        EchoAdapter(name=f"{alias or spec.model_id}(cloud-blocked)"),
                        alias=alias or "anthropic",
                        params=params,
                    )
                base = AnthropicAdapter(
                    model=spec.model_id or "claude-3-haiku-20240307"
                )
            elif provider == "claude_cli":
                # Claude CLI uses subscription auth - always allowed since it's user's own subscription
                base = ClaudeCLIAdapter(
                    model=spec.model_id or "claude-3-5-sonnet-20241022"
                )
            elif provider == "codex_cli":
                # OpenAI Codex CLI (subscription-backed); model id is a label only
                base = CodexCLIAdapter(model=spec.model_id or "default")
            elif provider == "gemini_cli":
                # Gemini CLI shim (subscription-backed or API key); always allowed since it's user's own subscription
                base = GeminiCLIAdapter(model=spec.model_id or "gemini-1.5-flash")
            elif provider == "google":
                if not allow_cloud:
                    return BoundAdapter(
                        EchoAdapter(name=f"{alias or spec.model_id}(cloud-blocked)"),
                        alias=alias or "google",
                        params=params,
                    )
                base = GeminiAdapter(model=spec.model_id or "gemini-1.5-flash-latest")
            elif provider == "echo":
                base = EchoAdapter(name=alias or (spec.model_id or "echo"))
            else:
                base = EchoAdapter(name=alias or provider)
        except Exception:
            # Fallback to echo when adapter init fails (e.g., missing API key)
            base = EchoAdapter(name=alias or (spec.model_id or provider))
        return BoundAdapter(
            base, alias=alias or getattr(base, "name", None), params=params
        )
