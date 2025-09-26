from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass(frozen=True)
class MoodPreset:
    name: str
    temperature: Optional[float] = None
    system: Optional[str] = None


MOOD_PRESETS: Dict[str, MoodPreset] = {
    "cautious": MoodPreset(
        name="cautious",
        temperature=0.2,
        system="Prefer concise, conservative judgments.",
    ),
    "creative": MoodPreset(
        name="creative",
        temperature=0.8,
        system="Explore alternatives; propose novel ideas.",
    ),
    "friday": MoodPreset(
        name="friday",
        temperature=0.9,
        system="Relaxed tone; quick heuristics; jovial ⚡",
    ),
}


def resolve_mood(name: str) -> Optional[MoodPreset]:
    return MOOD_PRESETS.get(name.lower())


def apply_mood(params: Dict[str, object], mood: MoodPreset) -> Dict[str, object]:
    """Return a new params dict with mood applied (non-destructive)."""
    out = dict(params)
    if mood.temperature is not None:
        out["temperature"] = float(mood.temperature)
    if mood.system:
        # Append or set system prompt gently
        sys0 = str(out.get("system", ""))
        out["system"] = (sys0 + "\n" + mood.system).strip() if sys0 else mood.system
    return out
