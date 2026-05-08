# Evaluation Path Initiative

Goal: make ActCLI independently tryable by a Pricing R&D actuary who saw a demo
and wants to evaluate the product safely.

The first milestone is an offline, deterministic evaluation kit command that
requires no cloud keys and emits inspectable artifacts: prompt, transcript,
workpaper, audit metadata, and reproduction instructions.

## Active Sprint

`2026-05-08_first-10-minutes-evaluation-kit`

This sprint should create:

```bash
actcli demo pricing-rnd --out out/evaluation/pricing-rnd
```

The output folder should contain:

```text
README.md
prompt.md
transcript.md
workpaper.md
audit.json
repro.sh
```

Do not widen the sprint into PyPI/Homebrew/binaries, PDFs, real provider setup,
or landing-page work. Those become follow-up sprints only after this first
offline evaluation kit validates.
