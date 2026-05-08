# Merge Note - First 10 Minutes Evaluation Kit

## Branches

- working branch: `feature/evaluation-path/first-10-minutes-evaluation-kit`
- merge target: `main`
- validation branch: `validation/evaluation-path/first-10-minutes-evaluation-kit`

## Validation Outcome

- implementation host: `Acer-HL`
- validation host: `iMacDebian`
- tested product commit: `be32010`
- implementation commits:
  - `f459fe3` - `docs: seed first evaluation-path sprint`
  - `24b8aa2` - `docs: add evaluation-path handoff breadcrumbs`
  - `364b657` - `feat(demo): add offline pricing-rnd evaluation kit command`
  - `be32010` - `docs: fill result template with commit hash`
- validation evidence commits:
  - original validation branch: `bb5c65f`
  - validation PR: `#26`
  - squash-merged onto feature branch: `45bb04e`
- verdict: **PASS**
- result path:
  `testing/initiatives/evaluation-path/2026-05-08_first-10-minutes-evaluation-kit/result.md`

## Evidence Summary

- `python -m pytest tests/integration/test_demo_pricing_rnd.py -q`:
  2 passed.
- `python -m pytest tests/integration/test_chat_roundtable.py tests/unit/test_transcript.py -q`:
  2 passed.
- Direct demo run created all six expected files:
  `README.md`, `audit.json`, `prompt.md`, `repro.sh`,
  `transcript.md`, and `workpaper.md`.
- Artifact safety checks passed: 3 local/demo participants, synthetic
  markers present, and no `/home/alex` or `/Users/alex` paths in
  `repro.sh`.
- Validation ran on iMacDebian with Python 3.13.5 in
  `/home/alex/.venvs/actcli-python`.

## Findings

- `actcli demo pricing-rnd --out out/evaluation/pricing-rnd` is now
  the first concrete "try ActCLI safely" path.
- The demo is intentionally offline and synthetic. It requires no real
  API keys, no proprietary files, and no network/model-provider setup.
- The implementer fixed two pre-existing import/syntax issues in
  `factory.py` and `rounds.py` to unblock the demo/regression tests.
- Validation evidence landed in the correct nested testing directory.
  One assertion-only evidence file was empty despite `result.md`
  recording PASS; future validation probes should print assertion
  context before exiting so evidence files are self-explanatory.

## Decision

- merge to `main`: yes
- close sprint: yes
- split follow-up: yes

## Follow-Up

- `pypi-readiness-dry-run`: prove the package can build/install from a
  clean artifact and run `actcli demo pricing-rnd`.
- `landing-demo-script`: turn the validated evaluation kit into a
  5-minute demo/video outline for the first public-facing touch.
