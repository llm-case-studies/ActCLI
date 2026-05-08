from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from rich.console import Console
from rich.panel import Panel

from ..seminar.adapters.echo import EchoAdapter
from ..seminar.coordinator import run_round, TurnResult
from ..seminar.synthesizer import summarize
from ..transcript import write_transcript_md, write_audit_json

console = Console()

SYNTHETIC_PROMPT_PRICING_RND = """SYNTHETIC DEMO PROMPT — PRICING R&D ROUNDTABLE

You are participating in a simulated actuarial roundtable. The following scenario
is synthetic and uses no real client data, no proprietary models, and no
production pricing parameters. It was generated for evaluation purposes only.

**Context**: A mid-size P&C carrier ("SyntheticCo") is evaluating its property
catastrophe reinsurance program for the upcoming 1/1 renewal. The carrier writes
$500M GWP across homeowners and small commercial property in the southeastern US.

**Current Program**: 3-layer property cat XoL tower: $50M xs $10M, $75M xs $60M,
$100M xs $135M. Attachment at $10M. Current rate-on-line: 12.5% on the first
layer.

**Change Drivers**: PML has increased ~15% due to inflation and exposure growth.
RMS v21 model output suggests the $10M attachment point now has a ~8% annual
exceedance probability (up from ~5% three years ago). Reinsurer appetite for
Gulf/Wind exposure has tightened.

**Options Under Consideration**:
1. Renew as-is: accept expected +8-12% rate increase on first layer, keep
   structure identical.
2. Raise attachment to $15M, buy additional drop-down cover at $5M xs $5M, and
   request quotes for the adjusted tower.
3. Supplement the XoL program with an aggregate stop-loss: $10M annual aggregate
   deductible, $30M limit, covering cat losses only.

**Questions for the panel**:
1. Compare the cost and capital efficiency of the three options. Which best
   balances expected loss cost against tail risk?
2. What basis risk does each option introduce, and how would you quantify it?
3. Are there regulatory, rating-agency, or accounting considerations that favor
   one structure over the others?
4. If you could request one additional piece of analysis before the renewal
   deadline, what would it be and why?

Note: This is a synthetic exercise. All figures, company names, and model
outputs are fabricated for demonstration."""


def _build_demo_participants() -> List[EchoAdapter]:
    return [
        EchoAdapter(name="Pricing Actuary (local-demo)", version="demo-1.0"),
        EchoAdapter(name="Reinsurance Buyer (local-demo)", version="demo-1.0"),
        EchoAdapter(name="Risk Manager (local-demo)", version="demo-1.0"),
    ]


def _write_prompt_md(path: Path, prompt: str) -> None:
    path.write_text(f"# Synthetic Demo Prompt — pricing-rnd\n\n{prompt}\n", encoding="utf-8")


