# Evaluation Path Initiative

Goal: make ActCLI independently tryable by a Pricing R&D actuary who saw a demo
and wants to evaluate the product safely.

The first milestone is an offline, deterministic evaluation kit command that
requires no cloud keys and emits inspectable artifacts: prompt, transcript,
workpaper, audit metadata, and reproduction instructions.

## Completed Sprints

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

`2026-05-08_pypi-readiness-dry-run`

This sprint answered the next evaluator question: "Can I install this like a
normal Python CLI and run the demo without knowing the repo layout?"

The sprint proved:

- build artifacts can be created locally with the declared build backend
- package metadata passes a dry-run check
- a wheel can be installed into a fresh virtual environment outside the repo
- the installed `actcli` console script can run `actcli version`,
  `actcli doctor`, and `actcli demo pricing-rnd`

Verdict: PASS with findings. The non-blocking finding is that generated demo
`repro.sh` still uses `python -m actcli` and repo-root assumptions even though
the installed `actcli` console script works.

## Queued Follow-Ups

- `portable-demo-repro-script`: make generated demo reproduction instructions
  match installed-package usage before a real PyPI release.
- `landing-demo-script`: turn the validated evaluation kit and package dry-run
  into a 5-minute demo/video outline.
