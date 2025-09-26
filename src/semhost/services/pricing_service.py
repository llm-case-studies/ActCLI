from __future__ import annotations

from typing import List

from ..schemas.pricing import PricingInfo, PricingRow


def pricing_catalog() -> List[PricingRow]:
    rows: List[PricingRow] = []
    # OpenAI examples (illustrative only; update from official pages periodically)
    rows.append(
        PricingRow(
            provider="openai",
            id="gpt-4o-mini",
            pricing=PricingInfo(
                model="per-token",
                unit="1K tokens",
                input=0.15,
                output=0.60,
                currency="USD",
                source_url="https://openai.com/pricing",
            ),
        )
    )
    rows.append(
        PricingRow(
            provider="openai",
            id="gpt-4o",
            pricing=PricingInfo(
                model="per-token",
                unit="1K tokens",
                input=2.50,
                output=5.00,
                currency="USD",
                source_url="https://openai.com/pricing",
            ),
        )
    )
    # Anthropic / Google — placeholders; exact numbers depend on plans
    rows.append(
        PricingRow(
            provider="anthropic",
            id="claude-3-5-sonnet-20241022",
            pricing=PricingInfo(
                model="per-token",
                unit="1M tokens",
                note="See Anthropic pricing",
                source_url="https://www.anthropic.com/pricing",
            ),
        )
    )
    rows.append(
        PricingRow(
            provider="google",
            id="gemini-1.5-flash-latest",
            pricing=PricingInfo(
                model="per-token",
                unit="1M tokens",
                note="See Google pricing",
                source_url="https://ai.google.dev/pricing",
            ),
        )
    )
    # CLI-backed — subscription/freemium
    for prov, label in (
        ("claude_cli", "Claude CLI"),
        ("codex_cli", "Codex CLI"),
        ("gemini_cli", "Gemini CLI"),
    ):
        rows.append(
            PricingRow(
                provider=prov,
                id="default",
                pricing=PricingInfo(
                    model="subscription",
                    note=f"{label} subscription/free tier; see vendor docs",
                ),
            )
        )
    return rows