def _write_workpaper_md(
    path: Path,
    prompt: str,
    results: List[TurnResult],
    synthesis: str,
    disagreement: float,
) -> None:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# Workpaper: Synthetic Pricing R&D Roundtable",
        "",
        "**Scenario**: pricing-rnd",
        f"**Date generated**: {now}",
        "**Status**: SYNTHETIC DEMO — not for production use. All figures and",
        "responses are fabricated for evaluation purposes only.",
        "",
        "## Executive Summary",
        "",
        "This workpaper summarizes a synthetic roundtable discussion among three",
        "demo personas (Pricing Actuary, Reinsurance Buyer, Risk Manager) that",
        "deliberated on a fabricated property catastrophe reinsurance renewal",
        "scenario. The exercise demonstrates ActCLI's multi-model panel pattern",
        "in offline mode with no cloud dependencies.",
        "",
        "## Participants",
        "",
    ]
    for r in results:
        local_tag = "local-demo" if r.info.is_local else "cloud"
        lines.append(f"- **{r.info.name}** ({local_tag}, v{r.info.model_version}) — latency {r.latency_ms} ms")
    lines.extend([
        "",
        "## Synthesis",
        "",
        synthesis,
        f"Disagreement score: {disagreement:.2f}",
        "",
        "## Key Observations",
        "",
        "1. All three personas responded to the synthetic prompt without cloud",
        "   API keys, network access, or proprietary data.",
        "2. The roundtable pattern with critique and synthesis mirrors how an",
        "   actuarial peer review might surface differing assumptions.",
        "3. The disagreement score reflects lexical overlap, not actuarial",
        "   correctness — the demo is a product evaluation tool, not a model",
        "   accuracy benchmark.",
        "",
        "## Important Disclaimer",
        "",
        "This is a **synthetic** demonstration. No real actuarial analysis,",
        "client data, or production models were used. The responses are",
        "deterministic EchoAdapter outputs that simulate the roundtable UX.",
        "Do not interpret any response as actuarial advice or validated",
        "pricing guidance.",
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_readme_md(path: Path, scenario: str, out_dir: Path) -> None:
    lines = [
        "# ActCLI Evaluation Kit — pricing-rnd Demo",
        "",
        "## What This Is",
        "",
        "This folder contains the output of a self-contained, offline ActCLI",
        "demo. The demo simulates a multi-model roundtable discussion of a",
        "**synthetic** pricing and reinsurance scenario. No cloud API keys,",
        "network access, or proprietary data were used.",
        "",
        "## How to Inspect",
        "",
        "1. Start with `workpaper.md` for a quick overview.",
        "2. Read `prompt.md` to understand the synthetic scenario.",
        "3. Review `transcript.md` for the full round-by-round discussion.",
        "4. Check `audit.json` to confirm all participants were local/demo.",
        "",
        "## Files",
        "",
        "| File | Purpose |",
        "|------|---------|",
        "| `prompt.md` | The synthetic scenario fed to the panel |",
        "| `transcript.md` | Complete round-by-round responses from each persona |",
        "| `workpaper.md` | Evaluator-friendly summary for quick review |",
        "| `audit.json` | Machine-readable metadata (participants, timestamps, versions) |",
        "| `repro.sh` | Exact command to reproduce this run |",
        "| `README.md` | This file |",
        "",
        "## Reproducing",
        "",
        "```bash",
        "bash repro.sh",
        "```",
        "",
        "## Disclaimer",
        "",
        "This is a **synthetic** demonstration. No real actuarial analysis,",
        "client data, or production models were used. All figures, company",
        "names, and model outputs are fabricated for evaluation purposes.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_repro_sh(path: Path, scenario: str, out_dir: Path) -> None:
    lines = [
        "#!/usr/bin/env bash",
        "# Reproduce the pricing-rnd evaluation kit",
        "# Run from the ActCLI repository root.",
        "set -euo pipefail",
        "python -m actcli demo pricing-rnd --out out/evaluation/pricing-rnd",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    path.chmod(0o755)


def run_demo(scenario: str, out: str) -> None:
    if scenario != "pricing-rnd":
        console.print(
            f"[red]Unknown demo scenario: {scenario}[/red]\n"
            f"Available: pricing-rnd"
        )
        raise SystemExit(2)

    out_dir = Path(out)
    out_dir.mkdir(parents=True, exist_ok=True)

    prompt = SYNTHETIC_PROMPT_PRICING_RND
    participants = _build_demo_participants()

    console.print(Panel(
        "ActCLI Demo — pricing-rnd\n\n"
        "Running a synthetic, offline roundtable with three local-demo personas.\n"
        "No cloud keys, no network, no proprietary data.",
        title="Demo",
        border_style="cyan",
        padding=(0, 1),
    ))

    r1 = asyncio.run(
        run_round(participants, prompt, seed=42, timeout_s=30, round_index=1)
    )
    console.print(f"\nRound 1 complete — {len(r1)} responses")

    snippets: list[str] = []
    for res in r1:
        if res.text:
            text = res.text.replace("\n", " ")
            snippets.append(f"{res.info.name}: {text[:220]}")
    quoted = "\n".join(snippets)

    r2 = asyncio.run(
        run_round(
            participants,
            prompt,
            seed=42,
            timeout_s=30,
            round_index=2,
            context_snippets=quoted,
        )
    )
    console.print(f"Round 2 complete — {len(r2)} responses")

    final_results = r2
    syn, disagree = summarize(final_results)
    console.print(f"Synthesis: {syn}")
    console.print(f"Disagreement score: {disagree}")

    _write_prompt_md(out_dir / "prompt.md", prompt)
    write_transcript_md(
        out_dir / "transcript.md",
        header="Pricing R&D Demo — synthetic roundtable",
        prompt=prompt,
        results=final_results,
        synthesis=syn,
    )
    _write_workpaper_md(out_dir / "workpaper.md", prompt, final_results, syn, disagree)
    write_audit_json(
        out_dir / "audit.json",
        prompt=prompt,
        results=final_results,
        disagreement=disagree,
    )
    _write_readme_md(out_dir / "README.md", scenario, out_dir)
    _write_repro_sh(out_dir / "repro.sh", scenario, out_dir)

    console.print("\n[bold green]Demo complete.[/bold green]")
    console.print(f"Output: [cyan]{out_dir}[/cyan]")
    console.print(
        "Open [bold]README.md[/bold] → [bold]workpaper.md[/bold] → [bold]transcript.md[/bold]"
    )
