# Evaluation Path Initiative

Goal: make ActCLI independently tryable by a Pricing R&D actuary who saw a demo
and wants to evaluate the product safely.

The first milestone is an offline, deterministic evaluation kit command that
requires no cloud keys and emits inspectable artifacts: prompt, transcript,
workpaper, audit metadata, and reproduction instructions.

## First Completed Sprint

`2026-05-08_first-10-minutes-evaluation-kit`

This sprint created and validated:

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

Do not treat PyPI/Homebrew/binaries, PDFs, real provider setup, or landing-page
work as part of this completed scope. Those are follow-up sprints that should
use the validated demo command as their smoke target.

## Active Sprint

`2026-05-08_pypi-readiness-dry-run`

This sprint answers the next evaluator question: "Can I install this like a
normal Python CLI and run the demo without knowing the repo layout?"

The sprint should prove:

- build artifacts can be created locally with the declared build backend
- package metadata passes a dry-run check
- a wheel can be installed into a fresh virtual environment outside the repo
- the installed `actcli` console script can run `actcli version`,
  `actcli doctor`, and `actcli demo pricing-rnd`

It must not publish to PyPI, create a Homebrew formula, build binaries, or use
real provider credentials.
