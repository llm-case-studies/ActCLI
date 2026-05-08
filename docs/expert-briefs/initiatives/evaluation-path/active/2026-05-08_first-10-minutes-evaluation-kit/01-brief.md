# Sprint Brief - First 10 Minutes Evaluation Kit

**Initiative:** `evaluation-path`
**Sprint:** `2026-05-08_first-10-minutes-evaluation-kit`
**Target branch:** `feature/evaluation-path/first-10-minutes-evaluation-kit`
**Merge target:** `main`
**Validation branch:** `validation/evaluation-path/first-10-minutes-evaluation-kit`

## Goal

Create a self-contained ActCLI demo command for a Pricing R&D actuary who wants
to try the product after seeing a demo:

```bash
actcli demo pricing-rnd --out out/evaluation/pricing-rnd
```

When done, the command runs offline, uses deterministic demo participants, and
writes an evaluation kit with:

- `README.md` - what was run and how to inspect it
- `prompt.md` - synthetic pricing/reinsurance prompt
- `transcript.md` - model/persona responses and synthesis
- `workpaper.md` - evaluator-friendly summary suitable for review
- `audit.json` - metadata proving this was a local deterministic demo
- `repro.sh` - command to reproduce the run

## Why Now

`docs/DEPLOYMENT_AND_DISTRIBUTION_2026-05-08.md` makes the strategic point:
technical packaging matters, but the first product question is "how does a
Pricing R&D actuary safely try this in 10 minutes?" This sprint turns that
question into a concrete product surface before PyPI/Homebrew/binary packaging
work starts.

## Scope Fence

Expected touch set:

- `src/actcli/cli.py`
- `src/actcli/commands/demo.py` (new)
- `src/actcli/transcript.py` or a small helper if needed
- `tests/integration/test_demo_pricing_rnd.py` (new)
- `README.md`
- `docs/DEPLOYMENT_AND_DISTRIBUTION_2026-05-08.md` if a short follow-up note is useful

Good scope:

- A `demo` command with a `pricing-rnd` scenario argument.
- A deterministic offline run using `EchoAdapter` or equivalent local demo
  participants.
- Synthetic actuarial context that is recognizable but contains no proprietary
  data.
- An output folder that a non-developer evaluator can inspect.
- A clear console success message that tells the user which files to open next.
- Tests that parse `audit.json` and assert the expected artifact filenames.

Still out of scope:

- PyPI release, Homebrew, binaries, installers, Docker, or signing.
- Real OpenAI/Anthropic/Google/Ollama setup.
- PDF/DOCX/XLSX generation.
- Browser/landing-page work.
- Pricing calculations that imply actuarial correctness.
- Uploading proprietary data or prompting users to use proprietary data.
- Refactoring the existing roundtable engine beyond what the demo command needs.

## Acceptance Target

- `python -m pytest tests/integration/test_demo_pricing_rnd.py -q` exits 0.
- `python -m pytest tests/integration/test_chat_roundtable.py tests/unit/test_transcript.py -q`
  exits 0.
- `python -m actcli demo pricing-rnd --out "$TMPDIR/pricing-rnd"` exits 0.
- The demo output directory contains exactly the expected top-level artifacts:
  `README.md`, `prompt.md`, `transcript.md`, `workpaper.md`, `audit.json`,
  and `repro.sh`.
- `audit.json` is valid JSON and records at least three participants, all local
  or explicitly marked as demo/offline.
- `README.md`, `prompt.md`, and `workpaper.md` contain the word `synthetic`.
- `repro.sh` contains no host-specific absolute path such as `/home/alex` or
  `/Users/alex`.
- Running with cloud API env vars unset still passes.

## Honest-Failure Mode

If the existing chat/transcript path makes a clean `demo` command awkward,
record the smallest interface change you recommend in the result note. Do not
turn this sprint into packaging, PDF export, model-provider setup, or a landing
page.

## Hosts

- coding host: `Acer-HL`
- validation host: `iMacDebian`
- orchestration host: local Codex/Claude session on the user's primary
  workstation

## Host Safety

No protected production services are involved in this sprint. Standard host
safety still applies:

- do not commit host-local Claude/Codex memory
- do not install project dependencies into system Python
- do not use real API keys or proprietary data
- do not contact cloud providers during the demo tests
- keep all probes local to the repo checkout
